"""Outward-document entry window for sales and dispatch records."""

import csv
import os
import re
import tkinter as tk
from xml.sax.saxutils import escape
from datetime import date, datetime
from tkinter import messagebox, ttk

import config
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from tkcalendar import DateEntry


OUTWARD_CSV = os.path.join(config.CSV_DIR, "outward_entries.csv")
OUTWARD_HEADERS = ["document_type", "document_date", "document_no", "customer", "department", "item_description", "quantity", "rate", "amount", "notes"]
DOCUMENT_TYPES = ("Quotation", "Proforma Invoice", "Invoice", "Delivery Challan", "Returnable / Retainable Challan")
DEPARTMENTS = ("Production", "R&D", "Panel Department", "Office", "Sales", "Marketing", "Other")
CUSTOMERS_CSV = os.path.join(config.CSV_DIR, "customers_detailed.csv")
OUTWARD_OUTPUT_DIR = os.path.join(config.SCRIPT_DIR, "outward_documents")


def ensure_outward_file():
    if not os.path.exists(OUTWARD_CSV):
        with open(OUTWARD_CSV, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=OUTWARD_HEADERS).writeheader()


def load_catalog():
    path = os.path.join(config.SCRIPT_DIR, "price_list_clean.csv")
    catalog = {}
    if not os.path.exists(path):
        return catalog
    with open(path, newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            item = (row.get("Item Name") or "").strip()
            if item:
                label = f"{item} | {row.get('CAPACITY', '').strip()} {row.get('Unit', '').strip()} | {row.get('Supplier', '').strip()}"
                catalog[label] = row
    return catalog


def load_customers():
    if not os.path.exists(CUSTOMERS_CSV):
        return []
    with open(CUSTOMERS_CSV, newline="", encoding="utf-8-sig") as file:
        return sorted({(row.get("company_name") or "").strip() for row in csv.DictReader(file) if (row.get("company_name") or "").strip()})


def safe_name(value):
    return re.sub(r'[^A-Za-z0-9._-]+', "_", value).strip("_") or "document"


def next_document_number(document_type, document_date):
    """Return the next editable, date-based number for this document type."""
    ensure_outward_file()
    type_code = "".join(word[0] for word in re.findall(r"[A-Za-z]+", document_type)).upper() or "DOC"
    date_code = re.sub(r"[^0-9]", "", document_date) or date.today().strftime("%Y%m%d")
    prefix = f"{type_code}-{date_code}-"
    highest = 0
    with open(OUTWARD_CSV, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            number = (row.get("document_no") or "").strip()
            if number.startswith(prefix):
                try:
                    highest = max(highest, int(number[len(prefix):]))
                except ValueError:
                    pass
    return f"{prefix}{highest + 1:03d}"


class OutwardWindow(ttk.Frame):
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.on_complete = on_complete or (lambda: None)
        self.catalog = load_catalog()
        self.catalog_labels = list(self.catalog)
        self.customers = load_customers()
        self.customer_matches = []
        self.items = []
        self.doc_vars = {"document_type": tk.StringVar(value="Quotation"), "document_date": tk.StringVar(value=date.today().isoformat()), "document_no": tk.StringVar(), "customer": tk.StringVar(), "department": tk.StringVar()}
        self._setting_document_number = False
        self._document_number_is_manual = False
        self.item_vars = {"catalog": tk.StringVar(), "description": tk.StringVar(), "quantity": tk.StringVar(value="1"), "rate": tk.StringVar(value="0")}
        self.total_var = tk.StringVar(value="0.00")
        self._build()
        self.update_document_number()

    def _build(self):
        form = ttk.Frame(self, padding=14)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)
        form.rowconfigure(3, weight=1)
        header = ttk.LabelFrame(form, text=" Outward Document Details ", padding=10)
        header.grid(row=0, column=0, sticky="ew")
        for column in (1, 3):
            header.columnconfigure(column, weight=1)
        fields = (("Document Type", "document_type"), ("Document Date", "document_date"), ("Document No.", "document_no"), ("Customer Name", "customer"), ("Department", "department"))
        for index, (label, key) in enumerate(fields):
            row, group = divmod(index, 2)
            column = group * 2
            ttk.Label(header, text=f"{label}:").grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
            if key == "document_type":
                widget = ttk.Combobox(header, textvariable=self.doc_vars[key], values=DOCUMENT_TYPES, state="readonly")
            elif key == "document_date":
                widget = DateEntry(header, textvariable=self.doc_vars[key], date_pattern="yyyy-mm-dd")
            elif key == "customer":
                widget = ttk.Combobox(header, textvariable=self.doc_vars[key], values=self.customers[:5], height=5)
                self.customer_combo = widget
                widget.bind("<KeyRelease>", self.filter_customers)
            elif key == "department":
                widget = ttk.Combobox(header, textvariable=self.doc_vars[key], values=DEPARTMENTS, state="readonly")
            else:
                widget = ttk.Entry(header, textvariable=self.doc_vars[key])
            widget.grid(row=row, column=column + 1, sticky="ew", padx=(0, 16), pady=4)
        self.customer_match_list = tk.Listbox(header, height=5, exportselection=False)
        self.customer_match_list.grid(row=3, column=3, sticky="ew", padx=(0, 16), pady=(0, 4))
        self.customer_match_list.grid_remove()
        self.customer_match_list.bind("<<ListboxSelect>>", self.select_customer_match)
        self.doc_vars["document_type"].trace_add("write", self.update_document_number)
        self.doc_vars["document_date"].trace_add("write", self.update_document_number)
        self.doc_vars["document_no"].trace_add("write", self.mark_document_number_manual)

        add_box = ttk.LabelFrame(form, text=" Add Product / Material ", padding=10)
        add_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        add_box.columnconfigure(1, weight=1)
        ttk.Label(add_box, text="Existing Product:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        combo = ttk.Combobox(add_box, textvariable=self.item_vars["catalog"], values=self.catalog_labels, width=70)
        combo.grid(row=0, column=1, columnspan=3, sticky="ew")
        combo.bind("<<ComboboxSelected>>", self.use_catalog_product)
        ttk.Label(add_box, text="Description:").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(8, 0))
        ttk.Entry(add_box, textvariable=self.item_vars["description"]).grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Label(add_box, text="Qty:").grid(row=1, column=2, padx=(12, 5), pady=(8, 0))
        ttk.Entry(add_box, textvariable=self.item_vars["quantity"], width=8).grid(row=1, column=3, pady=(8, 0))
        ttk.Label(add_box, text="Rate:").grid(row=1, column=4, padx=(12, 5), pady=(8, 0))
        ttk.Entry(add_box, textvariable=self.item_vars["rate"], width=12).grid(row=1, column=5, pady=(8, 0))
        ttk.Button(add_box, text="Add Item", command=self.add_item).grid(row=1, column=6, padx=(12, 0), pady=(8, 0))

        table_box = ttk.LabelFrame(form, text=" Items in This Document ", padding=8)
        table_box.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        form.rowconfigure(2, weight=1)
        self.tree = ttk.Treeview(table_box, columns=("description", "quantity", "rate", "amount"), show="headings", height=9)
        for col, heading, width in (("description", "Product / Material", 470), ("quantity", "Qty", 90), ("rate", "Rate", 115), ("amount", "Amount", 125)):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w" if col == "description" else "e")
        self.tree.pack(fill="both", expand=True)
        footer = ttk.Frame(form)
        footer.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(footer, text="Remove Selected Item", command=self.remove_item).pack(side="left")
        ttk.Label(footer, textvariable=self.total_var, font=("Helvetica", 11, "bold")).pack(side="right")
        ttk.Label(footer, text="Document Total:", font=("Helvetica", 10, "bold")).pack(side="right", padx=(0, 6))
        ttk.Label(form, text="Notes:").grid(row=5, column=0, sticky="w", pady=(10, 2))
        self.notes = tk.Text(form, height=3)
        self.notes.grid(row=6, column=0, sticky="ew")
        actions = ttk.Frame(form)
        actions.grid(row=7, column=0, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Back", command=self.on_complete).pack(side="right")
        ttk.Button(actions, text="Save Outward Document", command=self.save).pack(side="right", padx=(0, 8))

    def update_document_number(self, *_args):
        if self._document_number_is_manual:
            return
        self._setting_document_number = True
        self.doc_vars["document_no"].set(next_document_number(
            self.doc_vars["document_type"].get(), self.doc_vars["document_date"].get()
        ))
        self._setting_document_number = False

    def mark_document_number_manual(self, *_args):
        if not self._setting_document_number:
            self._document_number_is_manual = True

    def use_catalog_product(self, _event=None):
        row = self.catalog.get(self.item_vars["catalog"].get())
        if not row:
            return
        self.item_vars["description"].set(f"{row.get('Item Name', '').strip()} {row.get('CAPACITY', '').strip()} {row.get('Unit', '').strip()}".strip())
        self.item_vars["rate"].set((row.get("List Price") or row.get("DP") or "0").replace(",", ""))

    def filter_customers(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        search = self.doc_vars["customer"].get().strip().casefold()
        self.customer_matches = [name for name in self.customers if search in name.casefold()][:5]
        self.customer_combo["values"] = self.customer_matches
        if self.customer_matches and search:
            self.customer_match_list.delete(0, tk.END)
            for name in self.customer_matches:
                self.customer_match_list.insert(tk.END, name)
            self.customer_match_list.grid()
        else:
            self.customer_match_list.grid_remove()

    def select_customer_match(self, _event=None):
        selected = self.customer_match_list.curselection()
        if selected:
            self.doc_vars["customer"].set(self.customer_match_list.get(selected[0]))
            self.customer_match_list.grid_remove()

    def add_item(self):
        description = self.item_vars["description"].get().strip()
        try:
            quantity, rate = float(self.item_vars["quantity"].get()), float(self.item_vars["rate"].get())
            if quantity <= 0 or rate < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Item Details", "Enter a product, valid quantity, and valid rate.", parent=self)
            return
        if not description:
            messagebox.showwarning("Item Details", "Enter or select a product first.", parent=self)
            return
        self.items.append((description, quantity, rate, quantity * rate))
        self.item_vars["catalog"].set("")
        self.item_vars["description"].set("")
        self.item_vars["quantity"].set("1")
        self.item_vars["rate"].set("0")
        self.refresh_items()

    def refresh_items(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = 0.0
        for index, item in enumerate(self.items):
            total += item[3]
            self.tree.insert("", "end", iid=str(index), values=(item[0], f"{item[1]:g}", f"{item[2]:.2f}", f"{item[3]:.2f}"))
        self.total_var.set(f"{total:,.2f}")

    def remove_item(self):
        selected = self.tree.selection()
        if selected:
            del self.items[int(selected[0])]
            self.refresh_items()

    def save(self):
        if not self.doc_vars["document_no"].get().strip() or not self.doc_vars["customer"].get().strip():
            messagebox.showwarning("Document Details", "Document number and customer name are required.", parent=self)
            return
        if not self.items:
            messagebox.showwarning("No Items", "Add at least one product or material.", parent=self)
            return
        ensure_outward_file()
        notes = self.notes.get("1.0", "end-1c").strip()
        with open(OUTWARD_CSV, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=OUTWARD_HEADERS)
            for item in self.items:
                writer.writerow({"document_type": self.doc_vars["document_type"].get(), "document_date": self.doc_vars["document_date"].get(), "document_no": self.doc_vars["document_no"].get().strip(), "customer": self.doc_vars["customer"].get().strip(), "department": self.doc_vars["department"].get().strip(), "item_description": item[0], "quantity": f"{item[1]:g}", "rate": f"{item[2]:.2f}", "amount": f"{item[3]:.2f}", "notes": notes})
        try:
            output_dir = self.generate_document_files(notes)
        except Exception as error:
            messagebox.showerror("Document Saved", f"The outward entry was saved, but files could not be generated:\n{error}", parent=self)
            return
        messagebox.showinfo("Saved", f"Outward document saved successfully.\n\nCSV, Excel, and printable PDF created in:\n{output_dir}", parent=self)
        self.on_complete()

    def generate_document_files(self, notes):
        document_no = self.doc_vars["document_no"].get().strip()
        base_name = safe_name(f"{self.doc_vars['document_type'].get()}_{document_no}_{datetime.now():%Y%m%d_%H%M%S}")
        output_dir = os.path.join(OUTWARD_OUTPUT_DIR, base_name)
        os.makedirs(output_dir, exist_ok=True)
        rows = [{"document_type": self.doc_vars["document_type"].get(), "document_date": self.doc_vars["document_date"].get(), "document_no": document_no, "customer": self.doc_vars["customer"].get().strip(), "department": self.doc_vars["department"].get().strip(), "item_description": item[0], "quantity": f"{item[1]:g}", "rate": f"{item[2]:.2f}", "amount": f"{item[3]:.2f}", "notes": notes} for item in self.items]
        with open(os.path.join(output_dir, f"{base_name}.csv"), "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=OUTWARD_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Outward Document"
        sheet.append(OUTWARD_HEADERS)
        for row in rows:
            sheet.append([row[key] for key in OUTWARD_HEADERS])
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 45)
        workbook.save(os.path.join(output_dir, f"{base_name}.xlsx"))
        styles = getSampleStyleSheet()
        pdf = SimpleDocTemplate(os.path.join(output_dir, f"{base_name}.pdf"), pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=14 * mm)
        story = [Paragraph(escape(self.doc_vars["document_type"].get()), styles["Title"]), Spacer(1, 5 * mm), Paragraph(f"<b>Document No.:</b> {escape(document_no)}<br/><b>Date:</b> {escape(self.doc_vars['document_date'].get())}<br/><b>Customer:</b> {escape(self.doc_vars['customer'].get())}<br/><b>Department:</b> {escape(self.doc_vars['department'].get())}", styles["Normal"]), Spacer(1, 5 * mm)]
        data = [["No.", "Product / Material", "Qty", "Rate", "Amount"]]
        for index, item in enumerate(self.items, 1):
            data.append([str(index), item[0], f"{item[1]:g}", f"{item[2]:.2f}", f"{item[3]:.2f}"])
        data.append(["", "", "", "Total", self.total_var.get()])
        table = Table(data, colWidths=(12 * mm, 88 * mm, 18 * mm, 28 * mm, 28 * mm))
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("ALIGN", (2, 1), (-1, -1), "RIGHT"), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold")]))
        story.extend([table, Spacer(1, 5 * mm), Paragraph(f"<b>Notes:</b> {escape(notes or '-')}", styles["Normal"])])
        pdf.build(story)
        return output_dir
