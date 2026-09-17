"""
Warehouse Management Module for Electronic Panels and Components
Handles Item Master, Serial/Batch Tracking, Location Management, Inbound/Outbound Operations, and Stock Audit
"""

import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
from datetime import datetime

# Try to import config, handle if not available
try:
    import config
except ImportError:
    # Fallback if config is not available
    class Config:
        CSV_DIR = "csv_data"
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    config = Config()


class WarehouseManagementView(ttk.Frame):
    """Main Warehouse Management View with tabbed interface."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def create_widgets(self):
        """Create the tabbed interface for warehouse management."""
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Add tabs for different warehouse functions
        ItemMasterTab(notebook, user_data=self.user_data).add_tab(notebook)
        SerialBatchTab(notebook, user_data=self.user_data).add_tab(notebook)
        WarehouseLocationTab(notebook, user_data=self.user_data).add_tab(notebook)
        InboundOutboundTab(notebook, user_data=self.user_data).add_tab(notebook)
        StockAuditTab(notebook, user_data=self.user_data).add_tab(notebook)


class ItemMasterTab(ttk.Frame):
    """Item Master - Product & Panel Catalog Management."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def add_tab(self, notebook):
        """Add this tab to the notebook."""
        notebook.add(self, text="📦 Item Master")
        return self

    def create_widgets(self):
        """Create Item Master interface."""
        ttk.Label(self, text="Item Master - Product & Panel Catalog", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Add Item", command=self.add_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Item", command=self.edit_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Item", command=self.delete_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_items).pack(side="right", padx=5)

        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔍 Search", command=self.search_items).pack(side="left", padx=5)

        # Treeview for items
        columns = ["Item ID", "SKU Code", "Item Name", "Item Type", "Category", "Manufacturer", "Model", "Voltage", "Current", "UOM", "Min Stock", "Max Stock"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_item())

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.load_items()

    def load_items(self):
        """Load items from CSV."""
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_ITEMS_CSV", os.path.join(config.CSV_DIR, "warehouse_items.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 12:
                    self.tree.insert("", "end", values=row[:12])

    def add_item(self):
        """Open dialog to add new item."""
        ItemDialog(self, callback=self.load_items)

    def edit_item(self):
        """Open dialog to edit selected item."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an item to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ItemDialog(self, callback=self.load_items, edit_values=item_values)

    def delete_item(self):
        """Delete selected item."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an item to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?", parent=self):
            csv_file = getattr(config, "WAREHOUSE_ITEMS_CSV", os.path.join(config.CSV_DIR, "warehouse_items.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_items()

    def search_items(self):
        """Search items based on criteria."""
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            self.load_items()
            return

        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_ITEMS_CSV", os.path.join(config.CSV_DIR, "warehouse_items.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 12:
                    row_text = " ".join(row).lower()
                    if search_term in row_text:
                        self.tree.insert("", "end", values=row[:12])

    def delete_row_from_csv(self, csv_file, row_index):
        """Delete a row from CSV file."""
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


class SerialBatchTab(ttk.Frame):
    """Serial Number & Batch Tracking for Electronics."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def add_tab(self, notebook):
        """Add this tab to the notebook."""
        notebook.add(self, text="🔢 Serial/Batch Tracking")
        return self

    def create_widgets(self):
        """Create Serial/Batch Tracking interface."""
        ttk.Label(self, text="Serial Number & Batch Tracking", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Add Serial/Batch", command=self.add_serial).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Serial/Batch", command=self.edit_serial).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Serial/Batch", command=self.delete_serial).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_serials).pack(side="right", padx=5)

        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search by Serial/Batch:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔍 Search", command=self.search_serials).pack(side="left", padx=5)

        # Treeview for serial/batch tracking
        columns = ["Serial Number", "Batch/Lot Number", "Item ID", "Item Name", "Manufacturing Date", "Expiry/Warranty Date", "QC Status"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_serial())

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.load_serials()

    def load_serials(self):
        """Load serial/batch data from CSV."""
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_SERIAL_CSV", os.path.join(config.CSV_DIR, "warehouse_serial.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 7:
                    self.tree.insert("", "end", values=row[:7])

    def add_serial(self):
        """Open dialog to add new serial/batch."""
        SerialDialog(self, callback=self.load_serials)

    def edit_serial(self):
        """Open dialog to edit selected serial/batch."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Serial/Batch", "Please select a serial/batch to edit.", parent=self)
            return
        serial_values = self.tree.item(selected[0], "values")
        SerialDialog(self, callback=self.load_serials, edit_values=serial_values)

    def delete_serial(self):
        """Delete selected serial/batch."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Serial/Batch", "Please select a serial/batch to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this serial/batch?", parent=self):
            csv_file = getattr(config, "WAREHOUSE_SERIAL_CSV", os.path.join(config.CSV_DIR, "warehouse_serial.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_serials()

    def search_serials(self):
        """Search serial/batch based on criteria."""
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            self.load_serials()
            return

        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_SERIAL_CSV", os.path.join(config.CSV_DIR, "warehouse_serial.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 7:
                    row_text = " ".join(row).lower()
                    if search_term in row_text:
                        self.tree.insert("", "end", values=row[:7])

    def delete_row_from_csv(self, csv_file, row_index):
        """Delete a row from CSV file."""
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


class WarehouseLocationTab(ttk.Frame):
    """Warehouse Location & Bin Management."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def add_tab(self, notebook):
        """Add this tab to the notebook."""
        notebook.add(self, text="📍 Location Management")
        return self

    def create_widgets(self):
        """Create Location Management interface."""
        ttk.Label(self, text="Warehouse Location & Bin Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Add Location", command=self.add_location).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Location", command=self.edit_location).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Location", command=self.delete_location).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_locations).pack(side="right", padx=5)

        # Treeview for locations
        columns = ["Location ID", "Zone/Hall", "Aisle & Rack", "Shelf/Bin Number", "Storage Condition", "Assigned Item", "Capacity", "Current Usage"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_location())

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.load_locations()

    def load_locations(self):
        """Load locations from CSV."""
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_LOCATION_CSV", os.path.join(config.CSV_DIR, "warehouse_location.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 8:
                    self.tree.insert("", "end", values=row[:8])

    def add_location(self):
        """Open dialog to add new location."""
        LocationDialog(self, callback=self.load_locations)

    def edit_location(self):
        """Open dialog to edit selected location."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Location", "Please select a location to edit.", parent=self)
            return
        location_values = self.tree.item(selected[0], "values")
        LocationDialog(self, callback=self.load_locations, edit_values=location_values)

    def delete_location(self):
        """Delete selected location."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Location", "Please select a location to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this location?", parent=self):
            csv_file = getattr(config, "WAREHOUSE_LOCATION_CSV", os.path.join(config.CSV_DIR, "warehouse_location.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_locations()

    def delete_row_from_csv(self, csv_file, row_index):
        """Delete a row from CSV file."""
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


class InboundOutboundTab(ttk.Frame):
    """Inbound & Outbound Operations Management."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def add_tab(self, notebook):
        """Add this tab to the notebook."""
        notebook.add(self, text="📥📤 Inbound/Outbound")
        return self

    def create_widgets(self):
        """Create Inbound/Outbound interface."""
        ttk.Label(self, text="Inbound & Outbound Operations", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Add Inbound", command=self.add_inbound).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="➕ Add Outbound", command=self.add_outbound).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Transaction", command=self.edit_transaction).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Transaction", command=self.delete_transaction).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_transactions).pack(side="right", padx=5)

        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Filter by Type:").pack(side="left", padx=5)
        self.type_combo = ttk.Combobox(search_frame, values=["All", "Inbound", "Outbound"], width=15, state="readonly")
        self.type_combo.set("All")
        self.type_combo.pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔍 Filter", command=self.filter_transactions).pack(side="left", padx=5)

        # Treeview for transactions
        columns = ["Transaction ID", "Type", "Item ID", "Item Name", "Quantity", "PO/SO Number", "Vendor/Client", "Date", "Status"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_transaction())

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.load_transactions()

    def load_transactions(self):
        """Load transactions from CSV."""
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_TRANSACTIONS_CSV", os.path.join(config.CSV_DIR, "warehouse_transactions.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 9:
                    self.tree.insert("", "end", values=row[:9])

    def add_inbound(self):
        """Open dialog to add inbound transaction."""
        TransactionDialog(self, callback=self.load_transactions, transaction_type="Inbound")

    def add_outbound(self):
        """Open dialog to add outbound transaction."""
        TransactionDialog(self, callback=self.load_transactions, transaction_type="Outbound")

    def edit_transaction(self):
        """Open dialog to edit selected transaction."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Transaction", "Please select a transaction to edit.", parent=self)
            return
        transaction_values = self.tree.item(selected[0], "values")
        TransactionDialog(self, callback=self.load_transactions, edit_values=transaction_values)

    def delete_transaction(self):
        """Delete selected transaction."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Transaction", "Please select a transaction to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?", parent=self):
            csv_file = getattr(config, "WAREHOUSE_TRANSACTIONS_CSV", os.path.join(config.CSV_DIR, "warehouse_transactions.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_transactions()

    def filter_transactions(self):
        """Filter transactions by type."""
        filter_type = self.type_combo.get()
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_TRANSACTIONS_CSV", os.path.join(config.CSV_DIR, "warehouse_transactions.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 9:
                    if filter_type == "All" or row[1] == filter_type:
                        self.tree.insert("", "end", values=row[:9])

    def delete_row_from_csv(self, csv_file, row_index):
        """Delete a row from CSV file."""
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


class StockAuditTab(ttk.Frame):
    """Stock Audit & Adjustments Management."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.create_widgets()

    def add_tab(self, notebook):
        """Add this tab to the notebook."""
        notebook.add(self, text="📊 Stock Audit")
        return self

    def create_widgets(self):
        """Create Stock Audit interface."""
        ttk.Label(self, text="Stock Audit & Adjustments", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Add Audit", command=self.add_audit).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit Audit", command=self.edit_audit).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Audit", command=self.delete_audit).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_audits).pack(side="right", padx=5)

        # Treeview for audits
        columns = ["Audit ID", "Item ID", "Item Name", "Physical Count", "System Count", "Variance", "Reason", "Date", "Audited By"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_audit())

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.load_audits()

    def load_audits(self):
        """Load audits from CSV."""
        self.tree.delete(*self.tree.get_children())
        csv_file = getattr(config, "WAREHOUSE_AUDIT_CSV", os.path.join(config.CSV_DIR, "warehouse_audit.csv"))

        if not os.path.exists(csv_file):
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 9:
                    self.tree.insert("", "end", values=row[:9])

    def add_audit(self):
        """Open dialog to add new audit."""
        AuditDialog(self, callback=self.load_audits)

    def edit_audit(self):
        """Open dialog to edit selected audit."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Audit", "Please select an audit to edit.", parent=self)
            return
        audit_values = self.tree.item(selected[0], "values")
        AuditDialog(self, callback=self.load_audits, edit_values=audit_values)

    def delete_audit(self):
        """Delete selected audit."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Audit", "Please select an audit to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this audit?", parent=self):
            csv_file = getattr(config, "WAREHOUSE_AUDIT_CSV", os.path.join(config.CSV_DIR, "warehouse_audit.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_audits()

    def delete_row_from_csv(self, csv_file, row_index):
        """Delete a row from CSV file."""
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


# Dialog Classes for Data Entry

class ItemDialog(tk.Toplevel):
    """Dialog for Item Master management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Item" if self.is_edit else "Add New Item")
        self.geometry("700x650")
        self.minsize(600, 500)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        """Create form fields for item management."""
        ttk.Label(self, text="Item Master - Product & Panel Catalog", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Save Item", command=self.save_item).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

        frame = scrollable_frame
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(11, weight=1)

        # Item ID/SKU
        ttk.Label(frame, text="Item ID / SKU Code*:").grid(row=0, column=0, sticky="w", pady=5)
        self.item_id_entry = ttk.Entry(frame, width=40)
        self.item_id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Item Name
        ttk.Label(frame, text="Item Name*:").grid(row=1, column=0, sticky="w", pady=5)
        self.item_name_entry = ttk.Entry(frame, width=40)
        self.item_name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Item Type
        ttk.Label(frame, text="Item Type*:").grid(row=2, column=0, sticky="w", pady=5)
        self.item_type_combo = ttk.Combobox(frame, values=["Finished Electronic Panel", "Raw Component", "Spare Part", "Sub-Assembly"], width=37, state="readonly")
        self.item_type_combo.grid(row=2, column=1, sticky="ew", pady=5)

        # Category
        ttk.Label(frame, text="Category:").grid(row=3, column=0, sticky="w", pady=5)
        self.category_entry = ttk.Entry(frame, width=40)
        self.category_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Manufacturer
        ttk.Label(frame, text="Manufacturer/Brand:").grid(row=4, column=0, sticky="w", pady=5)
        self.manufacturer_entry = ttk.Entry(frame, width=40)
        self.manufacturer_entry.grid(row=4, column=1, sticky="ew", pady=5)

        # Model Number
        ttk.Label(frame, text="Model/Part Number:").grid(row=5, column=0, sticky="w", pady=5)
        self.model_entry = ttk.Entry(frame, width=40)
        self.model_entry.grid(row=5, column=1, sticky="ew", pady=5)

        # Voltage Rating
        ttk.Label(frame, text="Voltage Rating:").grid(row=6, column=0, sticky="w", pady=5)
        self.voltage_entry = ttk.Entry(frame, width=40)
        self.voltage_entry.grid(row=6, column=1, sticky="ew", pady=5)

        # Current Rating
        ttk.Label(frame, text="Current Rating:").grid(row=7, column=0, sticky="w", pady=5)
        self.current_entry = ttk.Entry(frame, width=40)
        self.current_entry.grid(row=7, column=1, sticky="ew", pady=5)

        # Dimensions
        ttk.Label(frame, text="Dimensions/Enclosure:").grid(row=8, column=0, sticky="w", pady=5)
        self.dimensions_entry = ttk.Entry(frame, width=40)
        self.dimensions_entry.grid(row=8, column=1, sticky="ew", pady=5)

        # UOM
        ttk.Label(frame, text="Unit of Measurement*:").grid(row=9, column=0, sticky="w", pady=5)
        self.uom_combo = ttk.Combobox(frame, values=["Pcs", "Meters", "Sets", "Packets", "Kg", "Liters"], width=37, state="readonly")
        self.uom_combo.grid(row=9, column=1, sticky="ew", pady=5)

        # Min Stock Level
        ttk.Label(frame, text="Min Stock Level*:").grid(row=10, column=0, sticky="w", pady=5)
        self.min_stock_entry = ttk.Entry(frame, width=40)
        self.min_stock_entry.grid(row=10, column=1, sticky="ew", pady=5)

        # Max Stock Level
        ttk.Label(frame, text="Max Stock Level*:").grid(row=11, column=0, sticky="w", pady=5)
        self.max_stock_entry = ttk.Entry(frame, width=40)
        self.max_stock_entry.grid(row=11, column=1, sticky="ew", pady=5)

    def populate_values(self, values):
        """Populate form with existing values."""
        try:
            self.item_id_entry.insert(0, values[0])
            self.item_name_entry.insert(0, values[2])
            self.item_type_combo.set(values[3])
            self.category_entry.insert(0, values[4])
            self.manufacturer_entry.insert(0, values[5])
            self.model_entry.insert(0, values[6])
            self.voltage_entry.insert(0, values[7])
            self.current_entry.insert(0, values[8])
            self.uom_combo.set(values[9])
            self.min_stock_entry.insert(0, values[10])
            self.max_stock_entry.insert(0, values[11])
        except IndexError:
            pass

    def save_item(self):
        """Save item to CSV."""
        item_id = self.item_id_entry.get().strip()
        item_name = self.item_name_entry.get().strip()
        item_type = self.item_type_combo.get()
        uom = self.uom_combo.get()
        min_stock = self.min_stock_entry.get().strip()
        max_stock = self.max_stock_entry.get().strip()

        if not item_id or not item_name or not item_type or not uom or not min_stock or not max_stock:
            messagebox.showwarning("Input Error", "All required fields must be filled.", parent=self)
            return

        row_data = [
            item_id,
            item_id,  # SKU Code same as Item ID
            item_name,
            item_type,
            self.category_entry.get().strip(),
            self.manufacturer_entry.get().strip(),
            self.model_entry.get().strip(),
            self.voltage_entry.get().strip(),
            self.current_entry.get().strip(),
            uom,
            min_stock,
            max_stock
        ]

        csv_file = getattr(config, "WAREHOUSE_ITEMS_CSV", os.path.join(config.CSV_DIR, "warehouse_items.csv"))
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Item ID", "SKU Code", "Item Name", "Item Type", "Category", "Manufacturer", "Model", "Voltage", "Current", "UOM", "Min Stock", "Max Stock"])
            writer.writerow(row_data)

        messagebox.showinfo("Success", "Item saved successfully!", parent=self)
        self.destroy()
        if self.callback:
            self.callback()


class SerialDialog(tk.Toplevel):
    """Dialog for Serial/Batch management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Serial/Batch" if self.is_edit else "Add Serial/Batch")
        self.geometry("550x500")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        """Create form fields for serial/batch management."""
        ttk.Label(self, text="Serial Number & Batch Tracking", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Save Serial/Batch", command=self.save_serial).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

        frame = scrollable_frame
        frame.columnconfigure(1, weight=1)

        # Serial Number
        ttk.Label(frame, text="Serial Number*:").grid(row=0, column=0, sticky="w", pady=5)
        self.serial_entry = ttk.Entry(frame, width=40)
        self.serial_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Batch/Lot Number
        ttk.Label(frame, text="Batch/Lot Number:").grid(row=1, column=0, sticky="w", pady=5)
        self.batch_entry = ttk.Entry(frame, width=40)
        self.batch_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Item ID
        ttk.Label(frame, text="Item ID*:").grid(row=2, column=0, sticky="w", pady=5)
        self.item_id_entry = ttk.Entry(frame, width=40)
        self.item_id_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # Item Name
        ttk.Label(frame, text="Item Name:").grid(row=3, column=0, sticky="w", pady=5)
        self.item_name_entry = ttk.Entry(frame, width=40)
        self.item_name_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Manufacturing Date
        ttk.Label(frame, text="Manufacturing Date:").grid(row=4, column=0, sticky="w", pady=5)
        self.mfg_date_entry = ttk.Entry(frame, width=40)
        self.mfg_date_entry.grid(row=4, column=1, sticky="ew", pady=5)

        # Expiry/Warranty Date
        ttk.Label(frame, text="Expiry/Warranty Date:").grid(row=5, column=0, sticky="w", pady=5)
        self.expiry_date_entry = ttk.Entry(frame, width=40)
        self.expiry_date_entry.grid(row=5, column=1, sticky="ew", pady=5)

        # QC Status
        ttk.Label(frame, text="QC Status*:").grid(row=6, column=0, sticky="w", pady=5)
        self.qc_combo = ttk.Combobox(frame, values=["Pending Inspection", "Passed", "Rejected", "Rework"], width=37, state="readonly")
        self.qc_combo.set("Pending Inspection")
        self.qc_combo.grid(row=6, column=1, sticky="ew", pady=5)

    def populate_values(self, values):
        """Populate form with existing values."""
        try:
            self.serial_entry.insert(0, values[0])
            self.batch_entry.insert(0, values[1])
            self.item_id_entry.insert(0, values[2])
            self.item_name_entry.insert(0, values[3])
            self.mfg_date_entry.insert(0, values[4])
            self.expiry_date_entry.insert(0, values[5])
            self.qc_combo.set(values[6])
        except IndexError:
            pass

    def save_serial(self):
        """Save serial/batch to CSV."""
        serial_number = self.serial_entry.get().strip()
        item_id = self.item_id_entry.get().strip()
        qc_status = self.qc_combo.get()

        if not serial_number or not item_id:
            messagebox.showwarning("Input Error", "Serial Number and Item ID are required.", parent=self)
            return

        row_data = [
            serial_number,
            self.batch_entry.get().strip(),
            item_id,
            self.item_name_entry.get().strip(),
            self.mfg_date_entry.get().strip(),
            self.expiry_date_entry.get().strip(),
            qc_status
        ]

        csv_file = getattr(config, "WAREHOUSE_SERIAL_CSV", os.path.join(config.CSV_DIR, "warehouse_serial.csv"))
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Serial Number", "Batch/Lot Number", "Item ID", "Item Name", "Manufacturing Date", "Expiry/Warranty Date", "QC Status"])
            writer.writerow(row_data)

        messagebox.showinfo("Success", "Serial/Batch saved successfully!", parent=self)
        self.destroy()
        if self.callback:
            self.callback()


class LocationDialog(tk.Toplevel):
    """Dialog for Location management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Location" if self.is_edit else "Add Location")
        self.geometry("550x450")
        self.minsize(480, 380)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        """Create form fields for location management."""
        ttk.Label(self, text="Warehouse Location & Bin Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Save Location", command=self.save_location).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

        frame = scrollable_frame
        frame.columnconfigure(1, weight=1)

        # Location ID
        ttk.Label(frame, text="Location ID*:").grid(row=0, column=0, sticky="w", pady=5)
        self.location_id_entry = ttk.Entry(frame, width=40)
        self.location_id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Zone/Hall
        ttk.Label(frame, text="Zone/Hall*:").grid(row=1, column=0, sticky="w", pady=5)
        self.zone_entry = ttk.Entry(frame, width=40)
        self.zone_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Aisle & Rack
        ttk.Label(frame, text="Aisle & Rack*:").grid(row=2, column=0, sticky="w", pady=5)
        self.aisle_entry = ttk.Entry(frame, width=40)
        self.aisle_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # Shelf/Bin Number
        ttk.Label(frame, text="Shelf/Bin Number*:").grid(row=3, column=0, sticky="w", pady=5)
        self.shelf_entry = ttk.Entry(frame, width=40)
        self.shelf_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Storage Condition
        ttk.Label(frame, text="Storage Condition:").grid(row=4, column=0, sticky="w", pady=5)
        self.condition_combo = ttk.Combobox(frame, values=["Standard", "Anti-Static Zone", "Moisture-Sensitive (Dry Storage)", "Temperature Controlled"], width=37, state="readonly")
        self.condition_combo.set("Standard")
        self.condition_combo.grid(row=4, column=1, sticky="ew", pady=5)

        # Assigned Item
        ttk.Label(frame, text="Assigned Item:").grid(row=5, column=0, sticky="w", pady=5)
        self.assigned_item_entry = ttk.Entry(frame, width=40)
        self.assigned_item_entry.grid(row=5, column=1, sticky="ew", pady=5)

        # Capacity
        ttk.Label(frame, text="Capacity:").grid(row=6, column=0, sticky="w", pady=5)
        self.capacity_entry = ttk.Entry(frame, width=40)
        self.capacity_entry.grid(row=6, column=1, sticky="ew", pady=5)

        # Current Usage
        ttk.Label(frame, text="Current Usage:").grid(row=7, column=0, sticky="w", pady=5)
        self.usage_entry = ttk.Entry(frame, width=40)
        self.usage_entry.grid(row=7, column=1, sticky="ew", pady=5)

    def populate_values(self, values):
        """Populate form with existing values."""
        try:
            self.location_id_entry.insert(0, values[0])
            self.zone_entry.insert(0, values[1])
            self.aisle_entry.insert(0, values[2])
            self.shelf_entry.insert(0, values[3])
            self.condition_combo.set(values[4])
            self.assigned_item_entry.insert(0, values[5])
            self.capacity_entry.insert(0, values[6])
            self.usage_entry.insert(0, values[7])
        except IndexError:
            pass

    def save_location(self):
        """Save location to CSV."""
        location_id = self.location_id_entry.get().strip()
        zone = self.zone_entry.get().strip()
        aisle = self.aisle_entry.get().strip()
        shelf = self.shelf_entry.get().strip()

        if not location_id or not zone or not aisle or not shelf:
            messagebox.showwarning("Input Error", "Location ID, Zone, Aisle & Rack, and Shelf/Bin are required.", parent=self)
            return

        row_data = [
            location_id,
            zone,
            aisle,
            shelf,
            self.condition_combo.get(),
            self.assigned_item_entry.get().strip(),
            self.capacity_entry.get().strip(),
            self.usage_entry.get().strip()
        ]

        csv_file = getattr(config, "WAREHOUSE_LOCATION_CSV", os.path.join(config.CSV_DIR, "warehouse_location.csv"))
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Location ID", "Zone/Hall", "Aisle & Rack", "Shelf/Bin Number", "Storage Condition", "Assigned Item", "Capacity", "Current Usage"])
            writer.writerow(row_data)

        messagebox.showinfo("Success", "Location saved successfully!", parent=self)
        self.destroy()
        if self.callback:
            self.callback()


class TransactionDialog(tk.Toplevel):
    """Dialog for Inbound/Outbound transaction management."""

    def __init__(self, parent, callback=None, edit_values=None, transaction_type=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.transaction_type = transaction_type
        self.title("Edit Transaction" if self.is_edit else f"Add {transaction_type if transaction_type else 'Transaction'}")
        self.geometry("600x550")
        self.minsize(520, 450)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        """Create form fields for transaction management."""
        ttk.Label(self, text="Inbound & Outbound Operations", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Save Transaction", command=self.save_transaction).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

        frame = scrollable_frame
        frame.columnconfigure(1, weight=1)

        # Transaction Type
        ttk.Label(frame, text="Transaction Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.type_combo = ttk.Combobox(frame, values=["Inbound", "Outbound"], width=37, state="readonly")
        if self.transaction_type:
            self.type_combo.set(self.transaction_type)
        self.type_combo.grid(row=0, column=1, sticky="ew", pady=5)

        # Item ID
        ttk.Label(frame, text="Item ID*:").grid(row=1, column=0, sticky="w", pady=5)
        self.item_id_entry = ttk.Entry(frame, width=40)
        self.item_id_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Item Name
        ttk.Label(frame, text="Item Name:").grid(row=2, column=0, sticky="w", pady=5)
        self.item_name_entry = ttk.Entry(frame, width=40)
        self.item_name_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # Quantity
        ttk.Label(frame, text="Quantity*:").grid(row=3, column=0, sticky="w", pady=5)
        self.quantity_entry = ttk.Entry(frame, width=40)
        self.quantity_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # PO/SO Number
        ttk.Label(frame, text="PO/SO Number:").grid(row=4, column=0, sticky="w", pady=5)
        self.po_so_entry = ttk.Entry(frame, width=40)
        self.po_so_entry.grid(row=4, column=1, sticky="ew", pady=5)

        # Vendor/Client
        ttk.Label(frame, text="Vendor/Client*:").grid(row=5, column=0, sticky="w", pady=5)
        self.vendor_entry = ttk.Entry(frame, width=40)
        self.vendor_entry.grid(row=5, column=1, sticky="ew", pady=5)

        # Date
        ttk.Label(frame, text="Date*:").grid(row=6, column=0, sticky="w", pady=5)
        self.date_entry = ttk.Entry(frame, width=40)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=6, column=1, sticky="ew", pady=5)

        # Status
        ttk.Label(frame, text="Status*:").grid(row=7, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Pending", "In Progress", "Completed", "Cancelled"], width=37, state="readonly")
        self.status_combo.set("Pending")
        self.status_combo.grid(row=7, column=1, sticky="ew", pady=5)

    def populate_values(self, values):
        """Populate form with existing values."""
        try:
            self.type_combo.set(values[1])
            self.item_id_entry.insert(0, values[2])
            self.item_name_entry.insert(0, values[3])
            self.quantity_entry.insert(0, values[4])
            self.po_so_entry.insert(0, values[5])
            self.vendor_entry.insert(0, values[6])
            self.date_entry.insert(0, values[7])
            self.status_combo.set(values[8])
        except IndexError:
            pass

    def save_transaction(self):
        """Save transaction to CSV."""
        transaction_type = self.type_combo.get()
        item_id = self.item_id_entry.get().strip()
        quantity = self.quantity_entry.get().strip()
        vendor = self.vendor_entry.get().strip()
        date = self.date_entry.get().strip()
        status = self.status_combo.get()

        if not transaction_type or not item_id or not quantity or not vendor or not date:
            messagebox.showwarning("Input Error", "Transaction Type, Item ID, Quantity, Vendor/Client, and Date are required.", parent=self)
            return

        row_data = [
            f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            transaction_type,
            item_id,
            self.item_name_entry.get().strip(),
            quantity,
            self.po_so_entry.get().strip(),
            vendor,
            date,
            status
        ]

        csv_file = getattr(config, "WAREHOUSE_TRANSACTIONS_CSV", os.path.join(config.CSV_DIR, "warehouse_transactions.csv"))
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Transaction ID", "Type", "Item ID", "Item Name", "Quantity", "PO/SO Number", "Vendor/Client", "Date", "Status"])
            writer.writerow(row_data)

        messagebox.showinfo("Success", "Transaction saved successfully!", parent=self)
        self.destroy()
        if self.callback:
            self.callback()


class AuditDialog(tk.Toplevel):
    """Dialog for Stock Audit management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Audit" if self.is_edit else "Add Stock Audit")
        self.geometry("550x450")
        self.minsize(480, 380)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        """Create form fields for audit management."""
        ttk.Label(self, text="Stock Audit & Adjustments", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="💾 Save Audit", command=self.save_audit).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

        frame = scrollable_frame
        frame.columnconfigure(1, weight=1)

        # Item ID
        ttk.Label(frame, text="Item ID*:").grid(row=0, column=0, sticky="w", pady=5)
        self.item_id_entry = ttk.Entry(frame, width=40)
        self.item_id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Item Name
        ttk.Label(frame, text="Item Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.item_name_entry = ttk.Entry(frame, width=40)
        self.item_name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Physical Count
        ttk.Label(frame, text="Physical Count*:").grid(row=2, column=0, sticky="w", pady=5)
        self.physical_count_entry = ttk.Entry(frame, width=40)
        self.physical_count_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # System Count
        ttk.Label(frame, text="System Count*:").grid(row=3, column=0, sticky="w", pady=5)
        self.system_count_entry = ttk.Entry(frame, width=40)
        self.system_count_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Reason
        ttk.Label(frame, text="Reason for Adjustment*:").grid(row=4, column=0, sticky="w", pady=5)
        self.reason_combo = ttk.Combobox(frame, values=["Damaged during handling", "Manufacturing defect", "Missing item", "Counting error", "Theft/Loss", "Other"], width=37, state="readonly")
        self.reason_combo.grid(row=4, column=1, sticky="ew", pady=5)

        # Date
        ttk.Label(frame, text="Audit Date*:").grid(row=5, column=0, sticky="w", pady=5)
        self.date_entry = ttk.Entry(frame, width=40)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=5, column=1, sticky="ew", pady=5)

        # Audited By
        ttk.Label(frame, text="Audited By*:").grid(row=6, column=0, sticky="w", pady=5)
        self.audited_by_entry = ttk.Entry(frame, width=40)
        self.audited_by_entry.grid(row=6, column=1, sticky="ew", pady=5)

    def populate_values(self, values):
        """Populate form with existing values."""
        try:
            self.item_id_entry.insert(0, values[1])
            self.item_name_entry.insert(0, values[2])
            self.physical_count_entry.insert(0, values[3])
            self.system_count_entry.insert(0, values[4])
            self.reason_combo.set(values[6])
            self.date_entry.insert(0, values[7])
            self.audited_by_entry.insert(0, values[8])
        except IndexError:
            pass

    def save_audit(self):
        """Save audit to CSV."""
        item_id = self.item_id_entry.get().strip()
        physical_count = self.physical_count_entry.get().strip()
        system_count = self.system_count_entry.get().strip()
        reason = self.reason_combo.get()
        date = self.date_entry.get().strip()
        audited_by = self.audited_by_entry.get().strip()

        if not item_id or not physical_count or not system_count or not reason or not date or not audited_by:
            messagebox.showwarning("Input Error", "All required fields must be filled.", parent=self)
            return

        # Calculate variance
        try:
            variance = int(physical_count) - int(system_count)
        except ValueError:
            variance = "N/A"

        row_data = [
            f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            item_id,
            self.item_name_entry.get().strip(),
            physical_count,
            system_count,
            str(variance),
            reason,
            date,
            audited_by
        ]

        csv_file = getattr(config, "WAREHOUSE_AUDIT_CSV", os.path.join(config.CSV_DIR, "warehouse_audit.csv"))
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        file_exists = os.path.exists(csv_file)
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Audit ID", "Item ID", "Item Name", "Physical Count", "System Count", "Variance", "Reason", "Date", "Audited By"])
            writer.writerow(row_data)

        messagebox.showinfo("Success", "Audit saved successfully!", parent=self)
        self.destroy()
        if self.callback:
            self.callback()