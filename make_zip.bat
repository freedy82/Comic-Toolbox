@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Edit this version when preparing a new release; do not include the v prefix.
set "VERSION=0.9.2"

set "COMIC_TOOLBOX_ZIP_SOURCE=%~dp0dist\ComicToolbox"
set "COMIC_TOOLBOX_ZIP_OUTPUT=%~dp0dist\ComicToolbox_windows_x64.v%VERSION%.zip"

if not exist "%COMIC_TOOLBOX_ZIP_SOURCE%\ComicToolbox.exe" (
    echo The built ComicToolbox folder was not found. Run make_exe.bat first.
    goto failed
)

echo Packaging ComicToolbox version %VERSION%...
rem .NET includes hidden files and supports large ZIP archives. Include the
rem ComicToolbox folder itself, with both EXEs and the complete _internal tree.
rem Replace an existing ZIP only after the new archive has finished writing.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command ^
    "$ErrorActionPreference = 'Stop'; $source = $env:COMIC_TOOLBOX_ZIP_SOURCE; $output = $env:COMIC_TOOLBOX_ZIP_OUTPUT; $temporary = $output + '.' + [guid]::NewGuid().ToString('N') + '.tmp'; try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory($source, $temporary, [System.IO.Compression.CompressionLevel]::Optimal, $true); Move-Item -LiteralPath $temporary -Destination $output -Force } catch { Write-Error $_; exit 1 } finally { if ([System.IO.File]::Exists($temporary)) { [System.IO.File]::Delete($temporary) } }"
if errorlevel 1 goto failed

echo.
echo ZIP created: %COMIC_TOOLBOX_ZIP_OUTPUT%
echo.
pause
exit /b 0

:failed
echo.
echo Packaging failed. See the error above.
echo.
pause
exit /b 1
