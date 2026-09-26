import os
import sys

# ---------------------------------------------------------------------------
# Path resolution for frozen (PyInstaller) and development environments
# ---------------------------------------------------------------------------

def _get_bundle_dir():
    """Return the directory containing bundled resources.

    In a PyInstaller one-file build, sys._MEIPRESS points to the temporary
    extraction directory.  In development, it is simply the project root.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys._MEIPASS in onefile mode; in onedir it is
        # not set, so fall back to the executable's directory.
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return meipass
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _get_data_dir():
    """Return the writable data directory.

    In frozen mode we copy bundled data into a per-user directory so that
    the temp _MEIPASS extraction (which is read-only) is never written to.
    """
    if getattr(sys, "frozen", False):
        app_name = "SaarkEnterprise"
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            base = os.environ.get("HOME", os.path.expanduser("~"))
        return os.path.join(base, app_name)
    return os.path.dirname(os.path.abspath(__file__))


def _copy_bundled_data(src, dst):
    """Copy bundled data files from the PyInstaller temp dir to the writable
    data directory on first launch.  Existing files are never overwritten so
    user edits persist across runs."""
    import shutil

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif os.path.isfile(s) and not os.path.exists(d):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)


# Base directory where config.py is located (frozen bundle in pyinstaller)
SCRIPT_DIR = _get_bundle_dir()
DATA_DIR = _get_data_dir()

if getattr(sys, "frozen", False) and os.path.isdir(os.path.join(SCRIPT_DIR, "csv_data")):
    _copy_bundled_data(SCRIPT_DIR, DATA_DIR)

# Script directory is now also the writable data directory so that every
# module referencing config.SCRIPT_DIR gets the writable, data-populated path.
SCRIPT_DIR = DATA_DIR


# Dedicated folder path for CSV storage (writable)
CSV_DIR = os.path.join(DATA_DIR, "csv_data")
HR_DIR = os.path.join(CSV_DIR, "HR")
# One CSV file per customer holding that customer's quotation records
QUOTATION_DIR = os.path.join(CSV_DIR, "quotation")

# Ensure the 'csv_data', 'csv_data/HR' and 'csv_data/quotation' folders exist on startup
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(HR_DIR, exist_ok=True)
os.makedirs(QUOTATION_DIR, exist_ok=True)

# CSV File Absolute Paths inside 'csv_data'
PRODUCTS_CSV = os.path.join(CSV_DIR, "products.csv")
CUSTOMERS_CSV = os.path.join(CSV_DIR, "customers.csv")
CUSTOMERS_DETAILED_CSV = os.path.join(CSV_DIR, "customers_detailed.csv")
CUSTOMER_SERVICES_CSV = os.path.join(CSV_DIR, "customer_services.csv")
BOM_EXPORT_CSV = os.path.join(CSV_DIR, "generated_bom_export.csv")
MATERIAL_COMPANIES_CSV = os.path.join(CSV_DIR, "material_companies.csv")
PRODUCT_PRICE_CALCULATOR_CSV = os.path.join(
    CSV_DIR, "Product Price Calculator", "price_list.csv"
)
PRICE_LIST_CSV = PRODUCT_PRICE_CALCULATOR_CSV
PANEL_MATERIAL_LIST_DIR = os.path.join(CSV_DIR, "panel material list")
os.makedirs(PANEL_MATERIAL_LIST_DIR, exist_ok=True)

# Supply Chain & Logistics CSV Files
SUPPLIERS_CSV = os.path.join(CSV_DIR, "suppliers.csv")
DEMAND_FORECAST_CSV = os.path.join(CSV_DIR, "demand_forecast.csv")
PRODUCTION_ORDERS_CSV = os.path.join(CSV_DIR, "production_orders.csv")
RISK_MANAGEMENT_CSV = os.path.join(CSV_DIR, "risk_management.csv")
INVENTORY_CSV = os.path.join(CSV_DIR, "inventory.csv")
SHIPMENTS_CSV = os.path.join(CSV_DIR, "shipments.csv")
ORDERS_CSV = os.path.join(CSV_DIR, "orders.csv")
RETURNS_CSV = os.path.join(CSV_DIR, "returns.csv")

# Legal & Compliance CSV Files
INTERNAL_DOCS_CSV = os.path.join(CSV_DIR, "internal_documents.csv")
EXTERNAL_DOCS_CSV = os.path.join(CSV_DIR, "external_documents.csv")
DATA_PROTECTION_CSV = os.path.join(CSV_DIR, "data_protection.csv")
CONTRACTS_CSV = os.path.join(CSV_DIR, "contracts.csv")
EMPLOYEE_AGREEMENTS_CSV = os.path.join(CSV_DIR, "employee_agreements.csv")
DOCUMENT_TEMPLATES_CSV = os.path.join(CSV_DIR, "document_templates.csv")

# Company Maintenance (CMMS/EAM) CSV Files
ASSETS_CSV = os.path.join(CSV_DIR, "assets.csv")
WORK_ORDERS_CSV = os.path.join(CSV_DIR, "work_orders.csv")
PM_SCHEDULES_CSV = os.path.join(CSV_DIR, "pm_schedules.csv")
SPARE_PARTS_CSV = os.path.join(CSV_DIR, "spare_parts.csv")
COMPLIANCE_CSV = os.path.join(CSV_DIR, "compliance_records.csv")
MAINTENANCE_VENDORS_CSV = os.path.join(CSV_DIR, "maintenance_vendors.csv")
IOT_SENSORS_CSV = os.path.join(CSV_DIR, "iot_sensors.csv")

# IT Workspace CSV Files
IT_PROVISIONING_CSV = os.path.join(CSV_DIR, "it_provisioning.csv")
IT_SECURITY_CSV = os.path.join(CSV_DIR, "it_security.csv")
IT_TICKETS_CSV = os.path.join(CSV_DIR, "it_tickets.csv")
IT_ASSETS_CSV = os.path.join(CSV_DIR, "it_assets.csv")
IT_IAM_CSV = os.path.join(CSV_DIR, "it_iam.csv")

# R&D/Engineering CSV Files
PDLC_PRODUCTS_CSV = os.path.join(CSV_DIR, "pdlc_products.csv")
RND_TASKS_CSV = os.path.join(CSV_DIR, "rnd_tasks.csv")
SPRINTS_CSV = os.path.join(CSV_DIR, "sprints.csv")
HARDWARE_CSV = os.path.join(CSV_DIR, "hardware.csv")
RND_COMPONENTS_CSV = os.path.join(CSV_DIR, "rnd_components.csv")
RND_RISKS_CSV = os.path.join(CSV_DIR, "rnd_risks.csv")
RND_TEAM_CSV = os.path.join(CSV_DIR, "rnd_team.csv")
COMPLIANCE_CERTS_CSV = os.path.join(CSV_DIR, "compliance_certs.csv")

# Warehouse Management CSV Files
WAREHOUSE_ITEMS_CSV = os.path.join(CSV_DIR, "warehouse_items.csv")
WAREHOUSE_SERIAL_CSV = os.path.join(CSV_DIR, "warehouse_serial.csv")
WAREHOUSE_LOCATION_CSV = os.path.join(CSV_DIR, "warehouse_location.csv")
WAREHOUSE_TRANSACTIONS_CSV = os.path.join(CSV_DIR, "warehouse_transactions.csv")
WAREHOUSE_AUDIT_CSV = os.path.join(CSV_DIR, "warehouse_audit.csv")

# CSV File Headers
PRODUCTS_HEADERS = [
    "pump_type",
    "pump_current",
    "switch_gear_make",
    "num_pumps",
    "num_vfd",
    "vfd_make",
    "bypass",
    "panel_type",
    "panel_size",
    "panel_class",
    "main_incomer",
    "olr_required",
    "indicator_light",
    "price",
]

CUSTOMERS_HEADERS = [
    "customer_name",
    "percentage",
]

CUSTOMERS_DETAILED_HEADERS = [
    "company_name",
    "website",
    "contact_number",
    "address",
    "location",
    "note",
    "call_conversion_time",
    "company_data_sent",
    "enquiry_received",
    "communication_details",
    "meeting_schedule_time",
    "meeting_agenda",
    "meeting_completed_details",
    "country",
]