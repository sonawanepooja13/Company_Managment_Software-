@echo off
:: Change directory to the folder where this batch file is located
cd /d "%~dp0"

echo Building Booster Pump Control Panel .exe file...
echo.

:: Set Python path based on your environment
set "PROJECT_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
set "PROJECT_SCRIPTS=%LocalAppData%\Programs\Python\Python314\Scripts"

if exist "%PROJECT_PYTHON%" (
    echo Installing/Updating PyInstaller...
    "%PROJECT_PYTHON%" -m pip install --upgrade pyinstaller
    
    echo.
    echo Starting build process...
    "%PROJECT_SCRIPTS%\pyinstaller.exe" --noconfirm --onefile --windowed --name "BoosterPumpControlPanel" main.py
) else (
    echo Python not found at default path, trying global python...
    pip install --upgrade pyinstaller
    pyinstaller --noconfirm --onefile --windowed --name "BoosterPumpControlPanel" main.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed.
    pause
) else (
    echo.
    echo [SUCCESS] Build completed! Check the 'dist' folder for your .exe file.
    pause
)