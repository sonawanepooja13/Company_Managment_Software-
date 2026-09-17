import tkinter as tk
from tkinter import messagebox, ttk
import auth_manager


class UserAccessControlDialog(tk.Toplevel):
    """User Access & Permission Control Dialog matching your UI window layout.

    Includes Full Name, Mobile Number, Role Designation, and Tab
    Permissions.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Access & Permission Control")
        self.geometry("520x680")
        self.minsize(520, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Make dialog fullscreen (maximized) for full screen user access control
        try:
            self.state('zoomed')
        except Exception:
            pass

        # Dynamically create permission variables for every permission header
        self.permission_vars = {
            permission: tk.BooleanVar(value=(permission in ("allow_price", "allow_material")) )
            for permission in auth_manager.PERMISSION_HEADERS
        }

        self.users_cache = []
        self.selected_user = None

        self.setup_ui()
        self.load_accounts_dropdown()

    def setup_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        # Title Header
        ttk.Label(
            container,
            text="User Account & Tab Access Control",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 15))

        # ------------------------------------------------------------------
        # Top Section: Select Account to Modify
        # ------------------------------------------------------------------
        ttk.Label(
            container,
            text="Select Account to Modify:",
            font=("Helvetica", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        self.combo_accounts = ttk.Combobox(
            container, state="readonly", font=("Helvetica", 9)
        )
        self.combo_accounts.pack(fill="x", pady=(0, 15))
        self.combo_accounts.bind(
            "<<ComboboxSelected>>", self.on_account_selected
        )

        # ------------------------------------------------------------------
        # Middle Section: Account Credentials & User Details
        # ------------------------------------------------------------------
        cred_frame = ttk.LabelFrame(
            container, text=" Account Credentials ", padding=12
        )
        cred_frame.pack(fill="x", pady=(0, 15))

        # Username
        ttk.Label(cred_frame, text="Username:").pack(anchor="w", pady=(2, 2))
        self.ent_username = ttk.Entry(cred_frame)
        self.ent_username.pack(fill="x", pady=(0, 8))

        # Full Name
        ttk.Label(cred_frame, text="Full Name:").pack(anchor="w", pady=(2, 2))
        self.ent_full_name = ttk.Entry(cred_frame)
        self.ent_full_name.pack(fill="x", pady=(0, 8))

        # Mobile Number
        ttk.Label(cred_frame, text="Mobile Number:").pack(
            anchor="w", pady=(2, 2)
        )
        self.ent_mobile = ttk.Entry(cred_frame)
        self.ent_mobile.pack(fill="x", pady=(0, 8))

        # New Password
        ttk.Label(
            cred_frame, text="New Password (leave blank to keep current):"
        ).pack(anchor="w", pady=(2, 2))
        self.ent_password = ttk.Entry(cred_frame, show="*")
        self.ent_password.pack(fill="x", pady=(0, 8))

        # Role Designation
        ttk.Label(cred_frame, text="Role Designation:").pack(
            anchor="w", pady=(2, 2)
        )
        self.combo_role = ttk.Combobox(
            cred_frame, state="readonly", values=["User", "Admin"]
        )
        self.combo_role.set("User")
        self.combo_role.pack(fill="x", pady=(0, 4))

        # ------------------------------------------------------------------
        # Bottom Section: Controlled Window / Tab Permissions
        # ------------------------------------------------------------------
        perm_frame = ttk.LabelFrame(
            container, text=" Controlled Window / Tab Permissions ", padding=12
        )
        perm_frame.pack(fill="both", expand=True, pady=(0, 15))

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

        groups = {}
        labels = getattr(auth_manager, 'WINDOW_PERMISSION_LABELS', {})
        for permission in auth_manager.PERMISSION_HEADERS:
            label = labels.get(permission, permission.replace('allow_', '').replace('_', ' ').title())
            low = label.lower()
            if permission.startswith('allow_rnd'):
                group = 'R&D / Engineering'
            elif 'it' in low or 'iam' in low or 'assets' in low or 'helpdesk' in low or 'security' in low:
                group = 'IT'
            elif 'account' in low or 'inward' in low or 'outward' in low or 'vendor' in low or 'cheque' in low:
                group = 'Accounts & Finance'
            elif any(k in low for k in ('price', 'material', 'crm', 'sales', 'marketing')):
                group = 'Sales & Marketing'
            elif any(k in low for k in ('production', 'panel', 'manufacturing')):
                group = 'Production / Manufacturing'
            elif 'hr' in low or 'employee' in low:
                group = 'HR'
            elif 'legal' in low:
                group = 'Legal & Compliance'
            elif 'supply' in low or 'chain' in low:
                group = 'Supply Chain'
            elif 'admin' in low:
                group = 'Administration'
            else:
                group = 'Other'
            groups.setdefault(group, []).append((permission, label))

        for grp_name in sorted(groups.keys()):
            gf = ttk.LabelFrame(perm_inner, text=f" {grp_name} ", padding=8)
            gf.pack(fill="x", pady=(6, 6), padx=6)
            items = groups[grp_name]
            for idx, (perm, lbl) in enumerate(items):
                row = idx // 2
                col = idx % 2
                ttk.Checkbutton(
                    gf,
                    text=lbl,
                    variable=self.permission_vars[perm],
                ).grid(row=row, column=col, sticky="w", padx=8, pady=4)

        # ------------------------------------------------------------------
        # Bottom Action Buttons
        # ------------------------------------------------------------------
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(
            btn_frame,
            text="Save / Apply Permissions",
            command=self.save_user_details,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            btn_frame, text="Delete User", command=self.delete_user_account
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def load_accounts_dropdown(self):
        """Loads all accounts into dropdown displaying Name and Mobile Number."""
        self.users_cache = auth_manager.load_users()
        dropdown_list = ["-- Create New User --"]

        for u in self.users_cache:
            username = u.get("username", "")
            full_name = u.get("full_name", "")
            mobile = u.get("mobile_number", "")

            # Format item: admin (System Admin - 9876543210)
            details = []
            if full_name:
                details.append(full_name)
            if mobile:
                details.append(mobile)

            detail_str = f" ({' - '.join(details)})" if details else ""
            dropdown_list.append(f"{username}{detail_str}")

        self.combo_accounts["values"] = dropdown_list
        self.combo_accounts.set(dropdown_list[0])
        self.clear_fields()

    def on_account_selected(self, event):
        """Populates form fields when an account is selected from dropdown."""
        selected_text = self.combo_accounts.get()

        if selected_text == "-- Create New User --":
            self.selected_user = None
            self.clear_fields()
            self.ent_username.config(state="normal")
            return

        # Extract actual username from dropdown string
        username = selected_text.split(" (")[0].strip()
        user_data = next(
            (u for u in self.users_cache if u["username"] == username), None
        )

        if user_data:
            self.selected_user = user_data
            self.ent_username.config(state="normal")
            self.ent_username.delete(0, tk.END)
            self.ent_username.insert(0, user_data.get("username", ""))
            self.ent_username.config(state="disabled")  # Lock primary key

            self.ent_full_name.delete(0, tk.END)
            self.ent_full_name.insert(0, user_data.get("full_name", ""))

            self.ent_mobile.delete(0, tk.END)
            self.ent_mobile.insert(0, user_data.get("mobile_number", ""))

            self.ent_password.delete(0, tk.END)

            self.combo_role.set(user_data.get("role", "User"))

            # Populate dynamically-managed permission variables
            for p, var in self.permission_vars.items():
                var.set(user_data.get(p, True if p in ("allow_price", "allow_material") else False))

    def set_all_permissions(self, enabled):
        for permission, variable in self.permission_vars.items():
            variable.set(enabled)

    def reset_default_permissions(self):
        for permission, variable in self.permission_vars.items():
            default_val = permission in ("allow_price", "allow_material")
            variable.set(default_val)

    def clear_fields(self):
        """Clears all input fields."""
        self.ent_username.config(state="normal")
        self.ent_username.delete(0, tk.END)
        self.ent_full_name.delete(0, tk.END)
        self.ent_mobile.delete(0, tk.END)
        self.ent_password.delete(0, tk.END)
        self.combo_role.set("User")

        # Reset dynamic permission variables to defaults
        for p, var in self.permission_vars.items():
            default_val = True if p in ("allow_price", "allow_material") else False
            var.set(default_val)

    def save_user_details(self):
        """Saves or updates account with Full Name and Mobile Number."""
        username = self.ent_username.get().strip()
        full_name = self.ent_full_name.get().strip()
        mobile_number = self.ent_mobile.get().strip()
        password = self.ent_password.get().strip()
        role = self.combo_role.get()

        if not username:
            messagebox.showwarning(
                "Input Error", "Username is required.", parent=self
            )
            return

        if not self.selected_user and not password:
            messagebox.showwarning(
                "Input Error",
                "Password is required for new accounts.",
                parent=self,
            )
            return
        perm_data = {k: v.get() for k, v in self.permission_vars.items()}
        perm_data = {k: v.get() for k, v in self.permission_vars.items()}
        auth_manager.add_or_update_user(
            username=username,
            password=password if password else None,
            full_name=full_name,
            mobile_number=mobile_number,
            designation="",
            role=role,
            **perm_data,
        )

        messagebox.showinfo(
            "Success",
            f"Account details for '{username}' updated successfully!",
            parent=self,
        )
        self.load_accounts_dropdown()

    def delete_user_account(self):
        """Deletes selected user account."""
        if not self.selected_user:
            messagebox.showwarning(
                "Selection Error",
                "Please select an existing account to delete.",
                parent=self,
            )
            return

        username = self.selected_user["username"]

        if username == "admin":
            messagebox.showerror(
                "Action Denied",
                "Default 'admin' account cannot be deleted.",
                parent=self,
            )
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?",
            parent=self,
        ):
            auth_manager.delete_user(username)
            messagebox.showinfo(
                "Deleted", f"User '{username}' deleted.", parent=self
            )
            self.load_accounts_dropdown()


# Helper function to open dialog
def open_user_access_control_window(parent):
    dialog = UserAccessControlDialog(parent)
    parent.wait_window(dialog)