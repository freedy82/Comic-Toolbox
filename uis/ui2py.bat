@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0.."
if errorlevel 1 exit /b 1

rem Prefer the same interpreter and PyQt6 version as the application.
set "UI2PY_PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%UI2PY_PYTHON%" set "UI2PY_PYTHON=python"

echo Converting Qt Designer UI files with PyQt6...
"%UI2PY_PYTHON%" "build_support\compile_ui.py"
set "UI2PY_RESULT=%ERRORLEVEL%"
if not "%UI2PY_RESULT%"=="0" (
    echo.
    echo UI conversion failed. See the error above.
)

popd
if /I not "%~1"=="--no-pause" pause
exit /b %UI2PY_RESULT%
