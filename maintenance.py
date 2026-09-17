import csv
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk, filedialog
import config


class MaintenanceView(ttk.Frame):
    """Main Company Maintenance (CMMS/EAM) Module with tabbed interface."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        # Create notebook for different maintenance components
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Add tabs for each component
        self.assets_tab = AssetHierarchyTab(self.notebook)
        self.notebook.add(self.assets_tab, text=" Asset Hierarchy ")

        self.work_orders_tab = WorkOrderManagementTab(self.notebook)
        self.notebook.add(self.work_orders_tab, text=" Work Orders ")

        self.preventive_tab = PreventiveMaintenanceTab(self.notebook)
        self.notebook.add(self.preventive_tab, text=" Preventive Maintenance ")

        self.inventory_tab = SparePartsInventoryTab(self.notebook)
        self.notebook.add(self.inventory_tab, text=" Spare Parts Inventory ")

        self.compliance_tab = ComplianceSafetyTab(self.notebook)
        self.notebook.add(self.compliance_tab, text=" Compliance & Safety ")

        self.vendors_tab = MaintenanceVendorsTab(self.notebook)
        self.notebook.add(self.vendors_tab, text=" Maintenance Vendors ")

        self.iot_tab = IoTIntegrationTab(self.notebook)
        self.notebook.add(self.iot_tab, text=" IoT & Sensors ")


class AssetHierarchyTab(ttk.Frame):
    """Asset and Equipment Hierarchy - Detailed asset profiles with parent-child relationships."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_assets()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Asset Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Assets:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_assets_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_assets_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Critical Assets:").grid(row=0, column=2, sticky="w", padx=5)
        self.critical_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.critical_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Warranty Expiring:").grid(row=0, column=4, sticky="w", padx=5)
        self.warranty_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.warranty_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Asset", command=self.add_asset).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_asset).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_asset).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_assets).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Category:").pack(side="left", padx=5)
        self.category_filter = ttk.Combobox(filter_frame, values=["All", "Machinery", "Vehicles", "IT Hardware", "HVAC", "Electrical", "Other"], width=20, state="readonly")
        self.category_filter.set("All")
        self.category_filter.pack(side="left", padx=5)
        self.category_filter.bind("<<ComboboxSelected>>", self.filter_assets)

        # Assets table
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

        columns = ["asset_id", "asset_name", "category", "serial_number", "parent_asset", "location", "installation_date", "warranty_expiry", "status", "criticality"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_assets(self):
        csv_file = getattr(config, "ASSETS_CSV", os.path.join(config.CSV_DIR, "assets.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def filter_assets(self, event=None):
        filter_category = self.category_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_category == "All" or values[2] == filter_category:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        critical = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 9 and self.tree.item(item, "values")[9] == "Critical")
        warranty_expiring = 0
        today = datetime.now()
        warning_days = 90

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 7 and values[7]:  # warranty_expiry
                try:
                    warranty_date = datetime.strptime(values[7], "%Y-%m-%d")
                    days_until_expiry = (warranty_date - today).days
                    if 0 <= days_until_expiry <= warning_days:
                        warranty_expiring += 1
                except ValueError:
                    pass

        self.total_assets_var.set(str(total))
        self.critical_var.set(str(critical))
        self.warranty_var.set(str(warranty_expiring))

    def add_asset(self):
        AssetDialog(self, callback=self.load_assets)

    def edit_asset(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Asset", "Please select an asset to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        AssetDialog(self, callback=self.load_assets, edit_values=item_values)

    def delete_asset(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Asset", "Please select an asset to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this asset?", parent=self):
            csv_file = getattr(config, "ASSETS_CSV", os.path.join(config.CSV_DIR, "assets.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_assets()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class AssetDialog(tk.Toplevel):
    """Dialog for asset management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Asset" if self.is_edit else "Add New Asset")
        self.geometry("600x650")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Asset Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Category dropdown
        ttk.Label(frame, text="Category*:").grid(row=0, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(frame, values=["Machinery", "Vehicles", "IT Hardware", "HVAC", "Electrical", "Other"], width=30, state="readonly")
        self.category_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Asset Name*", "asset_name"),
            ("Serial Number", "serial_number"),
            ("Parent Asset ID", "parent_asset"),
            ("Location*", "location"),
            ("Installation Date", "installation_date"),
            ("Warranty Expiry", "warranty_expiry"),
            ("Manufacturer", "manufacturer"),
            ("Model", "model"),
            ("Manual Path", "manual_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button for manual
        ttk.Button(frame, text="Browse Manual", command=self.browse_manual).grid(row=9, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=10, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Operational", "Under Maintenance", "Out of Service", "Retired"], width=30, state="readonly")
        self.status_combo.set("Operational")
        self.status_combo.grid(row=10, column=1, sticky="w", pady=5)

        # Criticality dropdown
        ttk.Label(frame, text="Criticality:").grid(row=11, column=0, sticky="w", pady=5)
        self.criticality_combo = ttk.Combobox(frame, values=["Low", "Medium", "High", "Critical"], width=30, state="readonly")
        self.criticality_combo.set("Medium")
        self.criticality_combo.grid(row=11, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=12, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=12, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Asset", command=self.save_asset).pack(pady=15)

    def browse_manual(self):
        file_path = filedialog.askopenfilename(
            title="Select Equipment Manual",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["manual_path"].delete(0, tk.END)
            self.entries["manual_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.category_combo.set(values[2])
            self.entries["asset_name"].insert(0, values[1])
            self.entries["serial_number"].insert(0, values[3])
            self.entries["parent_asset"].insert(0, values[4])
            self.entries["location"].insert(0, values[5])
            self.entries["installation_date"].insert(0, values[6])
            self.entries["warranty_expiry"].insert(0, values[7])
            self.status_combo.set(values[8])
            self.criticality_combo.set(values[9])
            self.entries["manufacturer"].insert(0, values[10] if len(values) > 10 else "")
            self.entries["model"].insert(0, values[11] if len(values) > 11 else "")
            self.entries["manual_path"].insert(0, values[12] if len(values) > 12 else "")
            self.notes_text.insert("1.0", values[13] if len(values) > 13 else "")
        except IndexError:
            pass

    def save_asset(self):
        asset_name = self.entries["asset_name"].get().strip()
        category = self.category_combo.get()
        location = self.entries["location"].get().strip()

        if not asset_name or not category or not location:
            messagebox.showwarning("Input Error", "Asset name, category, and location are required.", parent=self)
            return

        csv_file = getattr(config, "ASSETS_CSV", os.path.join(config.CSV_DIR, "assets.csv"))
        asset_id = f"AST-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            asset_id,
            asset_name,
            category,
            self.entries["serial_number"].get().strip(),
            self.entries["parent_asset"].get().strip(),
            location,
            self.entries["installation_date"].get().strip(),
            self.entries["warranty_expiry"].get().strip(),
            self.status_combo.get(),
            self.criticality_combo.get(),
            self.entries["manufacturer"].get().strip(),
            self.entries["model"].get().strip(),
            self.entries["manual_path"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["asset_id", "asset_name", "category", "serial_number", "parent_asset", "location", "installation_date", "warranty_expiry", "status", "criticality", "manufacturer", "model", "manual_path", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Asset '{asset_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save asset: {e}", parent=self)


class WorkOrderManagementTab(ttk.Frame):
    """Work Order Management - The core engine for maintenance requests and tracking."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_work_orders()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Work Order Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total WOs:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_wo_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_wo_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Emergency:").grid(row=0, column=2, sticky="w", padx=5)
        self.emergency_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.emergency_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="In Progress:").grid(row=0, column=4, sticky="w", padx=5)
        self.in_progress_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.in_progress_var, font=("Helvetica", 10, "bold"), foreground="blue").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Work Order", command=self.add_work_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_work_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_work_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_work_orders).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Status:").pack(side="left", padx=5)
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Requested", "Approved", "Assigned", "In Progress", "Completed", "On Hold"], width=20, state="readonly")
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.bind("<<ComboboxSelected>>", self.filter_work_orders)

        # Work orders table
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

        columns = ["wo_id", "asset_id", "asset_name", "wo_type", "priority", "status", "assigned_to", "created_date", "target_date", "estimated_hours", "actual_hours", "labor_cost", "parts_cost"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=90, anchor="w")

    def load_work_orders(self):
        csv_file = getattr(config, "WORK_ORDERS_CSV", os.path.join(config.CSV_DIR, "work_orders.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=90, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def filter_work_orders(self, event=None):
        filter_status = self.status_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_status == "All" or values[5] == filter_status:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        emergency = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 4 and self.tree.item(item, "values")[4] == "Emergency")
        in_progress = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 5 and self.tree.item(item, "values")[5] == "In Progress")
        self.total_wo_var.set(str(total))
        self.emergency_var.set(str(emergency))
        self.in_progress_var.set(str(in_progress))

    def add_work_order(self):
        WorkOrderDialog(self, callback=self.load_work_orders)

    def edit_work_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Work Order", "Please select a work order to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        WorkOrderDialog(self, callback=self.load_work_orders, edit_values=item_values)

    def delete_work_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Work Order", "Please select a work order to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this work order?", parent=self):
            csv_file = getattr(config, "WORK_ORDERS_CSV", os.path.join(config.CSV_DIR, "work_orders.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_work_orders()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class WorkOrderDialog(tk.Toplevel):
    """Dialog for work order management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Work Order" if self.is_edit else "New Work Order")
        self.geometry("650x700")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Work Order Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Work order type dropdown
        ttk.Label(frame, text="WO Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.wo_type_combo = ttk.Combobox(frame, values=["Breakdown", "Inspection", "Preventive", "Corrective", "Project"], width=30, state="readonly")
        self.wo_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Priority dropdown
        ttk.Label(frame, text="Priority*:").grid(row=1, column=0, sticky="w", pady=5)
        self.priority_combo = ttk.Combobox(frame, values=["Emergency", "High", "Medium", "Low"], width=30, state="readonly")
        self.priority_combo.set("Medium")
        self.priority_combo.grid(row=1, column=1, sticky="w", pady=5)

        fields = [
            ("Asset ID*", "asset_id"),
            ("Asset Name", "asset_name"),
            ("Assigned To", "assigned_to"),
            ("Created Date*", "created_date"),
            ("Target Date", "target_date"),
            ("Estimated Hours", "estimated_hours"),
            ("Actual Hours", "actual_hours"),
            ("Labor Cost", "labor_cost"),
            ("Parts Cost", "parts_cost"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+2, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+2, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=11, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Requested", "Approved", "Assigned", "In Progress", "Completed", "On Hold"], width=30, state="readonly")
        self.status_combo.set("Requested")
        self.status_combo.grid(row=11, column=1, sticky="w", pady=5)

        # Description
        ttk.Label(frame, text="Description:").grid(row=12, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=30, height=4)
        self.description_text.grid(row=12, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Work Order", command=self.save_work_order).pack(pady=15)

    def populate_values(self, values):
        try:
            self.wo_type_combo.set(values[3])
            self.priority_combo.set(values[4])
            self.entries["asset_id"].insert(0, values[1])
            self.entries["asset_name"].insert(0, values[2])
            self.status_combo.set(values[5])
            self.entries["assigned_to"].insert(0, values[6])
            self.entries["created_date"].insert(0, values[7])
            self.entries["target_date"].insert(0, values[8])
            self.entries["estimated_hours"].insert(0, values[9])
            self.entries["actual_hours"].insert(0, values[10])
            self.entries["labor_cost"].insert(0, values[11])
            self.entries["parts_cost"].insert(0, values[12])
            self.description_text.insert("1.0", values[13] if len(values) > 13 else "")
        except IndexError:
            pass

    def save_work_order(self):
        wo_type = self.wo_type_combo.get()
        priority = self.priority_combo.get()
        asset_id = self.entries["asset_id"].get().strip()
        created_date = self.entries["created_date"].get().strip()

        if not wo_type or not priority or not asset_id or not created_date:
            messagebox.showwarning("Input Error", "WO type, priority, asset ID, and created date are required.", parent=self)
            return

        csv_file = getattr(config, "WORK_ORDERS_CSV", os.path.join(config.CSV_DIR, "work_orders.csv"))
        wo_id = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            wo_id,
            asset_id,
            self.entries["asset_name"].get().strip(),
            wo_type,
            priority,
            self.status_combo.get(),
            self.entries["assigned_to"].get().strip(),
            created_date,
            self.entries["target_date"].get().strip(),
            self.entries["estimated_hours"].get().strip(),
            self.entries["actual_hours"].get().strip(),
            self.entries["labor_cost"].get().strip(),
            self.entries["parts_cost"].get().strip(),
            self.description_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["wo_id", "asset_id", "asset_name", "wo_type", "priority", "status", "assigned_to", "created_date", "target_date", "estimated_hours", "actual_hours", "labor_cost", "parts_cost", "description"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Work Order '{wo_id}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save work order: {e}", parent=self)


class PreventiveMaintenanceTab(ttk.Frame):
    """Preventive and Predictive Maintenance - Scheduled routines and IoT integration."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_pm_schedules()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" PM Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Active PMs:").grid(row=0, column=0, sticky="w", padx=5)
        self.active_pm_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_pm_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Due This Week:").grid(row=0, column=2, sticky="w", padx=5)
        self.due_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.due_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Overdue:").grid(row=0, column=4, sticky="w", padx=5)
        self.overdue_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.overdue_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New PM Schedule", command=self.add_pm_schedule).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_pm_schedule).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_pm_schedule).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_pm_schedules).pack(side="left", padx=5)

        # PM schedules table
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

        columns = ["pm_id", "asset_id", "asset_name", "pm_type", "frequency", "last_performed", "next_due", "trigger_type", "trigger_value", "status", "assigned_tech"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_pm_schedules(self):
        csv_file = getattr(config, "PM_SCHEDULES_CSV", os.path.join(config.CSV_DIR, "pm_schedules.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def update_summary(self):
        total = len(self.tree.get_children())
        active = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 9 and self.tree.item(item, "values")[9] == "Active")
        due_this_week = 0
        overdue = 0
        today = datetime.now()
        week_from_now = today + timedelta(days=7)

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 6 and values[6]:  # next_due
                try:
                    next_due = datetime.strptime(values[6], "%Y-%m-%d")
                    if next_due < today:
                        overdue += 1
                    elif today <= next_due <= week_from_now:
                        due_this_week += 1
                except ValueError:
                    pass

        self.active_pm_var.set(str(active))
        self.due_var.set(str(due_this_week))
        self.overdue_var.set(str(overdue))

    def add_pm_schedule(self):
        PMScheduleDialog(self, callback=self.load_pm_schedules)

    def edit_pm_schedule(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select PM Schedule", "Please select a PM schedule to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        PMScheduleDialog(self, callback=self.load_pm_schedules, edit_values=item_values)

    def delete_pm_schedule(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select PM Schedule", "Please select a PM schedule to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this PM schedule?", parent=self):
            csv_file = getattr(config, "PM_SCHEDULES_CSV", os.path.join(config.CSV_DIR, "pm_schedules.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_pm_schedules()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class PMScheduleDialog(tk.Toplevel):
    """Dialog for preventive maintenance schedules."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit PM Schedule" if self.is_edit else "New PM Schedule")
        self.geometry("600x600")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Preventive Maintenance Schedule", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # PM type dropdown
        ttk.Label(frame, text="PM Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.pm_type_combo = ttk.Combobox(frame, values=["Time-Based", "Usage-Based", "Condition-Based", "Predictive"], width=30, state="readonly")
        self.pm_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Trigger type dropdown
        ttk.Label(frame, text="Trigger Type*:").grid(row=1, column=0, sticky="w", pady=5)
        self.trigger_type_combo = ttk.Combobox(frame, values=["Calendar Days", "Operating Hours", "Mileage", "Sensor Reading", "Production Count"], width=30, state="readonly")
        self.trigger_type_combo.grid(row=1, column=1, sticky="w", pady=5)

        fields = [
            ("Asset ID*", "asset_id"),
            ("Asset Name", "asset_name"),
            ("Frequency/Value*", "frequency"),
            ("Last Performed", "last_performed"),
            ("Next Due*", "next_due"),
            ("Assigned Technician", "assigned_tech"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+2, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+2, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=8, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "Inactive", "Suspended"], width=30, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=8, column=1, sticky="w", pady=5)

        # Description
        ttk.Label(frame, text="Description:").grid(row=9, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=30, height=3)
        self.description_text.grid(row=9, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save PM Schedule", command=self.save_pm_schedule).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["asset_id"].insert(0, values[1])
            self.entries["asset_name"].insert(0, values[2])
            self.pm_type_combo.set(values[3])
            self.entries["frequency"].insert(0, values[4])
            self.entries["last_performed"].insert(0, values[5])
            self.entries["next_due"].insert(0, values[6])
            self.trigger_type_combo.set(values[7])
            self.entries["assigned_tech"].insert(0, values[10] if len(values) > 10 else "")
            self.status_combo.set(values[9])
            self.description_text.insert("1.0", values[11] if len(values) > 11 else "")
        except IndexError:
            pass

    def save_pm_schedule(self):
        pm_type = self.pm_type_combo.get()
        trigger_type = self.trigger_type_combo.get()
        asset_id = self.entries["asset_id"].get().strip()
        frequency = self.entries["frequency"].get().strip()
        next_due = self.entries["next_due"].get().strip()

        if not pm_type or not trigger_type or not asset_id or not frequency or not next_due:
            messagebox.showwarning("Input Error", "PM type, trigger type, asset ID, frequency, and next due date are required.", parent=self)
            return

        csv_file = getattr(config, "PM_SCHEDULES_CSV", os.path.join(config.CSV_DIR, "pm_schedules.csv"))
        pm_id = f"PM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            pm_id,
            asset_id,
            self.entries["asset_name"].get().strip(),
            pm_type,
            frequency,
            self.entries["last_performed"].get().strip(),
            next_due,
            trigger_type,
            self.entries["frequency"].get().strip(),  # trigger_value same as frequency
            self.status_combo.get(),
            self.entries["assigned_tech"].get().strip(),
            self.description_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["pm_id", "asset_id", "asset_name", "pm_type", "frequency", "last_performed", "next_due", "trigger_type", "trigger_value", "status", "assigned_tech", "description"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"PM Schedule '{pm_id}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PM schedule: {e}", parent=self)


class SparePartsInventoryTab(ttk.Frame):
    """Inventory and Spare Parts Management - Stock alerts and vendor management."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_inventory()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Inventory Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Parts:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_parts_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_parts_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Low Stock:").grid(row=0, column=2, sticky="w", padx=5)
        self.low_stock_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.low_stock_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Out of Stock:").grid(row=0, column=4, sticky="w", padx=5)
        self.out_of_stock_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.out_of_stock_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Part", command=self.add_part).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_part).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_part).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_inventory).pack(side="left", padx=5)

        # Inventory table
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

        columns = ["part_id", "part_name", "part_number", "category", "quantity", "reorder_level", "unit_cost", "vendor", "location", "last_ordered"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_inventory(self):
        csv_file = getattr(config, "SPARE_PARTS_CSV", os.path.join(config.CSV_DIR, "spare_parts.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def update_summary(self):
        total = len(self.tree.get_children())
        low_stock = 0
        out_of_stock = 0

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 5:
                try:
                    quantity = int(values[4])
                    reorder_level = int(values[5])
                    if quantity == 0:
                        out_of_stock += 1
                    elif quantity <= reorder_level:
                        low_stock += 1
                except (ValueError, IndexError):
                    pass

        self.total_parts_var.set(str(total))
        self.low_stock_var.set(str(low_stock))
        self.out_of_stock_var.set(str(out_of_stock))

    def add_part(self):
        SparePartDialog(self, callback=self.load_inventory)

    def edit_part(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Part", "Please select a part to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        SparePartDialog(self, callback=self.load_inventory, edit_values=item_values)

    def delete_part(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Part", "Please select a part to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this part?", parent=self):
            csv_file = getattr(config, "SPARE_PARTS_CSV", os.path.join(config.CSV_DIR, "spare_parts.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_inventory()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class SparePartDialog(tk.Toplevel):
    """Dialog for spare parts management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Part" if self.is_edit else "Add Spare Part")
        self.geometry("550x550")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Spare Parts Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Category dropdown
        ttk.Label(frame, text="Category*:").grid(row=0, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(frame, values=["Electrical", "Mechanical", "Hydraulic", "Pneumatic", "IT Components", "Other"], width=30, state="readonly")
        self.category_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Part Name*", "part_name"),
            ("Part Number", "part_number"),
            ("Quantity*", "quantity"),
            ("Reorder Level*", "reorder_level"),
            ("Unit Cost", "unit_cost"),
            ("Vendor", "vendor"),
            ("Location*", "location"),
            ("Last Ordered", "last_ordered"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=9, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=9, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Part", command=self.save_part).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["part_name"].insert(0, values[1])
            self.entries["part_number"].insert(0, values[2])
            self.category_combo.set(values[3])
            self.entries["quantity"].insert(0, values[4])
            self.entries["reorder_level"].insert(0, values[5])
            self.entries["unit_cost"].insert(0, values[6])
            self.entries["vendor"].insert(0, values[7])
            self.entries["location"].insert(0, values[8])
            self.entries["last_ordered"].insert(0, values[9])
            self.notes_text.insert("1.0", values[10] if len(values) > 10 else "")
        except IndexError:
            pass

    def save_part(self):
        part_name = self.entries["part_name"].get().strip()
        category = self.category_combo.get()
        quantity = self.entries["quantity"].get().strip()
        reorder_level = self.entries["reorder_level"].get().strip()
        location = self.entries["location"].get().strip()

        if not part_name or not category or not quantity or not reorder_level or not location:
            messagebox.showwarning("Input Error", "Part name, category, quantity, reorder level, and location are required.", parent=self)
            return

        csv_file = getattr(config, "SPARE_PARTS_CSV", os.path.join(config.CSV_DIR, "spare_parts.csv"))
        part_id = f"PART-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            part_id,
            part_name,
            self.entries["part_number"].get().strip(),
            category,
            quantity,
            reorder_level,
            self.entries["unit_cost"].get().strip(),
            self.entries["vendor"].get().strip(),
            location,
            self.entries["last_ordered"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["part_id", "part_name", "part_number", "category", "quantity", "reorder_level", "unit_cost", "vendor", "location", "last_ordered", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Part '{part_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save part: {e}", parent=self)


class ComplianceSafetyTab(ttk.Frame):
    """Compliance, Safety, and Auditing - LOTO procedures and regulatory logs."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_compliance_records()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Compliance Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Records:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_records_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_records_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Pending Inspections:").grid(row=0, column=2, sticky="w", padx=5)
        self.pending_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.pending_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="LOTO Procedures:").grid(row=0, column=4, sticky="w", padx=5)
        self.loto_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.loto_var, font=("Helvetica", 10, "bold"), foreground="blue").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Record", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_record).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_record).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_compliance_records).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Type:").pack(side="left", padx=5)
        self.type_filter = ttk.Combobox(filter_frame, values=["All", "LOTO Procedure", "Safety Inspection", "EHS Audit", "Regulatory Compliance"], width=25, state="readonly")
        self.type_filter.set("All")
        self.type_filter.pack(side="left", padx=5)
        self.type_filter.bind("<<ComboboxSelected>>", self.filter_records)

        # Compliance table
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

        columns = ["record_id", "record_type", "asset_id", "asset_name", "inspection_date", "next_inspection", "inspector", "status", "findings", "regulatory_body"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_compliance_records(self):
        csv_file = getattr(config, "COMPLIANCE_CSV", os.path.join(config.CSV_DIR, "compliance_records.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def filter_records(self, event=None):
        filter_type = self.type_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_type == "All" or values[1] == filter_type:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        pending = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 7 and self.tree.item(item, "values")[7] == "Pending")
        loto_count = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 1 and "LOTO" in self.tree.item(item, "values")[1])
        self.total_records_var.set(str(total))
        self.pending_var.set(str(pending))
        self.loto_var.set(str(loto_count))

    def add_record(self):
        ComplianceDialog(self, callback=self.load_compliance_records)

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ComplianceDialog(self, callback=self.load_compliance_records, edit_values=item_values)

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?", parent=self):
            csv_file = getattr(config, "COMPLIANCE_CSV", os.path.join(config.CSV_DIR, "compliance_records.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_compliance_records()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class ComplianceDialog(tk.Toplevel):
    """Dialog for compliance and safety records."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Record" if self.is_edit else "Add Compliance Record")
        self.geometry("600x650")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Compliance & Safety Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Record type dropdown
        ttk.Label(frame, text="Record Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.record_type_combo = ttk.Combobox(frame, values=["LOTO Procedure", "Safety Inspection", "EHS Audit", "Regulatory Compliance"], width=30, state="readonly")
        self.record_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Asset ID", "asset_id"),
            ("Asset Name", "asset_name"),
            ("Inspection Date*", "inspection_date"),
            ("Next Inspection", "next_inspection"),
            ("Inspector*", "inspector"),
            ("Regulatory Body", "regulatory_body"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Compliant", "Non-Compliant", "Pending", "Corrective Action Required"], width=30, state="readonly")
        self.status_combo.set("Pending")
        self.status_combo.grid(row=7, column=1, sticky="w", pady=5)

        # Findings
        ttk.Label(frame, text="Findings:").grid(row=8, column=0, sticky="nw", pady=5)
        self.findings_text = tk.Text(frame, width=30, height=4)
        self.findings_text.grid(row=8, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=9, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=9, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Record", command=self.save_record).pack(pady=15)

    def populate_values(self, values):
        try:
            self.record_type_combo.set(values[1])
            self.entries["asset_id"].insert(0, values[2])
            self.entries["asset_name"].insert(0, values[3])
            self.entries["inspection_date"].insert(0, values[4])
            self.entries["next_inspection"].insert(0, values[5])
            self.entries["inspector"].insert(0, values[6])
            self.status_combo.set(values[7])
            self.findings_text.insert("1.0", values[8])
            self.entries["regulatory_body"].insert(0, values[9] if len(values) > 9 else "")
            self.notes_text.insert("1.0", values[10] if len(values) > 10 else "")
        except IndexError:
            pass

    def save_record(self):
        record_type = self.record_type_combo.get()
        inspection_date = self.entries["inspection_date"].get().strip()
        inspector = self.entries["inspector"].get().strip()

        if not record_type or not inspection_date or not inspector:
            messagebox.showwarning("Input Error", "Record type, inspection date, and inspector are required.", parent=self)
            return

        csv_file = getattr(config, "COMPLIANCE_CSV", os.path.join(config.CSV_DIR, "compliance_records.csv"))
        record_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            record_id,
            record_type,
            self.entries["asset_id"].get().strip(),
            self.entries["asset_name"].get().strip(),
            inspection_date,
            self.entries["next_inspection"].get().strip(),
            inspector,
            self.status_combo.get(),
            self.findings_text.get("1.0", tk.END).strip(),
            self.entries["regulatory_body"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["record_id", "record_type", "asset_id", "asset_name", "inspection_date", "next_inspection", "inspector", "status", "findings", "regulatory_body", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Compliance record saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save record: {e}", parent=self)


class MaintenanceVendorsTab(ttk.Frame):
    """Vendor Management for maintenance suppliers and parts."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_vendors()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Vendor Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Vendors:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_vendors_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_vendors_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Active Contracts:").grid(row=0, column=2, sticky="w", padx=5)
        self.active_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Vendor", command=self.add_vendor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_vendor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_vendor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_vendors).pack(side="left", padx=5)

        # Vendors table
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

        columns = ["vendor_id", "vendor_name", "contact_person", "email", "phone", "specialization", "contract_status", "rating", "delivery_time", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_vendors(self):
        csv_file = getattr(config, "MAINTENANCE_VENDORS_CSV", os.path.join(config.CSV_DIR, "maintenance_vendors.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def update_summary(self):
        total = len(self.tree.get_children())
        active = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 6 and self.tree.item(item, "values")[6] == "Active")
        self.total_vendors_var.set(str(total))
        self.active_var.set(str(active))

    def add_vendor(self):
        MaintenanceVendorDialog(self, callback=self.load_vendors)

    def edit_vendor(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Vendor", "Please select a vendor to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        MaintenanceVendorDialog(self, callback=self.load_vendors, edit_values=item_values)

    def delete_vendor(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Vendor", "Please select a vendor to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this vendor?", parent=self):
            csv_file = getattr(config, "MAINTENANCE_VENDORS_CSV", os.path.join(config.CSV_DIR, "maintenance_vendors.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_vendors()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class MaintenanceVendorDialog(tk.Toplevel):
    """Dialog for maintenance vendor management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Vendor" if self.is_edit else "Add Maintenance Vendor")
        self.geometry("550x500")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Maintenance Vendor Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Specialization dropdown
        ttk.Label(frame, text="Specialization*:").grid(row=0, column=0, sticky="w", pady=5)
        self.specialization_combo = ttk.Combobox(frame, values=["Electrical", "Mechanical", "HVAC", "IT Hardware", "General Maintenance", "Spare Parts"], width=30, state="readonly")
        self.specialization_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Vendor Name*", "vendor_name"),
            ("Contact Person", "contact_person"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Rating (1-5)", "rating"),
            ("Delivery Time (days)", "delivery_time"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Contract status dropdown
        ttk.Label(frame, text="Contract Status:").grid(row=7, column=0, sticky="w", pady=5)
        self.contract_status_combo = ttk.Combobox(frame, values=["Active", "Inactive", "Pending", "Expired"], width=30, state="readonly")
        self.contract_status_combo.set("Active")
        self.contract_status_combo.grid(row=7, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=8, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Vendor", command=self.save_vendor).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["vendor_name"].insert(0, values[1])
            self.entries["contact_person"].insert(0, values[2])
            self.entries["email"].insert(0, values[3])
            self.entries["phone"].insert(0, values[4])
            self.specialization_combo.set(values[5])
            self.contract_status_combo.set(values[6])
            self.entries["rating"].insert(0, values[7])
            self.entries["delivery_time"].insert(0, values[8])
            self.notes_text.insert("1.0", values[9] if len(values) > 9 else "")
        except IndexError:
            pass

    def save_vendor(self):
        vendor_name = self.entries["vendor_name"].get().strip()
        specialization = self.specialization_combo.get()

        if not vendor_name or not specialization:
            messagebox.showwarning("Input Error", "Vendor name and specialization are required.", parent=self)
            return

        csv_file = getattr(config, "MAINTENANCE_VENDORS_CSV", os.path.join(config.CSV_DIR, "maintenance_vendors.csv"))
        vendor_id = f"VEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            vendor_id,
            vendor_name,
            self.entries["contact_person"].get().strip(),
            self.entries["email"].get().strip(),
            self.entries["phone"].get().strip(),
            specialization,
            self.contract_status_combo.get(),
            self.entries["rating"].get().strip(),
            self.entries["delivery_time"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["vendor_id", "vendor_name", "contact_person", "email", "phone", "specialization", "contract_status", "rating", "delivery_time", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Vendor '{vendor_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save vendor: {e}", parent=self)


class IoTIntegrationTab(ttk.Frame):
    """IoT & Sensor Integration - Modern maintenance with live data monitoring."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_sensors()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" IoT Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Sensors:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_sensors_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_sensors_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Active Alerts:").grid(row=0, column=2, sticky="w", padx=5)
        self.alerts_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.alerts_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Online:").grid(row=0, column=4, sticky="w", padx=5)
        self.online_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.online_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Sensor", command=self.add_sensor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_sensor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_sensor).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_sensors).pack(side="left", padx=5)

        # Sensors table
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

        columns = ["sensor_id", "sensor_name", "asset_id", "sensor_type", "measurement_type", "current_value", "threshold_min", "threshold_max", "status", "last_reading", "location"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_sensors(self):
        csv_file = getattr(config, "IOT_SENSORS_CSV", os.path.join(config.CSV_DIR, "iot_sensors.csv"))
        self.populate_table(csv_file)
        self.update_summary()

    def populate_table(self, csv_file):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=100, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def update_summary(self):
        total = len(self.tree.get_children())
        alerts = 0
        online = 0

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 8:
                if values[8] == "Alert":
                    alerts += 1
                elif values[8] == "Online":
                    online += 1

        self.total_sensors_var.set(str(total))
        self.alerts_var.set(str(alerts))
        self.online_var.set(str(online))

    def add_sensor(self):
        IoTSensorDialog(self, callback=self.load_sensors)

    def edit_sensor(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Sensor", "Please select a sensor to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        IoTSensorDialog(self, callback=self.load_sensors, edit_values=item_values)

    def delete_sensor(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Sensor", "Please select a sensor to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this sensor?", parent=self):
            csv_file = getattr(config, "IOT_SENSORS_CSV", os.path.join(config.CSV_DIR, "iot_sensors.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_sensors()

    def delete_row_from_csv(self, csv_file, row_index):
        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if row_index + 1 < len(rows):
            del rows[row_index + 1]

        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class IoTSensorDialog(tk.Toplevel):
    """Dialog for IoT sensor management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Sensor" if self.is_edit else "Add IoT Sensor")
        self.geometry("550x580")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="IoT Sensor Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Sensor type dropdown
        ttk.Label(frame, text="Sensor Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.sensor_type_combo = ttk.Combobox(frame, values=["Vibration", "Temperature", "Pressure", "Humidity", "Flow Rate", "Current", "Voltage", "Other"], width=30, state="readonly")
        self.sensor_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Measurement type dropdown
        ttk.Label(frame, text="Measurement Type*:").grid(row=1, column=0, sticky="w", pady=5)
        self.measurement_combo = ttk.Combobox(frame, values=["Continuous", "Periodic", "Event-Based"], width=30, state="readonly")
        self.measurement_combo.grid(row=1, column=1, sticky="w", pady=5)

        fields = [
            ("Sensor Name*", "sensor_name"),
            ("Asset ID*", "asset_id"),
            ("Current Value", "current_value"),
            ("Threshold Min", "threshold_min"),
            ("Threshold Max", "threshold_max"),
            ("Location", "location"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+2, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+2, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=8, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Online", "Offline", "Alert", "Maintenance"], width=30, state="readonly")
        self.status_combo.set("Online")
        self.status_combo.grid(row=8, column=1, sticky="w", pady=5)

        # Last reading
        ttk.Label(frame, text="Last Reading:").grid(row=9, column=0, sticky="w", pady=5)
        self.entries["last_reading"] = ttk.Entry(frame, width=32)
        self.entries["last_reading"].grid(row=9, column=1, sticky="w", pady=5)
        self.entries["last_reading"].insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=10, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=10, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Sensor", command=self.save_sensor).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["sensor_name"].insert(0, values[1])
            self.entries["asset_id"].insert(0, values[2])
            self.sensor_type_combo.set(values[3])
            self.measurement_combo.set(values[4])
            self.entries["current_value"].insert(0, values[5])
            self.entries["threshold_min"].insert(0, values[6])
            self.entries["threshold_max"].insert(0, values[7])
            self.status_combo.set(values[8])
            self.entries["last_reading"].delete(0, tk.END)
            self.entries["last_reading"].insert(0, values[9])
            self.entries["location"].insert(0, values[10] if len(values) > 10 else "")
            self.notes_text.insert("1.0", values[11] if len(values) > 11 else "")
        except IndexError:
            pass

    def save_sensor(self):
        sensor_name = self.entries["sensor_name"].get().strip()
        sensor_type = self.sensor_type_combo.get()
        measurement_type = self.measurement_combo.get()
        asset_id = self.entries["asset_id"].get().strip()

        if not sensor_name or not sensor_type or not measurement_type or not asset_id:
            messagebox.showwarning("Input Error", "Sensor name, type, measurement type, and asset ID are required.", parent=self)
            return

        csv_file = getattr(config, "IOT_SENSORS_CSV", os.path.join(config.CSV_DIR, "iot_sensors.csv"))
        sensor_id = f"IOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            sensor_id,
            sensor_name,
            asset_id,
            sensor_type,
            measurement_type,
            self.entries["current_value"].get().strip(),
            self.entries["threshold_min"].get().strip(),
            self.entries["threshold_max"].get().strip(),
            self.status_combo.get(),
            self.entries["last_reading"].get().strip(),
            self.entries["location"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["sensor_id", "sensor_name", "asset_id", "sensor_type", "measurement_type", "current_value", "threshold_min", "threshold_max", "status", "last_reading", "location", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Sensor '{sensor_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sensor: {e}", parent=self)