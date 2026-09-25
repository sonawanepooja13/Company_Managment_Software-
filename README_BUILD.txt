How to build a Windows executable (.exe) for this project

Prerequisites
- Windows machine with Python 3.8+ installed and available as `python` on PATH.
- Recommended: run from an Administrator command prompt for install permissions.

Quick build (recommended)
1. Open Command Prompt and change directory to the project root:
   cd "D:\python code\porduct selector"

2. Run the provided batch script to create a venv, install build dependencies and produce a single-file executable:
   build_exe.bat

What the script does
- Creates/uses a local virtual environment (.venv)
- Installs packages from requirements.txt (PyInstaller and openpyxl)
- Runs PyInstaller to create a single-file GUI executable named CompanyManagementSoftware.exe
- Includes the project_management_exports folder as data so exported files are available in the packaged app's runtime directory

Where to find the executable
- After a successful run look in the dist folder:
  dist\CompanyManagementSoftware.exe

Notes & troubleshooting
- The build may be large because PyInstaller bundles Python runtime and dependencies.
- If you need a console for debugging remove --windowed from the pyinstaller command in build_exe.bat.
- If the app requires additional data files (images, config files), add them to the --add-data list in build_exe.bat. On Windows use the syntax "source_path;dest_path".
- To debug missing module errors, run PyInstaller once with the console enabled and inspect the log for missing imports.
- If you prefer a one-time system install of PyInstaller and openpyxl instead of the venv, you can run:
    pip install pyinstaller openpyxl
    pyinstaller --onefile --windowed --name "CompanyManagementSoftware" --add-data "project_management_exports;project_management_exports" main.py

If you want, I can:
- Run the build here (I may encounter environment limitations). I can try but earlier PowerShell init failed; the batch script uses cmd which may work.
- Create a signed installer (requires code-signing certificate and additional steps).
- Produce a portable folder build instead of a single-file exe (sometimes more reliable).

Tell me which of those you'd like me to do next.