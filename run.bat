@echo off
:: Change directory to the folder where this batch file is located
cd /d "%~dp0"

echo =====================================
echo   Saark Enterprise Management System
echo =====================================
echo.
echo Choose Application Type:
echo   1. Desktop Application (main.py)
echo   2. Web Application (saarkweb.py)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo =====================================
    echo   Starting Desktop Application
    echo =====================================
    echo.
    echo Access: Desktop GUI Application
    echo.
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
) else if "%choice%"=="2" (
    echo.
    echo =====================================
    echo   Starting Web Application
    echo =====================================
    echo.
    echo Username: a
    echo Password: a
    echo.
    echo Local Access: http://127.0.0.1:5000
    echo Network Access: http://192.168.1.116:5000
    echo.
    echo Press CTRL+C to stop the web server
    echo =====================================
    echo.
    
    set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
    
   if exist "%PROJECT_PYTHON%" (
    "%PROJECT_PYTHON%" "%~dp0saarkweb.py"
) else (
    python "%~dp0saarkweb.py"
)    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Web server closed unexpectedly.
        pause
    )
) else (
    echo.
    echo Invalid choice. Please enter 1 or 2.
    pause
)
