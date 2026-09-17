import csv
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
import config


class SupplyChainLogisticsView(ttk.Frame):
    """Main Supply Chain & Logistics Management Module with tabbed interface."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        # Create notebook for different SCM components
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Add tabs for each component
        self.sourcing_tab = SourcingProcurementTab(self.notebook)
        self.notebook.add(self.sourcing_tab, text=" Sourcing & Procurement ")

        self.procurement_tab = ProcurementLifecycleTab(self.notebook)
        self.notebook.add(self.procurement_tab, text=" Purchase / Procurement ")

        self.planning_tab = DemandForecastingTab(self.notebook)
        self.notebook.add(self.planning_tab, text=" Demand Forecasting ")

        self.production_tab = ProductionManagementTab(self.notebook)
        self.notebook.add(self.production_tab, text=" Production Management ")

        self.risk_tab = RiskManagementTab(self.notebook)
        self.notebook.add(self.risk_tab, text=" Risk Management ")

        self.warehouse_tab = WarehousingTab(self.notebook)
        self.notebook.add(self.warehouse_tab, text=" Warehousing & Inventory ")

        self.transport_tab = TransportationTab(self.notebook)
        self.notebook.add(self.transport_tab, text=" Transportation & Fleet ")

        self.order_tab = OrderFulfillmentTab(self.notebook)
        self.notebook.add(self.order_tab, text=" Order Fulfillment ")

        self.returns_tab = ReverseLogisticsTab(self.notebook)
        self.notebook.add(self.returns_tab, text=" Returns & Reverse Logistics ")


class SourcingProcurementTab(ttk.Frame):
    """Sourcing & Procurement Management - Supplier vetting and raw material purchasing."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        # Top control panel
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add New Supplier", command=self.add_supplier).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_supplier).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_supplier).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_suppliers).pack(side="left", padx=5)

        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="Search Suppliers:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_suppliers)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=5)

        # Supplier table
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

        # Define columns
        columns = ["supplier_id", "name", "contact_person", "email", "phone", "rating", "status", "materials_supplied"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")

    def load_suppliers(self):
        csv_file = getattr(config, "SUPPLIERS_CSV", os.path.join(config.CSV_DIR, "suppliers.csv"))
        self.populate_table(csv_file)

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
                    self.tree.column(h, width=120, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def filter_suppliers(self, *args):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if search_term in " ".join(str(v) for v in values).lower():
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def add_supplier(self):
        SupplierDialog(self, callback=self.load_suppliers)

    def edit_supplier(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Supplier", "Please select a supplier to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        SupplierDialog(self, callback=self.load_suppliers, edit_values=item_values)

    def delete_supplier(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Supplier", "Please select a supplier to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this supplier?", parent=self):
            csv_file = getattr(config, "SUPPLIERS_CSV", os.path.join(config.CSV_DIR, "suppliers.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_suppliers()

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


class SupplierDialog(tk.Toplevel):
    """Dialog for adding/editing supplier information."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Supplier" if self.is_edit else "Add New Supplier")
        self.geometry("500x450")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Supplier Information", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Supplier Name*", "name"),
            ("Contact Person", "contact_person"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Rating (1-5)", "rating"),
            ("Status", "status"),
            ("Materials Supplied", "materials_supplied"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=35)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        self.entries["status"] = ttk.Combobox(frame, values=["Active", "Inactive", "Under Review"], width=32, state="readonly")
        self.entries["status"].set("Active")
        self.entries["status"].grid(row=4, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Supplier", command=self.save_supplier).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["name"].insert(0, values[1])
            self.entries["contact_person"].insert(0, values[2])
            self.entries["email"].insert(0, values[3])
            self.entries["phone"].insert(0, values[4])
            self.entries["rating"].insert(0, values[5])
            self.entries["status"].set(values[6])
            self.entries["materials_supplied"].insert(0, values[7])
        except IndexError:
            pass

    def save_supplier(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Supplier name is required.", parent=self)
            return

        csv_file = getattr(config, "SUPPLIERS_CSV", os.path.join(config.CSV_DIR, "suppliers.csv"))
        supplier_id = f"SUP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            supplier_id,
            name,
            self.entries["contact_person"].get().strip(),
            self.entries["email"].get().strip(),
            self.entries["phone"].get().strip(),
            self.entries["rating"].get().strip(),
            self.entries["status"].get(),
            self.entries["materials_supplied"].get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["supplier_id", "name", "contact_person", "email", "phone", "rating", "status", "materials_supplied"])

        if self.is_edit:
            # Update existing row (simplified - normally would match by ID)
            rows.append(row)
        else:
            rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Supplier '{name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save supplier: {e}", parent=self)


class ProcurementLifecycleTab(ttk.Frame):
    """Purchase-to-pay lifecycle with requisition approvals and invoice matching."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        summary_frame = ttk.LabelFrame(self, text=" Procurement Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Requisitions: ").grid(row=0, column=0, sticky="w", padx=5)
        self.requisition_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.requisition_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Pending Approvals: ").grid(row=0, column=2, sticky="w", padx=5)
        self.approval_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.approval_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Matched Invoices: ").grid(row=0, column=4, sticky="w", padx=5)
        self.matched_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.matched_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="＋ New Requisition", command=self.add_requisition).pack(side="left", padx=5)
        ttk.Button(control_frame, text="＋ New PO", command=self.add_purchase_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="＋ New Invoice", command=self.add_invoice).pack(side="left", padx=5)
        ttk.Button(control_frame, text="⚙️ Run 3-Way Match", command=self.run_three_way_match).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_records).pack(side="left", padx=5)

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

        columns = ["record_id", "record_type", "reference_no", "vendor", "amount", "status", "approval", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")

    def load_records(self):
        records = []
        for file_name, record_type in [
            ("procurement_requisitions.csv", "Requisition"),
            ("procurement_purchase_orders.csv", "Purchase Order"),
            ("procurement_invoices.csv", "Invoice"),
        ]:
            csv_file = os.path.join(config.CSV_DIR, file_name)
            if not os.path.exists(csv_file):
                continue
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows:
                continue
            headers = rows[0]
            for row in rows[1:]:
                if not row:
                    continue
                data = dict(zip(headers, row))
                if record_type == "Requisition":
                    records.append({
                        "record_id": data.get("record_id", ""),
                        "record_type": "Requisition",
                        "reference_no": data.get("requisition_no", ""),
                        "vendor": data.get("vendor", ""),
                        "amount": data.get("amount", "0"),
                        "status": data.get("status", "Draft"),
                        "approval": data.get("approval", "Pending"),
                        "notes": data.get("notes", ""),
                    })
                elif record_type == "Purchase Order":
                    records.append({
                        "record_id": data.get("record_id", ""),
                        "record_type": "Purchase Order",
                        "reference_no": data.get("po_no", ""),
                        "vendor": data.get("vendor", ""),
                        "amount": data.get("amount", "0"),
                        "status": data.get("status", "Draft"),
                        "approval": data.get("approval", "Pending"),
                        "notes": data.get("notes", ""),
                    })
                elif record_type == "Invoice":
                    records.append({
                        "record_id": data.get("record_id", ""),
                        "record_type": "Invoice",
                        "reference_no": data.get("invoice_no", ""),
                        "vendor": data.get("vendor", ""),
                        "amount": data.get("amount", "0"),
                        "status": data.get("status", "Draft"),
                        "approval": data.get("three_way_match", "Pending"),
                        "notes": data.get("notes", ""),
                    })

        self.populate_records(records)
        self.update_summary(records)

    def populate_records(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in records:
            self.tree.insert("", "end", values=[
                record.get("record_id", ""),
                record.get("record_type", ""),
                record.get("reference_no", ""),
                record.get("vendor", ""),
                record.get("amount", "0"),
                record.get("status", ""),
                record.get("approval", ""),
                record.get("notes", ""),
            ])

    def update_summary(self, records):
        requisitions = sum(1 for row in records if row["record_type"] == "Requisition")
        pending = sum(1 for row in records if row["approval"] in {"Pending", "Awaiting Approval", "Requires Review"})
        matched = sum(1 for row in records if row["record_type"] == "Invoice" and row["approval"].lower() == "matched")
        self.requisition_var.set(str(requisitions))
        self.approval_var.set(str(pending))
        self.matched_var.set(str(matched))

    def add_requisition(self):
        ProcurementRequisitionDialog(self, callback=self.load_records)

    def add_purchase_order(self):
        ProcurementPurchaseOrderDialog(self, callback=self.load_records)

    def add_invoice(self):
        ProcurementInvoiceDialog(self, callback=self.load_records)

    def run_three_way_match(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Invoice", "Please select an invoice to run three-way matching.", parent=self)
            return

        values = self.tree.item(selected[0], "values")
        if values[1] != "Invoice":
            messagebox.showwarning("Invalid Selection", "Please select an invoice record for matching.", parent=self)
            return

        invoice_no = values[2]
        invoice_file = os.path.join(config.CSV_DIR, "procurement_invoices.csv")
        if not os.path.exists(invoice_file):
            messagebox.showwarning("No Data", "No invoice data found.", parent=self)
            return

        with open(invoice_file, mode="r", encoding="utf-8-sig") as f:
            invoice_rows = list(csv.reader(f))

        target_row = None
        for row in invoice_rows[1:]:
            if row and row[2] == invoice_no:
                target_row = row
                break

        if target_row is None:
            messagebox.showinfo("Not Found", "Selected invoice could not be located.", parent=self)
            return

        po_no = target_row[3] if len(target_row) > 3 else ""
        po_file = os.path.join(config.CSV_DIR, "procurement_purchase_orders.csv")
        po_amount = 0.0
        if os.path.exists(po_file):
            with open(po_file, mode="r", encoding="utf-8-sig") as f:
                po_rows = list(csv.reader(f))
            for row in po_rows[1:]:
                if row and row[2] == po_no:
                    po_amount = float(row[5]) if len(row) > 5 else 0.0
                    break

        try:
            invoice_amount = float(target_row[5]) if len(target_row) > 5 else 0.0
            received_qty = float(target_row[6]) if len(target_row) > 6 and target_row[6] else 0.0
            invoice_qty = float(target_row[7]) if len(target_row) > 7 and target_row[7] else 0.0
        except ValueError:
            invoice_amount = 0.0
            received_qty = 0.0
            invoice_qty = 0.0

        price_ok = abs(invoice_amount - po_amount) <= max(po_amount * 0.02, 1.0)
        qty_ok = abs(invoice_qty - received_qty) <= max(received_qty * 0.05, 1.0)
        match_status = "Matched" if price_ok and qty_ok else "Exception"

        for idx, row in enumerate(invoice_rows[1:], start=1):
            if row and row[2] == invoice_no:
                invoice_rows[idx][8] = match_status
                invoice_rows[idx][9] = "Auto-match result: price_ok=%s, qty_ok=%s" % (price_ok, qty_ok)
                break

        with open(invoice_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(invoice_rows)

        messagebox.showinfo("Three-Way Match", f"Match status: {match_status}", parent=self)
        self.load_records()

    @staticmethod
    def get_approval_matrix(amount):
        if amount <= 10000:
            return "Department Manager"
        if amount <= 50000:
            return "Department Head + Finance"
        if amount <= 150000:
            return "Procurement + Finance + CFO"
        return "Procurement + Finance + CFO + Board"


class ProcurementRequisitionDialog(tk.Toplevel):
    """Dialog for creating or editing requisitions."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("New Requisition" if not self.is_edit else "Edit Requisition")
        self.geometry("520x500")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Procurement Requisition", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Requisition No*", "requisition_no"),
            ("Department*", "department"),
            ("Requested By*", "requested_by"),
            ("Vendor", "vendor"),
            ("Item Name*", "item_name"),
            ("Amount*", "amount"),
            ("Status", "status"),
            ("Notes", "notes"),
        ]

        self.entries = {}
        for idx, (label_text, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label_text}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=35)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        ttk.Button(self, text="Save Requisition", command=self.save_requisition).pack(pady=(0, 10))

    def save_requisition(self):
        requisition_no = self.entries["requisition_no"].get().strip()
        department = self.entries["department"].get().strip()
        requested_by = self.entries["requested_by"].get().strip()
        item_name = self.entries["item_name"].get().strip()
        amount_text = self.entries["amount"].get().strip()

        if not requisition_no or not department or not requested_by or not item_name or not amount_text:
            messagebox.showwarning("Input Error", "Please fill all required requisition fields.", parent=self)
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be numeric.", parent=self)
            return

        csv_file = os.path.join(config.CSV_DIR, "procurement_requisitions.csv")
        record_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        status = self.entries["status"].get().strip() or "Submitted"
        approval = ProcurementLifecycleTab.get_approval_matrix(amount)
        notes = self.entries["notes"].get().strip()

        row = [
            record_id,
            "Requisition",
            requisition_no,
            department,
            requested_by,
            self.entries["vendor"].get().strip(),
            item_name,
            amount,
            status,
            approval,
            notes,
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))

        if not rows:
            rows.append(["record_id", "record_type", "requisition_no", "department", "requested_by", "vendor", "item_name", "amount", "status", "approval", "notes"])

        rows.append(row)
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        messagebox.showinfo("Success", "Requisition saved successfully.", parent=self)
        if self.callback:
            self.callback()
        self.destroy()


class ProcurementPurchaseOrderDialog(tk.Toplevel):
    """Dialog for creating purchase orders from requisitions."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.title("New Purchase Order")
        self.geometry("520x480")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Purchase Order", font=("Helvetica", 12, "bold")).pack(pady=10)
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("PO No*", "po_no"),
            ("Requisition No*", "requisition_no"),
            ("Vendor*", "vendor"),
            ("Amount*", "amount"),
            ("Expected Delivery", "expected_delivery"),
            ("Status", "status"),
            ("Approval", "approval"),
            ("Notes", "notes"),
        ]

        self.entries = {}
        for idx, (label_text, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label_text}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=35)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        ttk.Button(self, text="Save Purchase Order", command=self.save_po).pack(pady=(0, 10))

    def save_po(self):
        po_no = self.entries["po_no"].get().strip()
        requisition_no = self.entries["requisition_no"].get().strip()
        vendor = self.entries["vendor"].get().strip()
        amount_text = self.entries["amount"].get().strip()

        if not po_no or not requisition_no or not vendor or not amount_text:
            messagebox.showwarning("Input Error", "Make sure PO number, requisition number, vendor, and amount are filled.", parent=self)
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be numeric.", parent=self)
            return

        csv_file = os.path.join(config.CSV_DIR, "procurement_purchase_orders.csv")
        record_id = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        status = self.entries["status"].get().strip() or "Approved"
        approval = self.entries["approval"].get().strip() or ProcurementLifecycleTab.get_approval_matrix(amount)
        notes = self.entries["notes"].get().strip()

        row = [
            record_id,
            "Purchase Order",
            po_no,
            requisition_no,
            vendor,
            amount,
            status,
            self.entries["expected_delivery"].get().strip(),
            approval,
            notes,
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))

        if not rows:
            rows.append(["record_id", "record_type", "po_no", "requisition_no", "vendor", "amount", "status", "expected_delivery", "approval", "notes"])

        rows.append(row)
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        messagebox.showinfo("Success", "Purchase order saved successfully.", parent=self)
        if self.callback:
            self.callback()
        self.destroy()


class ProcurementInvoiceDialog(tk.Toplevel):
    """Dialog for entering vendor invoices and checking variation."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.title("New Invoice")
        self.geometry("520x500")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Vendor Invoice", font=("Helvetica", 12, "bold")).pack(pady=10)
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Invoice No*", "invoice_no"),
            ("PO No*", "po_no"),
            ("Vendor*", "vendor"),
            ("Invoice Amount*", "amount"),
            ("Received Qty", "received_quantity"),
            ("Invoice Qty", "invoice_quantity"),
            ("Status", "status"),
            ("Notes", "notes"),
        ]

        self.entries = {}
        for idx, (label_text, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label_text}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=35)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        ttk.Button(self, text="Save Invoice", command=self.save_invoice).pack(pady=(0, 10))

    def save_invoice(self):
        invoice_no = self.entries["invoice_no"].get().strip()
        po_no = self.entries["po_no"].get().strip()
        vendor = self.entries["vendor"].get().strip()
        amount_text = self.entries["amount"].get().strip()

        if not invoice_no or not po_no or not vendor or not amount_text:
            messagebox.showwarning("Input Error", "Please fill the required invoice fields.", parent=self)
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a numeric value.", parent=self)
            return

        csv_file = os.path.join(config.CSV_DIR, "procurement_invoices.csv")
        record_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        status = self.entries["status"].get().strip() or "Submitted"
        match_status = "Pending"
        notes = self.entries["notes"].get().strip()

        row = [
            record_id,
            "Invoice",
            invoice_no,
            po_no,
            vendor,
            amount,
            self.entries["received_quantity"].get().strip(),
            self.entries["invoice_quantity"].get().strip(),
            match_status,
            status,
            notes,
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))

        if not rows:
            rows.append(["record_id", "record_type", "invoice_no", "po_no", "vendor", "amount", "received_quantity", "invoice_quantity", "three_way_match", "status", "notes"])

        rows.append(row)
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        messagebox.showinfo("Success", "Invoice saved successfully.", parent=self)
        if self.callback:
            self.callback()
        self.destroy()


class DemandForecastingTab(ttk.Frame):
    """Product Planning & Demand Forecasting - Market analysis and demand prediction."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_forecasts()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Forecast Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Products:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_products_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_products_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="High Demand Items:").grid(row=0, column=2, sticky="w", padx=5)
        self.high_demand_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.high_demand_var, font=("Helvetica", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Forecast", command=self.add_forecast).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_forecast).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_forecasts).pack(side="left", padx=5)

        # Forecast table
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

        columns = ["product_id", "product_name", "forecast_period", "predicted_demand", "confidence_level", "current_stock", "reorder_status"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")

    def load_forecasts(self):
        csv_file = getattr(config, "DEMAND_FORECAST_CSV", os.path.join(config.CSV_DIR, "demand_forecast.csv"))
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
                    self.tree.column(h, width=120, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def update_summary(self):
        total = len(self.tree.get_children())
        high_demand = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[6] == "Reorder Required")
        self.total_products_var.set(str(total))
        self.high_demand_var.set(str(high_demand))

    def add_forecast(self):
        ForecastDialog(self, callback=self.load_forecasts)

    def edit_forecast(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Forecast", "Please select a forecast to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ForecastDialog(self, callback=self.load_forecasts, edit_values=item_values)


class ForecastDialog(tk.Toplevel):
    """Dialog for demand forecasting."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Forecast" if self.is_edit else "Add New Forecast")
        self.geometry("450x400")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Demand Forecast Information", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Product Name*", "product_name"),
            ("Forecast Period*", "forecast_period"),
            ("Predicted Demand*", "predicted_demand"),
            ("Confidence Level (%)", "confidence_level"),
            ("Current Stock", "current_stock"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        ttk.Button(self, text="Save Forecast", command=self.save_forecast).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["product_name"].insert(0, values[1])
            self.entries["forecast_period"].insert(0, values[2])
            self.entries["predicted_demand"].insert(0, values[3])
            self.entries["confidence_level"].insert(0, values[4])
            self.entries["current_stock"].insert(0, values[5])
        except IndexError:
            pass

    def save_forecast(self):
        product_name = self.entries["product_name"].get().strip()
        forecast_period = self.entries["forecast_period"].get().strip()
        predicted_demand = self.entries["predicted_demand"].get().strip()

        if not product_name or not forecast_period or not predicted_demand:
            messagebox.showwarning("Input Error", "Product name, forecast period, and predicted demand are required.", parent=self)
            return

        csv_file = getattr(config, "DEMAND_FORECAST_CSV", os.path.join(config.CSV_DIR, "demand_forecast.csv"))
        product_id = f"DF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            current_stock = int(self.entries["current_stock"].get().strip() or "0")
            predicted = int(predicted_demand)
            reorder_status = "Reorder Required" if current_stock < predicted * 0.3 else "Sufficient"
        except ValueError:
            reorder_status = "Unknown"

        row = [
            product_id,
            product_name,
            forecast_period,
            predicted_demand,
            self.entries["confidence_level"].get().strip(),
            self.entries["current_stock"].get().strip(),
            reorder_status,
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["product_id", "product_name", "forecast_period", "predicted_demand", "confidence_level", "current_stock", "reorder_status"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Forecast for '{product_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save forecast: {e}", parent=self)


class ProductionManagementTab(ttk.Frame):
    """Manufacturing/Production - Factory schedules and quality control."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_production_orders()

    def setup_ui(self):
        # Status frame
        status_frame = ttk.LabelFrame(self, text=" Production Status ", padding=10)
        status_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(status_frame, text="Active Orders:").grid(row=0, column=0, sticky="w", padx=5)
        self.active_orders_var = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.active_orders_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(status_frame, text="Completed Today:").grid(row=0, column=2, sticky="w", padx=5)
        self.completed_today_var = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.completed_today_var, font=("Helvetica", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Production Order", command=self.add_production_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_production_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_production_orders).pack(side="left", padx=5)

        # Production table
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

        columns = ["order_id", "product_name", "quantity", "start_date", "target_date", "status", "quality_check", "assigned_team"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_production_orders(self):
        csv_file = getattr(config, "PRODUCTION_ORDERS_CSV", os.path.join(config.CSV_DIR, "production_orders.csv"))
        self.populate_table(csv_file)
        self.update_status()

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

    def update_status(self):
        all_orders = self.tree.get_children()
        active = sum(1 for item in all_orders if self.tree.item(item, "values")[5] in ["In Progress", "Pending"])
        completed = sum(1 for item in all_orders if self.tree.item(item, "values")[5] == "Completed")
        self.active_orders_var.set(str(active))
        self.completed_today_var.set(str(completed))

    def add_production_order(self):
        ProductionOrderDialog(self, callback=self.load_production_orders)

    def edit_production_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Order", "Please select a production order to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ProductionOrderDialog(self, callback=self.load_production_orders, edit_values=item_values)


class ProductionOrderDialog(tk.Toplevel):
    """Dialog for production orders."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Production Order" if self.is_edit else "New Production Order")
        self.geometry("480x450")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Production Order Details", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Product Name*", "product_name"),
            ("Quantity*", "quantity"),
            ("Start Date*", "start_date"),
            ("Target Date*", "target_date"),
            ("Assigned Team", "assigned_team"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=5, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Pending", "In Progress", "Completed", "On Hold"], width=28, state="readonly")
        self.status_combo.set("Pending")
        self.status_combo.grid(row=5, column=1, sticky="w", pady=5)

        # Quality check dropdown
        ttk.Label(frame, text="Quality Check:").grid(row=6, column=0, sticky="w", pady=5)
        self.quality_combo = ttk.Combobox(frame, values=["Pending", "Passed", "Failed", "In Progress"], width=28, state="readonly")
        self.quality_combo.set("Pending")
        self.quality_combo.grid(row=6, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Production Order", command=self.save_production_order).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["product_name"].insert(0, values[1])
            self.entries["quantity"].insert(0, values[2])
            self.entries["start_date"].insert(0, values[3])
            self.entries["target_date"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.quality_combo.set(values[6])
            self.entries["assigned_team"].insert(0, values[7])
        except IndexError:
            pass

    def save_production_order(self):
        product_name = self.entries["product_name"].get().strip()
        quantity = self.entries["quantity"].get().strip()
        start_date = self.entries["start_date"].get().strip()
        target_date = self.entries["target_date"].get().strip()

        if not product_name or not quantity or not start_date or not target_date:
            messagebox.showwarning("Input Error", "Product name, quantity, and dates are required.", parent=self)
            return

        csv_file = getattr(config, "PRODUCTION_ORDERS_CSV", os.path.join(config.CSV_DIR, "production_orders.csv"))
        order_id = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            order_id,
            product_name,
            quantity,
            start_date,
            target_date,
            self.status_combo.get(),
            self.quality_combo.get(),
            self.entries["assigned_team"].get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["order_id", "product_name", "quantity", "start_date", "target_date", "status", "quality_check", "assigned_team"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Production order for '{product_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save production order: {e}", parent=self)


class RiskManagementTab(ttk.Frame):
    """Risk Management - Anticipating and mitigating disruptions."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_risks()

    def setup_ui(self):
        # Risk summary frame
        summary_frame = ttk.LabelFrame(self, text=" Risk Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Risks:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_risks_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_risks_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Critical Risks:").grid(row=0, column=2, sticky="w", padx=5)
        self.critical_risks_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.critical_risks_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Risk", command=self.add_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_risks).pack(side="left", padx=5)

        # Risk table
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

        columns = ["risk_id", "risk_type", "description", "probability", "impact", "mitigation_plan", "status", "responsible"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_risks(self):
        csv_file = getattr(config, "RISK_MANAGEMENT_CSV", os.path.join(config.CSV_DIR, "risk_management.csv"))
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
        critical = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[6] == "Critical")
        self.total_risks_var.set(str(total))
        self.critical_risks_var.set(str(critical))

    def add_risk(self):
        RiskDialog(self, callback=self.load_risks)

    def edit_risk(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Risk", "Please select a risk to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        RiskDialog(self, callback=self.load_risks, edit_values=item_values)

    def delete_risk(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Risk", "Please select a risk to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this risk?", parent=self):
            csv_file = getattr(config, "RISK_MANAGEMENT_CSV", os.path.join(config.CSV_DIR, "risk_management.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_risks()

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


class RiskDialog(tk.Toplevel):
    """Dialog for risk management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Risk" if self.is_edit else "Add New Risk")
        self.geometry("500x500")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Risk Management Details", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Risk type dropdown
        ttk.Label(frame, text="Risk Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.risk_type_combo = ttk.Combobox(frame, values=["Supplier Bankruptcy", "Natural Disaster", "Geopolitical", "Demand Spike", "Quality Issue", "Logistics Delay", "Other"], width=28, state="readonly")
        self.risk_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Description*:").grid(row=1, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=30, height=3)
        self.description_text.grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Probability (Low/Med/High)*:").grid(row=2, column=0, sticky="w", pady=5)
        self.probability_combo = ttk.Combobox(frame, values=["Low", "Medium", "High"], width=28, state="readonly")
        self.probability_combo.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Impact (Low/Med/High)*:").grid(row=3, column=0, sticky="w", pady=5)
        self.impact_combo = ttk.Combobox(frame, values=["Low", "Medium", "High"], width=28, state="readonly")
        self.impact_combo.grid(row=3, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Mitigation Plan:").grid(row=4, column=0, sticky="nw", pady=5)
        self.mitigation_text = tk.Text(frame, width=30, height=3)
        self.mitigation_text.grid(row=4, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Status:").grid(row=5, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Open", "In Progress", "Mitigated", "Critical"], width=28, state="readonly")
        self.status_combo.set("Open")
        self.status_combo.grid(row=5, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Responsible Person:").grid(row=6, column=0, sticky="w", pady=5)
        self.responsible_entry = ttk.Entry(frame, width=30)
        self.responsible_entry.grid(row=6, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Risk", command=self.save_risk).pack(pady=15)

    def populate_values(self, values):
        try:
            self.risk_type_combo.set(values[1])
            self.description_text.insert("1.0", values[2])
            self.probability_combo.set(values[3])
            self.impact_combo.set(values[4])
            self.mitigation_text.insert("1.0", values[5])
            self.status_combo.set(values[6])
            self.responsible_entry.insert(0, values[7])
        except IndexError:
            pass

    def save_risk(self):
        risk_type = self.risk_type_combo.get()
        description = self.description_text.get("1.0", tk.END).strip()
        probability = self.probability_combo.get()
        impact = self.impact_combo.get()

        if not risk_type or not description or not probability or not impact:
            messagebox.showwarning("Input Error", "Risk type, description, probability, and impact are required.", parent=self)
            return

        csv_file = getattr(config, "RISK_MANAGEMENT_CSV", os.path.join(config.CSV_DIR, "risk_management.csv"))
        risk_id = f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            risk_id,
            risk_type,
            description,
            probability,
            impact,
            self.mitigation_text.get("1.0", tk.END).strip(),
            self.status_combo.get(),
            self.responsible_entry.get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["risk_id", "risk_type", "description", "probability", "impact", "mitigation_plan", "status", "responsible"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Risk '{risk_type}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save risk: {e}", parent=self)


class WarehousingTab(ttk.Frame):
    """Warehousing & Inventory Control - Storage facilities and stock tracking."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_inventory()

    def setup_ui(self):
        # Inventory summary frame
        summary_frame = ttk.LabelFrame(self, text=" Inventory Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Items:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_items_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_items_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Low Stock Items:").grid(row=0, column=2, sticky="w", padx=5)
        self.low_stock_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.low_stock_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Inventory Item", command=self.add_inventory).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_inventory).pack(side="left", padx=5)
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

        columns = ["item_id", "item_name", "sku", "quantity", "location", "warehouse_zone", "reorder_level", "last_updated"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_inventory(self):
        csv_file = getattr(config, "INVENTORY_CSV", os.path.join(config.CSV_DIR, "inventory.csv"))
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
        low_stock = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[6] and int(self.tree.item(item, "values")[6]) > int(self.tree.item(item, "values")[3]))
        self.total_items_var.set(str(total))
        self.low_stock_var.set(str(low_stock))

    def add_inventory(self):
        InventoryDialog(self, callback=self.load_inventory)

    def edit_inventory(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an inventory item to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        InventoryDialog(self, callback=self.load_inventory, edit_values=item_values)


class InventoryDialog(tk.Toplevel):
    """Dialog for inventory management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Inventory" if self.is_edit else "Add Inventory Item")
        self.geometry("450x420")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Inventory Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Item Name*", "item_name"),
            ("SKU*", "sku"),
            ("Quantity*", "quantity"),
            ("Location*", "location"),
            ("Warehouse Zone", "warehouse_zone"),
            ("Reorder Level", "reorder_level"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        ttk.Button(self, text="Save Inventory", command=self.save_inventory).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["item_name"].insert(0, values[1])
            self.entries["sku"].insert(0, values[2])
            self.entries["quantity"].insert(0, values[3])
            self.entries["location"].insert(0, values[4])
            self.entries["warehouse_zone"].insert(0, values[5])
            self.entries["reorder_level"].insert(0, values[6])
        except IndexError:
            pass

    def save_inventory(self):
        item_name = self.entries["item_name"].get().strip()
        sku = self.entries["sku"].get().strip()
        quantity = self.entries["quantity"].get().strip()
        location = self.entries["location"].get().strip()

        if not item_name or not sku or not quantity or not location:
            messagebox.showwarning("Input Error", "Item name, SKU, quantity, and location are required.", parent=self)
            return

        csv_file = getattr(config, "INVENTORY_CSV", os.path.join(config.CSV_DIR, "inventory.csv"))
        item_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")

        row = [
            item_id,
            item_name,
            sku,
            quantity,
            location,
            self.entries["warehouse_zone"].get().strip(),
            self.entries["reorder_level"].get().strip(),
            last_updated,
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["item_id", "item_name", "sku", "quantity", "location", "warehouse_zone", "reorder_level", "last_updated"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Inventory item '{item_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save inventory: {e}", parent=self)


class TransportationTab(ttk.Frame):
    """Transportation & Fleet Management - Transport modes and delivery routes."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_shipments()

    def setup_ui(self):
        # Shipment summary frame
        summary_frame = ttk.LabelFrame(self, text=" Shipment Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Active Shipments:").grid(row=0, column=0, sticky="w", padx=5)
        self.active_shipments_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_shipments_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Delayed Shipments:").grid(row=0, column=2, sticky="w", padx=5)
        self.delayed_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.delayed_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Shipment", command=self.add_shipment).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_shipment).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_shipments).pack(side="left", padx=5)

        # Shipment table
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

        columns = ["shipment_id", "origin", "destination", "transport_mode", "carrier", "estimated_delivery", "actual_delivery", "status", "tracking_number"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_shipments(self):
        csv_file = getattr(config, "SHIPMENTS_CSV", os.path.join(config.CSV_DIR, "shipments.csv"))
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
        all_shipments = self.tree.get_children()
        active = sum(1 for item in all_shipments if self.tree.item(item, "values")[7] in ["In Transit", "Picked Up"])
        delayed = sum(1 for item in all_shipments if self.tree.item(item, "values")[7] == "Delayed")
        self.active_shipments_var.set(str(active))
        self.delayed_var.set(str(delayed))

    def add_shipment(self):
        ShipmentDialog(self, callback=self.load_shipments)

    def edit_shipment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Shipment", "Please select a shipment to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ShipmentDialog(self, callback=self.load_shipments, edit_values=item_values)


class ShipmentDialog(tk.Toplevel):
    """Dialog for shipment management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Shipment" if self.is_edit else "New Shipment")
        self.geometry("480x450")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Shipment Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Origin*", "origin"),
            ("Destination*", "destination"),
            ("Carrier", "carrier"),
            ("Tracking Number", "tracking_number"),
            ("Estimated Delivery*", "estimated_delivery"),
            ("Actual Delivery", "actual_delivery"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Transport mode dropdown
        ttk.Label(frame, text="Transport Mode*:").grid(row=6, column=0, sticky="w", pady=5)
        self.transport_combo = ttk.Combobox(frame, values=["Truck", "Air Freight", "Sea Freight", "Rail", "Courier"], width=28, state="readonly")
        self.transport_combo.set("Truck")
        self.transport_combo.grid(row=6, column=1, sticky="w", pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Pending", "Picked Up", "In Transit", "Delivered", "Delayed", "Cancelled"], width=28, state="readonly")
        self.status_combo.set("Pending")
        self.status_combo.grid(row=7, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Shipment", command=self.save_shipment).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["origin"].insert(0, values[1])
            self.entries["destination"].insert(0, values[2])
            self.transport_combo.set(values[3])
            self.entries["carrier"].insert(0, values[4])
            self.entries["estimated_delivery"].insert(0, values[5])
            self.entries["actual_delivery"].insert(0, values[6])
            self.status_combo.set(values[7])
            self.entries["tracking_number"].insert(0, values[8])
        except IndexError:
            pass

    def save_shipment(self):
        origin = self.entries["origin"].get().strip()
        destination = self.entries["destination"].get().strip()
        estimated_delivery = self.entries["estimated_delivery"].get().strip()

        if not origin or not destination or not estimated_delivery:
            messagebox.showwarning("Input Error", "Origin, destination, and estimated delivery are required.", parent=self)
            return

        csv_file = getattr(config, "SHIPMENTS_CSV", os.path.join(config.CSV_DIR, "shipments.csv"))
        shipment_id = f"SHP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            shipment_id,
            origin,
            destination,
            self.transport_combo.get(),
            self.entries["carrier"].get().strip(),
            estimated_delivery,
            self.entries["actual_delivery"].get().strip(),
            self.status_combo.get(),
            self.entries["tracking_number"].get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["shipment_id", "origin", "destination", "transport_mode", "carrier", "estimated_delivery", "actual_delivery", "status", "tracking_number"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Shipment from '{origin}' to '{destination}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save shipment: {e}", parent=self)


class OrderFulfillmentTab(ttk.Frame):
    """Order Fulfillment - Picking, packing, and shipping orders."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        # Order summary frame
        summary_frame = ttk.LabelFrame(self, text=" Order Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Pending Orders:").grid(row=0, column=0, sticky="w", padx=5)
        self.pending_orders_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.pending_orders_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Shipped Today:").grid(row=0, column=2, sticky="w", padx=5)
        self.shipped_today_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.shipped_today_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Order", command=self.add_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_order).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_orders).pack(side="left", padx=5)

        # Order table
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

        columns = ["order_id", "customer_name", "product_items", "order_date", "priority", "pickup_status", "packing_status", "shipping_status"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_orders(self):
        csv_file = getattr(config, "ORDERS_CSV", os.path.join(config.CSV_DIR, "orders.csv"))
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
        all_orders = self.tree.get_children()
        pending = sum(1 for item in all_orders if self.tree.item(item, "values")[7] in ["Pending", "Processing"])
        shipped = sum(1 for item in all_orders if self.tree.item(item, "values")[7] == "Shipped")
        self.pending_orders_var.set(str(pending))
        self.shipped_today_var.set(str(shipped))

    def add_order(self):
        OrderDialog(self, callback=self.load_orders)

    def edit_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Order", "Please select an order to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        OrderDialog(self, callback=self.load_orders, edit_values=item_values)


class OrderDialog(tk.Toplevel):
    """Dialog for order fulfillment."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Order" if self.is_edit else "New Order")
        self.geometry("450x450")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Order Fulfillment", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Customer Name*", "customer_name"),
            ("Product Items*", "product_items"),
            ("Order Date*", "order_date"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Priority dropdown
        ttk.Label(frame, text="Priority:").grid(row=3, column=0, sticky="w", pady=5)
        self.priority_combo = ttk.Combobox(frame, values=["Normal", "High", "Urgent"], width=28, state="readonly")
        self.priority_combo.set("Normal")
        self.priority_combo.grid(row=3, column=1, sticky="w", pady=5)

        # Status dropdowns
        ttk.Label(frame, text="Pickup Status:").grid(row=4, column=0, sticky="w", pady=5)
        self.pickup_combo = ttk.Combobox(frame, values=["Pending", "Picked", "Completed"], width=28, state="readonly")
        self.pickup_combo.set("Pending")
        self.pickup_combo.grid(row=4, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Packing Status:").grid(row=5, column=0, sticky="w", pady=5)
        self.packing_combo = ttk.Combobox(frame, values=["Pending", "In Progress", "Packed"], width=28, state="readonly")
        self.packing_combo.set("Pending")
        self.packing_combo.grid(row=5, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Shipping Status:").grid(row=6, column=0, sticky="w", pady=5)
        self.shipping_combo = ttk.Combobox(frame, values=["Pending", "Processing", "Shipped", "Delivered"], width=28, state="readonly")
        self.shipping_combo.set("Pending")
        self.shipping_combo.grid(row=6, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Order", command=self.save_order).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["customer_name"].insert(0, values[1])
            self.entries["product_items"].insert(0, values[2])
            self.entries["order_date"].insert(0, values[3])
            self.priority_combo.set(values[4])
            self.pickup_combo.set(values[5])
            self.packing_combo.set(values[6])
            self.shipping_combo.set(values[7])
        except IndexError:
            pass

    def save_order(self):
        customer_name = self.entries["customer_name"].get().strip()
        product_items = self.entries["product_items"].get().strip()
        order_date = self.entries["order_date"].get().strip()

        if not customer_name or not product_items or not order_date:
            messagebox.showwarning("Input Error", "Customer name, product items, and order date are required.", parent=self)
            return

        csv_file = getattr(config, "ORDERS_CSV", os.path.join(config.CSV_DIR, "orders.csv"))
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            order_id,
            customer_name,
            product_items,
            order_date,
            self.priority_combo.get(),
            self.pickup_combo.get(),
            self.packing_combo.get(),
            self.shipping_combo.get(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["order_id", "customer_name", "product_items", "order_date", "priority", "pickup_status", "packing_status", "shipping_status"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Order for '{customer_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}", parent=self)


class ReverseLogisticsTab(ttk.Frame):
    """Reverse Logistics (Returns) - Managing returned goods."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_returns()

    def setup_ui(self):
        # Returns summary frame
        summary_frame = ttk.LabelFrame(self, text=" Returns Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Pending Returns:").grid(row=0, column=0, sticky="w", padx=5)
        self.pending_returns_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.pending_returns_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Processed Today:").grid(row=0, column=2, sticky="w", padx=5)
        self.processed_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.processed_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Return", command=self.add_return).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_return).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_returns).pack(side="left", padx=5)

        # Returns table
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

        columns = ["return_id", "original_order_id", "customer_name", "return_reason", "condition", "return_date", "resolution", "refund_status"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_returns(self):
        csv_file = getattr(config, "RETURNS_CSV", os.path.join(config.CSV_DIR, "returns.csv"))
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
        all_returns = self.tree.get_children()
        pending = sum(1 for item in all_returns if self.tree.item(item, "values")[6] in ["Pending", "Under Review"])
        processed = sum(1 for item in all_returns if self.tree.item(item, "values")[6] in ["Refunded", "Restocked", "Rejected"])
        self.pending_returns_var.set(str(pending))
        self.processed_var.set(str(processed))

    def add_return(self):
        ReturnDialog(self, callback=self.load_returns)

    def edit_return(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Return", "Please select a return to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ReturnDialog(self, callback=self.load_returns, edit_values=item_values)


class ReturnDialog(tk.Toplevel):
    """Dialog for returns management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Return" if self.is_edit else "New Return")
        self.geometry("480x480")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Return Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Original Order ID*", "original_order_id"),
            ("Customer Name*", "customer_name"),
            ("Return Date*", "return_date"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Return reason dropdown
        ttk.Label(frame, text="Return Reason*:").grid(row=3, column=0, sticky="w", pady=5)
        self.reason_combo = ttk.Combobox(frame, values=["Defective", "Damaged", "Wrong Item", "No Longer Needed", "Not as Described", "Other"], width=28, state="readonly")
        self.reason_combo.set("Defective")
        self.reason_combo.grid(row=3, column=1, sticky="w", pady=5)

        # Condition dropdown
        ttk.Label(frame, text="Condition:").grid(row=4, column=0, sticky="w", pady=5)
        self.condition_combo = ttk.Combobox(frame, values=["New", "Like New", "Good", "Fair", "Poor", "Damaged"], width=28, state="readonly")
        self.condition_combo.set("Good")
        self.condition_combo.grid(row=4, column=1, sticky="w", pady=5)

        # Resolution dropdown
        ttk.Label(frame, text="Resolution:").grid(row=5, column=0, sticky="w", pady=5)
        self.resolution_combo = ttk.Combobox(frame, values=["Pending", "Under Review", "Refunded", "Restocked", "Rejected", "Replacement"], width=28, state="readonly")
        self.resolution_combo.set("Pending")
        self.resolution_combo.grid(row=5, column=1, sticky="w", pady=5)

        # Refund status dropdown
        ttk.Label(frame, text="Refund Status:").grid(row=6, column=0, sticky="w", pady=5)
        self.refund_combo = ttk.Combobox(frame, values=["Pending", "Processed", "Partial", "None"], width=28, state="readonly")
        self.refund_combo.set("Pending")
        self.refund_combo.grid(row=6, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Return", command=self.save_return).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["original_order_id"].insert(0, values[1])
            self.entries["customer_name"].insert(0, values[2])
            self.reason_combo.set(values[3])
            self.condition_combo.set(values[4])
            self.entries["return_date"].insert(0, values[5])
            self.resolution_combo.set(values[6])
            self.refund_combo.set(values[7])
        except IndexError:
            pass

    def save_return(self):
        original_order_id = self.entries["original_order_id"].get().strip()
        customer_name = self.entries["customer_name"].get().strip()
        return_date = self.entries["return_date"].get().strip()

        if not original_order_id or not customer_name or not return_date:
            messagebox.showwarning("Input Error", "Original order ID, customer name, and return date are required.", parent=self)
            return

        csv_file = getattr(config, "RETURNS_CSV", os.path.join(config.CSV_DIR, "returns.csv"))
        return_id = f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            return_id,
            original_order_id,
            customer_name,
            self.reason_combo.get(),
            self.condition_combo.get(),
            return_date,
            self.resolution_combo.get(),
            self.refund_combo.get(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["return_id", "original_order_id", "customer_name", "return_reason", "condition", "return_date", "resolution", "refund_status"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Return for order '{original_order_id}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save return: {e}", parent=self)