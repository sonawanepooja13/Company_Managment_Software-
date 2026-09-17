@echo off
:: Change directory to the folder where this batch file is located
cd /d "%~dp0"

echo =====================================
echo   Saark Enterprise Management System
echo =====================================
echo.
echo Starting Desktop Application...
echo.
set "APP_AUTO_LOGIN=1"
set "APP_USERNAME=admin"
set "APP_PASSWORD=admin123"
set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"

if exist "%PROJECT_PYTHON%" (
    "%PROJECT_PYTHON%" "%~dp0main.py"
) else (
    python "%~dp0main.py"
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Desktop application closed unexpectedly.
    pause
)
