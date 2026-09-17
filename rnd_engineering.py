import csv
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk, filedialog

from tkcalendar import DateEntry

import config
from openpyxl import Workbook


def create_date_entry(parent, value="", width=32):
    widget = DateEntry(parent, width=max(12, width - 6), date_pattern="yyyy-mm-dd", state="readonly")
    if value:
        widget.delete(0, tk.END)
        try:
            widget.set_date(datetime.strptime(str(value).strip(), "%Y-%m-%d").date())
        except ValueError:
            try:
                widget.set_date(datetime.strptime(str(value).strip(), "%d/%m/%Y").date())
            except ValueError:
                widget.insert(0, str(value).strip())
    else:
        widget.delete(0, tk.END)
    return widget


def set_field_value(widget, value):
    if hasattr(widget, "set_date"):
        widget.delete(0, tk.END)
        value = str(value or "").strip()
        if value:
            try:
                widget.set_date(datetime.strptime(value, "%Y-%m-%d").date())
            except ValueError:
                try:
                    widget.set_date(datetime.strptime(value, "%d/%m/%Y").date())
                except ValueError:
                    widget.insert(0, value)
        return
    widget.delete(0, tk.END)
    if value:
        widget.insert(0, str(value).strip())


class RnDEngineeringView(ttk.Frame):
    """Main R&D/Engineering Management Module with tabbed interface."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.user_data = user_data
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.setup_ui()

    def setup_ui(self):
        # Create notebook for different R&D components
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Get user permissions
        user_permissions = {}
        if self.user_data:
            user_permissions = {k: v for k, v in self.user_data.items() if k.startswith('allow_rnd_')}

        # Add tabs for each component based on permissions
        if user_permissions.get('allow_rnd_pdlc', True):
            self.pdlc_tab = ProductDevelopmentTab(self.notebook)
            self.notebook.add(self.pdlc_tab, text=" Product Development (PDLC) ")
        else:
            self.pdlc_tab = None

        if user_permissions.get('allow_rnd_projects', True):
            self.projects_tab = ProjectsTasksTab(self.notebook)
            self.notebook.add(self.projects_tab, text=" Projects & Tasks ")
        else:
            self.projects_tab = None

        if user_permissions.get('allow_rnd_sprints', True):
            self.sprints_tab = SprintManagementTab(self.notebook)
            self.notebook.add(self.sprints_tab, text=" Sprint Management ")
        else:
            self.sprints_tab = None

        if user_permissions.get('allow_rnd_hardware', True):
            self.hardware_tab = HardwarePrototypeTab(self.notebook)
            self.notebook.add(self.hardware_tab, text=" Hardware & Prototypes ")
        else:
            self.hardware_tab = None

        if user_permissions.get('allow_rnd_components', True):
            self.components_tab = ComponentsTab(self.notebook)
            self.notebook.add(self.components_tab, text=" Components & Supply ")
        else:
            self.components_tab = None

        if user_permissions.get('allow_rnd_risk', True):
            self.risk_tab = RiskManagementTab(self.notebook)
            self.notebook.add(self.risk_tab, text=" Risk Management ")
        else:
            self.risk_tab = None

        if user_permissions.get('allow_rnd_team', True):
            self.team_tab = TeamResourceTab(self.notebook)
            self.notebook.add(self.team_tab, text=" Team & Resources ")
        else:
            self.team_tab = None

        if user_permissions.get('allow_rnd_compliance', True):
            self.compliance_tab = ComplianceCertificationTab(self.notebook)
            self.notebook.add(self.compliance_tab, text=" Compliance & Certification ")
        else:
            self.compliance_tab = None


class ProductDevelopmentTab(ttk.Frame):
    """Product Development Lifecycle (PDLC) - Hybrid Stage-Gate + Agile model."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" PDLC Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Active Products:").grid(row=0, column=0, sticky="w", padx=5)
        self.active_products_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_products_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="In Development:").grid(row=0, column=2, sticky="w", padx=5)
        self.in_dev_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.in_dev_var, font=("Helvetica", 10, "bold"), foreground="blue").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Ready for Deployment:").grid(row=0, column=4, sticky="w", padx=5)
        self.ready_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.ready_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Product", command=self.add_product).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_product).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_product).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_products).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Stage:").pack(side="left", padx=5)
        self.stage_filter = ttk.Combobox(filter_frame, values=["All", "Requirements", "Architecture", "Development", "Integration", "Compliance", "Deployment"], width=25, state="readonly")
        self.stage_filter.set("All")
        self.stage_filter.pack(side="left", padx=5)
        self.stage_filter.bind("<<ComboboxSelected>>", self.filter_products)

        # Products table
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

        columns = ["product_id", "product_name", "product_type", "current_stage", "stage_gate", "start_date", "target_date", "status", "priority", "team_lead", "completion_percentage"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_products(self):
        csv_file = getattr(config, "PDLC_PRODUCTS_CSV", os.path.join(config.CSV_DIR, "pdlc_products.csv"))
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

    def filter_products(self, event=None):
        filter_stage = self.stage_filter.get()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if filter_stage == "All" or values[3] == filter_stage:
                self.tree.item(item, tags=())
            else:
                self.tree.item(item, tags=("hidden",))
        self.tree.tag_configure("hidden", display="none")

    def update_summary(self):
        total = len(self.tree.get_children())
        active = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 7 and self.tree.item(item, "values")[7] == "Active")
        in_dev = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 3 and self.tree.item(item, "values")[3] in ["Development", "Integration"])
        ready = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 3 and self.tree.item(item, "values")[3] == "Deployment")
        self.active_products_var.set(str(active))
        self.in_dev_var.set(str(in_dev))
        self.ready_var.set(str(ready))

    def add_product(self):
        ProductDialog(self, callback=self.load_products)

    def edit_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Please select a product to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ProductDialog(self, callback=self.load_products, edit_values=item_values)
    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Please select a product to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?", parent=self):
            csv_file = getattr(config, "PDLC_PRODUCTS_CSV", os.path.join(config.CSV_DIR, "pdlc_products.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_products()

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


class ProductDialog(tk.Toplevel):
    """Dialog for product development management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.edit_values = edit_values
        self.title("Edit Product" if self.is_edit else "New Product Development")
        self.geometry("600x700")
        self.minsize(520, 560)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()
        self.bind("<Control-s>", lambda event: self.save_product())
        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Product Development Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Entry (CSV)", command=self.save_product).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(10, weight=1)

        # Product type dropdown
        ttk.Label(frame, text="Product Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.product_type_combo = ttk.Combobox(frame, values=["Embedded System", "IoT Device", "Firmware", "Hardware", "Software", "Other"], width=30, state="readonly")
        self.product_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Current stage dropdown
        ttk.Label(frame, text="Current Stage*:").grid(row=1, column=0, sticky="w", pady=5)
        self.stage_combo = ttk.Combobox(frame, values=["Requirements", "Architecture", "Development", "Integration", "Compliance", "Deployment"], width=30, state="readonly")
        self.stage_combo.set("Requirements")
        self.stage_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Stage gate dropdown
        ttk.Label(frame, text="Stage Gate*:").grid(row=2, column=0, sticky="w", pady=5)
        self.gate_combo = ttk.Combobox(frame, values=["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Complete"], width=30, state="readonly")
        self.gate_combo.set("Stage 1")
        self.gate_combo.grid(row=2, column=1, sticky="w", pady=5)

        fields = [
            ("Product Name*", "product_name"),
            ("Start Date*", "start_date"),
            ("Target Date*", "target_date"),
            ("Team Lead*", "team_lead"),
            ("Completion %", "completion_percentage"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+3, column=0, sticky="w", pady=5)
            entry = create_date_entry(frame, width=32) if "date" in key.lower() else ttk.Entry(frame, width=32)
            entry.grid(row=idx+3, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=8, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Active", "On Hold", "Completed", "Cancelled"], width=30, state="readonly")
        self.status_combo.set("Active")
        self.status_combo.grid(row=8, column=1, sticky="w", pady=5)

        # Priority dropdown
        ttk.Label(frame, text="Priority:").grid(row=9, column=0, sticky="w", pady=5)
        self.priority_combo = ttk.Combobox(frame, values=["Critical", "High", "Medium", "Low"], width=30, state="readonly")
        self.priority_combo.set("Medium")
        self.priority_combo.grid(row=9, column=1, sticky="w", pady=5)

        # Description
        ttk.Label(frame, text="Description:").grid(row=10, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=30, height=4)
        self.description_text.grid(row=10, column=1, sticky="nsew", pady=5)

    def populate_values(self, values):
        try:
            self.entries["product_name"].insert(0, values[1])
            self.product_type_combo.set(values[2])
            self.stage_combo.set(values[3])
            self.gate_combo.set(values[4])
            set_field_value(self.entries["start_date"], values[5])
            set_field_value(self.entries["target_date"], values[6])
            self.status_combo.set(values[7])
            self.priority_combo.set(values[8])
            self.entries["team_lead"].insert(0, values[9])
            self.entries["completion_percentage"].insert(0, values[10] if len(values) > 10 else "0")
            self.description_text.insert("1.0", values[11] if len(values) > 11 else "")
        except IndexError:
            pass

    def save_product(self):
        product_name = self.entries["product_name"].get().strip()
        product_type = self.product_type_combo.get()
        current_stage = self.stage_combo.get()
        stage_gate = self.gate_combo.get()
        start_date = self.entries["start_date"].get().strip()
        target_date = self.entries["target_date"].get().strip()
        team_lead = self.entries["team_lead"].get().strip()

        if not product_name or not product_type or not current_stage or not stage_gate or not start_date or not target_date or not team_lead:
            messagebox.showwarning("Input Error", "All required fields must be filled.", parent=self)
            return

        csv_file = getattr(config, "PDLC_PRODUCTS_CSV", os.path.join(config.CSV_DIR, "pdlc_products.csv"))
        product_id = (
            self.edit_values[0]
            if self.is_edit and self.edit_values
            else f"PDLC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        row = [
            product_id,
            product_name,
            product_type,
            current_stage,
            stage_gate,
            start_date,
            target_date,
            self.status_combo.get(),
            self.priority_combo.get(),
            team_lead,
            self.entries["completion_percentage"].get().strip(),
            self.description_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["product_id", "product_name", "product_type", "current_stage", "stage_gate", "start_date", "target_date", "status", "priority", "team_lead", "completion_percentage", "description"])

        if self.is_edit and self.edit_values:
            for index, existing_row in enumerate(rows[1:], start=1):
                if existing_row and existing_row[0] == self.edit_values[0]:
                    rows[index] = row
                    break
            else:
                rows.append(row)
        else:
            rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Product '{product_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product: {e}", parent=self)

    def export_excel(self):
        csv_file = getattr(config, "PDLC_PRODUCTS_CSV", os.path.join(config.CSV_DIR, "pdlc_products.csv"))
        if not os.path.exists(csv_file):
            messagebox.showwarning("No Products", "Save a product before exporting Excel.", parent=self)
            return

        with open(csv_file, mode="r", encoding="utf-8-sig") as file:
            rows = list(csv.reader(file))
        if len(rows) <= 1:
            messagebox.showwarning("No Products", "Save a product before exporting Excel.", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Product Development Excel",
            defaultextension=".xlsx",
            initialfile="pdlc_products.xlsx",
            filetypes=(("Excel workbook", "*.xlsx"),),
        )
        if not path:
            return

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Product Development"
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
        workbook.save(path)
        messagebox.showinfo("Exported", f"Excel sheet saved to:\n{path}", parent=self)


class ProjectsTasksTab(ttk.Frame):
    """Projects & Tasks Management - Embedded workflows with hardware dependencies."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Task Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Tasks:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_tasks_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_tasks_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Hardware Dependent:").grid(row=0, column=2, sticky="w", padx=5)
        self.hw_dep_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.hw_dep_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="In Progress:").grid(row=0, column=4, sticky="w", padx=5)
        self.in_progress_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.in_progress_var, font=("Helvetica", 10, "bold"), foreground="blue").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Task", command=self.add_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_tasks).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_frame, text="Filter by Status:").pack(side="left", padx=5)
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "To Do", "In Progress", "Code Review", "Hardware Testing", "Done"], width=25, state="readonly")
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.bind("<<ComboboxSelected>>", self.filter_tasks)

        # Tasks table
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

        columns = ["task_id", "task_name", "task_type", "product_id", "assigned_to", "status", "priority", "hardware_dependency", "sprint", "estimated_hours", "due_date", "blocked_by", "sub_task"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=90, anchor="w")

    def load_tasks(self):
        csv_file = getattr(config, "RND_TASKS_CSV", os.path.join(config.CSV_DIR, "rnd_tasks.csv"))
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

    def filter_tasks(self, event=None):
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
        hw_dep = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 7 and self.tree.item(item, "values")[7] == "Yes")
        in_progress = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 5 and self.tree.item(item, "values")[5] == "In Progress")
        self.total_tasks_var.set(str(total))
        self.hw_dep_var.set(str(hw_dep))
        self.in_progress_var.set(str(in_progress))

    def add_task(self):
        TaskDialog(self, callback=self.load_tasks)

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Task", "Please select a task to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        TaskDialog(self, callback=self.load_tasks, edit_values=item_values)

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Task", "Please select a task to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?", parent=self):
            csv_file = getattr(config, "RND_TASKS_CSV", os.path.join(config.CSV_DIR, "rnd_tasks.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_tasks()

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


class TaskDialog(tk.Toplevel):
    """Dialog for task management with embedded workflows."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Task" if self.is_edit else "New Task")
        self.geometry("600x650")
        self.minsize(520, 500)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Task Management - Embedded Workflow", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Task", command=self.save_task).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(12, weight=1)

        # Task type dropdown
        ttk.Label(frame, text="Task Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.task_type_combo = ttk.Combobox(frame, values=["Firmware", "Hardware", "Integration", "Testing", "Documentation", "Bug Fix"], width=30, state="readonly")
        self.task_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Status dropdown - Embedded workflow
        ttk.Label(frame, text="Status*:").grid(row=1, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["To Do", "In Progress", "Code Review", "Hardware Testing", "Done"], width=30, state="readonly")
        self.status_combo.set("To Do")
        self.status_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Priority dropdown
        ttk.Label(frame, text="Priority*:").grid(row=2, column=0, sticky="w", pady=5)
        self.priority_combo = ttk.Combobox(frame, values=["Critical", "High", "Medium", "Low"], width=30, state="readonly")
        self.priority_combo.set("Medium")
        self.priority_combo.grid(row=2, column=1, sticky="w", pady=5)

        fields = [
            ("Task Name*", "task_name"),
            ("Product ID", "product_id"),
            ("Assigned To*", "assigned_to"),
            ("Sprint", "sprint"),
            ("Estimated Hours", "estimated_hours"),
            ("Due Date", "due_date"),
            ("Blocked By", "blocked_by"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+3, column=0, sticky="w", pady=5)
            entry = create_date_entry(frame, width=32) if "date" in key.lower() else ttk.Entry(frame, width=32)
            entry.grid(row=idx+3, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Task structure options
        self.hw_dep_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Hardware Dependency", variable=self.hw_dep_var).grid(row=10, column=1, sticky="w", pady=5)

        self.sub_task_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="This is a sub-task", variable=self.sub_task_var).grid(row=11, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Sub-task Details:").grid(row=12, column=0, sticky="nw", pady=5)
        self.sub_task_text = tk.Text(frame, width=30, height=2)
        self.sub_task_text.grid(row=12, column=1, sticky="w", pady=5)

        # Description
        ttk.Label(frame, text="Description:").grid(row=13, column=0, sticky="nw", pady=5)
        self.description_text = tk.Text(frame, width=30, height=3)
        self.description_text.grid(row=13, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Task", command=self.save_task).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["task_name"].insert(0, values[1])
            self.task_type_combo.set(values[2])
            self.entries["product_id"].insert(0, values[3])
            self.entries["assigned_to"].insert(0, values[4])
            self.status_combo.set(values[5])
            self.priority_combo.set(values[6])
            self.hw_dep_var.set(values[7] == "Yes" if len(values) > 7 else False)
            self.entries["sprint"].insert(0, values[8] if len(values) > 8 else "")
            self.entries["estimated_hours"].insert(0, values[9] if len(values) > 9 else "")
            set_field_value(self.entries["due_date"], values[10] if len(values) > 10 else "")
            self.entries["blocked_by"].insert(0, values[11] if len(values) > 11 else "")
            if len(values) > 13:
                self.sub_task_var.set(bool(str(values[12]).strip()))
                self.sub_task_text.insert("1.0", values[12])
                self.description_text.insert("1.0", values[13])
            elif len(values) > 12:
                self.sub_task_var.set(False)
                self.sub_task_text.insert("1.0", "")
                self.description_text.insert("1.0", values[12])
            else:
                self.sub_task_var.set(False)
        except IndexError:
            pass

    def save_task(self):
        task_name = self.entries["task_name"].get().strip()
        task_type = self.task_type_combo.get()
        status = self.status_combo.get()
        priority = self.priority_combo.get()
        assigned_to = self.entries["assigned_to"].get().strip()

        if not task_name or not task_type or not status or not priority or not assigned_to:
            messagebox.showwarning("Input Error", "Task name, type, status, priority, and assignee are required.", parent=self)
            return

        csv_file = getattr(config, "RND_TASKS_CSV", os.path.join(config.CSV_DIR, "rnd_tasks.csv"))
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        sub_task_value = self.sub_task_text.get("1.0", tk.END).strip()
        if self.sub_task_var.get() and not sub_task_value:
            sub_task_value = "Parent task linked"

        row = [
            task_id,
            task_name,
            task_type,
            self.entries["product_id"].get().strip(),
            assigned_to,
            status,
            priority,
            "Yes" if self.hw_dep_var.get() else "No",
            self.entries["sprint"].get().strip(),
            self.entries["estimated_hours"].get().strip(),
            self.entries["due_date"].get().strip(),
            self.entries["blocked_by"].get().strip(),
            sub_task_value if self.sub_task_var.get() else "",
            self.description_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["task_id", "task_name", "task_type", "product_id", "assigned_to", "status", "priority", "hardware_dependency", "sprint", "estimated_hours", "due_date", "blocked_by", "sub_task", "description"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Task '{task_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task: {e}", parent=self)


class SprintManagementTab(ttk.Frame):
    """Sprint/Iteration Management - 2-week sprints for embedded development."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_sprints()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Sprint Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Active Sprints:").grid(row=0, column=0, sticky="w", padx=5)
        self.active_sprints_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.active_sprints_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Total Tasks:").grid(row=0, column=2, sticky="w", padx=5)
        self.total_tasks_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_tasks_var, font=("Helvetica", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Completed:").grid(row=0, column=4, sticky="w", padx=5)
        self.completed_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.completed_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ New Sprint", command=self.add_sprint).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_sprint).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_sprint).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_sprints).pack(side="left", padx=5)

        # Sprints table
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

        columns = ["sprint_id", "sprint_name", "start_date", "end_date", "status", "total_tasks", "completed_tasks", "velocity", "team_lead", "goal"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_sprints(self):
        csv_file = getattr(config, "SPRINTS_CSV", os.path.join(config.CSV_DIR, "sprints.csv"))
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
        active = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 4 and self.tree.item(item, "values")[4] == "Active")
        total_tasks = sum(int(self.tree.item(item, "values")[5]) if len(self.tree.item(item, "values")) > 5 and self.tree.item(item, "values")[5].isdigit() else 0 for item in self.tree.get_children())
        completed = sum(int(self.tree.item(item, "values")[6]) if len(self.tree.item(item, "values")) > 6 and self.tree.item(item, "values")[6].isdigit() else 0 for item in self.tree.get_children())
        self.active_sprints_var.set(str(active))
        self.total_tasks_var.set(str(total_tasks))
        self.completed_var.set(str(completed))

    def add_sprint(self):
        SprintDialog(self, callback=self.load_sprints)

    def edit_sprint(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Sprint", "Please select a sprint to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        SprintDialog(self, callback=self.load_sprints, edit_values=item_values)

    def delete_sprint(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Sprint", "Please select a sprint to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this sprint?", parent=self):
            csv_file = getattr(config, "SPRINTS_CSV", os.path.join(config.CSV_DIR, "sprints.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_sprints()

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


class SprintDialog(tk.Toplevel):
    """Dialog for sprint management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Sprint" if self.is_edit else "New Sprint")
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
        ttk.Label(self, text="Sprint Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Sprint", command=self.save_sprint).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(9, weight=1)

        fields = [
            ("Sprint Name*", "sprint_name"),
            ("Start Date*", "start_date"),
            ("End Date*", "end_date"),
            ("Team Lead*", "team_lead"),
            ("Total Tasks", "total_tasks"),
            ("Completed Tasks", "completed_tasks"),
            ("Velocity (story points)", "velocity"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=5)
            entry = create_date_entry(frame, width=32) if "date" in key.lower() else ttk.Entry(frame, width=32)
            entry.grid(row=idx, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Planning", "Active", "Completed", "Cancelled"], width=30, state="readonly")
        self.status_combo.set("Planning")
        self.status_combo.grid(row=7, column=1, sticky="w", pady=5)

        # Sprint goal
        ttk.Label(frame, text="Sprint Goal:").grid(row=8, column=0, sticky="nw", pady=5)
        self.goal_text = tk.Text(frame, width=30, height=3)
        self.goal_text.grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Sprint", command=self.save_sprint).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["sprint_name"].insert(0, values[1])
            set_field_value(self.entries["start_date"], values[2])
            set_field_value(self.entries["end_date"], values[3])
            self.status_combo.set(values[4])
            self.entries["total_tasks"].insert(0, values[5])
            self.entries["completed_tasks"].insert(0, values[6])
            self.entries["velocity"].insert(0, values[7])
            self.entries["team_lead"].insert(0, values[8])
            self.goal_text.insert("1.0", values[9] if len(values) > 9 else "")
        except IndexError:
            pass

    def save_sprint(self):
        sprint_name = self.entries["sprint_name"].get().strip()
        start_date = self.entries["start_date"].get().strip()
        end_date = self.entries["end_date"].get().strip()
        team_lead = self.entries["team_lead"].get().strip()

        if not sprint_name or not start_date or not end_date or not team_lead:
            messagebox.showwarning("Input Error", "Sprint name, dates, and team lead are required.", parent=self)
            return

        csv_file = getattr(config, "SPRINTS_CSV", os.path.join(config.CSV_DIR, "sprints.csv"))
        sprint_id = f"SPRINT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            sprint_id,
            sprint_name,
            start_date,
            end_date,
            self.status_combo.get(),
            self.entries["total_tasks"].get().strip(),
            self.entries["completed_tasks"].get().strip(),
            self.entries["velocity"].get().strip(),
            team_lead,
            self.goal_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["sprint_id", "sprint_name", "start_date", "end_date", "status", "total_tasks", "completed_tasks", "velocity", "team_lead", "goal"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Sprint '{sprint_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sprint: {e}", parent=self)


class HardwarePrototypeTab(ttk.Frame):
    """Hardware & Prototype Tracking - PCB layouts, prototypes, bring-up process."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_hardware()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Hardware Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Hardware:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_hw_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_hw_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="In Prototype:").grid(row=0, column=2, sticky="w", padx=5)
        self.prototype_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.prototype_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Bring-up Complete:").grid(row=0, column=4, sticky="w", padx=5)
        self.bringup_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.bringup_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Hardware", command=self.add_hardware).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_hardware).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_hardware).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_hardware).pack(side="left", padx=5)

        # Hardware table
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

        columns = ["hardware_id", "hardware_name", "hardware_type", "revision", "status", "pcb_status", "bring_up_status", "assigned_to", "expected_date", "actual_date"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_hardware(self):
        csv_file = getattr(config, "HARDWARE_CSV", os.path.join(config.CSV_DIR, "hardware.csv"))
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
        prototype = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 4 and self.tree.item(item, "values")[4] == "Prototype")
        bringup = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 6 and self.tree.item(item, "values")[6] == "Complete")
        self.total_hw_var.set(str(total))
        self.prototype_var.set(str(prototype))
        self.bringup_var.set(str(bringup))

    def add_hardware(self):
        HardwareDialog(self, callback=self.load_hardware)

    def edit_hardware(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Hardware", "Please select hardware to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        HardwareDialog(self, callback=self.load_hardware, edit_values=item_values)

    def delete_hardware(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Hardware", "Please select hardware to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this hardware?", parent=self):
            csv_file = getattr(config, "HARDWARE_CSV", os.path.join(config.CSV_DIR, "hardware.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_hardware()

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


class HardwareDialog(tk.Toplevel):
    """Dialog for hardware and prototype management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Hardware" if self.is_edit else "Add Hardware")
        self.geometry("550x550")
        self.minsize(480, 450)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Hardware & Prototype Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Hardware", command=self.save_hardware).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(10, weight=1)

        # Hardware type dropdown
        ttk.Label(frame, text="Hardware Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.hw_type_combo = ttk.Combobox(frame, values=["PCB", "Evaluation Board", "Prototype", "Production Unit", "Other"], width=30, state="readonly")
        self.hw_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status*:").grid(row=1, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Design", "Prototype", "Testing", "Production", "Retired"], width=30, state="readonly")
        self.status_combo.set("Design")
        self.status_combo.grid(row=1, column=1, sticky="w", pady=5)

        # PCB status dropdown
        ttk.Label(frame, text="PCB Status:").grid(row=2, column=0, sticky="w", pady=5)
        self.pcb_combo = ttk.Combobox(frame, values=["Not Started", "In Design", "Fabrication", "Assembly", "Complete"], width=30, state="readonly")
        self.pcb_combo.set("Not Started")
        self.pcb_combo.grid(row=2, column=1, sticky="w", pady=5)

        # Bring-up status dropdown
        ttk.Label(frame, text="Bring-up Status:").grid(row=3, column=0, sticky="w", pady=5)
        self.bringup_combo = ttk.Combobox(frame, values=["Not Started", "In Progress", "Complete", "Failed"], width=30, state="readonly")
        self.bringup_combo.set("Not Started")
        self.bringup_combo.grid(row=3, column=1, sticky="w", pady=5)

        fields = [
            ("Hardware Name*", "hardware_name"),
            ("Revision", "revision"),
            ("Assigned To", "assigned_to"),
            ("Expected Date", "expected_date"),
            ("Actual Date", "actual_date"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+4, column=0, sticky="w", pady=5)
            entry = create_date_entry(frame, width=32) if "date" in key.lower() else ttk.Entry(frame, width=32)
            entry.grid(row=idx+4, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=9, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=9, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Hardware", command=self.save_hardware).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["hardware_name"].insert(0, values[1])
            self.hw_type_combo.set(values[2])
            self.entries["revision"].insert(0, values[3])
            self.status_combo.set(values[4])
            self.pcb_combo.set(values[5])
            self.bringup_combo.set(values[6])
            self.entries["assigned_to"].insert(0, values[7])
            set_field_value(self.entries["expected_date"], values[8])
            set_field_value(self.entries["actual_date"], values[9])
            self.notes_text.insert("1.0", values[10] if len(values) > 10 else "")
        except IndexError:
            pass

    def save_hardware(self):
        hardware_name = self.entries["hardware_name"].get().strip()
        hw_type = self.hw_type_combo.get()
        status = self.status_combo.get()

        if not hardware_name or not hw_type or not status:
            messagebox.showwarning("Input Error", "Hardware name, type, and status are required.", parent=self)
            return

        csv_file = getattr(config, "HARDWARE_CSV", os.path.join(config.CSV_DIR, "hardware.csv"))
        hardware_id = f"HW-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            hardware_id,
            hardware_name,
            hw_type,
            self.entries["revision"].get().strip(),
            status,
            self.pcb_combo.get(),
            self.bringup_combo.get(),
            self.entries["assigned_to"].get().strip(),
            self.entries["expected_date"].get().strip(),
            self.entries["actual_date"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["hardware_id", "hardware_name", "hardware_type", "revision", "status", "pcb_status", "bring_up_status", "assigned_to", "expected_date", "actual_date", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Hardware '{hardware_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save hardware: {e}", parent=self)


class ComponentsTab(ttk.Frame):
    """Components & Supply Chain for R&D - Component selection and lifecycle."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_components()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Component Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Components:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_comp_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_comp_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Long Lead Time:").grid(row=0, column=2, sticky="w", padx=5)
        self.lead_time_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.lead_time_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="EOL Risk:").grid(row=0, column=4, sticky="w", padx=5)
        self.eol_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.eol_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Component", command=self.add_component).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_component).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_component).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_components).pack(side="left", padx=5)

        # Components table
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

        columns = ["component_id", "component_name", "part_number", "manufacturer", "category", "lifecycle_status", "lead_time_weeks", "availability", "alternatives", "last_ordered"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_components(self):
        csv_file = getattr(config, "RND_COMPONENTS_CSV", os.path.join(config.CSV_DIR, "rnd_components.csv"))
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
        lead_time = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 6 and self.tree.item(item, "values")[6] and int(self.tree.item(item, "values")[6]) > 8)
        eol = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 5 and "EOL" in self.tree.item(item, "values")[5])
        self.total_comp_var.set(str(total))
        self.lead_time_var.set(str(lead_time))
        self.eol_var.set(str(eol))

    def add_component(self):
        ComponentDialog(self, callback=self.load_components)

    def edit_component(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Component", "Please select a component to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        ComponentDialog(self, callback=self.load_components, edit_values=item_values)

    def delete_component(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Component", "Please select a component to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this component?", parent=self):
            csv_file = getattr(config, "RND_COMPONENTS_CSV", os.path.join(config.CSV_DIR, "rnd_components.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_components()

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


class ComponentDialog(tk.Toplevel):
    """Dialog for component management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Component" if self.is_edit else "Add Component")
        self.geometry("550x550")
        self.minsize(480, 450)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Component Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Component", command=self.save_component).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(10, weight=1)

        # Category dropdown
        ttk.Label(frame, text="Category*:").grid(row=0, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(frame, values=["MCU", "Sensor", "Power", "Connectivity", "Passive", "Other"], width=30, state="readonly")
        self.category_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Lifecycle status dropdown
        ttk.Label(frame, text="Lifecycle Status*:").grid(row=1, column=0, sticky="w", pady=5)
        self.lifecycle_combo = ttk.Combobox(frame, values=["Active", "NRND", "EOL", "Last Time Buy"], width=30, state="readonly")
        self.lifecycle_combo.set("Active")
        self.lifecycle_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Availability dropdown
        ttk.Label(frame, text="Availability*:").grid(row=2, column=0, sticky="w", pady=5)
        self.availability_combo = ttk.Combobox(frame, values=["In Stock", "Limited", "Not Available", "Pre-order"], width=30, state="readonly")
        self.availability_combo.set("In Stock")
        self.availability_combo.grid(row=2, column=1, sticky="w", pady=5)

        fields = [
            ("Component Name*", "component_name"),
            ("Part Number", "part_number"),
            ("Manufacturer", "manufacturer"),
            ("Lead Time (weeks)", "lead_time_weeks"),
            ("Alternatives", "alternatives"),
            ("Last Ordered", "last_ordered"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+3, column=0, sticky="w", pady=5)
            entry = create_date_entry(frame, width=32) if "date" in key.lower() or "ordered" in key.lower() else ttk.Entry(frame, width=32)
            entry.grid(row=idx+3, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=9, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=9, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Component", command=self.save_component).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["component_name"].insert(0, values[1])
            self.entries["part_number"].insert(0, values[2])
            self.entries["manufacturer"].insert(0, values[3])
            self.category_combo.set(values[4])
            self.lifecycle_combo.set(values[5])
            self.entries["lead_time_weeks"].insert(0, values[6])
            self.availability_combo.set(values[7])
            self.entries["alternatives"].insert(0, values[8])
            set_field_value(self.entries["last_ordered"], values[9])
            self.notes_text.insert("1.0", values[10] if len(values) > 10 else "")
        except IndexError:
            pass

    def save_component(self):
        component_name = self.entries["component_name"].get().strip()
        category = self.category_combo.get()
        lifecycle_status = self.lifecycle_combo.get()
        availability = self.availability_combo.get()

        if not component_name or not category or not lifecycle_status or not availability:
            messagebox.showwarning("Input Error", "Component name, category, lifecycle status, and availability are required.", parent=self)
            return

        csv_file = getattr(config, "RND_COMPONENTS_CSV", os.path.join(config.CSV_DIR, "rnd_components.csv"))
        component_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            component_id,
            component_name,
            self.entries["part_number"].get().strip(),
            self.entries["manufacturer"].get().strip(),
            category,
            lifecycle_status,
            self.entries["lead_time_weeks"].get().strip(),
            availability,
            self.entries["alternatives"].get().strip(),
            self.entries["last_ordered"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["component_id", "component_name", "part_number", "manufacturer", "category", "lifecycle_status", "lead_time_weeks", "availability", "alternatives", "last_ordered", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Component '{component_name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save component: {e}", parent=self)


class RiskManagementTab(ttk.Frame):
    """Risk Management & Mitigation - Hardware delays, scope creep, bottlenecks."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_risks()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Risk Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Risks:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_risks_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_risks_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="High Priority:").grid(row=0, column=2, sticky="w", padx=5)
        self.high_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.high_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Mitigated:").grid(row=0, column=4, sticky="w", padx=5)
        self.mitigated_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.mitigated_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Risk", command=self.add_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_risk).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_risks).pack(side="left", padx=5)

        # Risks table
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

        columns = ["risk_id", "risk_type", "description", "probability", "impact", "priority", "mitigation_plan", "status", "assigned_to", "target_date"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_risks(self):
        csv_file = getattr(config, "RND_RISKS_CSV", os.path.join(config.CSV_DIR, "rnd_risks.csv"))
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
        high = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 5 and self.tree.item(item, "values")[5] == "High")
        mitigated = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 7 and self.tree.item(item, "values")[7] == "Mitigated")
        self.total_risks_var.set(str(total))
        self.high_var.set(str(high))
        self.mitigated_var.set(str(mitigated))

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
            csv_file = getattr(config, "RND_RISKS_CSV", os.path.join(config.CSV_DIR, "rnd_risks.csv"))
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
        self.title("Edit Risk" if self.is_edit else "Add Risk")
        self.geometry("550x580")
        self.minsize(480, 480)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Risk Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Risk", command=self.save_risk).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(10, weight=1)

        # Risk type dropdown
        ttk.Label(frame, text="Risk Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.risk_type_combo = ttk.Combobox(frame, values=["Component Lead Time", "Hardware Bug", "Scope Creep", "Resource Shortage", "Technical Debt", "Other"], width=30, state="readonly")
        self.risk_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Probability dropdown
        ttk.Label(frame, text="Probability*:").grid(row=1, column=0, sticky="w", pady=5)
        self.probability_combo = ttk.Combobox(frame, values=["Low", "Medium", "High"], width=30, state="readonly")
        self.probability_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Impact dropdown
        ttk.Label(frame, text="Impact*:").grid(row=2, column=0, sticky="w", pady=5)
        self.impact_combo = ttk.Combobox(frame, values=["Low", "Medium", "High", "Critical"], width=30, state="readonly")
        self.impact_combo.grid(row=2, column=1, sticky="w", pady=5)

        # Priority dropdown
        ttk.Label(frame, text="Priority*:").grid(row=3, column=0, sticky="w", pady=5)
        self.priority_combo = ttk.Combobox(frame, values=["Low", "Medium", "High"], width=30, state="readonly")
        self.priority_combo.grid(row=3, column=1, sticky="w", pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status:").grid(row=4, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Open", "In Progress", "Mitigated", "Closed"], width=30, state="readonly")
        self.status_combo.set("Open")
        self.status_combo.grid(row=4, column=1, sticky="w", pady=5)

        fields = [
            ("Description*", "description"),
            ("Assigned To", "assigned_to"),
            ("Target Date", "target_date"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+5, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+5, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Mitigation plan
        ttk.Label(frame, text="Mitigation Plan:").grid(row=8, column=0, sticky="nw", pady=5)
        self.mitigation_text = tk.Text(frame, width=30, height=4)
        self.mitigation_text.grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Risk", command=self.save_risk).pack(pady=15)

    def populate_values(self, values):
        try:
            self.risk_type_combo.set(values[1])
            self.entries["description"].insert(0, values[2])
            self.probability_combo.set(values[3])
            self.impact_combo.set(values[4])
            self.priority_combo.set(values[5])
            self.mitigation_text.insert("1.0", values[6])
            self.status_combo.set(values[7])
            self.entries["assigned_to"].insert(0, values[8])
            self.entries["target_date"].insert(0, values[9])
        except IndexError:
            pass

    def save_risk(self):
        risk_type = self.risk_type_combo.get()
        description = self.entries["description"].get().strip()
        probability = self.probability_combo.get()
        impact = self.impact_combo.get()
        priority = self.priority_combo.get()

        if not risk_type or not description or not probability or not impact or not priority:
            messagebox.showwarning("Input Error", "Risk type, description, probability, impact, and priority are required.", parent=self)
            return

        csv_file = getattr(config, "RND_RISKS_CSV", os.path.join(config.CSV_DIR, "rnd_risks.csv"))
        risk_id = f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            risk_id,
            risk_type,
            description,
            probability,
            impact,
            priority,
            self.mitigation_text.get("1.0", tk.END).strip(),
            self.status_combo.get(),
            self.entries["assigned_to"].get().strip(),
            self.entries["target_date"].get().strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["risk_id", "risk_type", "description", "probability", "impact", "priority", "mitigation_plan", "status", "assigned_to", "target_date"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Risk saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save risk: {e}", parent=self)


class TeamResourceTab(ttk.Frame):
    """Team & Resource Allocation - Managing embedded developers and resources."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_team()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Team Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Team Members:").grid(row=0, column=0, sticky="w", padx=5)
        self.team_size_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.team_size_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Firmware Devs:").grid(row=0, column=2, sticky="w", padx=5)
        self.firmware_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.firmware_var, font=("Helvetica", 10, "bold"), foreground="blue").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Hardware Devs:").grid(row=0, column=4, sticky="w", padx=5)
        self.hardware_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.hardware_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Team Member", command=self.add_member).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_member).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_member).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_team).pack(side="left", padx=5)

        # Team table
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

        columns = ["member_id", "name", "role", "specialization", "current_project", "availability", "skills", "workload", "assigned_tasks"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_team(self):
        csv_file = getattr(config, "RND_TEAM_CSV", os.path.join(config.CSV_DIR, "rnd_team.csv"))
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
        firmware = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 3 and "Firmware" in self.tree.item(item, "values")[3])
        hardware = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 3 and "Hardware" in self.tree.item(item, "values")[3])
        self.team_size_var.set(str(total))
        self.firmware_var.set(str(firmware))
        self.hardware_var.set(str(hardware))

    def add_member(self):
        TeamMemberDialog(self, callback=self.load_team)

    def edit_member(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Member", "Please select a team member to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        TeamMemberDialog(self, callback=self.load_team, edit_values=item_values)

    def delete_member(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Member", "Please select a team member to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this team member?", parent=self):
            csv_file = getattr(config, "RND_TEAM_CSV", os.path.join(config.CSV_DIR, "rnd_team.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_team()

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


class TeamMemberDialog(tk.Toplevel):
    """Dialog for team member management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Team Member" if self.is_edit else "Add Team Member")
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
        ttk.Label(self, text="Team Member Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Team Member", command=self.save_member).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(9, weight=1)

        # Role dropdown
        ttk.Label(frame, text="Role*:").grid(row=0, column=0, sticky="w", pady=5)
        self.role_combo = ttk.Combobox(frame, values=["Engineer", "Senior Engineer", "Tech Lead", "Manager", "QA Engineer"], width=30, state="readonly")
        self.role_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Specialization dropdown
        ttk.Label(frame, text="Specialization*:").grid(row=1, column=0, sticky="w", pady=5)
        self.specialization_combo = ttk.Combobox(frame, values=["Firmware", "Hardware", "Firmware + Hardware", "Testing", "Documentation"], width=30, state="readonly")
        self.specialization_combo.grid(row=1, column=1, sticky="w", pady=5)

        # Availability dropdown
        ttk.Label(frame, text="Availability*:").grid(row=2, column=0, sticky="w", pady=5)
        self.availability_combo = ttk.Combobox(frame, values=["Available", "Partially Available", "Not Available"], width=30, state="readonly")
        self.availability_combo.set("Available")
        self.availability_combo.grid(row=2, column=1, sticky="w", pady=5)

        fields = [
            ("Name*", "name"),
            ("Current Project", "current_project"),
            ("Skills", "skills"),
            ("Workload %", "workload"),
            ("Assigned Tasks", "assigned_tasks"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+3, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+3, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=8, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Team Member", command=self.save_member).pack(pady=15)

    def populate_values(self, values):
        try:
            self.entries["name"].insert(0, values[1])
            self.role_combo.set(values[2])
            self.specialization_combo.set(values[3])
            self.entries["current_project"].insert(0, values[4])
            self.availability_combo.set(values[5])
            self.entries["skills"].insert(0, values[6])
            self.entries["workload"].insert(0, values[7])
            self.entries["assigned_tasks"].insert(0, values[8])
            self.notes_text.insert("1.0", values[9] if len(values) > 9 else "")
        except IndexError:
            pass

    def save_member(self):
        name = self.entries["name"].get().strip()
        role = self.role_combo.get()
        specialization = self.specialization_combo.get()
        availability = self.availability_combo.get()

        if not name or not role or not specialization or not availability:
            messagebox.showwarning("Input Error", "Name, role, specialization, and availability are required.", parent=self)
            return

        csv_file = getattr(config, "RND_TEAM_CSV", os.path.join(config.CSV_DIR, "rnd_team.csv"))
        member_id = f"TEAM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            member_id,
            name,
            role,
            specialization,
            self.entries["current_project"].get().strip(),
            availability,
            self.entries["skills"].get().strip(),
            self.entries["workload"].get().strip(),
            self.entries["assigned_tasks"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["member_id", "name", "role", "specialization", "current_project", "availability", "skills", "workload", "assigned_tasks", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Team member '{name}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save team member: {e}", parent=self)


class ComplianceCertificationTab(ttk.Frame):
    """Compliance & Certification Tracking - CE, FCC, ISO, OTA validation."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)
        self.setup_ui()
        self.load_compliance()

    def setup_ui(self):
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text=" Compliance Summary ", padding=10)
        summary_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(summary_frame, text="Total Certifications:").grid(row=0, column=0, sticky="w", padx=5)
        self.total_cert_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.total_cert_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Pending:").grid(row=0, column=2, sticky="w", padx=5)
        self.pending_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.pending_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(summary_frame, text="Valid:").grid(row=0, column=4, sticky="w", padx=5)
        self.valid_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.valid_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=5, sticky="w", padx=5)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(control_frame, text="+ Add Certification", command=self.add_certification).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✏️ Edit Selected", command=self.edit_certification).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_certification).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.load_compliance).pack(side="left", padx=5)

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

        columns = ["cert_id", "certification_type", "standard", "product_id", "status", "issue_date", "expiry_date", "certifying_body", "document_path", "notes"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, anchor="w")

    def load_compliance(self):
        csv_file = getattr(config, "COMPLIANCE_CERTS_CSV", os.path.join(config.CSV_DIR, "compliance_certs.csv"))
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
        pending = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 4 and self.tree.item(item, "values")[4] == "Pending")
        valid = sum(1 for item in self.tree.get_children() if len(self.tree.item(item, "values")) > 4 and self.tree.item(item, "values")[4] == "Valid")
        self.total_cert_var.set(str(total))
        self.pending_var.set(str(pending))
        self.valid_var.set(str(valid))

    def add_certification(self):
        CertificationDialog(self, callback=self.load_compliance)

    def edit_certification(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Certification", "Please select a certification to edit.", parent=self)
            return
        item_values = self.tree.item(selected[0], "values")
        CertificationDialog(self, callback=self.load_compliance, edit_values=item_values)

    def delete_certification(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Certification", "Please select a certification to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this certification?", parent=self):
            csv_file = getattr(config, "COMPLIANCE_CERTS_CSV", os.path.join(config.CSV_DIR, "compliance_certs.csv"))
            self.delete_row_from_csv(csv_file, self.tree.index(selected[0]))
            self.load_compliance()

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


class CertificationDialog(tk.Toplevel):
    """Dialog for compliance and certification management."""

    def __init__(self, parent, callback=None, edit_values=None):
        super().__init__(parent)
        self.callback = callback
        self.is_edit = edit_values is not None
        self.title("Edit Certification" if self.is_edit else "Add Certification")
        self.geometry("550x550")
        self.minsize(480, 450)
        self.resizable(True, True)
        self.state("zoomed")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Compliance & Certification Management", font=("Helvetica", 12, "bold")).pack(pady=10)

        action_frame = ttk.Frame(self, padding=(15, 0, 15, 15))
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Save Certification", command=self.save_certification).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

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
        frame.rowconfigure(9, weight=1)

        # Certification type dropdown
        ttk.Label(frame, text="Certification Type*:").grid(row=0, column=0, sticky="w", pady=5)
        self.cert_type_combo = ttk.Combobox(frame, values=["CE", "FCC", "ISO", "RoHS", "REACH", "Other"], width=30, state="readonly")
        self.cert_type_combo.grid(row=0, column=1, sticky="w", pady=5)

        # Status dropdown
        ttk.Label(frame, text="Status*:").grid(row=1, column=0, sticky="w", pady=5)
        self.status_combo = ttk.Combobox(frame, values=["Pending", "In Progress", "Valid", "Expired", "Failed"], width=30, state="readonly")
        self.status_combo.set("Pending")
        self.status_combo.grid(row=1, column=1, sticky="w", pady=5)

        fields = [
            ("Standard", "standard"),
            ("Product ID", "product_id"),
            ("Issue Date", "issue_date"),
            ("Expiry Date", "expiry_date"),
            ("Certifying Body", "certifying_body"),
            ("Document Path", "document_path"),
        ]

        self.entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}:").grid(row=idx+2, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=32)
            entry.grid(row=idx+2, column=1, sticky="w", pady=5)
            self.entries[key] = entry

        # File browse button
        ttk.Button(frame, text="Browse Document", command=self.browse_document).grid(row=7, column=2, sticky="w", padx=5, pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=8, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, width=30, height=3)
        self.notes_text.grid(row=8, column=1, sticky="w", pady=5)

        ttk.Button(self, text="Save Certification", command=self.save_certification).pack(pady=15)

    def browse_document(self):
        file_path = filedialog.askopenfilename(
            title="Select Certification Document",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            self.entries["document_path"].delete(0, tk.END)
            self.entries["document_path"].insert(0, file_path)

    def populate_values(self, values):
        try:
            self.cert_type_combo.set(values[1])
            self.entries["standard"].insert(0, values[2])
            self.entries["product_id"].insert(0, values[3])
            self.entries["document_path"].insert(0, values[8])
            self.notes_text.insert("1.0", values[9] if len(values) > 9 else "")
        except IndexError:
            pass

    def save_certification(self):
        cert_type = self.cert_type_combo.get()
        status = self.status_combo.get()

        if not cert_type or not status:
            messagebox.showwarning("Input Error", "Certification type and status are required.", parent=self)
            return

        csv_file = getattr(config, "COMPLIANCE_CERTS_CSV", os.path.join(config.CSV_DIR, "compliance_certs.csv"))
        cert_id = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        row = [
            cert_id,
            cert_type,
            self.entries["standard"].get().strip(),
            self.entries["product_id"].get().strip(),
            status,
            self.entries["issue_date"].get().strip(),
            self.entries["expiry_date"].get().strip(),
            self.entries["certifying_body"].get().strip(),
            self.entries["document_path"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
        ]

        rows = []
        if os.path.exists(csv_file):
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            rows.append(["cert_id", "certification_type", "standard", "product_id", "status", "issue_date", "expiry_date", "certifying_body", "document_path", "notes"])

        rows.append(row)

        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Certification '{cert_type}' saved successfully!", parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save certification: {e}", parent=self)