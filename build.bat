@echo off
setlocal enabledelayedexpansion
:: ===========================================================================
::  Saark Enterprise Management System  -  Full Project EXE Builder
::  ---------------------------------------------------------------------------
::  Generates a single-file Windows executable:
::        dist\CompanyManagementSoftware.exe
::
::  Just double-click this file.  It will:
::    1. Locate a usable Python interpreter
::    2. Install / update every build + runtime dependency
::    3. Clean old build artifacts
::    4. Package the WHOLE project (all modules + csv_data) into one .exe
::    5. Report the finished executable location
:: ===========================================================================

cd /d "%~dp0"

echo ===========================================================================
echo   Saark Enterprise Management System
echo   Building full-project Windows executable (.exe)
echo ===========================================================================
echo.

:: ---------------------------------------------------------------------------
:: 1. Locate Python
:: ---------------------------------------------------------------------------
set "PYTHON_EXE="

:: Preferred: the specific interpreter used to develop this project
set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
if exist "%PROJECT_PYTHON%" set "PYTHON_EXE=%PROJECT_PYTHON%"

:: Fallback 1: Windows "py" launcher
if not defined PYTHON_EXE (
    py -3 --version >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_EXE=py -3"
)

:: Fallback 2: python on PATH
if not defined PYTHON_EXE (
    python --version >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python was not found on this machine.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         and tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%v in ('%PYTHON_EXE% --version 2^>^&1') do set "PY_VERSION=%%v"
echo Using Python: !PY_VERSION!
echo Location      : %PYTHON_EXE%
echo.

:: ---------------------------------------------------------------------------
:: 2. Upgrade pip and install dependencies
:: ---------------------------------------------------------------------------
echo [1/5] Upgrading pip, setuptools and wheel ...
%PYTHON_EXE% -m pip install --upgrade pip setuptools wheel
if !errorlevel! neq 0 (
    echo [WARNING] pip upgrade failed - continuing with existing pip.
)
echo.

echo [2/5] Installing build + runtime dependencies ...
%PYTHON_EXE% -m pip install --upgrade ^
    pyinstaller ^
    openpyxl ^
    reportlab ^
    Pillow ^
    tkcalendar ^
    pandas ^
    paho-mqtt

if !errorlevel! neq 0 (
    echo [ERROR] Dependency installation failed. Check your internet connection.
    echo.
    pause
    exit /b 1
)

:: If a requirements.txt exists, honour it as well
if exist "requirements.txt" (
    echo.
    echo       Applying requirements.txt ...
    %PYTHON_EXE% -m pip install -r requirements.txt
)
echo.

:: ---------------------------------------------------------------------------
:: 3. Clean previous build artifacts
:: ---------------------------------------------------------------------------
echo [3/5] Cleaning previous build artifacts ...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
echo.

:: ---------------------------------------------------------------------------
:: 4. Build the executable from the spec file
:: ---------------------------------------------------------------------------
echo [4/5] Building executable (this can take several minutes) ...
echo.

if exist "CompanyManagementSoftware.spec" (
    %PYTHON_EXE% -m PyInstaller --noconfirm --clean CompanyManagementSoftware.spec
) else (
    echo [WARNING] CompanyManagementSoftware.spec not found - using command-line build.
    %PYTHON_EXE% -m PyInstaller --noconfirm --clean --onefile --windowed ^
        --name "CompanyManagementSoftware" ^
        --add-data "csv_data;csv_data" ^
        --hidden-import tabs ^
        --hidden-import tabs.admin_tab ^
        --hidden-import tabs.crm_tab ^
        --hidden-import tabs.material_tab ^
        --hidden-import tabs.price_tab ^
        --hidden-import task_manager ^
        main.py
)

if !errorlevel! neq 0 (
    echo.
    echo ===========================================================================
    echo   [ERROR] BUILD FAILED.
    echo   Scroll up to view the PyInstaller error messages.
    echo ===========================================================================
    echo.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: 5. Verify and report
:: ---------------------------------------------------------------------------
echo.
echo [5/5] Verifying output ...
set "EXE_PATH=dist\CompanyManagementSoftware.exe"

:: The freshly written file can take a moment to appear / be released,
:: so wait for it (up to ~30 seconds) before reporting.
set "EXE_FOUND="
for /l %%i in (1,1,15) do (
    if exist "%EXE_PATH%" (
        set "EXE_FOUND=1"
        goto :exe_ready
    )
    timeout /t 2 /nobreak >nul
)

:exe_ready
if defined EXE_FOUND (
    for %%A in ("%EXE_PATH%") do set "EXE_SIZE=%%~zA"
    set /a EXE_MB=!EXE_SIZE! / 1048576
    echo.
    echo ===========================================================================
    echo   [SUCCESS] BUILD COMPLETE
    echo ===========================================================================
    echo   Executable : %CD%\%EXE_PATH%
    echo   Size       : ~!EXE_MB! MB
    echo.
    echo   Installation on a client computer:
    echo     1. Copy CompanyManagementSoftware.exe to the client PC
    echo     2. Double-click it to run (no Python required)
    echo     3. User data is stored in:
    echo        %%LOCALAPPDATA%%\SaarkEnterprise
    echo ===========================================================================
    echo.
    echo Opening the dist folder ...
    start "" "dist"
) else (
    echo [WARNING] The .exe was not found at %EXE_PATH%.
    echo           Check the 'dist' folder manually.
)

echo.
pause
endlocal
