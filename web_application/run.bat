@echo off
echo Starting Enterprise Web Application...
echo Username: a
echo Password: a
echo.
echo Access at: http://127.0.0.1:5000
echo Network access: http://10.238.204.66:5000
echo.
cd /d "%~dp0"
python app.py
pause