@echo off
chcp 65001 > NUL
setlocal

if not exist .venv (
    echo .venv not found. creating...
    python -m venv .venv
)

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

echo.
echo Checking virtual environment Python...
if not exist "%VENV_PYTHON%" (
    echo.
    echo Virtual environment Python not found at: %VENV_PYTHON%
    exit /b 1
)

echo.
echo Python from environment:
"%VENV_PYTHON%" --version

echo.
echo Install dependencies from file requirements.txt...
"%VENV_PYTHON%" -m pip install -r requirements.txt > NUL 2>&1

echo.
echo Launching...
cls
"%VENV_PYTHON%" main.py

pause
endlocal
