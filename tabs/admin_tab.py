import csv
import ctypes
import ctypes.wintypes
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime
from openpyxl import Workbook

import auth_manager
import config


class UserPermissionsWindow(tk.Toplevel):
    """Dedicated Pop-Up Window for Admin to Control User Permissions"""

    def __init__(self, parent, on_update_callback, selected_username=None):
        super().__init__(parent)
        self.title("User Access & Permission Control")
        self.geometry("980x700")
        self.minsize(760, 520)
        self.resizable(True, True)
        self.on_update_callback = on_update_callback

        # Make window modal and stay on top
        self.transient(parent)
        self.grab_set()

        # Form Variables
        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()
        self.var_role = tk.StringVar(value="User")

        self.permission_vars = {
            permission: tk.BooleanVar(
                value=permission in ("allow_price", "allow_material")
            )
            for permission in auth_manager.PERMISSION_HEADERS
        }

        self.build_ui()
        self.center_window()

        if selected_username:
            self.combo_users.set(selected_username)
            self.on_user_select(None)

    def center_window(self):
        self.update_idletasks()
        left, top, right, bottom = self._safe_work_area()
        width = min(980, right - left)
        height = min(700, bottom - top)
        x = left + max(0, ((right - left) - width) // 2)
        y = top + max(0, ((bottom - top) - height) // 2)
        self.maxsize(right - left, bottom - top)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _windows_work_area(self):
        """Return the usable desktop rectangle, excluding the taskbar."""
        try:
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            return rect.left, rect.top, rect.right, rect.bottom
        except (AttributeError, OSError):
            return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight() - 48

    def _safe_work_area(self):
        left, top, right, bottom = self._windows_work_area()
        margin = 8
        return left + margin, top + margin, right - margin, bottom - margin

    def minimize_window(self):
        self.grab_release()
        self.iconify()

    def restore_window(self):
        self.deiconify()
        self.state("normal")
        self.center_window()
        self.grab_set()

    def maximize_window(self):
        left, top, right, bottom = self._safe_work_area()
        self.deiconify()
        self.state("normal")
        self.geometry(f"{right - left}x{bottom - top}+{left}+{top}")
        self.maxsize(right - left, bottom - top)
        self.grab_set()

    def close_window(self):
        self.grab_release()
        self.destroy()

    def build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        window_controls = ttk.Frame(frame)
        window_controls.pack(fill="x", pady=(0, 8))
        ttk.Label(window_controls, text="Window controls:").pack(side="left")
        ttk.Button(window_controls, text="Minimize", command=self.minimize_window).pack(side="right", padx=(6, 0))
        ttk.Button(window_controls, text="Maximize", command=self.maximize_window).pack(side="right", padx=(6, 0))
        ttk.Button(window_controls, text="Restore", command=self.restore_window).pack(side="right")
        ttk.Button(window_controls, text="Close", command=self.close_window).pack(side="right", padx=(6, 0))

        ttk.Label(
            frame,
            text="User Account & Tab Access Control",
            font=("Helvetica", 12, "bold"),
        ).pack(pady=(0, 15))

        # Dropdown to select existing user
        ttk.Label(frame, text="Select Account to Modify:").pack(anchor="w")
        self.combo_users = ttk.Combobox(frame, state="readonly")
        self.combo_users.pack(fill="x", pady=(0, 15))
        self.combo_users.bind("<<ComboboxSelected>>", self.on_user_select)

        # Credentials Box
        cred_frame = ttk.LabelFrame(
            frame, text=" Account Credentials ", padding=10
        )
        cred_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(cred_frame, text="Username:").pack(anchor="w")
        ttk.Entry(cred_frame, textvariable=self.var_user).pack(
            fill="x", pady=(0, 8)
        )

        ttk.Label(
            cred_frame, text="New Password (leave blank to keep current):"
        ).pack(anchor="w")
        ttk.Entry(cred_frame, textvariable=self.var_pass, show="*").pack(
            fill="x", pady=(0, 8)
        )

        ttk.Label(cred_frame, text="Role Designation:").pack(anchor="w")
        ttk.Combobox(
            cred_frame,
            textvariable=self.var_role,
            values=["Admin", "Sales", "Operator", "User"],
            state="readonly",
        ).pack(fill="x")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side="bottom", fill="x", pady=(10, 0))

        ttk.Button(
            btn_frame, text="Save / Apply Permissions", command=self.save_user
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(
            btn_frame, text="Delete User", command=self.delete_user
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Checkboxes for every application window and module
        perm_frame = ttk.LabelFrame(
            frame, text=" Controlled Window / Tab Permissions ", padding=10
        )
        perm_frame.pack(fill="both", expand=True, pady=(0, 15))
        perm_frame.pack_propagate(False)

        control_row = ttk.Frame(perm_frame)
        control_row.pack(fill="x", pady=(0, 8))
        ttk.Button(control_row, text="Open All", command=lambda: self.set_all_permissions(True)).pack(side="left", padx=(0, 5))
        ttk.Button(control_row, text="Close All", command=lambda: self.set_all_permissions(False)).pack(side="left", padx=5)
        ttk.Button(control_row, text="Default", command=self.reset_default_permissions).pack(side="left", padx=5)

        perm_canvas = tk.Canvas(perm_frame, borderwidth=0, highlightthickness=0)
        perm_scrollbar = ttk.Scrollbar(perm_frame, orient="vertical", command=perm_canvas.yview)
        perm_inner = ttk.Frame(perm_canvas)
        perm_inner.bind(
            "<Configure>",
            lambda e: perm_canvas.configure(scrollregion=perm_canvas.bbox("all"))
        )
        perm_canvas.create_window((0, 0), window=perm_inner, anchor="nw")
        perm_canvas.configure(yscrollcommand=perm_scrollbar.set)
        perm_canvas.pack(side="left", fill="both", expand=True)
        perm_scrollbar.pack(side="right", fill="y")

        # Use human-friendly labels defined in auth_manager when available
        permission_labels = {}
        for permission in auth_manager.PERMISSION_HEADERS:
            friendly = getattr(auth_manager, 'WINDOW_PERMISSION_LABELS', {}).get(permission)
            if not friendly:
                friendly = permission.replace('allow_', '').replace('_', ' ').title()
            permission_labels[permission] = friendly

        # Build grouped permission sections to keep the list readable
        groups = {
            "Sales & Marketing": [],
            "Production / Manufacturing": [],
            "Accounts & Finance": [],
            "HR": [],
            "IT": [],
            "Legal & Compliance": [],
            "Supply Chain": [],
            "Administration": [],
            "Other": [],
        }

        for permission in auth_manager.PERMISSION_HEADERS:
            label = permission_labels[permission].lower()
            if any(token in label for token in ["price", "material", "crm", "sales", "marketing"]):
                group = "Sales & Marketing"
            elif any(token in label for token in ["production", "manufacturing", "panel"]):
                group = "Production / Manufacturing"
            elif any(token in label for token in ["account", "inward", "outward", "vendor", "cheque"]):
                group = "Accounts & Finance"
            elif "hr" in label:
                group = "HR"
            elif "it" in label or "security" in label or "helpdesk" in label or "asset" in label or "iam" in label:
                group = "IT"
            elif "legal" in label or "compliance" in label:
                group = "Legal & Compliance"
            elif "supply" in label or "chain" in label:
                group = "Supply Chain"
            elif "admin" in label:
                group = "Administration"
            else:
                group = "Other"
            groups[group].append(permission)

        for group_name, permissions in groups.items():
            if not permissions:
                continue
            group_frame = ttk.LabelFrame(perm_inner, text=f" {group_name} ", padding=8)
            group_frame.pack(fill="x", pady=(6, 0), padx=2)
            for index, permission in enumerate(permissions):
                ttk.Checkbutton(
                    group_frame,
                    text=permission_labels[permission],
                    variable=self.permission_vars[permission],
                ).grid(row=index // 2, column=index % 2, sticky="w", padx=6, pady=4)

        self.refresh_user_dropdown()
        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def refresh_user_dropdown(self):
        user_list = [record["username"] for record in self._load_employee_access_records()]
        self.combo_users["values"] = user_list

    def _load_employee_access_records(self):
        auth_users = auth_manager.load_users()
        employee_path = os.path.join(config.HR_DIR, "employee record.csv")
        if not os.path.exists(employee_path):
            legacy_path = os.path.join(config.CSV_DIR, "employee record.csv")
            if os.path.exists(legacy_path):
                employee_path = legacy_path
            else:
                return auth_users

        records = []
        with open(employee_path, newline="", encoding="utf-8") as file:
            for employee in csv.DictReader(file):
                employee_id = (employee.get("employee_id") or "").strip()
                full_name = (employee.get("full_name") or "").strip()
                work_email = (employee.get("work_email") or "").strip().casefold()
                matched = next(
                    (
                        user for user in auth_users
                        if user.get("username", "").casefold() in {employee_id.casefold(), full_name.casefold()}
                        or (work_email and user.get("email", "").casefold() == work_email)
                    ),
                    None,
                )
                if matched is None:
                    matched = {
                        "username": employee_id or full_name,
                        "full_name": full_name,
                        "role": "User",
                        "account_status": "Pending",
                    }
                    matched.update({permission: False for permission in auth_manager.PERMISSION_HEADERS})
                else:
                    matched = dict(matched)
                matched["employee_id"] = employee_id
                matched["first_name"] = (employee.get("first_name") or "").strip()
                matched["middle_name"] = (employee.get("middle_name") or "").strip()
                matched["department"] = (employee.get("department") or "").strip()
                records.append(matched)

        employee_usernames = {record["username"] for record in records}
        records.extend(user for user in auth_users if user.get("username") not in employee_usernames)
        return records

    def set_all_permissions(self, enabled):
        for permission, variable in self.permission_vars.items():
            variable.set(enabled)

    def reset_default_permissions(self):
        for permission, variable in self.permission_vars.items():
            default_value = permission in ("allow_price", "allow_material")
            variable.set(default_value)

    def on_user_select(self, event):
        selected_username = self.combo_users.get()
        users = self._load_employee_access_records()

        for u in users:
            if u["username"] == selected_username:
                self.var_user.set(u["username"])
                self.var_pass.set("")
                self.var_role.set(u.get("role", "User"))
                for permission, variable in self.permission_vars.items():
                    variable.set(u.get(permission, False))
                break

    def save_user(self):
        user = self.var_user.get().strip()
        pwd = self.var_pass.get().strip()
        role = self.var_role.get()

        if not user:
            messagebox.showwarning(
                "Input Error", "Please enter a valid username.", parent=self
            )
            return
        auth_manager.add_or_update_user(
            username=user,
            password=pwd if pwd else None,
            role=role,
            **{
                permission: variable.get()
                for permission, variable in self.permission_vars.items()
            },
        )

        messagebox.showinfo(
            "Success",
            f"Permissions updated successfully for '{user}'!",
            parent=self,
        )
        self.refresh_user_dropdown()
        self.on_update_callback()

    def delete_user(self):
        user = self.var_user.get().strip()
        if not user:
            return

        if user == "admin":
            messagebox.showerror(
                "Action Prohibited",
                "The primary admin account cannot be deleted.",
                parent=self,
            )
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{user}'?",
            parent=self,
        ):
            auth_manager.delete_user(user)
            self.var_user.set("")
            self.var_pass.set("")
            self.refresh_user_dropdown()
            self.on_update_callback()


class AdminTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.audit_file = os.path.join(auth_manager.os.path.dirname(auth_manager.USERS_FILE) or ".", "admin_audit_logs.csv")
        self.build_ui()
        self.load_user_list()

    def _load_employee_access_records(self):
        auth_users = auth_manager.load_users()
        employee_path = os.path.join(config.HR_DIR, "employee record.csv")
        if not os.path.exists(employee_path):
            legacy_path = os.path.join(config.CSV_DIR, "employee record.csv")
            if os.path.exists(legacy_path):
                employee_path = legacy_path
            else:
                return auth_users

        records = []
        with open(employee_path, newline="", encoding="utf-8") as file:
            for employee in csv.DictReader(file):
                employee_id = (employee.get("employee_id") or "").strip()
                full_name = (employee.get("full_name") or "").strip()
                work_email = (employee.get("work_email") or "").strip().casefold()
                matched = next(
                    (
                        user for user in auth_users
                        if user.get("username", "").casefold() in {employee_id.casefold(), full_name.casefold()}
                        or (work_email and user.get("email", "").casefold() == work_email)
                    ),
                    None,
                )
                if matched is None:
                    matched = {
                        "username": employee_id or full_name,
                        "full_name": full_name,
                        "role": "User",
                        "account_status": "Pending",
                    }
                    matched.update({permission: False for permission in auth_manager.PERMISSION_HEADERS})
                else:
                    matched = dict(matched)
                matched["employee_id"] = employee_id
                matched["first_name"] = (employee.get("first_name") or "").strip()
                matched["middle_name"] = (employee.get("middle_name") or "").strip()
                matched["department"] = (employee.get("department") or "").strip()
                records.append(matched)

        employee_usernames = {record["username"] for record in records}
        records.extend(user for user in auth_users if user.get("username") not in employee_usernames)
        return records

    def build_ui(self):
        # Header Controls
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            header_frame,
            text="System Administrator Dashboard",
            font=("Helvetica", 12, "bold"),
        ).pack(side="left")

        # The Button to launch pop-up window
        btn_open_window = ttk.Button(
            header_frame,
            text="⚙ Open Permission Control Window",
            command=self.open_permission_window,
        )
        btn_open_window.pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        users_page = ttk.Frame(notebook, padding=8)
        audit_page = ttk.Frame(notebook, padding=8)
        settings_page = ttk.Frame(notebook, padding=8)
        notebook.add(users_page, text="Users & Access")
        notebook.add(audit_page, text="Audit Logs")
        notebook.add(settings_page, text="Settings")

        filter_frame = ttk.Frame(users_page)
        filter_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(filter_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_var, width=28).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Status:").pack(side="left", padx=(12, 3))
        self.status_filter = ttk.Combobox(filter_frame, values=("All", "Active", "Suspended", "Pending"), state="readonly", width=12)
        self.status_filter.set("All")
        self.status_filter.pack(side="left")
        ttk.Button(filter_frame, text="Search", command=self.load_user_list).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Export Excel", command=self.export_users).pack(side="right")

        action_frame = ttk.Frame(users_page)
        action_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(action_frame, text="Edit Role / Permissions", command=self.edit_selected_user).pack(side="left", padx=3)
        ttk.Button(action_frame, text="Deactivate / Activate", command=self.toggle_selected_user).pack(side="left", padx=3)
        ttk.Button(action_frame, text="Reset Password", command=self.reset_selected_password).pack(side="left", padx=3)

        table_frame = ttk.Frame(users_page)
        table_frame.pack(fill="both", expand=True)

        cols = (
            "Username", "Employee ID", "First Name", "Middle Name", "Full Name", "Department",
            "Role",
            "Status",
            "Price List",
            "Material Calc",
            "CRM Leads",
            "Admin Tools",
        )
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        self.tree.pack(fill="both", expand=True)

        audit_controls = ttk.Frame(audit_page)
        audit_controls.pack(fill="x", pady=(0, 8))
        ttk.Button(audit_controls, text="Refresh Logs", command=self.load_audit_logs).pack(side="left")
        ttk.Button(audit_controls, text="Export Logs", command=self.export_audit_logs).pack(side="right")
        self.audit_tree = ttk.Treeview(audit_page, columns=("Time", "Action", "User", "Details"), show="headings")
        for column in ("Time", "Action", "User", "Details"):
            self.audit_tree.heading(column, text=column)
            self.audit_tree.column(column, width=160 if column != "Details" else 420)
        self.audit_tree.pack(fill="both", expand=True)

        self.maintenance_var = tk.BooleanVar()
        ttk.Checkbutton(settings_page, text="Maintenance mode", variable=self.maintenance_var, command=self.save_settings).pack(anchor="w", pady=8)
        ttk.Label(settings_page, text="Settings are stored locally for this application.").pack(anchor="w")
        self.load_audit_logs()

    def open_permission_window(self):
        UserPermissionsWindow(
            self,
            on_update_callback=self.load_user_list,
            selected_username=self.selected_username(),
        )

    def load_user_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        query = self.search_var.get().strip().casefold()
        status = self.status_filter.get() if hasattr(self, "status_filter") else "All"
        users = self._load_employee_access_records()
        for u in users:
            if query and query not in f"{u.get('username', '')} {u.get('full_name', '')} {u.get('role', '')}".casefold():
                continue
            if status != "All" and u.get("account_status", "Active") != status:
                continue
            self.tree.insert(
                "",
                "end",
                values=(
                    u["username"],
                    u.get("employee_id", ""),
                    u.get("first_name", ""),
                    u.get("middle_name", ""),
                    u.get("full_name", "") or u.get("first_name", ""),
                    u.get("department", ""),
                    u.get("role", "User"),
                    u.get("account_status", "Active"),
                    "✓ Allowed" if u["allow_price"] else "✕ Blocked",
                    "✓ Allowed" if u["allow_material"] else "✕ Blocked",
                    "✓ Allowed" if u["allow_crm"] else "✕ Blocked",
                    "✓ Allowed" if u["allow_admin"] else "✕ Blocked",
                ),
            )

    def selected_username(self):
        selection = self.tree.selection()
        return self.tree.item(selection[0], "values")[0] if selection else None

    def edit_selected_user(self):
        if not self.selected_username():
            messagebox.showwarning("Select User", "Select a user first.", parent=self)
            return
        UserPermissionsWindow(self, on_update_callback=self.load_user_list)

    def toggle_selected_user(self):
        username = self.selected_username()
        if not username:
            messagebox.showwarning("Select User", "Select a user first.", parent=self)
            return
        users = auth_manager.load_users()
        for user in users:
            if user["username"] == username:
                user["account_status"] = "Suspended" if user.get("account_status", "Active") == "Active" else "Active"
                break
        auth_manager.save_users(users)
        self.write_audit("Account status changed", username, user["account_status"])
        self.load_user_list()

    def reset_selected_password(self):
        username = self.selected_username()
        if not username:
            messagebox.showwarning("Select User", "Select a user first.", parent=self)
            return
        password = simpledialog.askstring("Reset Password", f"New password for {username}:", show="*", parent=self)
        if not password:
            return
        users = auth_manager.load_users()
        selected = next((user for user in users if user["username"] == username), None)
        if selected:
            auth_manager.add_or_update_user(
                username=username,
                password=password,
                full_name=selected.get("full_name", ""),
                mobile_number=selected.get("mobile_number", ""),
                designation=selected.get("designation", ""),
                role=selected.get("role", "User"),
                **{key: selected.get(key, False) for key in auth_manager.PERMISSION_HEADERS},
            )
            self.write_audit("Password reset", username)
            messagebox.showinfo("Password Reset", "Password reset successfully.", parent=self)

    def write_audit(self, action, username, details=""):
        exists = os.path.exists(self.audit_file)
        with open(self.audit_file, "a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            if not exists:
                writer.writerow(("timestamp", "action", "user", "details"))
            writer.writerow((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, username, details))
        self.load_audit_logs()

    def load_audit_logs(self):
        self.audit_tree.delete(*self.audit_tree.get_children())
        if os.path.exists(self.audit_file):
            with open(self.audit_file, newline="", encoding="utf-8-sig") as file:
                for index, row in enumerate(csv.DictReader(file)):
                    self.audit_tree.insert("", "end", values=(row.get("timestamp", ""), row.get("action", ""), row.get("user", ""), row.get("details", "")))

    def export_users(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".xlsx", filetypes=(("Excel workbook", "*.xlsx"),))
        if not path:
            return
        workbook = Workbook()
        sheet = workbook.active
        headers = ("Username", "Employee ID", "First Name", "Middle Name", "Full Name", "Department", "Role", "Status")
        sheet.append(headers)
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            sheet.append(tuple(values[:8]))
        workbook.save(path)

    def export_audit_logs(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=(("CSV file", "*.csv"),))
        if path and os.path.exists(self.audit_file):
            with open(self.audit_file, "rb") as source, open(path, "wb") as target:
                target.write(source.read())

    def save_settings(self):
        settings_file = os.path.join(os.path.dirname(auth_manager.USERS_FILE) or ".", "admin_settings.csv")
        with open(settings_file, "w", newline="", encoding="utf-8-sig") as file:
            csv.writer(file).writerows((("maintenance_mode", "True" if self.maintenance_var.get() else "False"),))