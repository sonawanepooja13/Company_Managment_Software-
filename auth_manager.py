
#auth manager file
import csv
import hashlib
import os
from datetime import datetime
import openpyxl
from openpyxl import Workbook

import config

# Resolve data-file locations to the writable data directory.
# In frozen (PyInstaller) mode DATA_DIR is a per-user location; in
# development it is the project root, so relative behaviour is preserved.
DATA_DIR = getattr(config, "DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
PO_EXCEL_FILE = os.path.join(DATA_DIR, "Purchase_Orders.xlsx")

# Complete CSV Header Schema supporting all modules and sub-window actions.
HEADERS = [
    "username",
    "password_hash",
    "full_name",
    "mobile_number",
    "designation",
    "role",
    "account_status",
    "allow_price",
    "allow_material",
    "allow_crm",
    "allow_sales",
    "allow_production",
    "allow_project_management",
    "allow_task_manager",
    "allow_qc_qa",
    "allow_panel_mfg",
    "allow_accounts",
    "allow_hr",
    "allow_purchase",
    "allow_stores",
    "allow_maintenance",
    "allow_rnd",
    "allow_asset_management",
    "allow_ehs",
    "allow_pos_ecommerce",
    "allow_rnd_design_cad",
    "allow_rnd_prototyping_testing",
    "allow_rnd_bom",
    "allow_rnd_eco",
    "allow_it",
    "allow_customer_service",
    "allow_legal",
    "allow_admin_dept",
    "allow_supply_chain",
    "allow_admin",
    "allow_inward_entry",
    "allow_outward_document",
    "allow_vendor_registration",
    "allow_cheque_details",
    "allow_it_dashboard",
    "allow_it_security",
    "allow_it_helpdesk",
    "allow_it_assets",
    "allow_it_iam",
]
PERMISSION_HEADERS = HEADERS[7:]

WINDOW_PERMISSION_LABELS = {
    "allow_price": "Price List Search",
    "allow_material": "Material & Labor Calculator",
    "allow_crm": "Customer CRM & Leads",
    "allow_sales": "Sales & Marketing",
    "allow_production": "Production Process",
    "allow_project_management": "Project Management / Professional Services",
    "allow_task_manager": "Task Manager",
    "allow_qc_qa": "Quality Control (QC) / Quality Assurance (QA)",
    "allow_panel_mfg": "Panel Manufacturing",
    "allow_accounts": "Accounts & Finance",
    "allow_hr": "HR Module",
    "allow_purchase": "Purchase / Procurement",
    "allow_stores": "Stores / Warehouse",
    "allow_maintenance": "Maintenance",
    "allow_rnd": "R&D / Engineering",
    "allow_asset_management": "Asset Management / Fixed Assets",
    "allow_ehs": "Environment, Health, and Safety (EHS) / Risk Management",
    "allow_pos_ecommerce": "Point of Sale (POS) / E-Commerce",
    "allow_rnd_design_cad": "R&D -> Design & CAD",
    "allow_rnd_prototyping_testing": "R&D -> Prototyping & Testing",
    "allow_rnd_bom": "R&D -> Bill of Materials (BOM)",
    "allow_rnd_eco": "R&D -> Engineering Change Orders (ECO)",
    "allow_it": "IT Workspace",
    "allow_customer_service": "Customer Service",
    "allow_legal": "Legal & Compliance",
    "allow_admin_dept": "Administration",
    "allow_supply_chain": "Supply Chain / Logistics",
    "allow_admin": "Admin Settings",
    "allow_inward_entry": "Accounts -> New Inward Invoice",
    "allow_outward_document": "Accounts -> New Outward Document",
    "allow_vendor_registration": "Accounts -> Vendor Registration",
    "allow_cheque_details": "Accounts -> Cheque Details",
    "allow_it_dashboard": "IT -> Overview",
    "allow_it_security": "IT -> Security & Compliance",
    "allow_it_helpdesk": "IT -> Helpdesk",
    "allow_it_assets": "IT -> Assets",
    "allow_it_iam": "IT -> IAM",
}


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_user_file_exists():
    """Creates users.csv with default full-access admin if missing,
    or migrates existing headers if old fields are missing.
    """
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(HEADERS)
            # Default admin row with all permissions set to True
            admin_row = [
                "a",
                hash_password("a"),
                "System Admin",
                "",
                "Administrator",
                "Admin",
            ] + ["Active"] + ["True"] * (len(HEADERS) - 7)
            writer.writerow(admin_row)
    else:
        try:
            with open(
                USERS_FILE, mode="r", newline="", encoding="utf-8"
            ) as file:
                reader = csv.reader(file)
                existing_headers = next(reader, [])

            if set(HEADERS) - set(existing_headers):
                users = load_users()
                save_users(users)
        except Exception as e:
            print(f"Error during users.csv migration: {e}")


def load_users():
    """Reads all users, their profiles, and permissions from CSV."""
    if not os.path.exists(USERS_FILE):
        ensure_user_file_exists()

    users = []
    with open(USERS_FILE, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["full_name"] = row.get("full_name", "")
            row["mobile_number"] = row.get("mobile_number", "")
            row["designation"] = row.get("designation", "")
            row["role"] = row.get("role", "User")
            row["account_status"] = row.get("account_status", "Active") or "Active"

            # Dynamically parse all permission keys as booleans
            for h in PERMISSION_HEADERS:
                default_val = "True" if h in ["allow_price", "allow_material"] else "False"
                row[h] = str(row.get(h, default_val)).lower() == "true"

            users.append(row)
    return users


def save_users(users_list):
    """Overwrites user configuration in CSV file with standard headers."""
    with open(USERS_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)
        for u in users_list:
            row_data = [
                u.get("username", ""),
                u.get("password_hash", ""),
                u.get("full_name", ""),
                u.get("mobile_number", ""),
                u.get("designation", ""),
                u.get("role", "User"),
                u.get("account_status", "Active"),
            ]
            # Append values for all permission keys dynamically
            for h in PERMISSION_HEADERS:
                default_val = True if h in ["allow_price", "allow_material"] else False
                row_data.append(str(u.get(h, default_val)))
            
            writer.writerow(row_data)


def verify_login(username, password):
    """Verifies credentials and returns user record if valid."""
    users = load_users()
    pwd_hash = hash_password(password)

    for u in users:
        if u["username"] == username and u["password_hash"] == pwd_hash:
            return True, u

    return False, None


def add_or_update_user(
    username,
    password=None,
    full_name="",
    mobile_number="",
    designation="",
    role="User",
    **kwargs
):
    """Adds a new user or updates credentials, profile info, and dynamic permissions via kwargs."""
    users = load_users()
    updated = False

    for u in users:
        if u["username"] == username:
            if password:
                u["password_hash"] = hash_password(password)
            u["full_name"] = full_name
            u["mobile_number"] = mobile_number
            u["designation"] = designation
            u["role"] = role
            u.setdefault("account_status", "Active")
            
            # Update all permissions passed through kwargs
            for k, v in kwargs.items():
                if k in HEADERS:
                    u[k] = v
            updated = True
            break

    if not updated:
        new_user = {
            "username": username,
            "password_hash": hash_password(password) if password else "",
            "full_name": full_name,
            "mobile_number": mobile_number,
            "designation": designation,
            "role": role,
        }
        # Set permissions for new user from kwargs or use smart defaults
        for h in PERMISSION_HEADERS:
            default_val = True if h in ["allow_price", "allow_material"] else False
            new_user[h] = kwargs.get(h, default_val)

        users.append(new_user)

    save_users(users)


def delete_user(username):
    """Deletes a user account by username."""
    users = load_users()
    users = [u for u in users if u["username"] != username]
    save_users(users)


# --- PURCHASE ORDER EXCEL LOGGING ---


def log_to_purchase_order_excel(
    user_data, po_number="", total_amount="", remarks=""
):
    """Appends Purchase Order details alongside user metadata into Purchase_Orders.xlsx."""
    excel_headers = [
        "Timestamp",
        "PO Number",
        "Username",
        "Full Name",
        "Mobile Number",
        "Designation",
        "Role",
        "Total Amount",
        "Remarks",
    ]

    # Create file and sheet with headers if missing
    if not os.path.exists(PO_EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "Purchase Orders"
        ws.append(excel_headers)
        wb.save(PO_EXCEL_FILE)

    wb = openpyxl.load_workbook(PO_EXCEL_FILE)
    ws = wb.active

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row_data = [
        timestamp,
        po_number,
        user_data.get("username", ""),
        user_data.get("full_name", ""),
        user_data.get("mobile_number", ""),
        user_data.get("designation", ""),
        user_data.get("role", ""),
        total_amount,
        remarks,
    ]

    ws.append(row_data)
    wb.save(PO_EXCEL_FILE)
