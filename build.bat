@echo off
:: ===========================================================
::  Saark Enterprise Management System - Build Script
::  Produces a single-file Windows executable (CompanyManagementSoftware.exe)
:: ===========================================================
cd /d "%~dp0"

echo =====================================
echo   Saark Enterprise Management System
echo   Building Windows executable (.exe)
echo =====================================
echo.

:: Set Python path based on your environment
set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
set "PROJECT_SCRIPTS=%LocalAppData%\Programs\Python\Python314\Scripts"

if exist "%PROJECT_PYTHON%" (
    echo Installing/Updating build dependencies...
    "%PROJECT_PYTHON%" -m pip install --upgrade pyinstaller openpyxl reportlab Pillow tkcalendar

    echo.
    echo Starting build process (this may take several minutes)...
    "%PROJECT_SCRIPTS%\pyinstaller.exe" --noconfirm --clean CompanyManagementSoftware.spec
) else (
    echo Python not found at default path, trying global python...
    pip install --upgrade pyinstaller openpyxl reportlab Pillow tkcalendar
    pyinstaller --noconfirm --clean CompanyManagementSoftware.spec
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] Build completed!
    echo The executable is located at:
    echo   dist\CompanyManagementSoftware.exe
    echo.
    echo Double-click CompanyManagementSoftware.exe to run.
    pause
)
