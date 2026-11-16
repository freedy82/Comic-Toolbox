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
rem Exclude the application's root setting.ini, bookmarks.ini and colorize_models tree.
rem The local copies remain in the build folder for your own use.
rem Replace an existing ZIP only after the new archive has finished writing.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command ^
    "$ErrorActionPreference = 'Stop'; $source = [System.IO.Path]::GetFullPath($env:COMIC_TOOLBOX_ZIP_SOURCE).TrimEnd([System.IO.Path]::DirectorySeparatorChar); $prefix = $source + [System.IO.Path]::DirectorySeparatorChar; $rootEntry = [System.IO.Path]::GetFileName($source) + '/'; $output = $env:COMIC_TOOLBOX_ZIP_OUTPUT; $temporary = $output + '.' + [guid]::NewGuid().ToString('N') + '.tmp'; try { Add-Type -AssemblyName System.IO.Compression.FileSystem; $archive = [System.IO.Compression.ZipFile]::Open($temporary, [System.IO.Compression.ZipArchiveMode]::Create); try { $archive.CreateEntry($rootEntry) | Out-Null; foreach ($directory in [System.IO.Directory]::EnumerateDirectories($source, '*', [System.IO.SearchOption]::AllDirectories)) { $relative = $directory.Substring($prefix.Length).Replace('\', '/'); if ($relative -eq 'colorize_models' -or $relative.StartsWith('colorize_models/', [System.StringComparison]::OrdinalIgnoreCase)) { continue }; $archive.CreateEntry($rootEntry + $relative + '/') | Out-Null }; foreach ($file in [System.IO.Directory]::EnumerateFiles($source, '*', [System.IO.SearchOption]::AllDirectories)) { $relative = $file.Substring($prefix.Length).Replace('\', '/'); if ($relative -in @('setting.ini', 'bookmarks.ini') -or $relative.StartsWith('colorize_models/', [System.StringComparison]::OrdinalIgnoreCase)) { continue }; [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file, $rootEntry + $relative, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null } } finally { $archive.Dispose() }; Move-Item -LiteralPath $temporary -Destination $output -Force } catch { Write-Error $_; exit 1 } finally { if ([System.IO.File]::Exists($temporary)) { [System.IO.File]::Delete($temporary) } }"
if errorlevel 1 goto failed

echo.
echo ZIP created: %COMIC_TOOLBOX_ZIP_OUTPUT%
echo Excluded local files and folders: setting.ini, bookmarks.ini and colorize_models.
echo.
pause
exit /b 0

:failed
echo.
echo Packaging failed. See the error above.
echo.
pause
exit /b 1
