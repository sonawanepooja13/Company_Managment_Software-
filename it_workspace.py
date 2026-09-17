"""IT Workspace management module.

The module centralizes the core IT functions for a modern workplace:
- Streamlining Software & Hardware Provisioning
- Enforcing Cybersecurity & Compliance
- Centralized Helpdesk & Ticket Management
- Asset Lifecycle Tracking
- Identity and Access Management (IAM)
"""

import csv
import os
import tkinter as tk
from tkinter import messagebox, ttk

import config


class ITWorkspaceView(ttk.Frame):
    """Main IT workspace with dedicated tabs for provisioning, security, tickets, assets and IAM."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data or {}
        self.setup_ui()

    def setup_ui(self):
        intro = ttk.Label(
            self,
            text=(
                "IT Workspace • Provisioning, Security, Helpdesk, Asset Tracking, and IAM"
            ),
            font=("Helvetica", 12, "bold"),
        )
        intro.pack(anchor="w", pady=(0, 8))

        summary = ttk.Label(
            self,
            text=(
                "Streamlining Software & Hardware Provisioning • "
                "Enforcing Cybersecurity & Compliance • Centralized Helpdesk & Ticket Management • "
                "Asset Lifecycle Tracking • Identity and Access Management (IAM)"
            ),
            wraplength=980,
            justify="left",
        )
        summary.pack(anchor="w", pady=(0, 10))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.provisioning_tab = ProvisioningWorkspaceTab(self.notebook)
        self.notebook.add(self.provisioning_tab, text=" Provisioning ")

        self.security_tab = CybersecurityComplianceTab(self.notebook)
        self.notebook.add(self.security_tab, text=" Security & Compliance ")

        self.helpdesk_tab = HelpdeskTicketTab(self.notebook)
        self.notebook.add(self.helpdesk_tab, text=" Helpdesk ")

        self.asset_tab = AssetLifecycleTab(self.notebook)
        self.notebook.add(self.asset_tab, text=" Assets ")

        self.iam_tab = IdentityAccessTab(self.notebook)
        self.notebook.add(self.iam_tab, text=" IAM ")


class ITDataTab(ttk.Frame):
    """Reusable base frame for structured data management views."""

    def __init__(self, parent, title, csv_path, headers, summary_labels=None, extra_filter=None):
        super().__init__(parent, padding=12)
        self.title = title
        self.csv_path = csv_path
        self.headers = headers
        self.summary_labels = summary_labels or []
        self.extra_filter = extra_filter
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        if self.summary_labels:
            summary_frame = ttk.LabelFrame(self, text=" Overview ", padding=10)
            summary_frame.pack(fill="x", pady=(0, 10))
            for idx, label in enumerate(self.summary_labels):
                ttk.Label(summary_frame, text=label[0]).grid(
                    row=0, column=idx * 2, sticky="w", padx=(0, 5), pady=2
                )
                value_var = tk.StringVar(value=label[1])
                ttk.Label(
                    summary_frame,
                    textvariable=value_var,
                    font=("Helvetica", 10, "bold"),
                ).grid(row=0, column=(idx * 2) + 1, sticky="w", padx=(0, 15), pady=2)
                setattr(self, f"{label[2]}_var", value_var)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(control_frame, text="+ Add Record", command=self.add_record).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_record).pack(
            side="left", padx=5
        )
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_record).pack(
            side="left", padx=5
        )
        ttk.Button(control_frame, text="↻ Refresh", command=self.load_data).pack(
            side="left", padx=5
        )

        if self.extra_filter:
            filter_frame = ttk.Frame(self)
            filter_frame.pack(fill="x", pady=(0, 8))
            ttk.Label(filter_frame, text=self.extra_filter[0]).pack(side="left", padx=(0, 5))
            self.filter_combo = ttk.Combobox(
                filter_frame,
                values=self.extra_filter[1],
                state="readonly",
                width=24,
            )
            self.filter_combo.set(self.extra_filter[1][0])
            self.filter_combo.pack(side="left")
            self.filter_combo.bind("<<ComboboxSelected>>", self.filter_data)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree["columns"] = list(self.headers)
        for col in self.headers:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")

    def ensure_csv(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if os.path.exists(self.csv_path):
            return

        with open(self.csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(self.headers)
            writer.writerows(self.default_rows())

    def default_rows(self):
        return []

    def load_data(self):
        self.ensure_csv()
        with open(self.csv_path, mode="r", encoding="utf-8-sig") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)
        if not rows:
            return

        headers = rows[0]
        self.tree["columns"] = headers
        for h in headers:
            self.tree.heading(h, text=h.replace("_", " ").title())
            self.tree.column(h, width=120, anchor="w")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows[1:]:
            if len(row) == len(headers):
                self.tree.insert("", "end", values=row)

        if self.summary_labels:
            self.update_summary_values()

    def update_summary_values(self):
        pass

    def add_record(self):
        messagebox.showinfo(
            "IT Workspace",
            f"Add a new {self.title.lower()} record by extending the dataset in {self.csv_path}.",
            parent=self,
        )

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a record to edit.", parent=self)
            return
        messagebox.showinfo(
            "IT Workspace",
            f"Edit selected {self.title.lower()} record from the table.",
            parent=self,
        )

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a record to delete.", parent=self)
            return
        if messagebox.askyesno("Confirm Delete", "Delete the selected record?", parent=self):
            messagebox.showinfo("Deleted", "Selected record removed from view.", parent=self)

    def filter_data(self, event=None):
        if not self.extra_filter:
            return
        active_value = self.filter_combo.get()
        if active_value in (None, "All"):
            self.load_data()
            return
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and values[0] == active_value:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")


class ProvisioningWorkspaceTab(ITDataTab):
    """Tab focused on software and hardware onboarding."""

    def __init__(self, parent):
        headers = [
            "employee_name",
            "department",
            "requested_date",
            "laptop_model",
            "software_stack",
            "email_access",
            "status",
        ]
        self.title_text = "Provisioning"
        super().__init__(
            parent,
            title="Provisioning",
            csv_path=config.IT_PROVISIONING_CSV,
            headers=headers,
            summary_labels=[
                ("New Joinees", "0", "new_joinees"),
                ("Ready for Use", "0", "ready_for_use"),
                ("Pending", "0", "pending"),
            ],
            extra_filter=("Filter by Department", ["All", "Engineering", "Finance", "HR", "Sales"]),
        )

    def default_rows(self):
        return [
            ["Aisha Verma", "Engineering", "2026-08-24", "Dell Latitude 7440", "Microsoft 365, Jira, Slack", "Enabled", "Ready"],
            ["Daniel Lee", "Sales", "2026-08-25", "HP EliteBook 840", "Microsoft 365, Salesforce", "Enabled", "In Progress"],
        ]

    def update_summary_values(self):
        status_values = [self.tree.item(item, "values") for item in self.tree.get_children()]
        self.new_joinees_var.set(str(len(status_values)))
        self.ready_for_use_var.set(str(sum(1 for row in status_values if row[6].lower() == "ready")))
        self.pending_var.set(str(sum(1 for row in status_values if row[6].lower() in {"in progress", "pending"})))


class CybersecurityComplianceTab(ITDataTab):
    """Tab focused on MFA, password rules, data sharing controls and malware monitoring."""

    def __init__(self, parent):
        headers = [
            "control",
            "owner",
            "policy",
            "status",
            "next_review",
            "risk_level",
        ]
        super().__init__(
            parent,
            title="Security & Compliance",
            csv_path=config.IT_SECURITY_CSV,
            headers=headers,
            summary_labels=[
                ("Controls Active", "0", "controls_active"),
                ("At Risk", "0", "at_risk"),
                ("Pending Review", "0", "pending_review"),
            ],
            extra_filter=("Filter by Status", ["All", "Active", "Monitoring", "Needs Review"]),
        )

    def default_rows(self):
        return [
            ["MFA Enforcement", "Identity Team", "Require MFA for all remote and admin access", "Active", "2026-09-15", "Low"],
            ["Password Expiration", "IAM Team", "60-day rotation for privileged users", "Monitoring", "2026-08-30", "Medium"],
            ["File Sharing Restrictions", "Security Team", "Block external sharing outside approved groups", "Active", "2026-09-05", "Low"],
        ]

    def update_summary_values(self):
        status_values = [self.tree.item(item, "values") for item in self.tree.get_children()]
        self.controls_active_var.set(str(sum(1 for row in status_values if row[3].lower() == "active")))
        self.at_risk_var.set(str(sum(1 for row in status_values if row[5].lower() in {"high", "critical"})))
        self.pending_review_var.set(str(sum(1 for row in status_values if row[3].lower() == "needs review")))


class HelpdeskTicketTab(ITDataTab):
    """Tab focused on employee helpdesk tickets and issue resolution workflow."""

    def __init__(self, parent):
        headers = [
            "ticket_id",
            "employee",
            "issue",
            "priority",
            "status",
            "assigned_to",
            "sla_hours",
        ]
        super().__init__(
            parent,
            title="Helpdesk",
            csv_path=config.IT_TICKETS_CSV,
            headers=headers,
            summary_labels=[
                ("Open Tickets", "0", "open_tickets"),
                ("High Priority", "0", "high_priority"),
                ("Resolved Today", "0", "resolved_today"),
            ],
            extra_filter=("Filter by Priority", ["All", "Low", "Medium", "High", "Critical"]),
        )

    def default_rows(self):
        return [
            ["IT-1042", "Nina Foster", "VPN connection issue", "High", "Open", "A. Patel", "4"],
            ["IT-1045", "Martin Cruz", "Software upgrade request", "Medium", "In Progress", "K. Singh", "8"],
            ["IT-1051", "Sarah Ahmed", "Laptop battery replacement", "Low", "Resolved", "R. Shah", "2"],
        ]

    def update_summary_values(self):
        status_values = [self.tree.item(item, "values") for item in self.tree.get_children()]
        self.open_tickets_var.set(str(sum(1 for row in status_values if row[4].lower() in {"open", "in progress"})))
        self.high_priority_var.set(str(sum(1 for row in status_values if row[3].lower() in {"high", "critical"})))
        self.resolved_today_var.set(str(sum(1 for row in status_values if row[4].lower() == "resolved")))


class AssetLifecycleTab(ITDataTab):
    """Tab focused on lifecycle tracking of hardware and devices."""

    def __init__(self, parent):
        headers = [
            "asset_tag",
            "device_name",
            "type",
            "assigned_to",
            "purchase_date",
            "maintenance_due",
            "status",
            "retirement_date",
        ]
        super().__init__(
            parent,
            title="Asset Lifecycle",
            csv_path=config.IT_ASSETS_CSV,
            headers=headers,
            summary_labels=[
                ("Active Assets", "0", "active_assets"),
                ("Maintenance Due", "0", "maintenance_due"),
                ("Retired", "0", "retired"),
            ],
            extra_filter=("Filter by Type", ["All", "Laptop", "Monitor", "Mobile", "Server"]),
        )

    def default_rows(self):
        return [
            ["IT-1001", "Dell Latitude 7440", "Laptop", "Aisha Verma", "2025-06-10", "2026-09-10", "Assigned", ""],
            ["IT-1028", "Cisco Catalyst 9300", "Server", "Infrastructure Team", "2024-02-20", "2026-08-28", "Operational", ""],
            ["IT-1094", "Samsung Galaxy S24", "Mobile", "Daniel Lee", "2025-01-15", "2026-10-01", "Assigned", ""],
        ]

    def update_summary_values(self):
        status_values = [self.tree.item(item, "values") for item in self.tree.get_children()]
        self.active_assets_var.set(str(sum(1 for row in status_values if row[6].lower() == "assigned" or row[6].lower() == "operational")))
        self.maintenance_due_var.set(str(sum(1 for row in status_values if row[5] and row[5] <= "2026-09-30")))
        self.retired_var.set(str(sum(1 for row in status_values if row[7] and row[7] != "")))


class IdentityAccessTab(ITDataTab):
    """Tab focused on identity lifecycle and access governance."""

    def __init__(self, parent):
        headers = [
            "username",
            "employee_name",
            "role",
            "department",
            "access_scope",
            "last_review",
            "status",
        ]
        super().__init__(
            parent,
            title="IAM",
            csv_path=config.IT_IAM_CSV,
            headers=headers,
            summary_labels=[
                ("Active Accounts", "0", "active_accounts"),
                ("Role Changes", "0", "role_changes"),
                ("Revoked Access", "0", "revoked_access"),
            ],
            extra_filter=("Filter by Role", ["All", "Admin", "Manager", "User"]),
        )

    def default_rows(self):
        return [
            ["averma", "Aisha Verma", "Engineer", "Engineering", "ERP, GitHub, Jira", "2026-08-20", "Active"],
            ["dlee", "Daniel Lee", "Sales Manager", "Sales", "Salesforce, CRM", "2026-08-18", "Active"],
            ["rshah", "Rohit Shah", "IT Admin", "IT", "AD, VPN, Monitoring", "2026-08-22", "Active"],
        ]

    def update_summary_values(self):
        status_values = [self.tree.item(item, "values") for item in self.tree.get_children()]
        self.active_accounts_var.set(str(sum(1 for row in status_values if row[6].lower() == "active")))
        self.role_changes_var.set(str(sum(1 for row in status_values if row[2].lower() in {"manager", "admin"})))
        self.revoked_access_var.set(str(sum(1 for row in status_values if row[6].lower() == "revoked")))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("IT Workspace Demo")
    root.geometry("1100x700")
    ITWorkspaceView(root).pack(fill="both", expand=True)
    root.mainloop()
