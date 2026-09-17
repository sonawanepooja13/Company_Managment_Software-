import csv
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

import auth_manager
import config
import accounts_finance
import bom_engine
import panel_manufacturing
import production_window
import hr_window
from outward_window import OutwardWindow
from vendor_registration import VendorRegistrationWindow
import supply_chain_logistics
import legal_compliance
import maintenance
import it_workspace
import rnd_engineering
import customer_service
import warehouse_management
import qc_qa
import help as app_help
import crm_engine
import subprocess
import datetime


def speak_greeting(username):
    """Speak a time-appropriate greeting including the user's name using Windows TTS (PowerShell).

    Falls back silently on any error so it never blocks the UI.
    """
    try:
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Sanitize single quotes for PowerShell single-quoted string
        safe_name = str(username).replace("'", "''")
        # Include an introductory phrase after the personalized greeting
        message = f"{greeting}, {safe_name}. Welcome to Saark Operating System"
        ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{message}')"

        # Fire-and-forget so the GUI isn't blocked; suppress output
        subprocess.Popen([
            "powershell",
            "-NoProfile",
            "-Command",
            ps_cmd,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Do not raise — audio is a nice-to-have
        return


class RnDPermissionsWindow(tk.Toplevel):
    """Separate window for R&D granular permissions configuration."""

    def __init__(self, parent, module_vars):
        super().__init__(parent)
        self.parent = parent
        self.module_vars = module_vars
        self.title("🔬 R&D Granular Permissions Configuration")
        self.geometry("500x450")
        self.minsize(400, 350)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()

    def create_widgets(self):
        """Create R&D permissions interface."""
        ttk.Label(self, text="R&D Engineering Granular Access Control", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Apply Changes", command=self.apply_changes).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="❌ Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Create scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=15)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # R&D Permissions Header
        ttk.Label(scrollable_frame, text="R&D Module - Tab Access Control", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 5))

        # R&D granular permissions
        rnd_permissions = [
            ("allow_rnd_pdlc", "📊 Product Development (PDLC)"),
            ("allow_rnd_projects", "📋 Projects & Tasks"),
            ("allow_rnd_sprints", "🔄 Sprint Management"),
            ("allow_rnd_hardware", "🔧 Hardware & Prototypes"),
            ("allow_rnd_components", "⚙️ Components & Supply"),
            ("allow_rnd_risk", "⚠️ Risk Management"),
            ("allow_rnd_team", "👥 Team & Resource Allocation"),
            ("allow_rnd_compliance", "📋 Compliance & Certification"),
        ]
        rnd_sub_permissions = [
            ("allow_rnd_design_cad", "Design & CAD"),
            ("allow_rnd_prototyping_testing", "Prototyping & Testing"),
            ("allow_rnd_bom", "Bill of Materials (BOM)"),
            ("allow_rnd_eco", "Engineering Change Orders (ECO)"),
        ]

        for key, label_text in rnd_permissions:
            var = self.module_vars.get(key, tk.BooleanVar(value=False))
            ttk.Checkbutton(
                scrollable_frame, text=label_text, variable=var
            ).pack(anchor="w", pady=4, padx=5)

        ttk.Label(
            scrollable_frame,
            text="R&D Module - Sub-parts / Windows",
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(12, 5), padx=5)

        for key, label_text in rnd_sub_permissions:
            var = self.module_vars.get(key, tk.BooleanVar(value=False))
            ttk.Checkbutton(
                scrollable_frame, text=label_text, variable=var
            ).pack(anchor="w", pady=3, padx=20)

        # Utility buttons
        utility_frame = ttk.Frame(scrollable_frame)
        utility_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(
            utility_frame,
            text="📂 Open All R&D",
            command=self.open_all_rnd,
        ).pack(side="left", padx=5)

        ttk.Button(
            utility_frame,
            text="📁 Close All R&D",
            command=self.close_all_rnd,
        ).pack(side="left", padx=5)

        ttk.Button(
            utility_frame,
            text="⚙️ Default R&D",
            command=self.set_default_rnd,
        ).pack(side="left", padx=5)

    def open_all_rnd(self):
        """Open all R&D permissions."""
        rnd_keys = ["allow_rnd_pdlc", "allow_rnd_projects", "allow_rnd_sprints", 
                   "allow_rnd_hardware", "allow_rnd_components", "allow_rnd_risk", 
                   "allow_rnd_team", "allow_rnd_compliance"]
        for key in rnd_keys:
            if key in self.module_vars:
                self.module_vars[key].set(True)

    def close_all_rnd(self):
        """Close all R&D permissions."""
        rnd_keys = ["allow_rnd_pdlc", "allow_rnd_projects", "allow_rnd_sprints", 
                   "allow_rnd_hardware", "allow_rnd_components", "allow_rnd_risk", 
                   "allow_rnd_team", "allow_rnd_compliance"]
        for key in rnd_keys:
            if key in self.module_vars:
                self.module_vars[key].set(False)

    def set_default_rnd(self):
        """Set default R&D permissions."""
        rnd_keys = ["allow_rnd_pdlc", "allow_rnd_projects", "allow_rnd_sprints", 
                   "allow_rnd_hardware", "allow_rnd_components", "allow_rnd_risk", 
                   "allow_rnd_team", "allow_rnd_compliance"]
        for key in rnd_keys:
            if key in self.module_vars:
                self.module_vars[key].set(False)

    def apply_changes(self):
        """Apply R&D permission changes."""
        messagebox.showinfo("Success", "R&D permissions updated successfully!", parent=self)
        self.destroy()


class UserAccessControlFrame(ttk.Frame):
    """Integrated User Access & Permission Control Frame for side-by-side workspace layout."""

    def __init__(self, parent, main_app):
        super().__init__(parent, padding=15)
        self.main_app = main_app

        self.users_cache = []
        self.selected_user = None
        self.module_vars = {}
        self.subwindow_vars = {}

        self.setup_ui()
        self.load_accounts_dropdown()

    def setup_ui(self):
        # Master-Detail Layout: Left Side (Account Selection & Credentials), Right Side (Permissions)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Title Header across top
        title_lbl = ttk.Label(
            self,
            text="User Account & Module Access Control Panel",
            font=("Helvetica", 14, "bold"),
        )
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # --- LEFT COLUMN: Dropdown & Credentials ---
        left_panel = ttk.Frame(self)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.rowconfigure(2, weight=1)
        left_panel.columnconfigure(0, weight=1)

        # Dropdown Selection Frame
        select_frame = ttk.Frame(left_panel)
        select_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            select_frame,
            text="Select Account to Modify:",
            font=("Helvetica", 9, "bold"),
        ).pack(anchor="w", pady=(0, 2))

        self.combo_accounts = ttk.Combobox(
            select_frame, state="readonly", font=("Helvetica", 10)
        )
        self.combo_accounts.pack(fill="x")
        self.combo_accounts.bind(
            "<<ComboboxSelected>>", self.on_account_selected
        )

        # Account Credentials Frame
        cred_frame = ttk.LabelFrame(
            left_panel, text=" Account Credentials ", padding=12
        )
        cred_frame.pack(fill="x", pady=(0, 10))

        fields = [
            ("Username:", "ent_username", False),
            ("Full Name:", "ent_full_name", False),
            ("Mobile Number:", "ent_mobile", False),
            ("New Password:", "ent_password", True),
        ]

        for idx, (label_text, attr_name, is_password) in enumerate(fields):
            ttk.Label(cred_frame, text=label_text).grid(
                row=idx, column=0, sticky="w", pady=6, padx=5
            )
            entry = ttk.Entry(cred_frame, show="*" if is_password else "", width=30)
            entry.grid(row=idx, column=1, sticky="ew", pady=6, padx=5)
            setattr(self, attr_name, entry)

        # Role Designation Dropdown
        ttk.Label(cred_frame, text="Role Designation:").grid(
            row=4, column=0, sticky="w", pady=6, padx=5
        )
        self.combo_role = ttk.Combobox(
            cred_frame, state="readonly", values=["User", "Admin"], width=28
        )
        self.combo_role.set("User")
        self.combo_role.grid(row=4, column=1, sticky="ew", pady=6, padx=5)
        
        cred_frame.columnconfigure(1, weight=1)

        # Action Buttons Bottom Frame (inside left column)
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="💾 Save / Apply",
            command=self.save_user_details,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=4)

        ttk.Button(
            btn_frame, 
            text="🗑️ Delete User", 
            command=self.delete_user_account
        ).pack(side="right", fill="x", expand=True, padx=(5, 0), ipady=4)

        # Add save/delete buttons at the bottom of permissions section as well
        perm_btn_frame = ttk.Frame(self.perm_scrollable_inner)
        perm_btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            perm_btn_frame,
            text="💾 Save Permissions",
            command=self.save_user_details,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=4)

        ttk.Button(
            perm_btn_frame, 
            text="🗑️ Delete User", 
            command=self.delete_user_account
        ).pack(side="right", fill="x", expand=True, padx=(5, 0), ipady=4)

        # Add utility buttons for permissions
        utility_frame = ttk.Frame(self.perm_scrollable_inner)
        utility_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(
            utility_frame,
            text="📂 Open All",
            command=self.open_all_permissions,
        ).pack(side="left", padx=5)

        ttk.Button(
            utility_frame,
            text="📁 Close All",
            command=self.close_all_permissions,
        ).pack(side="left", padx=5)

        ttk.Button(
            utility_frame,
            text="⚙️ Default",
            command=self.set_default_permissions,
        ).pack(side="left", padx=5)

        # R&D Granular Permissions Button
        rnd_frame = ttk.Frame(self.perm_scrollable_inner)
        rnd_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            rnd_frame,
            text="🔬 R&D Granular Permissions:",
            font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=5)

        ttk.Button(
            rnd_frame,
            text="⚙️ Configure R&D Access",
            command=self.open_rnd_permissions_window,
        ).pack(side="left", padx=5)


        # --- RIGHT COLUMN: Scrollable Permissions ---
        right_panel = ttk.LabelFrame(
            self, text=" Module & Tab Access Permissions ", padding=10
        )
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        perm_canvas = tk.Canvas(right_panel, borderwidth=0, highlightthickness=0)
        perm_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=perm_canvas.yview)
        self.perm_scrollable_inner = ttk.Frame(perm_canvas, padding=5)

        self.perm_scrollable_inner.bind(
            "<Configure>",
            lambda e: perm_canvas.configure(scrollregion=perm_canvas.bbox("all"))
        )
        perm_canvas.create_window((0, 0), window=self.perm_scrollable_inner, anchor="nw")
        perm_canvas.configure(yscrollcommand=perm_scrollbar.set)

        perm_canvas.pack(side="left", fill="both", expand=True)
        perm_scrollbar.pack(side="right", fill="y")

        # Map all modules matching dashboard options
        self.defined_modules = [
            ("allow_price", "Price List Search Tab"),
            ("allow_material", "Material & Labor Calculator Tab"),
            ("allow_crm", "Customer CRM & Leads Tab"),
            ("allow_sales", "📈 Sales & Marketing Module"),
            ("allow_production", "🏭 Production Process Module"),
            ("allow_project_management", "📁 Project Management / Professional Services"),
            ("allow_task_manager", "Task Manager"),
            ("allow_qc_qa", "✅ Quality Control (QC) / Quality Assurance (QA)"),
            ("allow_panel_mfg", "🔧 Panel Manufacturing Module"),
            ("allow_accounts", "💰 Accounts & Finance Module"),
            ("allow_hr", "👥 HR (Human Resources) Module"),
            ("allow_purchase", "🛒 Purchase / Procurement Module"),
            ("allow_stores", "📦 Stores / Warehouse Module"),
            ("allow_maintenance", "🛠️ Maintenance Module"),
            ("allow_rnd", "🔬 R&D / Engineering Module"),
            ("allow_asset_management", "🏢 Asset Management / Fixed Assets"),
            ("allow_ehs", "🛡️ EHS / Risk Management"),
            ("allow_pos_ecommerce", "🛍️ Point of Sale (POS) / E-Commerce"),
            ("allow_it", "💻 IT Module"),
            ("allow_customer_service", "🎧 Customer Service Module"),
            ("allow_legal", "⚖️ Legal & Compliance Module"),
            ("allow_admin_dept", "📋 Administration Module"),
            ("allow_supply_chain", "🚚 Supply Chain / Logistics Module"),
            ("allow_admin", "⚙️ Admin Settings"),
        ]

        # R&D specific granular permissions
        self.rnd_permissions = [
            ("allow_rnd_pdlc", "📊 Product Development (PDLC)"),
            ("allow_rnd_projects", "📋 Projects & Tasks"),
            ("allow_rnd_sprints", "🔄 Sprint Management"),
            ("allow_rnd_hardware", "🔧 Hardware & Prototypes"),
            ("allow_rnd_components", "⚙️ Components & Supply"),
            ("allow_rnd_risk", "⚠️ Risk Management"),
            ("allow_rnd_team", "👥 Team & Resource Allocation"),
            ("allow_rnd_compliance", "📋 Compliance & Certification"),
        ]
        self.rnd_sub_permissions = [
            ("allow_rnd_design_cad", "Design & CAD"),
            ("allow_rnd_prototyping_testing", "Prototyping & Testing"),
            ("allow_rnd_bom", "Bill of Materials (BOM)"),
            ("allow_rnd_eco", "Engineering Change Orders (ECO)"),
        ]

        for key, label_text in self.defined_modules:
            var = tk.BooleanVar(value=False)
            self.module_vars[key] = var
            ttk.Checkbutton(
                self.perm_scrollable_inner, text=label_text, variable=var
            ).pack(anchor="w", pady=4, padx=5)

        self.rnd_sub_frame = ttk.Frame(self.perm_scrollable_inner)
        self.rnd_sub_frame.pack(fill="x", padx=(20, 5), pady=(0, 4))
        for key, label_text in self.rnd_sub_permissions:
            var = tk.BooleanVar(value=False)
            self.module_vars[key] = var
            ttk.Checkbutton(
                self.rnd_sub_frame, text=label_text, variable=var
            ).pack(anchor="w", pady=2, padx=10)

        # Initialize R&D granular permission variables
        for key, _ in self.rnd_permissions:
            var = tk.BooleanVar(value=False)
            self.module_vars[key] = var

        if "allow_rnd" in self.module_vars:
            self.module_vars["allow_rnd"].trace_add("write", self.on_rnd_toggle)
        self.update_rnd_sub_visibility()

    def load_accounts_dropdown(self):
        """Loads accounts into dropdown."""
        self.users_cache = auth_manager.load_users()
        dropdown_list = ["-- Create New User --"]

        for u in self.users_cache:
            username = u.get("username", "")
            full_name = u.get("full_name", "")
            mobile = u.get("mobile_number", "")

            details = [d for d in (full_name, mobile) if d]
            detail_str = f" ({' - '.join(details)})" if details else ""
            dropdown_list.append(f"{username}{detail_str}")

        self.combo_accounts["values"] = dropdown_list
        self.combo_accounts.set(dropdown_list[0])
        self.clear_fields()

    def on_account_selected(self, event):
        """Populates form when an account is selected."""
        selected_text = self.combo_accounts.get()

        if selected_text == "-- Create New User --":
            self.selected_user = None
            self.clear_fields()
            self.ent_username.config(state="normal")
            return

        username = selected_text.split(" (")[0].strip()
        user_data = next(
            (u for u in self.users_cache if u["username"] == username), None
        )

        if user_data:
            self.selected_user = user_data
            self.ent_username.config(state="normal")
            self.ent_username.delete(0, tk.END)
            self.ent_username.insert(0, user_data.get("username", ""))
            self.ent_username.config(state="disabled")

            self.ent_full_name.delete(0, tk.END)
            self.ent_full_name.insert(0, user_data.get("full_name", ""))

            self.ent_mobile.delete(0, tk.END)
            self.ent_mobile.insert(0, user_data.get("mobile_number", ""))

            self.ent_password.delete(0, tk.END)
            self.combo_role.set(user_data.get("role", "User"))

            for key, _ in self.defined_modules:
                default_val = True if key in ["allow_price", "allow_material"] else False
                self.module_vars[key].set(user_data.get(key, default_val))

            # Load R&D granular permissions
            for key, _ in self.rnd_permissions:
                self.module_vars[key].set(user_data.get(key, False))

            for key, _ in self.rnd_sub_permissions:
                self.module_vars[key].set(user_data.get(key, False))

            self.update_rnd_sub_visibility()

    def clear_fields(self):
        """Resets field values."""
        self.ent_username.config(state="normal")
        self.ent_username.delete(0, tk.END)
        self.ent_full_name.delete(0, tk.END)
        self.ent_mobile.delete(0, tk.END)
        self.ent_password.delete(0, tk.END)
        self.combo_role.set("User")

        for key, _ in self.defined_modules:
            default_val = True if key in ["allow_price", "allow_material"] else False
            self.module_vars[key].set(default_val)

        # Reset R&D granular permissions
        for key, _ in self.rnd_permissions:
            self.module_vars[key].set(False)
        for key, _ in self.rnd_sub_permissions:
            self.module_vars[key].set(False)
        self.update_rnd_sub_visibility()

    def update_rnd_sub_visibility(self):
        """Reveal nested R&D sub-permissions only when the parent module is enabled."""
        if "allow_rnd" not in self.module_vars:
            return
        if self.module_vars["allow_rnd"].get():
            self.rnd_sub_frame.pack(fill="x", padx=(20, 5), pady=(0, 4))
        else:
            self.rnd_sub_frame.pack_forget()

    def on_rnd_toggle(self, *args):
        """Keep the parent R&D checkbox synchronized with its sub-part permissions."""
        if "allow_rnd" not in self.module_vars:
            return

        parent_checked = self.module_vars["allow_rnd"].get()
        if parent_checked:
            for key, _ in self.rnd_sub_permissions:
                if key in self.module_vars and not self.module_vars[key].get():
                    self.module_vars[key].set(True)
        else:
            for key, _ in self.rnd_sub_permissions:
                if key in self.module_vars:
                    self.module_vars[key].set(False)

        self.update_rnd_sub_visibility()

    def open_all_permissions(self):
        """Open all permissions."""
        for key, var in self.module_vars.items():
            var.set(True)
        self.update_rnd_sub_visibility()

    def close_all_permissions(self):
        """Close all permissions."""
        for key, var in self.module_vars.items():
            var.set(False)
        self.update_rnd_sub_visibility()

    def set_default_permissions(self):
        """Set default permissions."""
        for key, var in self.module_vars.items():
            default_val = True if key in ["allow_price", "allow_material"] else False
            var.set(default_val)
        self.update_rnd_sub_visibility()

    def open_rnd_permissions_window(self):
        """Open separate window for R&D granular permissions."""
        RnDPermissionsWindow(self, self.module_vars)

    def save_user_details(self):
        """Saves or updates account in database."""
        username = self.ent_username.get().strip()
        full_name = self.ent_full_name.get().strip()
        mobile_number = self.ent_mobile.get().strip()
        password = self.ent_password.get().strip()
        role = self.combo_role.get()

        if not username:
            messagebox.showwarning("Input Error", "Username is required.", parent=self)
            return

        if not self.selected_user and not password:
            messagebox.showwarning("Input Error", "Password is required for new accounts.", parent=self)
            return

        perm_data = {key: var.get() for key, var in self.module_vars.items()}

        auth_manager.add_or_update_user(
            username=username,
            password=password if password else None,
            full_name=full_name,
            mobile_number=mobile_number,
            designation="",
            role=role,
            **perm_data
        )

        messagebox.showinfo("Success", f"User account '{username}' saved successfully!", parent=self)
        self.load_accounts_dropdown()

    def delete_user_account(self):
        """Deletes user account."""
        if not self.selected_user:
            messagebox.showwarning("Selection Error", "Please select an account to delete.", parent=self)
            return

        username = self.selected_user["username"]

        if username == "admin":
            messagebox.showerror("Action Denied", "Default 'admin' account cannot be deleted.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?", parent=self):
            auth_manager.delete_user(username)
            messagebox.showinfo("Deleted", f"User '{username}' deleted.", parent=self)
            self.load_accounts_dropdown()


