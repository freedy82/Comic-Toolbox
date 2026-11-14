@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1

rem Reuse the project's interpreter, or create its virtual environment.
if exist ".venv\Scripts\python.exe" goto install
echo Creating the build environment...
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv ".venv"
if errorlevel 1 goto failed
goto install

:use_python
python -m venv ".venv"
if errorlevel 1 goto failed

:install
echo Installing project and build dependencies...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade "PyInstaller>=6.22.3,<7" pyinstaller-hooks-contrib
if errorlevel 1 goto failed

echo.
echo Cleaning the previous build and application output...
set "COMIC_TOOLBOX_BUILD_ROOT=%CD%"
rem Resolve and check both targets before recursive deletion. Only generated
rem directories are removed; release ZIPs elsewhere in dist are preserved.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command ^
    "$ErrorActionPreference = 'Stop'; $root = [System.IO.Path]::GetFullPath($env:COMIC_TOOLBOX_BUILD_ROOT); $prefix = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar; $targets = @('build\pyinstaller', 'dist\ComicToolbox'); $resolved = @(); foreach ($relative in $targets) { $target = [System.IO.Path]::GetFullPath((Join-Path $root $relative)); if (-not $target.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup target is outside the project.' }; if (Test-Path -LiteralPath $target) { $item = Get-Item -LiteralPath $target -Force; if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw ('Refusing to clean a linked directory: ' + $target) }; $resolved += $target } }; foreach ($target in $resolved) { Write-Host ('Removing ' + $target); Remove-Item -LiteralPath $target -Recurse -Force }"
if errorlevel 1 goto failed

echo.
echo Building Comic Toolbox and its verification browser...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean ^
    --distpath "dist" --workpath "build\pyinstaller" ^
    "build_support\ComicToolbox.spec"
if errorlevel 1 goto failed

echo.
echo Build complete: %CD%\dist\ComicToolbox\ComicToolbox.exe
echo The browser helper, supporting DLLs, Python packages and resources are grouped in _internal.
echo Unused QML, video, Tkinter, debug resources and extra Qt languages are excluded.
echo Distribute the ENTIRE dist\ComicToolbox folder, including _internal.
echo Personal settings, bookmarks, downloaded comics and AI model packages are not copied.
echo Node.js, Tesseract and Real-CUGAN/Real-ESRGAN remain optional external tools.
echo.
popd
pause
exit /b 0

:failed
echo.
echo Build failed. See the error above.
echo Use a supported Python version and close any running copy of dist\ComicToolbox.
echo.
popd
pause
exit /b 1
