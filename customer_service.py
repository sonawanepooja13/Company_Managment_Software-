import csv
import datetime
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SERVICE_HEADERS = [
    "service_date", "customer", "service_type", "customer_problem",
    "actual_problem", "material_required", "material_installed",
]


class CustomerServiceView(ttk.Frame):
    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data or {}
        self.csv_path = config.CUSTOMER_SERVICES_CSV
        self.records = []
        self.selected_index = None
        self.customer_values = self.load_customer_names()
        self.build_ui()
        self.load_records()

    def load_customer_names(self):
        names = []
        for path in (config.CUSTOMERS_DETAILED_CSV, config.CUSTOMERS_CSV):
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8-sig") as file:
                for row in csv.DictReader(file):
                    name = (row.get("company_name") or row.get("customer_name") or "").strip()
                    if name and name not in names:
                        names.append(name)
        return sorted(names, key=str.casefold)

    def build_ui(self):
        ttk.Label(self, text="Customer Service", font=("Helvetica", 14, "bold")).pack(anchor="w")
        form = ttk.LabelFrame(self, text="Service Record", padding=8)
        form.pack(fill="x", pady=(8, 10))

        ttk.Label(form, text="Customer:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.customer_var = tk.StringVar()
        self.customer_combo = ttk.Combobox(form, textvariable=self.customer_var, values=self.customer_values, width=38)
        self.customer_combo.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(form, text="Service Type:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.service_type = tk.StringVar(value="Paid Service")
        ttk.Combobox(form, textvariable=self.service_type, values=("Paid Service", "Free Service"), state="readonly", width=18).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(form, text="Customer Problem:").grid(row=1, column=0, sticky="nw", padx=4, pady=4)
        self.customer_problem = tk.Text(form, height=3, width=42)
        self.customer_problem.grid(row=1, column=1, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(form, text="Actual Problem:").grid(row=2, column=0, sticky="nw", padx=4, pady=4)
        self.actual_problem = tk.Text(form, height=3, width=42)
        self.actual_problem.grid(row=2, column=1, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(form, text="Material Required:").grid(row=3, column=0, sticky="nw", padx=4, pady=4)
        self.material_required = tk.Text(form, height=2, width=42)
        self.material_required.grid(row=3, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
        self.material_installed = tk.BooleanVar()
        ttk.Checkbutton(form, text="Material Installed", variable=self.material_installed).grid(row=3, column=3, sticky="w", padx=4, pady=4)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Save Service", command=self.save_record).pack(side="left", padx=3)
        ttk.Button(actions, text="Update Service", command=self.update_record).pack(side="left", padx=3)
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left", padx=3)
        ttk.Button(actions, text="Customer PDF", command=self.export_pdf).pack(side="left", padx=3)
        ttk.Button(actions, text="Excel Sheet", command=self.export_excel).pack(side="left", padx=3)

        columns = ("Date", "Customer", "Type", "Customer Problem", "Actual Problem", "Material", "Installed")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=120, anchor="w")
        self.tree.column("Customer Problem", width=220)
        self.tree.column("Actual Problem", width=220)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.load_selected_record)

    def load_records(self):
        if os.path.exists(self.csv_path):
            with open(self.csv_path, newline="", encoding="utf-8-sig") as file:
                self.records = list(csv.DictReader(file))
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for index, record in enumerate(self.records):
            self.tree.insert("", "end", iid=str(index), values=(
                record.get("service_date", ""), record.get("customer", ""),
                record.get("service_type", ""), record.get("customer_problem", ""),
                record.get("actual_problem", ""), record.get("material_required", ""),
                record.get("material_installed", "No"),
            ))

    def save_record(self):
        customer = self.customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Customer Required", "Select or enter a customer.", parent=self)
            return
        record = {
            "service_date": datetime.date.today().isoformat(),
            "customer": customer,
            "service_type": self.service_type.get(),
            "customer_problem": self.customer_problem.get("1.0", tk.END).strip(),
            "actual_problem": self.actual_problem.get("1.0", tk.END).strip(),
            "material_required": self.material_required.get("1.0", tk.END).strip(),
            "material_installed": "Yes" if self.material_installed.get() else "No",
        }
        self.records.append(record)
        self.write_records()
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("Saved", "Customer service record saved.", parent=self)

    def update_record(self):
        if self.selected_index is None:
            messagebox.showwarning("Select Report", "Select a service report to edit first.", parent=self)
            return
        customer = self.customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Customer Required", "Select or enter a customer.", parent=self)
            return
        original = self.records[self.selected_index]
        self.records[self.selected_index] = {
            "service_date": original.get("service_date") or datetime.date.today().isoformat(),
            "customer": customer,
            "service_type": self.service_type.get(),
            "customer_problem": self.customer_problem.get("1.0", tk.END).strip(),
            "actual_problem": self.actual_problem.get("1.0", tk.END).strip(),
            "material_required": self.material_required.get("1.0", tk.END).strip(),
            "material_installed": "Yes" if self.material_installed.get() else "No",
        }
        self.write_records()
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("Updated", "Customer service report updated.", parent=self)

    def write_records(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=SERVICE_HEADERS)
            writer.writeheader()
            writer.writerows(self.records)

    def clear_form(self):
        self.selected_index = None
        self.customer_var.set("")
        self.service_type.set("Paid Service")
        for widget in (self.customer_problem, self.actual_problem, self.material_required):
            widget.delete("1.0", tk.END)
        self.material_installed.set(False)

    def load_selected_record(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_index = int(selection[0])
        record = self.records[self.selected_index]
        self.clear_form()
        self.customer_var.set(record.get("customer", ""))
        self.service_type.set(record.get("service_type", "Paid Service"))
        self.customer_problem.insert("1.0", record.get("customer_problem", ""))
        self.actual_problem.insert("1.0", record.get("actual_problem", ""))
        self.material_required.insert("1.0", record.get("material_required", ""))
        self.material_installed.set(record.get("material_installed") == "Yes")

    def selected_records(self):
        selection = self.tree.selection()
        return [self.records[int(selection[0])]] if selection else self.records

    def export_pdf(self):
        records = self.selected_records()
        if not records:
            messagebox.showwarning("No Records", "Save a service record before exporting.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Save Customer Service PDF", defaultextension=".pdf", filetypes=(("PDF file", "*.pdf"),))
        if not path:
            return
        styles = getSampleStyleSheet()
        story = [Paragraph("Customer Service Report", styles["Title"]), Spacer(1, 8)]
        for record in records:
            data = [[key.replace("_", " ").title(), value or "-"] for key, value in record.items()]
            table = Table(data, colWidths=(48 * mm, 125 * mm))
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, "#888888"),
                ("BACKGROUND", (0, 0), (0, -1), "#E8EEF2"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.extend((table, Spacer(1, 12)))
        SimpleDocTemplate(path, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm).build(story)
        messagebox.showinfo("Exported", f"PDF saved to:\n{path}", parent=self)

    def export_excel(self):
        records = self.selected_records()
        if not records:
            messagebox.showwarning("No Records", "Save a service record before exporting.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Save Customer Service Excel", defaultextension=".xlsx", filetypes=(("Excel workbook", "*.xlsx"),))
        if not path:
            return
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Customer Services"
        sheet.append(SERVICE_HEADERS)
        for record in records:
            sheet.append([record.get(header, "") for header in SERVICE_HEADERS])
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
        workbook.save(path)
        messagebox.showinfo("Exported", f"Excel sheet saved to:\n{path}", parent=self)
