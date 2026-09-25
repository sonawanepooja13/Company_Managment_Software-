import csv
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk, filedialog
import config


class LegalComplianceView(ttk.Frame):
    """Main Legal & Compliance Management Module with tabbed interface."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        # Create notebook for different legal components
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Add tabs for each component
        self.internal_tab = InternalDocumentsTab(self.notebook)
        self.notebook.add(self.internal_tab, text=" Internal Documents ")

        self.external_tab = ExternalDocumentsTab(self.notebook)
        self.notebook.add(self.external_tab, text=" External Documents ")

        self.data_protection_tab = DataProtectionTab(self.notebook)
        self.notebook.add(self.data_protection_tab, text=" Data Protection ")

        self.contracts_tab = ContractsTrackingTab(self.notebook)
        self.notebook.add(self.contracts_tab, text=" Contracts Tracking ")

        self.employee_agreements_tab = EmployeeAgreementsTab(self.notebook)
        self.notebook.add(self.employee_agreements_tab, text=" Employee Agreements ")

        self.templates_tab = DocumentTemplatesTab(self.notebook)
        self.notebook.add(self.templates_tab, text=" Document Templates ")


class InternalDocumentsTab(ttk.Frame):
    """Internal & Employment Documents - IP Assignment, NDA, Employment Contracts."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_documents()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Document Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Documents:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_docs_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_docs_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Expiring Soon:").grid(row=0, column=2, sticky="w", padx=5)
        self.expiring_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.expiring_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Document", command=self.add_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_documents).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Type:").pack(side="left", padx=5)
        self.doc_type_filter = ttk.Combobox(filter_frame, values=["All", "IP Assignment", "NDA", "Employment Contract"], width=20, state="readonly")
        self.doc_type_filter.set("All")
        self.doc_type_filter.pack(side="left", padx=5)
        self.doc_type_filter.bind("<<ComboboxSelected>>", self.filter_documents)

        # Documents table
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

        columns = ["doc_id", "doc_type", "employee_name", "effective_date", "expiry_date", "status", "file_path", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_documents(self):
        csv_file = getattr(config, "INTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "internal_documents.csv"))
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

    def filter_documents(self, event=None):
        filter_type = self.doc_type_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_type == "All" or values[1] == filter_type:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        expiring_count = 0
        today = datetime.now()
        warning_days = 30

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 4 and values[4]:  # expiry_date
                try:
                    expiry_date = datetime.strptime(values[4], "%Y-%m-%d")
                    days_until_expiry = (expiry_date - today).days
                    if 0 <= days_until_expiry <= warning_days:
                        expiring_count += 1
                except ValueError:
                    pass

        self.total_docs_var.set(str(total))
        self.expiring_var.set(str(expiring_count))

    def add_document(self):
        InternalDocumentDialog(self, callback=self.load_documents)

    def edit_document(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Document", "Please select a document to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        InternalDocumentDialog(self, callback=self.load_documents, edit_values=item_values)

    def delete_document(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Document", "Please select a document to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this document?", parent=self):
            csv_file = getattr(config, "INTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "internal_documents.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_documents()

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


class InternalDocumentDialog(tk.Toplevel):
    """Dialog for internal legal documents."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Document" if self.is_edit else "Add Internal Document")
        self.geometry("550x500")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Internal Legal Document", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Document type dropdown
        ttk.Label(frame, text="Document Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.doc_type_combo = ttk.Combobox(frame, values=["IP Assignment", "NDA", "Employment Contract"], width=30, state="readonly")
        self.doc_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Employee Name*", "employee_name"),
            ("Effective Date*", "effective_date"),
            ("Expiry Date", "expiry_date"),
            ("File Path", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=4, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=5, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "Expired", "Pending", "Terminated"], width=30, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=5, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=6, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=6, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Document", command=self.save_document).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Document File",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.doc_type_combo.set(values[1])
            self.entries["employee_name"].insert(0, values[2])
            self.entries["effective_date"].insert(0, values[3])
            self.entries["expiry_date"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.entries["file_path"].insert(0, values[6])
            self.notes_text.insert("1.0", values[7])
        except IndexError:
            pass

    def save_document(self):
        doc_type = self.doc_type_combo.get()
        employee_name = self.entries["employee_name"].get().strip()
        effective_date = self.entries["effective_date"].get().strip()

        if not doc_type or not employee_name or not effective_date:
            messagebox.showwarning("Input Error", "Document type, employee name, and effective date are required.", parent=self)
            return

        csv_file = getattr(config, "INTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "internal_documents.csv"))
        doc_id = f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            doc_id,
            doc_type,
            employee_name,
            effective_date,
            self.entries["expiry_date"].get().strip(),
            self.status_combo.get(),
            self.entries["file_path"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["doc_id", "doc_type", "employee_name", "effective_date", "expiry_date", "status", "file_path", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Document for '{employee_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save document: {e}", parent=self)


class ExternalDocumentsTab(ttk.Frame):
    """External & Commercial Documents - Software Development Agreement, License Agreement, MSA."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_documents()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Document Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Documents:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_docs_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_docs_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Active Contracts:").grid(row=0, column=2, sticky="w", padx=5)
        self.active_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Document", command=self.add_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_document).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_documents).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Type:").pack(side="left", padx=5)
        self.doc_type_filter = ttk.Combobox(filter_frame, values=["All", "Software Development Agreement", "License Agreement", "MSA"], width=25, state="readonly")
        self.doc_type_filter.set("All")
        self.doc_type_filter.pack(side="left", padx=5)
        self.doc_type_filter.bind("<<ComboboxSelected>>", self.filter_documents)

        # Documents table
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

        columns = ["doc_id", "doc_type", "client_vendor_name", "effective_date", "expiry_date", "status", "file_path", "value", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_documents(self):
        csv_file = getattr(config, "EXTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "external_documents.csv"))
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

    def filter_documents(self, event=None):
        filter_type = self.doc_type_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_type == "All" or values[1] == filter_type:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        active = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[5] == "Active")
        self.total_docs_var.set(str(total))
        self.active_var.set(str(active))

    def add_document(self):
        ExternalDocumentDialog(self, callback=self.load_documents)

    def edit_document(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Document", "Please select a document to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ExternalDocumentDialog(self, callback=self.load_documents, edit_values=item_values)

    def delete_document(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Document", "Please select a document to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this document?", parent=self):
            csv_file = getattr(config, "EXTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "external_documents.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_documents()

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


class ExternalDocumentDialog(tk.Toplevel):
    """Dialog for external legal documents."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Document" if self.is_edit else "Add External Document")
        self.geometry("550x520")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="External Legal Document", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Document type dropdown
        ttk.Label(frame, text="Document Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.doc_type_combo = ttk.Combobox(frame, values=["Software Development Agreement", "License Agreement", "MSA"], width=30, state="readonly")
        self.doc_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Client/Vendor Name*", "client_vendor_name"),
            ("Effective Date*", "effective_date"),
            ("Expiry Date", "expiry_date"),
            ("Contract Value", "value"),
            ("File Path", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=5, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=6, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "Expired", "Pending", "Terminated", "Renewed"], width=30, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=6, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=7, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Document", command=self.save_document).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Document File",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.doc_type_combo.set(values[1])
            self.entries["client_vendor_name"].insert(0, values[2])
            self.entries["effective_date"].insert(0, values[3])
            self.entries["expiry_date"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.entries["file_path"].insert(0, values[6])
            self.entries["value"].insert(0, values[7])
            self.notes_text.insert("1.0", values[8])
        except IndexError:
            pass

    def save_document(self):
        doc_type = self.doc_type_combo.get()
        client_name = self.entries["client_vendor_name"].get().strip()
        effective_date = self.entries["effective_date"].get().strip()

        if not doc_type or not client_name or not effective_date:
            messagebox.showwarning("Input Error", "Document type, client/vendor name, and effective date are required.", parent=self)
            return

        csv_file = getattr(config, "EXTERNAL_DOCS_CSV", os.path.join(config.CSV_DIR, "external_documents.csv"))
        doc_id = f"EXT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            doc_id,
            doc_type,
            client_name,
            effective_date,
            self.entries["expiry_date"].get().strip(),
            self.status_combo.get(),
            self.entries["file_path"].get().strip(),
            self.entries["value"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["doc_id", "doc_type", "client_vendor_name", "effective_date", "expiry_date", "status", "file_path", "value", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Document with '{client_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save document: {e}", parent=self)


class DataProtectionTab(ttk.Frame):
    """Data Protection & Cybersecurity Compliance - Privacy Policy, GDPR/DPDP."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_compliance_docs()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Compliance Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Policies:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_policies_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_policies_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Review Required:").grid(row=0, column=2, sticky="w", padx=5)
        self.review_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.review_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Policy", command=self.add_policy).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_policy).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_policy).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_compliance_docs).pack(side="left", padx=5)

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

        columns = ["policy_id", "policy_type", "applicable_law", "last_review_date", "next_review_date", "status", "file_path", "responsible_person", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_compliance_docs(self):
        csv_file = getattr(config, "DATA_PROTECTION_CSV", os.path.join(config.CSV_DIR, "data_protection.csv"))
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
        review_required = 0
        today = datetime.now()

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 5 and values[5] == "Review Required":
                review_required += 1
            elif len(values) > 4 and values[4]:  # next_review_date
                try:
                    next_review = datetime.strptime(values[4], "%Y-%m-%d")
                    if next_review <= today:
                        review_required += 1
                except ValueError:
                    pass

        self.total_policies_var.set(str(total))
        self.review_var.set(str(review_required))

    def add_policy(self):
        DataProtectionDialog(self, callback=self.load_compliance_docs)

    def edit_policy(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Policy", "Please select a policy to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        DataProtectionDialog(self, callback=self.load_compliance_docs, edit_values=item_values)

    def delete_policy(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Policy", "Please select a policy to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this policy?", parent=self):
            csv_file = getattr(config, "DATA_PROTECTION_CSV", os.path.join(config.CSV_DIR, "data_protection.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_compliance_docs()

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


class DataProtectionDialog(tk.Toplevel):
    """Dialog for data protection compliance documents."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Policy" if self.is_edit else "Add Data Protection Policy")
        self.geometry("550x580")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Data Protection & Compliance", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Policy type dropdown
        ttk.Label(frame, text="Policy Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.policy_type_combo = ttk.Combobox(frame, values=["Privacy Policy", "Terms of Service", "GDPR Compliance", "DPDP Act Compliance", "Data Breach Protocol"], width=30, state="readonly")
        self.policy_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Applicable law
        ttk.Label(frame, text="Applicable Law*:").grid(row=1, column=0, sticky="w", pady=5)
        self.law_combo = ttk.Combobox(frame, values=["GDPR", "DPDP Act", "CCPA", "Other", "Multiple"], width=30, state="readonly")
        self.law_combo.grid(row=1, column=1, sticky="w", pady=5)

        fields = [
            ("Last Review Date", "last_review_date"),
            ("Next Review Date*", "next_review_date"),
            ("Responsible Person", "responsible_person"),
            ("File Path", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+2, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+2, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=5, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=6, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "Review Required", "Outdated", "Draft"], width=30, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=6, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=7, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Policy", command=self.save_policy).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Policy Document",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("HTML Files", "*.html"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.policy_type_combo.set(values[1])
            self.law_combo.set(values[2])
            self.entries["last_review_date"].insert(0, values[3])
            self.entries["next_review_date"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.entries["file_path"].insert(0, values[6])
            self.entries["responsible_person"].insert(0, values[7])
            self.notes_text.insert("1.0", values[8])
        except IndexError:
            pass

    def save_policy(self):
        policy_type = self.policy_type_combo.get()
        applicable_law = self.law_combo.get()
        next_review_date = self.entries["next_review_date"].get().strip()

        if not policy_type or not applicable_law or not next_review_date:
            messagebox.showwarning("Input Error", "Policy type, applicable law, and next review date are required.", parent=self)
            return

        csv_file = getattr(config, "DATA_PROTECTION_CSV", os.path.join(config.CSV_DIR, "data_protection.csv"))
        policy_id = f"DP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            policy_id,
            policy_type,
            applicable_law,
            self.entries["last_review_date"].get().strip(),
            next_review_date,
            self.status_combo.get(),
            self.entries["file_path"].get().strip(),
            self.entries["responsible_person"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["policy_id", "policy_type", "applicable_law", "last_review_date", "next_review_date", "status", "file_path", "responsible_person", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Policy '{policy_type}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save policy: {e}", parent=self)


class ContractsTrackingTab(ttk.Frame):
    """Contract tracking and expiry management."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_contracts()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Contract Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Contracts:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_contracts_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_contracts_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Expiring in 30 Days:").grid(row=0, column=2, sticky="w", padx=5)
        self.expiring_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.expiring_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Contract", command=self.add_contract).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_contract).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_contract).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_contracts).pack(side="left", padx=5)

        # Contracts table
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

        columns = ["contract_id", "contract_name", "counterparty", "contract_type", "start_date", "end_date", "value", "status", "auto_renewal", "file_path"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_contracts(self):
        csv_file = getattr(config, "CONTRACTS_CSV", os.path.join(config.CSV_DIR, "contracts.csv"))
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
        expiring_count = 0
        today = datetime.now()
        warning_days = 30

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 5 and values[5]:  # end_date
                try:
                    end_date = datetime.strptime(values[5], "%Y-%m-%d")
                    days_until_expiry = (end_date - today).days
                    if 0 <= days_until_expiry <= warning_days:
                        expiring_count += 1
                except ValueError:
                    pass

        self.total_contracts_var.set(str(total))
        self.expiring_var.set(str(expiring_count))

    def add_contract(self):
        ContractDialog(self, callback=self.load_contracts)

    def edit_contract(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Contract", "Please select a contract to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ContractDialog(self, callback=self.load_contracts, edit_values=item_values)

    def delete_contract(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Contract", "Please select a contract to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this contract?", parent=self):
            csv_file = getattr(config, "CONTRACTS_CSV", os.path.join(config.CSV_DIR, "contracts.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_contracts()

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


class ContractDialog(tk.Toplevel):
    """Dialog for contract management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Contract" if self.is_edit else "Add Contract")
        self.geometry("580x600")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Contract Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        fields = [
            ("Contract Name*", "contract_name"),
            ("Counterparty*", "counterparty"),
            ("Contract Type*", "contract_type"),
            ("Start Date*", "start_date"),
            ("End Date*", "end_date"),
            ("Contract Value", "value"),
            ("File Path", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=35)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=6, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "Expired", "Pending", "Terminated", "Renewed"], width=33, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=7, column=1, sticky="w", pady=5)

        # Auto renewal checkbox
        self.auto_renewal_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Auto Renewal", variable=self.auto_renewal_var).grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Contract", command=self.save_contract).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Contract File",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.entries["contract_name"].insert(0, values[1])
            self.entries["counterparty"].insert(0, values[2])
            self.entries["contract_type"].insert(0, values[3])
            self.entries["start_date"].insert(0, values[4])
            self.entries["end_date"].insert(0, values[5])
            self.entries["value"].insert(0, values[6])
            self.status_combo.set(values[7])
            self.auto_renewal_var.set(values[8] == "Yes" if len(values) > 8 else False)
            self.entries["file_path"].insert(0, values[9] if len(values) > 9 else "")
        except IndexError:
            pass

    def save_contract(self):
        contract_name = self.entries["contract_name"].get().strip()
        counterparty = self.entries["counterparty"].get().strip()
        contract_type = self.entries["contract_type"].get().strip()
        start_date = self.entries["start_date"].get().strip()
        end_date = self.entries["end_date"].get().strip()

        if not contract_name or not counterparty or not contract_type or not start_date or not end_date:
            messagebox.showwarning("Input Error", "Contract name, counterparty, type, and dates are required.", parent=self)
            return

        csv_file = getattr(config, "CONTRACTS_CSV", os.path.join(config.CSV_DIR, "contracts.csv"))
        contract_id = f"CTR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            contract_id,
            contract_name,
            counterparty,
            contract_type,
            start_date,
            end_date,
            self.entries["value"].get().strip(),
            self.status_combo.get(),
            "Yes" if self.auto_renewal_var.get() else "No",
            self.entries["file_path"].get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["contract_id", "contract_name", "counterparty", "contract_type", "start_date", "end_date", "value", "status", "auto_renewal", "file_path"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Contract '{contract_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save contract: {e}", parent=self)


class EmployeeAgreementsTab(ttk.Frame):
    """Employee agreement tracking."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_agreements()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Agreement Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Agreements:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_agreements_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_agreements_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Pending Signatures:").grid(row=0, column=2, sticky="w", padx=5)
        self.pending_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.pending_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Agreement", command=self.add_agreement).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_agreement).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_agreement).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_agreements).pack(side="left", padx=5)

        # Agreements table
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

        columns = ["agreement_id", "employee_name", "agreement_type", "date_signed", "expiry_date", "status", "file_path", "department", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_agreements(self):
        csv_file = getattr(config, "EMPLOYEE_AGREEMENTS_CSV", os.path.join(config.CSV_DIR, "employee_agreements.csv"))
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
        pending = sum(1 for item in self.tree.get_children() if self.tree.item(item, "values")[5] == "Pending Signature")
        self.total_agreements_var.set(str(total))
        self.pending_var.set(str(pending))

    def add_agreement(self):
        EmployeeAgreementDialog(self, callback=self.load_agreements)

    def edit_agreement(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Agreement", "Please select an agreement to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        EmployeeAgreementDialog(self, callback=self.load_agreements, edit_values=item_values)

    def delete_agreement(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Agreement", "Please select an agreement to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this agreement?", parent=self):
            csv_file = getattr(config, "EMPLOYEE_AGREEMENTS_CSV", os.path.join(config.CSV_DIR, "employee_agreements.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_agreements()

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


class EmployeeAgreementDialog(tk.Toplevel):
    """Dialog for employee agreements."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Agreement" if self.is_edit else "Add Employee Agreement")
        self.geometry("550x500")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Employee Agreement Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Agreement type dropdown
        ttk.Label(frame, text="Agreement Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.agreement_type_combo = ttk.Combobox(frame, values=["IP Assignment", "NDA", "Employment Contract", "Non-Compete", "Non-Solicitation"], width=30, state="readonly")
        self.agreement_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Employee Name*", "employee_name"),
            ("Date Signed", "date_signed"),
            ("Expiry Date", "expiry_date"),
            ("Department", "department"),
            ("File Path", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+1, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=5, column=2, sticky="w", padx=5, pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=6, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Signed", "Pending Signature", "Expired", "Terminated"], width=30, state="readonly")
        self.status_combo.set("Pending Signature")
        self.status_combo.grid(row=6, column=1, sticky="w", pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=7, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Agreement", command=self.save_agreement).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Agreement File",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.entries["employee_name"].insert(0, values[1])
            self.agreement_type_combo.set(values[2])
            self.entries["date_signed"].insert(0, values[3])
            self.entries["expiry_date"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.entries["file_path"].insert(0, values[6])
            self.entries["department"].insert(0, values[7])
            self.notes_text.insert("1.0", values[8])
        except IndexError:
            pass

    def save_agreement(self):
        employee_name = self.entries["employee_name"].get().strip()
        agreement_type = self.agreement_type_combo.get()

        if not employee_name or not agreement_type:
            messagebox.showwarning("Input Error", "Employee name and agreement type are required.", parent=self)
            return

        csv_file = getattr(config, "EMPLOYEE_AGREEMENTS_CSV", os.path.join(config.CSV_DIR, "employee_agreements.csv"))
        agreement_id = f"EA-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            agreement_id,
            employee_name,
            agreement_type,
            self.entries["date_signed"].get().strip(),
            self.entries["expiry_date"].get().strip(),
            self.status_combo.get(),
            self.entries["file_path"].get().strip(),
            self.entries["department"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["agreement_id", "employee_name", "agreement_type", "date_signed", "expiry_date", "status", "file_path", "department", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Agreement for '{employee_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save agreement: {e}", parent=self)


class DocumentTemplatesTab(ttk.Frame):
    """Document templates management."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_templates()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Template Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Templates:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_templates_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_templates_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Template", command=self.add_template).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_template).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_template).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_templates).pack(side="left", padx=5)

        # Templates table
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

        columns = ["template_id", "template_name", "category", "description", "file_path", "last_updated", "is_active"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")

    def load_templates(self):
        csv_file = getattr(config, "DOCUMENT_TEMPLATES_CSV", os.path.join(config.CSV_DIR, "document_templates.csv"))
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
        self.total_templates_var.set(str(total))

    def add_template(self):
        TemplateDialog(self, callback=self.load_templates)

    def edit_template(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Template", "Please select a template to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        TemplateDialog(self, callback=self.load_templates, edit_values=item_values)

    def delete_template(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Template", "Please select a template to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this template?", parent=self):
            csv_file = getattr(config, "DOCUMENT_TEMPLATES_CSV", os.path.join(config.CSV_DIR, "document_templates.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_templates()

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


class TemplateDialog(tk.Toplevel):
    """Dialog for document templates."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Template" if self.is_edit else "Add Document Template")
        self.geometry("550x450")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Document Template Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Category dropdown
        ttk.Label(frame, text="Category*:").grid(row=0, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(frame, values=["Internal", "External", "Data Protection", "Employment", "Commercial"], width=30, state="readonly")
        self.category_combo.grid(row=0, column=1, sticky="w", pady=5)

        fields = [
            ("Template Name*", "template_name"),
            ("Description", "description"),
            ("File Path*", "file_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+1, column=0, sticky="w", pady=5)
            if key == "description":
                text_widget = tk.Text(frame, width=30, height=3)
                text_widget.grid(row=idx+1, column=1, sticky="w", pady=5)
                self.entries[key] = text_widget
            else:
                entry = ttk.Entry(frame, width=32)
                entry.grid(row=idx+1, column=1, sticky="w", pady=5)
                self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse File", command=self.browse_file).grid(row=3, column=2, sticky="w", padx=5, pady=5)

        # Active checkbox
        self.is_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Active Template", variable=self.is_active_var).grid(row=4, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Template", command=self.save_template).pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Template File",
            filetypes=[("Word Documents", "*.docx"), ("PDF Files", "*.pdf"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["file_path"].delete(0, tk.END)
            self.entries["file_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.entries["template_name"].insert(0, values[1])
            self.category_combo.set(values[2])
            self.entries["description"].insert("1.0", values[3])
            self.entries["file_path"].insert(0, values[4])
            self.is_active_var.set(values[6] == "Yes" if len(values) > 6 else True)
        except IndexError:
            pass

    def save_template(self):
        template_name = self.entries["template_name"].get().strip()
        category = self.category_combo.get()
        file_path = self.entries["file_path"].get().strip()

        if not template_name or not category or not file_path:
            messagebox.showwarning("Input Error", "Template name, category, and file path are required.", parent=self)
            return

        csv_file = getattr(config, "DOCUMENT_TEMPLATES_CSV", os.path.join(config.CSV_DIR, "document_templates.csv"))
        template_id = f"TPL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")

        row = [
            template_id,
            template_name,
            category,
            self.entries["description"].get("1.0", tk.END).strip(),
            file_path,
            last_updated,
            "Yes" if self.is_active_var.get() else "No",
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["template_id", "template_name", "category", "description", "file_path", "last_updated", "is_active"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Template '{template_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}", parent=self)