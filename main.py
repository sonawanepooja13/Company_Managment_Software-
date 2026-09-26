import csv
import os
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import webbrowser
import zipfile
import shutil
import subprocess
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import auth_manager
import config
import accounts_finance
import bom_engine
import panel_manufacturing
import production_window
import hr_window
from outward_window import DOCUMENT_TYPES, OutwardWindow
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

import sales_marketing_window
import accounts_finance_window
import generic_department_window


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
            ("allow_trading", "📈 B2B Trading Module"),
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

        # Modules read data paths through main_app.config (config package)
        self.config = config

        bom_engine.ensure_files_exist()
        auth_manager.ensure_user_file_exists()

        self.user_data = None
        self.content_frame = None

        # Theme settings
        self.dark_mode = False
        self.style = ttk.Style()
        self.apply_theme()

        # Module Managers
        self.sales_marketing_mgr = None
        self.accounts_finance_mgr = None
        self.generic_dept_mgr = None

        self.show_login_screen()

    def apply_theme(self):
        """Apply the selected light or dark theme across the application."""
        if self.dark_mode:
            bg_color = "#1e1e1e"
            fg_color = "#e0e0e0"
            btn_bg = "#2d2d2d"
            btn_fg = "#000000"
            accent = "#4a9eff"
            hover_bg = "#3d3d3d"
            hover_accent = "#6baeff"
        else:
            bg_color = "#f8f9fa"
            fg_color = "#1a202c"
            btn_bg = "#edf2f7"
            btn_fg = "#000000"
            accent = "#3182ce"
            hover_bg = "#e2e8f0"
            hover_accent = "#2b6cb0"

        # Update Root and Main Containers
        self.root.configure(bg=bg_color)

        # Safe configuration for containers that might have been destroyed
        if hasattr(self, "content_frame") and self.content_frame:
            try:
                if self.content_frame.winfo_exists():
                    pass
            except Exception:
                pass

        if hasattr(self, "content_container") and self.content_container:
            try:
                if self.content_container.winfo_exists():
                    self.content_container.configure(bg=bg_color)
            except Exception:
                pass

        # Configure ttk Style
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Helvetica", 10))
        self.style.configure("TButton", background=btn_bg, foreground=btn_fg, font=("Helvetica", 10))
        self.style.map("TButton",
                      background=[('active', hover_bg)],
                      foreground=[('active', btn_fg)])
        self.style.configure("TCombobox", fieldbackground=bg_color, foreground=fg_color)

        # Store colors for non-ttk widgets (like tk.Button)
        self.theme_colors = {
            "bg": bg_color,
            "fg": fg_color,
            "btn_bg": btn_bg,
            "btn_fg": btn_fg,
            "accent": accent,
            "hover_bg": hover_bg,
            "hover_accent": hover_accent
        }

    def toggle_theme(self):
        """Toggle between light and dark mode and refresh the current view."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()

        # Refresh dashboard if it's currently shown
        if hasattr(self, "content_frame") and self.content_frame:
            self.build_main_dashboard()

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

            # Initialize Module Managers
            self.accounts_finance_mgr = accounts_finance_window.AccountsFinanceWindow(self)
            self.generic_dept_mgr = generic_department_window.GenericDepartmentWindow(self)

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
                    lambda: self.show_sales_marketing_view("Booster Pump Control Panel"),
                )
            if os.environ.get("APP_OPEN_TASK_MANAGER") == "1":
                self.root.after(250, self.show_task_manager_view)
            if os.environ.get("APP_OPEN_SALES") == "1":
                self.root.after(250, self.show_sales_marketing_view)
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

    def csv_to_excel(self, csv_file, excel_file):
        """Convert CSV file to Excel format."""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            df.to_excel(excel_file, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Error converting {csv_file} to Excel: {e}")
            return False

    def csv_to_pdf(self, csv_file, pdf_file):
        """Convert CSV file to PDF format."""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_file, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Add title
            title = f"CSV Export: {os.path.basename(csv_file)}"
            elements.append(Paragraph(title, styles['Title']))
            
            # Convert DataFrame to table
            data = [df.columns.tolist()] + df.values.tolist()
            table = Table(data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            doc.build(elements)
            return True
        except Exception as e:
            print(f"Error converting {csv_file} to PDF: {e}")
            return False

    def download_database(self):
        """Download all CSV files as Excel and PDF with password protection."""
        # Password protection
        password = simpledialog.askstring("Password Required", "Enter password to download database:")
        if password != "28300191":
            messagebox.showerror("Access Denied", "Incorrect password. Access denied.")
            return

        try:
            # Get all CSV files from the project directory
            csv_files = []
            csv_dir = os.path.join(config.SCRIPT_DIR, "csv_data")
            
            # Collect all CSV files recursively
            for root, dirs, files in os.walk(csv_dir):
                for file in files:
                    if file.endswith('.csv'):
                        csv_files.append(os.path.join(root, file))
            
            # Also include CSV files in the main directory
            for file in os.listdir(config.SCRIPT_DIR):
                if file.endswith('.csv') and file not in ['.kilo']:
                    csv_files.append(os.path.join(config.SCRIPT_DIR, file))
            
            # Include Production directory
            production_dir = os.path.join(config.SCRIPT_DIR, "Production")
            if os.path.exists(production_dir):
                for root, dirs, files in os.walk(production_dir):
                    for file in files:
                        if file.endswith('.csv'):
                            csv_files.append(os.path.join(root, file))
            
            # Include project_management_exports directory
            pm_exports_dir = os.path.join(config.SCRIPT_DIR, "project_management_exports")
            if os.path.exists(pm_exports_dir):
                for file in os.listdir(pm_exports_dir):
                    if file.endswith('.csv'):
                        csv_files.append(os.path.join(pm_exports_dir, file))
            
            if not csv_files:
                messagebox.showinfo("No Files", "No CSV files found to download.")
                return

            # Ask user for save location
            save_dir = filedialog.askdirectory(title="Select folder to save database files")
            if not save_dir:
                return

            # Create timestamp for folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_folder = os.path.join(save_dir, f"Saark_Database_{timestamp}")
            os.makedirs(db_folder, exist_ok=True)

            # Create subfolders for different formats
            csv_folder = os.path.join(db_folder, "CSV_Files")
            excel_folder = os.path.join(db_folder, "Excel_Files")
            pdf_folder = os.path.join(db_folder, "PDF_Files")
            
            os.makedirs(csv_folder, exist_ok=True)
            os.makedirs(excel_folder, exist_ok=True)
            os.makedirs(pdf_folder, exist_ok=True)

            # Convert and save files in different formats
            converted_count = 0
            for csv_file in csv_files:
                try:
                    # Get relative path and filename
                    relative_path = os.path.relpath(csv_file, config.SCRIPT_DIR)
                    filename = os.path.splitext(os.path.basename(csv_file))[0]
                    
                    # Copy original CSV
                    csv_dest = os.path.join(csv_folder, os.path.basename(csv_file))
                    shutil.copy2(csv_file, csv_dest)
                    
                    # Convert to Excel
                    excel_dest = os.path.join(excel_folder, f"{filename}.xlsx")
                    if self.csv_to_excel(csv_file, excel_dest):
                        converted_count += 1
                    
                    # Convert to PDF
                    pdf_dest = os.path.join(pdf_folder, f"{filename}.pdf")
                    if self.csv_to_pdf(csv_file, pdf_dest):
                        converted_count += 1
                    
                except Exception as e:
                    print(f"Error processing {csv_file}: {e}")

            # Create a summary file
            summary_file = os.path.join(db_folder, "DATABASE_SUMMARY.txt")
            with open(summary_file, 'w') as f:
                f.write(f"Saark Enterprise Database Export\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total CSV Files: {len(csv_files)}\n")
                f.write(f"Converted Files: {converted_count}\n\n")
                f.write("Files included:\n")
                for csv_file in csv_files:
                    relative_path = os.path.relpath(csv_file, config.SCRIPT_DIR)
                    f.write(f"- {relative_path}\n")

            # Create ZIP file
            zip_path = os.path.join(save_dir, f"Saark_Database_{timestamp}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(db_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, db_folder)
                        zipf.write(file_path, arcname)

            # Clean up the temporary folder
            shutil.rmtree(db_folder)

            messagebox.showinfo("Download Complete", 
                              f"Database downloaded successfully!\n\n"
                              f"Total CSV Files: {len(csv_files)}\n"
                              f"Converted Files: {converted_count}\n"
                              f"Saved as: {zip_path}")

        except Exception as e:
            messagebox.showerror("Download Error", f"Failed to download database: {e}")

    def create_welcome_button(self, parent, text, command):
        bg = self.theme_colors["btn_bg"]
        fg = self.theme_colors["btn_fg"]
        accent = self.theme_colors["accent"]

        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=34,
            font=("Helvetica", 11, "bold"),
            foreground=fg,
            background=bg,
            activeforeground="#ffffff",
            activebackground=accent,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=accent,
            highlightcolor=accent,
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
                background=self.theme_colors["hover_bg"],
                highlightbackground=self.theme_colors["hover_accent"],
            ),
        )
        button.bind(
            "<Leave>",
            lambda event: event.widget.configure(
                background=self.theme_colors["btn_bg"],
                highlightbackground=accent,
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

        # Top bar for Welcome text and Theme Toggle
        top_bar = ttk.Frame(welcome_frame)
        top_bar.pack(fill="x", pady=(0, 15))

        welcome_text_frame = ttk.Frame(top_bar)
        welcome_text_frame.pack(side="left")
        ttk.Label(
            welcome_text_frame,
            text=f"Welcome, {username}!",
            font=("Helvetica", 16, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            welcome_text_frame,
            text="Select a workspace module to proceed:",
            font=("Helvetica", 11),
        ).pack(anchor="w")

        # Theme Toggle Section
        theme_frame = ttk.Frame(top_bar)
        theme_frame.pack(side="right")

        theme_label = ttk.Label(theme_frame, text="🌙 Dark Mode", font=("Helvetica", 10))
        theme_label.pack(side="left", padx=(0, 10))

        theme_switch = tk.Button(
            theme_frame,
            text="OFF" if not self.dark_mode else "ON",
            command=self.toggle_theme,
            width=4,
            font=("Helvetica", 10, "bold"),
            bg=self.theme_colors["btn_bg"],
            fg=self.theme_colors["btn_fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme_colors["accent"]
        )
        theme_switch.pack(side="left")

        btn_frame = ttk.Frame(welcome_frame)
        btn_frame.pack(fill="x")

        all_modules = [
            ("allow_sales", "📈 Sales & Marketing", self.show_sales_marketing_view),
            ("allow_trading", "📈 B2B Trading", lambda: self.show_sales_marketing_view("B2B Trading")),
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

        # Download Database button (password protected)
        self.create_welcome_button(
            module_grid,
            "📥 Download Database",
            self.download_database,
        ).grid(
            row=(len(all_modules) // 2) + 1,
            column=1,
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

    def show_sales_marketing_view(self, category=None):
        if not self.user_has_permission("allow_sales", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Sales & Marketing.", parent=self.root)
            return
        try:
            self.clear_workspace()
            from tally_navbar import TallyShell
            from sales_marketing_window import SalesMarketingView
            shell = TallyShell(
                self.content_frame,
                on_tab=lambda label: self._sales_tally_tab(
                    shell, getattr(shell, "view", None), label, from_nav=True),
                on_create=lambda label: self._sales_tally_create(
                    shell, getattr(shell, "view", None), label),
            )
            # view lives INSIDE shell body so header/nav never get cleared
            view = SalesMarketingView(shell.body, self)
            view.pack(fill="both", expand=True)
            shell.view = view
            # slim utility strip: back to main dashboard + FY echo
            strip = tk.Frame(shell.body)
            strip.pack(fill="x", padx=10, pady=(6, 0))
            tk.Button(strip, text="⬅ Back to Dashboard",
                      font=("Helvetica", 9), cursor="hand2",
                      command=self.build_main_dashboard).pack(side="left")
            tk.Label(strip, textvariable=shell.fy_var,
                     font=("Helvetica", 9)).pack(side="right")
            # keep sales view below the strip
            view.pack_forget()
            view.pack(fill="both", expand=True)
            if category:
                if category == "B2B Trading":
                    shell.set_active("Dashboard")
                elif category == "Customer CRM & Leads":
                    shell.set_active("Customer / Vendor")
                elif category == "Saark Product Sector":
                    shell.set_active("Products / Services")
                elif category == "Quotation":
                    shell.set_active("Dashboard")
                view.show_category_content(category)
            else:
                shell.set_active("Dashboard")

        except Exception as e:
            messagebox.showerror(
                "Error Loading View", f"Could not load Sales module:\n{e}"
            )

    def _sales_tally_embed(self, shell, widget_cls, *args, **kwargs):
        """Show an accounts/outward view inside shell body, hiding sales view."""
        view = getattr(shell, "view", None)
        try:
            if view is not None and view.winfo_exists():
                view.pack_forget()
        except Exception:
            pass
        shell.clear_body()
        # back button on top of embedded page
        tk.Button(shell.body, text="⬅ Back to Sales Dashboard",
                  command=lambda: self._sales_tally_tab(
                      shell, getattr(shell, "view", None), "Dashboard"),
                  font=("Helvetica", 9), cursor="hand2").pack(anchor="w", padx=10, pady=(8, 0))
        widget = widget_cls(shell.body, *args, **kwargs)
        widget.pack(fill="both", expand=True, padx=6, pady=6)
        return widget

    def _sales_tally_show_view(self, shell, view):
        """Return to the SalesMarketingView inside shell body."""
        shell.clear_body()
        view = getattr(shell, "view", None)
        try:
            exists = bool(view is not None and view.winfo_exists())
        except Exception:
            exists = False
        if not exists:
            from sales_marketing_window import SalesMarketingView
            view = SalesMarketingView(shell.body, self)
            shell.view = view
        try:
            view.pack(fill="both", expand=True)
        except Exception:
            pass
        return view

    def _sales_tally_tab(self, shell, view, label, from_nav=False):
        try:
            base = label.replace("\n", " ").strip()
            if base == "Dashboard":
                if from_nav:
                    # The "Dashboard" tab of the Tally nav strip is the home tab,
                    # so it leaves the Sales module and shows the main Welcome page.
                    self.build_main_dashboard()
                    return
                view = self._sales_tally_show_view(shell, view)
                try:
                    view.show_product_category_selector()
                except Exception:
                    pass
            elif base == "Customer / Vendor":
                view = self._sales_tally_show_view(shell, view)
                view.show_category_content("Customer CRM & Leads")
            elif base == "Products / Services":
                view = self._sales_tally_show_view(shell, view)
                view.show_category_content("Saark Product Sector")
            elif base == "Sale Invoice":
                self._sales_tally_embed(
                    shell, accounts_finance.SalesIncomeView,
                    user_data=self.user_data, navigator=self)
            elif base == "Purchase Invoice":
                self._sales_tally_embed(
                    shell, accounts_finance.PurchaseProcurementView,
                    user_data=self.user_data, navigator=self)
            elif base == "Payment":
                self._sales_tally_embed(
                    shell, accounts_finance.BankCashView,
                    user_data=self.user_data, navigator=self)
            elif base == "Expense Income":
                self._sales_tally_embed(
                    shell, accounts_finance.ExpensesView,
                    user_data=self.user_data, navigator=self)
            elif base == "Other Documents":
                from outward_window import OutwardWindow
                self._sales_tally_embed(
                    shell, OutwardWindow,
                    on_complete=lambda: self._sales_tally_tab(shell, view, "Dashboard"))
            elif base == "Report":
                self._sales_tally_embed(
                    shell, accounts_finance.FinancialReportsView,
                    user_data=self.user_data, navigator=self)
        except Exception as e:
            messagebox.showerror("Error Loading Tab", f"Could not open {label}:\n{e}")

    def _sales_tally_create(self, shell, view, label):
        try:
            if label == "Sale Invoice":
                shell.select("Sale\nInvoice")
            elif label == "Purchase Invoice":
                shell.select("Purchase\nInvoice")
            elif "Payment" in label:
                shell.select("Payment")
            elif label == "Quotation":
                view = self._sales_tally_show_view(shell, view)
                shell.set_active("Dashboard")
                view.show_category_content("Quotation")
            elif "Customer" in label:
                shell.select("Customer / Vendor")
            elif "Product" in label:
                shell.select("Products / Services")
            elif label in DOCUMENT_TYPES:
                # Proforma, Sales Order, Purchase Order, Delivery Challan,
                # Job Work, Credit Note, Debit Note, Service Request ...
                self._sales_tally_create_document(shell, view, label)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create {label}:\n{e}")

    def _sales_tally_create_document(self, shell, view, document_type):
        """Open the document entry form from the Create menu with its type preset."""
        shell.set_active("Other\nDocuments")
        return self._sales_tally_embed(
            shell, OutwardWindow,
            on_complete=lambda: self._sales_tally_tab(shell, view, "Dashboard"),
            document_type=document_type)

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
    if getattr(sys, "frozen", False):
        os.chdir(config.DATA_DIR)
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
