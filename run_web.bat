@echo off
echo =====================================
echo   Saark Web Server Startup
echo =====================================
echo.
echo Starting Web Application Server...
echo.
echo Access Information:
echo   Local: http://127.0.0.1:5000
echo   Network: http://192.168.1.116:5000
echo.
echo Login Credentials:
echo   Username: a
echo   Password: a
echo.
echo Press CTRL+C to stop the server
echo =====================================
echo.

cd /d "%~dp0"

set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"

if exist "%PROJECT_PYTHON%" (
    "%PROJECT_PYTHON%" saarkweb.py
) else (
    python saarkweb.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Web server closed unexpectedly.
    pause
)