class MainApp:
    """Master Application Window for Booster Pump Control System."""

    def __init__(self, root):
        self.root = root
        self.root.title("Company Manegement Software")

        bom_engine.ensure_files_exist()
        auth_manager.ensure_user_file_exists()

        self.user_data = None
        self.content_frame = None
        self.show_login_screen()

    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_main_window_size(self):
        try:
            if self.root.state() == "normal":
                self.root.state("zoomed")
            else:
                self.root.state("normal")
        except Exception:
            self.root.geometry("420x280")

    def show_login_screen(self):
        self.root.title("Company Manegement Software")
        self.root.configure(bg="#efefef")
        self.root.geometry("420x280")
        self.root.minsize(420, 280)
        self.root.resizable(True, True)

        self.content_container = tk.Frame(self.root, bg="#f3f3f3")
        self.content_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.login_frame = ttk.Frame(self.content_container, padding=25)
        self.login_frame.pack(fill="both", expand=True)

        ttk.Label(
            self.login_frame,
            text="System Login",
            font=("Helvetica", 12, "bold"),
        ).pack(pady=(0, 15))

        ttk.Label(self.login_frame, text="Username:").pack(anchor="w")
        self.entry_user = ttk.Entry(self.login_frame)
        self.entry_user.pack(fill="x", pady=(0, 10))
        self.entry_user.focus_set()

        ttk.Label(self.login_frame, text="Password:").pack(anchor="w")
        self.entry_pwd = ttk.Entry(self.login_frame, show="*")
        self.entry_pwd.pack(fill="x", pady=(0, 15))
        self.entry_pwd.bind("<Return>", lambda event: self.handle_login())

        btn_login = ttk.Button(
            self.login_frame, text="Login", command=self.handle_login
        )
        btn_login.pack(fill="x")

        if os.environ.get("APP_AUTO_LOGIN") == "1":
            self.entry_user.insert(0, os.environ.get("APP_USERNAME", ""))
            self.entry_pwd.insert(0, os.environ.get("APP_PASSWORD", ""))
            self.root.after(100, self.handle_login)

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pwd.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Login Error", "Please enter both username and password."
            )
            return

        success, user_data = auth_manager.verify_login(username, password)

        if success:
            self.user_data = user_data

            # Speak a friendly greeting (non-blocking)
            try:
                speak_greeting(self.user_data.get("username", "User"))
            except Exception:
                pass

            if hasattr(self, "title_bar"):
                self.title_bar.destroy()
            if hasattr(self, "content_container"):
                self.content_container.destroy()
            if hasattr(self, "login_frame"):
                self.login_frame.destroy()
            self.build_main_dashboard()
            if os.environ.get("APP_OPEN_BOOSTER_PANEL") == "1":
                self.root.after(
                    250,
                    lambda: self.show_category_content("Booster Pump Control Panel"),
                )
        else:
            messagebox.showerror(
                "Access Denied",
                "Invalid username or password.\n\nPlease check your credentials.",
            )
            self.entry_pwd.delete(0, tk.END)
            self.entry_pwd.focus_set()

    def clear_workspace(self):
        if hasattr(self, "content_frame") and self.content_frame:
            self.content_frame.destroy()

        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill="both", expand=True)

    def create_welcome_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=34,
            font=("Helvetica", 11, "bold"),
            foreground="#17324d",
            background="#e8f3f8",
            activeforeground="#ffffff",
            activebackground="#1f6f9f",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#7aa8bf",
            highlightcolor="#2f789f",
            padx=16,
            pady=12,
                justify="center",
                anchor="center",
                wraplength=280,
            cursor="hand2",
        )
        button.bind(
            "<Enter>",
            lambda event: event.widget.configure(
                background="#d9eef9",
                highlightbackground="#2f789f",
            ),
        )
        button.bind(
            "<Leave>",
            lambda event: event.widget.configure(
                background="#e8f3f8",
                highlightbackground="#7aa8bf",
            ),
        )
        return button

    def build_main_dashboard(self):
        self.center_window(1050, 780)
        self.root.resizable(True, True)
        # Use the complete desktop workspace while keeping normal Windows controls.
        self.root.state("zoomed")

        username = self.user_data.get("username", "User")
        role = self.user_data.get("role", "User")
        self.root.title(
            f"Company Manegement Software — Logged in: {username} ({role})"
        )

        self.clear_workspace()

        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=20)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        welcome_frame = ttk.Frame(scrollable_frame)
        welcome_frame.pack(expand=True, fill="x")

        ttk.Label(
            welcome_frame,
            text=f"Welcome, {username}!",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=(0, 5))

        ttk.Label(
            welcome_frame,
            text="Select a workspace module to proceed:",
            font=("Helvetica", 11),
        ).pack(pady=(0, 15))

        btn_frame = ttk.Frame(welcome_frame)
        btn_frame.pack(fill="x")

        all_modules = [
            ("allow_sales", "📈 Sales & Marketing", self.show_sales_marketing_view),
            ("allow_production", "🏭 Production Process", self.show_production_view),
            ("allow_project_management", "📁 Project Management / Professional Services", lambda: self.show_generic_department_view("Project Management / Professional Services")),
            ("allow_task_manager", "✅ Task Manager", self.show_task_manager_view),
            ("allow_qc_qa", "✅ Quality Control (QC) / Quality Assurance (QA)", lambda: self.show_generic_department_view("Quality Control (QC) / Quality Assurance (QA)")),
            ("allow_panel_mfg", "🔧 Panel Manufacturing", self.show_panel_manufacturing_view),
            ("allow_accounts", "💰 Accounts & Finance", self.show_accounts_finance_view),
            ("allow_hr", "👥 HR (Human Resources)", self.show_hr_view),
            ("allow_purchase", "🛒 Purchase / Procurement", self.show_purchase_procurement_view),
            ("allow_stores", "📦 Stores / Warehouse", self.show_warehouse_view),
            ("allow_maintenance", "🛠️ Maintenance", lambda: self.show_generic_department_view("Maintenance")),
            ("allow_rnd", "🔬 R&D / Engineering", lambda: self.show_generic_department_view("R&D / Engineering")),
            ("allow_asset_management", "🏢 Asset Management / Fixed Assets", lambda: self.show_generic_department_view("Asset Management / Fixed Assets")),
            ("allow_ehs", "🛡️ EHS / Risk Management", lambda: self.show_generic_department_view("Environment, Health, and Safety (EHS) / Risk Management")),
            ("allow_pos_ecommerce", "🛍️ Point of Sale (POS) / E-Commerce", lambda: self.show_generic_department_view("Point of Sale (POS) / E-Commerce")),
            ("allow_it", "💻 IT", lambda: self.show_generic_department_view("IT")),
            ("allow_customer_service", "🎧 Customer Service", self.show_customer_service_view),
            ("allow_legal", "⚖️ Legal & Compliance", lambda: self.show_generic_department_view("Legal & Compliance")),
            ("allow_admin_dept", "📋 Administration", lambda: self.show_generic_department_view("Administration")),
            ("allow_supply_chain", "🚚 Supply Chain / Logistics", lambda: self.show_generic_department_view("Supply Chain / Logistics")),
        ]

        is_admin = (self.user_data.get("role") == "Admin")

        module_grid = ttk.Frame(btn_frame)
        module_grid.pack(anchor="e")

        for index, (perm_key, label, cmd) in enumerate(all_modules):
            if not (is_admin or self.user_data.get(perm_key, False)):
                continue

            row = index // 2
            col = index % 2
            self.create_welcome_button(module_grid, label, cmd).grid(
                row=row, column=col, padx=10, pady=6, sticky="ew"
            )

        module_grid.columnconfigure(0, weight=1)
        module_grid.columnconfigure(1, weight=1)

        if is_admin or self.user_data.get("allow_admin", False):
            self.create_welcome_button(
                module_grid,
                "⚙️ Admin Settings",
                self.show_admin_settings_view,
            ).grid(
                row=(len(all_modules) // 2) + 1,
                column=0,
                padx=10,
                pady=6,
                sticky="ew",
            )

    def create_back_header(self, title_text, back_command=None, back_text="⬅ Back to Menu"):
        header_frame = ttk.Frame(self.content_frame, padding=8)
        header_frame.pack(fill="x", side="top")

        btn_back = ttk.Button(
            header_frame,
            text=back_text,
            command=back_command or self.build_main_dashboard,
        )
        btn_back.pack(side="left", padx=5)

        ttk.Button(
            header_frame,
            text="❓ Help",
            command=lambda: app_help.open_help_window(self.root, title_text),
        ).pack(side="left", padx=5)

        ttk.Label(
            header_frame, text=title_text, font=("Helvetica", 12, "bold")
        ).pack(side="left", padx=15)

        ttk.Separator(self.content_frame, orient="horizontal").pack(
            fill="x", pady=(0, 5)
        )

    def user_has_permission(self, permission_key, default_value=False):
        if not self.user_data:
            return False
        if self.user_data.get("role") == "Admin":
            return True
        return bool(self.user_data.get(permission_key, default_value))

    def switch_tab(self, tab_index):
        if hasattr(self, "sales_notebook") and self.sales_notebook is not None:
            try:
                self.sales_notebook.select(tab_index)
                
                # If switching to Material Calculator tab (index 1), update with Price List data
                if tab_index == 1 and hasattr(self, 'material_calculator_data'):
                    # Use after to ensure tab is fully loaded before updating
                    self.root.after(100, self._update_material_calculator)
            except Exception:
                pass
    
    def _update_material_calculator(self):
        """Update Material Calculator with Price List data."""
        try:
            if hasattr(self, 'material_tab_instance') and self.material_tab_instance:
                self.material_tab_instance.update_price_tab_data(self.material_calculator_data)
        except Exception:
            pass

    def show_sales_marketing_view(self):
        if not self.user_has_permission("allow_sales", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Sales & Marketing.", parent=self.root)
            return
        try:
            self.clear_workspace()
            self.create_back_header("Sales & Marketing Module", self.build_main_dashboard, "⬅ Back to Dashboard")
            self.show_product_category_selector()

        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Sales module:\n{e}"
            )

    def show_product_category_selector(self):
        """Show product category selector for Sales & Marketing module."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Back header
        header_frame = ttk.Frame(self.content_frame, padding=8)
        header_frame.pack(fill="x", side="top")
        ttk.Button(
            header_frame,
            text="⬅ Back to Dashboard",
            command=self.build_main_dashboard,
        ).pack(side="left", padx=5)
        ttk.Label(
            header_frame,
            text="Sales & Marketing Module",
            font=("Helvetica", 12, "bold"),
        ).pack(side="left", padx=15)
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=(0, 5))

        container = ttk.Frame(self.content_frame, padding=40)
        container.pack(expand=True)

        ttk.Label(
            container, text="Select Product Category", font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))

        category_frame = ttk.Frame(container)
        category_frame.pack()

        categories = [
            "Customer CRM & Leads",
            "Saark Product Sector",
            "Booster Pump Control Panel", 
            "STP Panel",
            "Water Meter",
            "BMS"
        ]

        for category in categories:
            button_label = (
                "Booster Pump Control Panel Desing,Materil & Price Calculator"
                if category == "Booster Pump Control Panel"
                else category
            )
            btn = self.create_welcome_button(
                category_frame,
                button_label,
                lambda cat=category: self.show_category_content(cat),
            )
            btn.pack(pady=10)

    def show_saark_product_sector(self):
        """Display the Product Sector entry form used by Sales & Marketing."""
        self.clear_workspace()
        self.create_back_header(
            "Sales & Marketing - Saark Product Sector",
            self.show_product_category_selector,
            "â¬… Back to Categories",
        )

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        sector_tab = ttk.Frame(notebook, padding=20)
        product_tab = ttk.Frame(notebook)
        promotion_tab = ttk.Frame(notebook, padding=16)
        notebook.add(sector_tab, text=" 1. Select / Add Sector ")
        notebook.add(product_tab, text=" 2. Basic Product Information ")
        notebook.add(promotion_tab, text=" 3. Promotion Material Management ")

        default_sectors = (
            "Booster Pump Control Panel", "STP Panel", "Water Meter", "BMS", "Other"
        )
        sector_file_path = os.path.join(config.CSV_DIR, "saark_product_sector_list.csv")
        selected_sector = tk.StringVar()
        new_sector_name = tk.StringVar()

        def get_sectors():
            sectors = list(default_sectors)
            if os.path.exists(sector_file_path):
                with open(sector_file_path, newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
                        sector_name = (row.get("sector_name") or "").strip()
                        if sector_name and sector_name not in sectors:
                            sectors.append(sector_name)
            return sectors

        # Promotion Material Management is a reusable corporate asset library.
        # Every Save creates another item, allowing multiple YouTube videos,
        # Instagram Reels, brochures, photos, and product videos per sector.
        crm_engine.init_crm_db()
        promo_sector = tk.StringVar()
        promo_title = tk.StringVar()
        promo_type = tk.StringVar(value="YouTube Video")
        promo_campaign = tk.StringVar()
        promo_platform = tk.StringVar(value="YouTube")
        promo_url = tk.StringVar()
        promo_attachment = tk.StringVar()

        ttk.Label(
            promotion_tab, text="Promotion Material Management",
            font=("Helvetica", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            promotion_tab,
            text="Maintain approved corporate marketing assets. Add each link or attachment as a separate item.",
        ).pack(anchor="w", pady=(4, 14))
        promo_form = ttk.LabelFrame(promotion_tab, text=" Add Promotion Material ", padding=14)
        promo_form.pack(fill="x")
        promo_form.columnconfigure(1, weight=1)

        def promo_row(row, label, widget):
            ttk.Label(promo_form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )
            widget.grid(row=row, column=1, sticky="ew", pady=5)

        promo_sector_combo = ttk.Combobox(
            promo_form, textvariable=promo_sector, values=get_sectors(), state="readonly"
        )
        promo_row(0, "Product Sector", promo_sector_combo)
        promo_row(1, "Material Title", ttk.Entry(promo_form, textvariable=promo_title))
        promo_row(2, "Material Type", ttk.Combobox(
            promo_form, textvariable=promo_type, state="readonly",
            values=("YouTube Video", "Instagram Reel", "Instagram Photo", "Product Photo",
                    "Product Video", "Brochure / Catalogue", "Datasheet", "Case Study", "Other"),
        ))
        promo_row(3, "Campaign / Product Name", ttk.Entry(promo_form, textvariable=promo_campaign))
        promo_row(4, "Platform", ttk.Combobox(
            promo_form, textvariable=promo_platform,
            values=("YouTube", "Instagram", "Website", "LinkedIn", "WhatsApp", "Internal", "Other"),
        ))
        promo_row(5, "Published / Upload Link", ttk.Entry(promo_form, textvariable=promo_url))

        attachment_box = ttk.Frame(promo_form)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=promo_attachment).grid(row=0, column=0, sticky="ew")

        def choose_promotion_attachment():
            path = filedialog.askopenfilename(
                parent=self.root, title="Attach promotion material",
                filetypes=(
                    ("Promotion files", "*.pdf *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.gif *.webp *.mp4 *.mov *.avi *.mkv *.webm"),
                    ("All files", "*.*"),
                ),
            )
            if path:
                promo_attachment.set(path)

        ttk.Button(attachment_box, text="Attach File", command=choose_promotion_attachment).grid(
            row=0, column=1, padx=(6, 0)
        )
        promo_row(6, "Attachment", attachment_box)
        ttk.Label(promo_form, text="Notes / Approval:").grid(
            row=7, column=0, sticky="nw", padx=(0, 12), pady=5
        )
        promo_notes = tk.Text(promo_form, height=3, wrap="word")
        promo_notes.grid(row=7, column=1, sticky="ew", pady=5)

        promo_table = ttk.LabelFrame(promotion_tab, text=" Saved Promotion Materials ", padding=8)
        promo_table.pack(fill="both", expand=True, pady=(14, 0))
        promo_columns = ("id", "product_sector", "material_type", "title", "platform", "url", "attachment_path", "created_at")
        promo_tree = ttk.Treeview(promo_table, columns=promo_columns, show="headings", height=11)
        promo_headings = ("ID", "Sector", "Type", "Title", "Platform", "Link", "Attachment", "Saved On")
        for column, heading, width in zip(promo_columns, promo_headings, (55, 165, 150, 205, 100, 240, 240, 145)):
            promo_tree.heading(column, text=heading)
            promo_tree.column(column, width=width, anchor="w")
        promo_scroll_y = ttk.Scrollbar(promo_table, orient="vertical", command=promo_tree.yview)
        promo_scroll_x = ttk.Scrollbar(promo_table, orient="horizontal", command=promo_tree.xview)
        promo_tree.configure(yscrollcommand=promo_scroll_y.set, xscrollcommand=promo_scroll_x.set)
        promo_tree.grid(row=0, column=0, sticky="nsew")
        promo_scroll_y.grid(row=0, column=1, sticky="ns")
        promo_scroll_x.grid(row=1, column=0, sticky="ew")
        promo_table.columnconfigure(0, weight=1)
        promo_table.rowconfigure(0, weight=1)

        def refresh_promotion_materials():
            for item in promo_tree.get_children():
                promo_tree.delete(item)
            for row in crm_engine.fetch_promotional_materials(promo_sector.get().strip() or None):
                promo_tree.insert("", "end", values=[row[column] or "" for column in promo_columns])

        def clear_promotion_form():
            promo_title.set("")
            promo_type.set("YouTube Video")
            promo_campaign.set("")
            promo_platform.set("YouTube")
            promo_url.set("")
            promo_attachment.set("")
            promo_notes.delete("1.0", tk.END)

        def save_promotion_material():
            sector = promo_sector.get().strip()
            title = promo_title.get().strip()
            if not sector or not title:
                messagebox.showwarning("Required Information", "Select a Product Sector and enter a Material Title.", parent=self.root)
                return
            if not promo_url.get().strip() and not promo_attachment.get().strip():
                messagebox.showwarning("Link or Attachment Required", "Add a published link or attach a file before saving.", parent=self.root)
                return
            crm_engine.add_promotional_material(
                sector, title, promo_type.get().strip(), promo_campaign.get().strip(),
                promo_platform.get().strip(), promo_url.get().strip(), promo_attachment.get().strip(),
                promo_notes.get("1.0", tk.END).strip(),
            )
            refresh_promotion_materials()
            clear_promotion_form()
            messagebox.showinfo("Saved", "Promotion material saved successfully.", parent=self.root)

        def selected_promotion_values():
            selected = promo_tree.selection()
            return promo_tree.item(selected[0], "values") if selected else None

        def open_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.root)
                return
            link, attachment = values[5], values[6]
            if link:
                webbrowser.open(link)
            elif attachment and os.path.exists(attachment):
                os.startfile(attachment)
            else:
                messagebox.showwarning("File Not Found", "The saved attachment is no longer available.", parent=self.root)

        def delete_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.root)
                return
            if messagebox.askyesno("Delete Material", f"Delete '{values[3]}' from the promotion library?", parent=self.root):
                crm_engine.delete_promotional_material(int(values[0]))
                refresh_promotion_materials()

        promo_actions = ttk.Frame(promotion_tab)
        promo_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(promo_actions, text="Save Material", command=save_promotion_material).pack(side="left")
        ttk.Button(promo_actions, text="Clear Form", command=clear_promotion_form).pack(side="left", padx=6)
        ttk.Button(promo_actions, text="Refresh List", command=refresh_promotion_materials).pack(side="left")
        ttk.Button(promo_actions, text="Open Link / Attachment", command=open_promotion_material).pack(side="right")
        ttk.Button(promo_actions, text="Delete Selected", command=delete_promotion_material).pack(side="right", padx=6)
        promo_sector_combo.bind("<<ComboboxSelected>>", lambda _event: refresh_promotion_materials())
        refresh_promotion_materials()

        ttk.Label(sector_tab, text="Product Sector Setup", font=("Helvetica", 15, "bold")).pack(anchor="w")
        ttk.Label(sector_tab, text="Select an existing sector or add a new sector before entering product details.").pack(anchor="w", pady=(4, 18))
        sector_setup = ttk.LabelFrame(sector_tab, text=" Sector ", padding=16)
        sector_setup.pack(fill="x", anchor="n")
        sector_setup.columnconfigure(1, weight=1)
        ttk.Label(sector_setup, text="Select Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        sector_selector = ttk.Combobox(sector_setup, textvariable=selected_sector, values=get_sectors(), state="readonly")
        sector_selector.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(sector_setup, text="New Sector Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(sector_setup, textvariable=new_sector_name).grid(row=1, column=1, sticky="ew", pady=7)

        form_canvas = tk.Canvas(product_tab, highlightthickness=0)
        form_scrollbar = ttk.Scrollbar(
            product_tab, orient="vertical", command=form_canvas.yview
        )
        form_canvas.configure(yscrollcommand=form_scrollbar.set)
        form_scrollbar.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)

        container = ttk.Frame(form_canvas, padding=20)
        form_window = form_canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind(
            "<Configure>",
            lambda _event: form_canvas.configure(scrollregion=form_canvas.bbox("all")),
        )
        form_canvas.bind(
            "<Configure>", lambda event: form_canvas.itemconfigure(form_window, width=event.width)
        )

        def scroll_product_form(event):
            form_canvas.yview_scroll(int(-event.delta / 120), "units")

        form_canvas.bind("<Enter>", lambda _event: form_canvas.bind_all("<MouseWheel>", scroll_product_form))
        form_canvas.bind("<Leave>", lambda _event: form_canvas.unbind_all("<MouseWheel>"))
        form = ttk.LabelFrame(container, text=" Basic Product Information ", padding=16)
        form.pack(fill="x", anchor="n")
        form.columnconfigure(1, weight=1)

        fields = {
            "product_sector": tk.StringVar(),
            "product_name": tk.StringVar(),
            "sku_model_number": tk.StringVar(),
            "product_category": tk.StringVar(),
            "short_description_file": tk.StringVar(),
            "detailed_description_file": tk.StringVar(),
            "target_applications_file": tk.StringVar(),
            "input_voltage": tk.StringVar(),
            "rated_frequency": tk.StringVar(),
            "min_power_rating": tk.StringVar(),
            "max_power_rating": tk.StringVar(),
            "power_rating_unit": tk.StringVar(value="HP"),
            "starter_drive_type": tk.StringVar(),
            "enclosure_ip_rating": tk.StringVar(),
            "pump_support_capacity": tk.StringVar(),
            "min_pressure": tk.StringVar(),
            "max_pressure": tk.StringVar(),
            "pressure_unit": tk.StringVar(value="bar"),
            "user_interface_display": tk.StringVar(),
            "product_images": tk.StringVar(),
            "datasheet_manual": tk.StringVar(),
            "wiring_sld": tk.StringVar(),
            "promotional_video": tk.StringVar(),
            "photo_name": tk.StringVar(),
            "photo_description": tk.StringVar(),
            "photo_attachment": tk.StringVar(),
            "setting_video_type": tk.StringVar(),
            "setting_video_details": tk.StringVar(),
            "setting_video_attachment": tk.StringVar(),
        }
        multi_selects = {}

        def refresh_sector_selectors():
            sectors = get_sectors()
            sector_selector["values"] = sectors
            basic_sector_combo["values"] = sectors
            promo_sector_combo["values"] = sectors

        def use_selected_sector(_event=None):
            fields["product_sector"].set(selected_sector.get())
            notebook.select(product_tab)

        def add_sector():
            sector_name = new_sector_name.get().strip()
            if not sector_name:
                messagebox.showwarning("Sector Name Required", "Enter a new sector name first.", parent=self.root)
                return
            sectors = get_sectors()
            if sector_name not in sectors:
                with open(sector_file_path, "a", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("sector_name",))
                    if os.path.getsize(sector_file_path) == 0:
                        writer.writeheader()
                    writer.writerow({"sector_name": sector_name})
            selected_sector.set(sector_name)
            fields["product_sector"].set(sector_name)
            new_sector_name.set("")
            refresh_sector_selectors()
            notebook.select(product_tab)

        sector_selector.bind("<<ComboboxSelected>>", use_selected_sector)
        ttk.Button(sector_setup, text="Add Sector", command=add_sector).grid(
            row=2, column=1, sticky="e", pady=(10, 0)
        )

        def add_text_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Entry(form, textvariable=fields[field]).grid(
                row=row, column=1, sticky="ew", pady=7
            )

        def add_attachment_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(form)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(
                row=0, column=0, sticky="ew"
            )

            def choose_file():
                path = filedialog.askopenfilename(
                    parent=self.root,
                    title=f"Attach {label}",
                    filetypes=(
                        ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                        ("All files", "*.*"),
                    ),
                )
                if path:
                    fields[field].set(path)

            ttk.Button(attachment_box, text="Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        def add_dropdown_field(section, row, label, field, values):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Combobox(
                section, textvariable=fields[field], values=values, state="readonly"
            ).grid(row=row, column=1, sticky="ew", pady=7)

        def add_checklist(section, row, label, field, options):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="nw", padx=(0, 12), pady=7
            )
            choice_box = ttk.Frame(section)
            choice_box.grid(row=row, column=1, sticky="ew", pady=4)
            selected_options = []
            for index, option in enumerate(options):
                option_var = tk.BooleanVar()
                ttk.Checkbutton(choice_box, text=option, variable=option_var).grid(
                    row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=2
                )
                selected_options.append((option, option_var))
            multi_selects[field] = selected_options

        def add_file_field(section, row, label, field, *, multiple=False, filetypes=None):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(section)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(row=0, column=0, sticky="ew")

            def choose_file():
                selected_filetypes = filetypes or (
                    ("Documents and images", "*.pdf *.doc *.docx *.jpg *.jpeg *.png *.bmp"),
                    ("All files", "*.*"),
                )
                if multiple:
                    paths = filedialog.askopenfilenames(parent=self.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if paths:
                        fields[field].set(" | ".join(paths))
                else:
                    path = filedialog.askopenfilename(parent=self.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if path:
                        fields[field].set(path)

            ttk.Button(attachment_box, text="Attach Files" if multiple else "Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        ttk.Label(form, text="Product Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        basic_sector_combo = ttk.Combobox(
            form, textvariable=fields["product_sector"], values=get_sectors(), state="readonly"
        )
        basic_sector_combo.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Name / Title:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["product_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="SKU / Model Number:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["sku_model_number"]).grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Category / Sub-category:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Combobox(
            form, textvariable=fields["product_category"],
            values=("Control Panel", "Pump", "Water Treatment", "Water Metering", "Automation", "Other")
        ).grid(row=3, column=1, sticky="ew", pady=7)
        add_attachment_field(4, "Short Description", "short_description_file")
        add_attachment_field(5, "Detailed Description / Features", "detailed_description_file")
        add_attachment_field(6, "Target Applications", "target_applications_file")

        electrical = ttk.LabelFrame(container, text=" 2. Electrical & Power Specifications ", padding=16)
        electrical.pack(fill="x", anchor="n", pady=(14, 0))
        electrical.columnconfigure(1, weight=1)
        add_dropdown_field(electrical, 0, "Input Voltage", "input_voltage", ("230V 1-Phase", "415V 3-Phase", "110V"))
        add_dropdown_field(electrical, 1, "Rated Frequency", "rated_frequency", ("50 Hz", "60 Hz", "50/60 Hz Dual"))
        ttk.Label(electrical, text="Power Rating Range:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        power_box = ttk.Frame(electrical)
        power_box.grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Entry(power_box, textvariable=fields["min_power_rating"], width=12).pack(side="left")
        ttk.Label(power_box, text=" to ").pack(side="left")
        ttk.Entry(power_box, textvariable=fields["max_power_rating"], width=12).pack(side="left")
        ttk.Combobox(power_box, textvariable=fields["power_rating_unit"], values=("HP", "kW"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_dropdown_field(electrical, 3, "Starter / Drive Type", "starter_drive_type", ("DOL", "Star-Delta", "Integrated VFD", "Soft Starter"))
        add_dropdown_field(electrical, 4, "Enclosure / IP Protection Rating", "enclosure_ip_rating", ("IP54", "IP55", "IP65", "NEMA 4X"))

        pump = ttk.LabelFrame(container, text=" 3. Pump Configuration & Control Parameters ", padding=16)
        pump.pack(fill="x", anchor="n", pady=(14, 0))
        pump.columnconfigure(1, weight=1)
        add_dropdown_field(pump, 0, "Pump Support Capacity", "pump_support_capacity", ("1 Pump", "2 Pumps [1W+1S]", "3 Pumps", "4+ Multi-Cascade"))
        add_checklist(pump, 1, "Control Modes", "control_modes", ("Constant Pressure", "Auto-Alternation", "Duty/Assist/Standby", "Manual Override"))
        add_checklist(pump, 2, "Pressure Sensor Compatibility", "pressure_sensor_compatibility", ("4-20 mA", "0-10V", "RS-485 Digital", "Pressure Switch"))
        ttk.Label(pump, text="Supported Pressure Range:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        pressure_box = ttk.Frame(pump)
        pressure_box.grid(row=3, column=1, sticky="ew", pady=7)
        ttk.Entry(pressure_box, textvariable=fields["min_pressure"], width=12).pack(side="left")
        ttk.Label(pressure_box, text=" to ").pack(side="left")
        ttk.Entry(pressure_box, textvariable=fields["max_pressure"], width=12).pack(side="left")
        ttk.Combobox(pressure_box, textvariable=fields["pressure_unit"], values=("bar", "PSI"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_checklist(pump, 4, "Level Sensor Inputs", "level_sensor_inputs", ("Float Switch", "Ultrasonic", "Conductive Probes", "Dry Run Float"))

        smart = ttk.LabelFrame(container, text=" 4. Smart Features, Display & Connectivity ", padding=16)
        smart.pack(fill="x", anchor="n", pady=(14, 0))
        smart.columnconfigure(1, weight=1)
        add_dropdown_field(smart, 0, "User Interface / Display", "user_interface_display", ("Touchscreen HMI", "Multi-line LCD", "7-Segment LED", "Indicator LEDs"))
        add_checklist(smart, 1, "Communication Protocols", "communication_protocols", ("RS-485 Modbus RTU", "Modbus TCP/IP", "BACnet", "Ethernet"))
        add_checklist(smart, 2, "IoT / Cloud Features", "iot_cloud_features", ("GSM/4G Remote Telemetry", "Wi-Fi Dashboard", "Mobile App Support", "SMS Alerts"))
        add_checklist(smart, 3, "Data Logging", "data_logging", ("Historical Fault Log", "Run-Hour Meter", "Pressure Trends"))

        protections = ttk.LabelFrame(container, text=" 5. Protections & Alarms ", padding=16)
        protections.pack(fill="x", anchor="n", pady=(14, 0))
        protections.columnconfigure(1, weight=1)
        add_checklist(protections, 0, "Electrical Protections", "electrical_protections", ("Overload", "Under/Over-Voltage", "Phase Failure", "Phase Reversal", "Short Circuit"))
        add_checklist(protections, 1, "Hydraulic Protections", "hydraulic_protections", ("Dry Run Protection (Auto-Reset)", "High/Low Pressure Cutoff", "Pipe Burst / Leakage Detection", "Anti-Seize Cycling"))

        media = ttk.LabelFrame(container, text=" 6. Media, Documents & Compliance ", padding=16)
        media.pack(fill="x", anchor="n", pady=(14, 0))
        media.columnconfigure(1, weight=1)
        add_file_field(media, 0, "Product Images", "product_images", multiple=True)
        add_file_field(media, 1, "Datasheet / Manual", "datasheet_manual")
        add_file_field(media, 2, "Wiring / Single Line Diagram (SLD)", "wiring_sld")
        add_checklist(media, 3, "Certifications", "certifications", ("CE", "RoHS", "ISO 9001", "CPRI Approved"))

        promotion = ttk.LabelFrame(container, text=" Promotional Material ", padding=16)
        promotion.pack(fill="x", anchor="n", pady=(14, 0))
        promotion.columnconfigure(1, weight=1)
        video_filetypes = (
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.webm"),
            ("All files", "*.*"),
        )
        add_file_field(promotion, 0, "Add Video", "promotional_video", filetypes=video_filetypes)
        ttk.Label(promotion, text="Photo Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(promotion, text="Photo Description:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_description"]).grid(row=2, column=1, sticky="ew", pady=7)
        add_file_field(
            promotion, 3, "Attach Photo", "photo_attachment",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All files", "*.*")),
        )
        add_dropdown_field(
            promotion, 4, "Setting Video", "setting_video_type",
            ("Installation / Setup", "Configuration", "Commissioning", "Operation", "Troubleshooting", "Other"),
        )
        ttk.Label(promotion, text="Setting Video Details:").grid(row=5, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["setting_video_details"]).grid(row=5, column=1, sticky="ew", pady=7)
        add_file_field(promotion, 6, "Attach Setting Video", "setting_video_attachment", filetypes=video_filetypes)

        saved_products = ttk.LabelFrame(container, text=" Saved Products — Select a row to edit ", padding=10)
        saved_products.pack(fill="both", expand=True, anchor="n", pady=(14, 0))
        product_columns = ("product_sector", "product_category", "product_name", "sku_model_number")
        products_tree = ttk.Treeview(saved_products, columns=product_columns, show="headings", height=8)
        for column, label in zip(product_columns, ("Sector", "Category", "Product Name", "SKU / Model No.")):
            products_tree.heading(column, text=label)
            products_tree.column(column, width=190, anchor="w")
        products_scrollbar = ttk.Scrollbar(saved_products, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=products_scrollbar.set)
        products_scrollbar.pack(side="right", fill="y")
        products_tree.pack(side="left", fill="both", expand=True)
        selected_record_index = {"value": None}

        def product_headers():
            return tuple(fields) + tuple(multi_selects)

        def read_product_records():
            file_path = os.path.join(config.CSV_DIR, "saark_product_sectors.csv")
            if not os.path.exists(file_path):
                return []
            with open(file_path, newline="", encoding="utf-8") as file:
                return list(csv.DictReader(file))

        def write_product_records(records):
            file_path = os.path.join(config.CSV_DIR, "saark_product_sectors.csv")
            with tempfile.NamedTemporaryFile(
                "w", newline="", encoding="utf-8", delete=False, dir=config.CSV_DIR
            ) as file:
                temporary_path = file.name
                writer = csv.DictWriter(file, fieldnames=product_headers(), extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
            os.replace(temporary_path, file_path)

        def current_product_record():
            product_name = fields["product_name"].get().strip()
            if not product_name:
                messagebox.showwarning(
                    "Product Name Required",
                    "Enter the Product Name / Title before saving.",
                    parent=self.root,
                )
                return None
            record = {key: value.get().strip() for key, value in fields.items()}
            record.update({
                key: "; ".join(option for option, value in options if value.get())
                for key, options in multi_selects.items()
            })
            return record

        def clear_product_sector_form():
            for value in fields.values():
                value.set("")
            fields["power_rating_unit"].set("HP")
            fields["pressure_unit"].set("bar")
            for options in multi_selects.values():
                for _option, value in options:
                    value.set(False)
            selected_record_index["value"] = None
            for item in products_tree.selection():
                products_tree.selection_remove(item)

        def load_saved_products():
            for item in products_tree.get_children():
                products_tree.delete(item)
            for index, record in enumerate(read_product_records()):
                products_tree.insert(
                    "", "end", iid=str(index), values=[record.get(column, "") for column in product_columns]
                )

        def load_selected_product(_event=None):
            selected = products_tree.selection()
            if not selected:
                return
            index = int(selected[0])
            records = read_product_records()
            if index >= len(records):
                return
            record = records[index]
            for key, value in fields.items():
                value.set(record.get(key, ""))
            for key, options in multi_selects.items():
                selected_options = {item.strip() for item in record.get(key, "").split(";") if item.strip()}
                for option, value in options:
                    value.set(option in selected_options)
            selected_record_index["value"] = index

        def add_product():
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            records.append(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Saved", "Product added successfully.", parent=self.root)

        def update_selected_product():
            index = selected_record_index["value"]
            if index is None:
                messagebox.showwarning("Select Product", "Select a saved product to edit first.", parent=self.root)
                return
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            if index >= len(records):
                messagebox.showwarning("Product Not Found", "Reload the saved product list and try again.", parent=self.root)
                return
            records[index].update(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Updated", "Product updated successfully.", parent=self.root)

        products_tree.bind("<<TreeviewSelect>>", load_selected_product)
        load_saved_products()

        actions = ttk.Frame(container)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="Clear / Add New", command=clear_product_sector_form).pack(
            side="right"
        )
        ttk.Button(actions, text="Update Selected Product", command=update_selected_product).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(actions, text="Add Product", command=add_product).pack(
            side="right", padx=(0, 8)
        )

    def show_category_content(self, category):
        """Show content based on selected product category."""
        try:
            from tabs import CrmTab, MaterialTab, PriceTab

            self.clear_workspace()
            self.create_back_header(f"Sales & Marketing - {category}", self.show_product_category_selector, "⬅ Back to Categories")

            if category == "Saark Product Sector":
                self.show_saark_product_sector()

            elif category == "Customer CRM & Leads":
                if self.user_has_permission("allow_crm", False):
                    tab_crm = CrmTab(self.content_frame)
                    tab_crm.pack(fill="both", expand=True)
                else:
                    messagebox.showwarning("Access Denied", "You do not have permission to access Customer CRM & Leads.", parent=self.root)
                    self.show_product_category_selector()

            elif category == "Booster Pump Control Panel":
                notebook = ttk.Notebook(self.content_frame)
                notebook.pack(fill="both", expand=True, padx=5, pady=5)
                self.sales_notebook = notebook  # Store notebook for tab switching
                self.material_calculator_data = {}  # Store data from Price List
                self.material_tab_instance = None  # Store material tab reference

                if self.user_has_permission("allow_price", True):
                    tab_price = PriceTab(notebook, self)
                    notebook.add(tab_price, text=" Price List Search ")

                if self.user_has_permission("allow_material", True):
                    tab_material = MaterialTab(notebook, self.material_calculator_data)
                    notebook.add(tab_material, text=" Material & Labor Calculator ")
                    self.material_tab_instance = tab_material  # Store reference

            elif category in ["STP Panel", "Water Meter", "BMS"]:
                # Placeholder for future categories
                placeholder_frame = ttk.Frame(self.content_frame, padding=40)
                placeholder_frame.pack(expand=True)

                ttk.Label(
                    placeholder_frame, 
                    text=f"{category}", 
                    font=("Helvetica", 16, "bold")
                ).pack(pady=(0, 20))

                ttk.Label(
                    placeholder_frame,
                    text="This module is under development.",
                    font=("Helvetica", 12)
                ).pack(pady=10)

        except Exception as e:
            messagebox.showerror(
                "Error Loading Category", f"Could not load {category}:\n{e}"
            )

    def show_production_view(self):
        if not self.user_has_permission("allow_production", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Production.", parent=self.root)
            return
        try:
            self.clear_workspace()
            self.create_back_header("Production Module")

            production_panel = production_window.ProductionView(
                self.content_frame,
                user_data=self.user_data,
            )
            production_panel.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Production module:\n{e}"
            )

    def show_panel_manufacturing_view(self):
        if not self.user_has_permission("allow_panel_mfg", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Panel Manufacturing.", parent=self.root)
            return
        try:
            self.clear_workspace()
            self.create_back_header("Panel Manufacturing Module")

            mfg_panel = panel_manufacturing.PanelManufacturingView(
                self.content_frame, user_data=self.user_data
            )
            mfg_panel.pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror(
                "Error Loading View",
                f"Could not load Panel Manufacturing module:\n{e}",
            )

    def show_accounts_finance_view(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts & Finance.", parent=self.root)
            return
        try:
            self._accounts_return_view = self.show_accounts_finance_view
            self.clear_workspace()
            self.create_back_header("Accounts & Finance Module", self.build_main_dashboard, "⬅ Back to Dashboard")
            accounts_finance.AccountsFinanceView(
                self.content_frame, user_data=self.user_data, navigator=self
            ).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error Loading View", f"Could not load Accounts & Finance module:\n{e}")

    def show_purchase_procurement_view(self):
        """Purchase / Procurement module — inward/outward/vendor/cheque (no Sales/Income)."""
        if not (self.user_has_permission("allow_purchase", False) or self.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Purchase / Procurement.", parent=self.root)
            return
        try:
            self._accounts_return_view = self.show_purchase_procurement_view
            self.clear_workspace()
            self.create_back_header("Purchase / Procurement Module", self.build_main_dashboard, "⬅ Back to Dashboard")
            accounts_finance.PurchaseProcurementView(
                self.content_frame, user_data=self.user_data, navigator=self
            ).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Purchase / Procurement module:\n{e}"
            )

    def show_inward_entry_page(self):
        if not (self.user_has_permission("allow_inward_entry", False) or self.user_has_permission("allow_purchase", False) or self.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open the New Inward Invoice window.", parent=self.root)
            return
        parent_view = getattr(self, "_accounts_return_view", self.show_accounts_finance_view)
        self.clear_workspace()
        self.create_back_header("New Inward Invoice", parent_view, "⬅ Back to Accounts & Finance")
        accounts_finance.InwardEntryDialog(self.content_frame, parent_view,
                                            parent_view,
                                            lambda: self.show_vendor_registration_page(self.show_inward_entry_page)).pack(fill="both", expand=True, padx=12, pady=12)

    def show_outward_document_page(self):
        if not (self.user_has_permission("allow_outward_document", False) or self.user_has_permission("allow_purchase", False) or self.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open the New Outward Document window.", parent=self.root)
            return
        parent_view = getattr(self, "_accounts_return_view", self.show_accounts_finance_view)
        self.clear_workspace()
        self.create_back_header("New Outward Document", parent_view, "⬅ Back to Accounts & Finance")
        OutwardWindow(self.content_frame, on_complete=parent_view).pack(fill="both", expand=True, padx=12, pady=12)

    def show_vendor_registration_page(self, return_to=None):
        if not (self.user_has_permission("allow_vendor_registration", False) or self.user_has_permission("allow_purchase", False) or self.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Vendor Registration.", parent=self.root)
            return
        parent_view = getattr(self, "_accounts_return_view", self.show_accounts_finance_view)
        return_to = return_to or parent_view
        self.clear_workspace()
        self.create_back_header("Vendor Registration", return_to, "⬅ Back to Previous Page")
        VendorRegistrationWindow(self.content_frame, on_complete=return_to).pack(fill="both", expand=True, padx=12, pady=12)

    def show_cheque_details_page(self):
        if not (self.user_has_permission("allow_cheque_details", False) or self.user_has_permission("allow_purchase", False) or self.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Cheque Details.", parent=self.root)
            return
        parent_view = getattr(self, "_accounts_return_view", self.show_accounts_finance_view)
        self.clear_workspace()
        self.create_back_header("Cheque Details", parent_view, "⬅ Back to Accounts & Finance")
        accounts_finance.ChequeDetailsWindow(self.content_frame, on_complete=parent_view).pack(fill="both", expand=True, padx=12, pady=12)

    def show_sales_income_page(self):
        if not (self.user_has_permission("allow_accounts", False) or self.user_has_permission("allow_sales", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Sales / Income.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Sales / Income", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.SalesIncomeView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_expenses_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Expenses.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Expenses", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.ExpensesView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_bank_cash_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Bank & Cash.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Bank & Cash", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.BankCashView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_accounts_receivable_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts Receivable.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Accounts Receivable", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.AccountsReceivableView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_accounts_payable_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts Payable.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Accounts Payable", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.AccountsPayableView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_inventory_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Inventory / Stock.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Inventory / Stock", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.InventoryStockView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_employee_salary_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Employee Salary.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Employee Salary", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.EmployeeSalaryView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_gst_tax_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open GST & Tax.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("GST & Tax", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.GSTTaxView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_financial_reports_page(self):
        if not self.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Financial Reports.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Financial Reports", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.FinancialReportsView(
            self.content_frame, user_data=self.user_data, navigator=self
        ).pack(fill="both", expand=True)

    def show_warehouse_view(self):
        if not self.user_has_permission("allow_stores", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Stores / Warehouse.", parent=self.root)
            return
        self.clear_workspace()
        self.create_back_header("Stores / Warehouse Management", self.build_main_dashboard, "⬅ Back to Dashboard")
        warehouse_panel = warehouse_management.WarehouseManagementView(self.content_frame, user_data=self.user_data)
        warehouse_panel.pack(fill="both", expand=True)

    def show_generic_department_view(self, dept_name):
        permission_map = {
            "Purchase / Procurement": "allow_purchase",
            "Maintenance": "allow_maintenance",
            "R&D / Engineering": "allow_rnd",
            "IT": "allow_it",
            "Information Technology": "allow_it",
            "Legal & Compliance": "allow_legal",
            "Administration": "allow_admin_dept",
            "Supply Chain / Logistics": "allow_supply_chain",
            "Customer Service": "allow_customer_service",
            "Project Management / Professional Services": "allow_project_management",
            "Quality Control (QC) / Quality Assurance (QA)": "allow_qc_qa",
            "Asset Management / Fixed Assets": "allow_asset_management",
            "Environment, Health, and Safety (EHS) / Risk Management": "allow_ehs",
            "EHS / Risk Management": "allow_ehs",
            "Point of Sale (POS) / E-Commerce": "allow_pos_ecommerce",
            "POS / E-Commerce": "allow_pos_ecommerce",
        }
        required_permission = permission_map.get(dept_name)
        if required_permission and not self.user_has_permission(required_permission, False):
            messagebox.showwarning("Access Denied", f"You do not have permission to open the {dept_name} module.", parent=self.root)
            return

        try:
            self.clear_workspace()
            self.create_back_header(f"{dept_name} Module", self.build_main_dashboard)

            if "Purchase" in dept_name or "Procurement" in dept_name:
                accounts_panel = accounts_finance.AccountsFinanceView(
                    self.content_frame, user_data=self.user_data, navigator=self
                )
                accounts_panel.pack(fill="both", expand=True)

            elif "Project Management" in dept_name or "Professional Services" in dept_name:
                try:
                    import project_management

                    pm_panel = project_management.ProjectManagementView(self.content_frame, user_data=self.user_data)
                    pm_panel.pack(fill="both", expand=True)
                except Exception as pm_e:
                    messagebox.showerror("Error Loading Module", f"Could not load Project Management:\n{pm_e}", parent=self.root)

            if "R&D" in dept_name or "Engineering" in dept_name:
                rnd_panel = rnd_engineering.RnDEngineeringView(
                    self.content_frame, user_data=self.user_data
                )
                rnd_panel.pack(fill="both", expand=True, padx=0, pady=0)

            elif "Supply Chain" in dept_name:
                supply_chain_panel = supply_chain_logistics.SupplyChainLogisticsView(
                    self.content_frame, user_data=self.user_data
                )
                supply_chain_panel.pack(fill="both", expand=True)
            elif "Quality Control" in dept_name or "Quality Assurance" in dept_name:
                quality_panel = qc_qa.QCQAView(self.content_frame, user_data=self.user_data)
                quality_panel.pack(fill="both", expand=True)
            elif "Legal" in dept_name:
                legal_panel = legal_compliance.LegalComplianceView(
                    self.content_frame, user_data=self.user_data
                )
                legal_panel.pack(fill="both", expand=True)
            elif "Maintenance" in dept_name:
                maintenance_panel = maintenance.MaintenanceView(
                    self.content_frame, user_data=self.user_data
                )
                maintenance_panel.pack(fill="both", expand=True)
            elif "IT" in dept_name or "Information Technology" in dept_name:
                it_panel = it_workspace.ITWorkspaceView(
                    self.content_frame, user_data=self.user_data
                )
                it_panel.pack(fill="both", expand=True)
            elif "Stores" in dept_name or "Warehouse" in dept_name:
                warehouse_panel = warehouse_management.WarehouseManagementView(
                    self.content_frame, user_data=self.user_data
                )
                warehouse_panel.pack(fill="both", expand=True)
            else:
                dept_frame = ttk.Frame(self.content_frame, padding=30)
                dept_frame.pack(fill="both", expand=True)

                ttk.Label(
                    dept_frame,
                    text=f"{dept_name} Workspace",
                    font=("Helvetica", 14, "bold"),
                ).pack(pady=(0, 15))

                ttk.Label(
                    dept_frame,
                    text=f"Welcome to the {dept_name} dashboard management system.",
                    font=("Helvetica", 11),
                ).pack(pady=(0, 20))

                info_box = ttk.LabelFrame(dept_frame, text=" Department Status ", padding=15)
                info_box.pack(fill="x", padx=10, pady=10)

                ttk.Label(info_box, text="• Module Active: Yes").pack(anchor="w", pady=2)
                ttk.Label(info_box, text=f"• User Role Access: {self.user_data.get('role', 'User')}").pack(anchor="w", pady=2)
                ttk.Label(info_box, text=f"• Current Active User: {self.user_data.get('full_name', self.user_data.get('username'))}").pack(anchor="w", pady=2)

        except Exception as e:
            messagebox.showerror(
                "Error Loading View",
                f"Could not load {dept_name} module:\n{e}",
            )

    def show_customer_service_view(self):
        if not self.user_has_permission("allow_customer_service", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Customer Service.", parent=self.root)
            return
        try:
            self.clear_workspace()
            self.create_back_header("Customer Service Module")
            panel = customer_service.CustomerServiceView(
                self.content_frame, user_data=self.user_data
            )
            panel.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Customer Service module:\n{e}"
            )

    def show_hr_view(self):
        if not self.user_has_permission("allow_hr", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open HR.", parent=self.root)
            return
        try:
            self.clear_workspace()
            self.create_back_header("Human Resources")
            hr_window.HRView(self.content_frame, user_data=self.user_data).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error Loading View", f"Could not load HR module:\n{e}")

    def show_task_manager_view(self):
        """Open the embedded Task Manager for users with the dedicated permission."""
        if not self.user_has_permission("allow_task_manager", False):
            messagebox.showwarning(
                "Access Denied", "You do not have permission to open Task Manager.", parent=self.root
            )
            return
        try:
            from task_manager import TaskManagerView

            self.clear_workspace()
            self.create_back_header("Task Manager", self.build_main_dashboard, "Back to Dashboard")
            TaskManagerView(
                self.content_frame, user_data=self.user_data
            ).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error Loading Task Manager", str(e), parent=self.root)

    def show_admin_settings_view(self):
        if not self.user_has_permission("allow_admin", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Admin Settings.", parent=self.root)
            return
        try:
            from tabs.admin_tab import AdminTab

            self.clear_workspace()
            self.create_back_header("Administration Settings & Access Controls")
            admin_view = AdminTab(self.content_frame)
            admin_view.pack(fill="both", expand=True, padx=10, pady=10)

        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Admin module:\n{e}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
