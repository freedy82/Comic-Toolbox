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
rem Migrate old x64 environments to DirectML. Runtime variants share files,
rem so remove conflicting packages before reinstalling the selected backend.
".venv\Scripts\python.exe" -c "import platform, sys; from importlib.metadata import distributions; names = {d.metadata['Name'].lower() for d in distributions()}; sys.exit(0 if platform.machine() == 'AMD64' and names.intersection({'onnxruntime', 'onnxruntime-gpu'}) else 1)"
if errorlevel 1 goto requirements
".venv\Scripts\python.exe" -m pip uninstall -y onnxruntime onnxruntime-gpu
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --force-reinstall --no-deps "onnxruntime-directml>=1.24.4,<2"
if errorlevel 1 goto failed

:requirements
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
echo Copying local settings and bookmarks into the application folder...
for %%F in (bookmarks.ini setting.ini) do (
    if exist "%%F" (
        copy /Y "%%F" "dist\ComicToolbox\%%F" >nul
        if errorlevel 1 goto failed
        echo Copied %%F.
    ) else (
        echo %%F not found in the project root; skipped.
    )
)

echo.
echo Copying local Colorize models into the application folder...
if exist "colorize_models\" (
    robocopy "colorize_models" "dist\ComicToolbox\colorize_models" /E /XJ /R:1 /W:1 /XF *.part /NFL /NDL /NJH /NJS /NP
    if errorlevel 8 goto failed
    echo Copied colorize_models.
) else (
    echo colorize_models not found in the project root; skipped.
)

echo.
echo Build complete: %CD%\dist\ComicToolbox\ComicToolbox.exe
echo The browser helper, supporting DLLs, Python packages and resources are grouped in _internal.
echo Unused QML, video, Tkinter, debug resources and extra Qt languages are excluded.
echo Use make_zip.bat for distribution; it excludes setting.ini, bookmarks.ini and colorize_models.
echo Keep the entire application folder, including _internal, together.
echo Local Colorize models are included beside the EXE when available.
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
