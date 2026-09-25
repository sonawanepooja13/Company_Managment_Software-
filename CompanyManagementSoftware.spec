# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Saark Enterprise Management System (Company Management Software).

Build with:
    pyinstaller --noconfirm CompanyManagementSoftware.spec
"""

import os
from PyInstaller.utils.hooks import collect_submodules


def collect_data(project_root):
    """Collect all non-Python data files that the application needs at runtime."""
    datas = []

    def _add_dir(src_dir):
        if not os.path.isdir(src_dir):
            return
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if f == ".DS_Store":
                    continue
                rel_root = os.path.relpath(root, project_root)
                datas.append((os.path.join(root, f), rel_root))

    def _add_root_file(filename):
        if os.path.isfile(os.path.join(project_root, filename)):
            datas.append((filename, "."))

    # Core data directory (all CSVs, subdirectories, etc.)
    _add_dir(os.path.join(project_root, "csv_data"))

    # Root-level shipped data files
    for f in [
        "price_list_clean.csv",
        "users.csv",
        "admin_audit_logs.csv",
        "admin_settings.csv",
        "enquiry_status.csv",
        "projects.db",
        "product_maneger.txt",
        "cloud_settings.example.json",
    ]:
        _add_root_file(f)

    # Empty output directories (created at runtime, but bundle as empty dirs
    # so the directory structure exists for apps that expect them).
    for d in [
        "project_management_exports",
        "Customer_Photos",
        "cheque_photos",
        "inward_invoices",
        "outward_documents",
        "reports",
    ]:
        full = os.path.join(project_root, d)
        if os.path.isdir(full) and not os.listdir(full):
            datas.append((full, d))

    return datas


proj_root = os.path.abspath(".")
datas = collect_data(proj_root)

# Hidden imports for modules loaded dynamically inside functions
hiddenimports = [
    "tabs",
    "tabs.admin_tab",
    "tabs.crm_tab",
    "tabs.material_tab",
    "tabs.price_tab",
    "task_manager",
]

# OpenPyXL uses a namespace package that PyInstaller sometimes misses
for sub in collect_submodules("openpyxl"):
    if sub not in hiddenimports:
        hiddenimports.append(sub)

a = Analysis(
    ["main.py"],
    pathex=[proj_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CompanyManagementSoftware",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile=True,
)
