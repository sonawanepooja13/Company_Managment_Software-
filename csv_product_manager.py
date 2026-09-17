"""CSV price-list uploader and editor for product records."""

import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config


class CSVProductManagerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("CSV Price List Manager")
        self.geometry("1100x680")
        self.minsize(900, 550)
        self.file_path = None
        self.headers = []
        self.rows = []
        self.field_vars = {}
        self.selected_index = None
        self.file_name_var = tk.StringVar(value="No CSV file selected")
        self._build()
        self.build_editor_for_empty_state()
        default_file = os.path.join(config.SCRIPT_DIR, "price_list_clean.csv")
        if os.path.exists(default_file):
            self.open_file(default_file)

    def _build(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(12, 8))
        ttk.Button(top, text="Upload CSV File", command=self.choose_file).pack(side="left")
        ttk.Label(top, textvariable=self.file_name_var).pack(side="left", padx=12)
        ttk.Button(top, text="Reload", command=self.reload_file).pack(side="right")

        table_box = ttk.LabelFrame(root, text=" Products in CSV Price List ", padding=8)
        table_box.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_box, show="headings", selectmode="browse")
        scroll_y = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_box, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.bind("<<TreeviewSelect>>", self.load_selected_product)

        self.editor = ttk.LabelFrame(root, text=" Product Details ", padding=10)
        self.editor.pack(fill="x", pady=(10, 0))
        self.editor_inner = ttk.Frame(self.editor)
        self.editor_inner.pack(fill="x")

        actions = ttk.Frame(root, padding=(0, 8, 0, 0))
        actions.pack(fill="x")
        ttk.Button(actions, text="+ New Product", command=self.new_product).pack(side="left")
        ttk.Button(actions, text="Save Product", command=self.save_product).pack(side="left", padx=8)

    def build_editor_for_empty_state(self):
        for widget in self.editor_inner.winfo_children():
            widget.destroy()
        self.field_vars = {}
        ttk.Label(self.editor_inner, text="Upload a CSV file to edit products or create a new product after opening a file.", wraplength=700).pack(anchor="w")

    def choose_file(self):
        path = filedialog.askopenfilename(parent=self, title="Choose Price List CSV File", filetypes=(("CSV files", "*.csv"),))
        if path:
            self.open_file(path)

    def open_file(self, path):
        try:
            with open(path, newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                self.headers = reader.fieldnames or []
                self.rows = list(reader)
            if not self.headers:
                raise ValueError("The CSV file does not have a header row.")
            self.file_path = path
            self.file_name_var.set(os.path.basename(path))
            self.build_editor()
            self.refresh_table()
            self.new_product()
        except Exception as error:
            messagebox.showerror("Cannot Open CSV", f"Could not open this CSV file:\n{error}", parent=self)

    def build_editor(self):
        for widget in self.editor_inner.winfo_children():
            widget.destroy()
        self.field_vars = {header: tk.StringVar() for header in self.headers}
        for index, header in enumerate(self.headers):
            row, group = divmod(index, 2)
            column = group * 2
            ttk.Label(self.editor_inner, text=f"{header}:").grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
            ttk.Entry(self.editor_inner, textvariable=self.field_vars[header], width=34).grid(row=row, column=column + 1, sticky="ew", padx=(0, 18), pady=4)
        self.editor_inner.columnconfigure(1, weight=1)
        self.editor_inner.columnconfigure(3, weight=1)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = self.headers
        for header in self.headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=145, minwidth=90, anchor="w")
        for index, row in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(index), values=[row.get(header, "") for header in self.headers])

    def load_selected_product(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_index = int(selected[0])
        row = self.rows[self.selected_index]
        for header, variable in self.field_vars.items():
            variable.set(row.get(header, ""))

    def new_product(self):
        self.selected_index = None
        for variable in self.field_vars.values():
            variable.set("")
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def save_product(self):
        if not self.file_path:
            messagebox.showwarning("Upload Needed", "Upload a CSV price list first.", parent=self)
            return
        if not self.field_vars:
            messagebox.showwarning("Upload Needed", "Open a valid CSV file before creating or editing products.", parent=self)
            return
        row = {header: variable.get().strip() for header, variable in self.field_vars.items()}
        if not any(row.values()):
            messagebox.showwarning("Product Details", "Enter at least one product detail before saving.", parent=self)
            return
        if self.selected_index is None:
            self.rows.append(row)
        else:
            self.rows[self.selected_index] = row
        try:
            with open(self.file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(self.rows)
            self.refresh_table()
            self.new_product()
            messagebox.showinfo("Saved", "Product details were saved to the CSV file.", parent=self)
        except PermissionError:
            messagebox.showerror("File Is Open", "Close the CSV file in another program, then save again.", parent=self)
        except Exception as error:
            messagebox.showerror("Save Failed", f"Could not save the CSV file:\n{error}", parent=self)

    def reload_file(self):
        if self.file_path:
            self.open_file(self.file_path)
