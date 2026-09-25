import csv
import datetime
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import auth_manager
from production_directory import ExistingProductionView


class ProductionView(ttk.Frame):
    """File 2: Main controller handles Mode Selection and New Production Start creation."""
    def __init__(self, parent):
        super().__init__(parent)

        self.prod_dir = os.path.join(os.getcwd(), "Production")
        self.new_prod_dir = os.path.join(self.prod_dir, "New Production Start")
        self.csv_path = os.path.join(self.prod_dir, "products_list.csv")

        self.products = []
        self.attached_file_path = None
        self.selected_personnel = {}

        self.ensure_production_storage()
        self.load_products_from_csv()
        self.show_mode_selection()

    def ensure_production_storage(self):
        os.makedirs(self.prod_dir, exist_ok=True)
        os.makedirs(self.new_prod_dir, exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Product_Name", "Created_Date"])

    def load_products_from_csv(self):
        self.products = []
        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if row and row[0].strip():
                            p_name = row[0].strip()
                            if p_name not in self.products:
                                self.products.append(p_name)
            except Exception as e:
                print(f"Error reading product CSV: {e}")

    def save_product_to_csv(self, product_name):
        if product_name in self.products: return
        self.products.append(product_name)
        try:
            with open(self.csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([product_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except Exception as e:
            messagebox.showerror("Storage Error", f"{e}", parent=self)

    def clear_view(self):
        for child in self.winfo_children():
            child.destroy()

    def show_mode_selection(self):
        self.clear_view()
        container = ttk.Frame(self, padding=40)
        container.pack(expand=True)

        ttk.Label(container, text="Production Management", font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
        btn_frame = ttk.Frame(container)
        btn_frame.pack()

        ttk.Button(btn_frame, text="➕ New Production Start", width=32, command=self.setup_new_production_ui).pack(pady=10)
        ttk.Button(btn_frame, text="📁 Existing Production Directory", width=32, command=self.open_existing_directory_view).pack(pady=10)

    def open_existing_directory_view(self):
        self.clear_view()
        ExistingProductionView(self, back_callback=self.show_mode_selection).pack(fill="both", expand=True)

    def setup_new_production_ui(self):
        self.clear_view()
        self.attached_file_path = None

        now = datetime.datetime.now()
        self.start_datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.batch_number = f"BATCH-{now.strftime('%Y%m%d_%H%M%S')}"

        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(fill="x")
        ttk.Button(top_bar, text="⬅ Back to Option", command=self.show_mode_selection).pack(side="left")
        ttk.Label(top_bar, text="New Production Process", font=("Helvetica", 13, "bold")).pack(side="left", padx=15)

        main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas, padding=10)

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        meta_frame = ttk.LabelFrame(scrollable_frame, text=" 1. Schedule & Details ", padding=12)
        meta_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(meta_frame, text=f"Batch Number: {self.batch_number}", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=4)
        ttk.Label(meta_frame, text=f"Start Date: {self.start_datetime_str}", font=("Helvetica", 10)).grid(row=0, column=1, sticky="w", padx=10, pady=4)

        ttk.Label(meta_frame, text="Expected Completion Date:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        self.entry_exp_date = ttk.Entry(meta_frame, width=20)
        self.entry_exp_date.insert(0, (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
        self.entry_exp_date.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(meta_frame, text="Meeting Date:").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        self.entry_meeting_date = ttk.Entry(meta_frame, width=20)
        self.entry_meeting_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_meeting_date.grid(row=2, column=1, sticky="w", padx=10, pady=6)

        prod_frame = ttk.LabelFrame(scrollable_frame, text=" 2. Select or Add Product ", padding=12)
        prod_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(prod_frame, text="Select Product:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.load_products_from_csv()
        self.product_combo = ttk.Combobox(prod_frame, width=35, state="readonly", values=self.products)
        self.product_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        if self.products: self.product_combo.set(self.products[0])

        ttk.Button(prod_frame, text="+ Add New Product", command=self.open_add_product_dialog).grid(row=0, column=2, padx=10, pady=5)

        person_frame = ttk.LabelFrame(scrollable_frame, text=" 3. Assigned Personnel ", padding=12)
        person_frame.pack(fill="x", padx=10, pady=8)

        users = auth_manager.load_users()
        self.selected_personnel = {}
        if users:
            col_idx, row_idx = 0, 0
            for u in users:
                uname = u.get("username", "") if isinstance(u, dict) else getattr(u, "username", "")
                fname = u.get("full_name") or uname if isinstance(u, dict) else getattr(u, "full_name", uname)
                if uname:
                    var = tk.BooleanVar(value=False)
                    ttk.Checkbutton(person_frame, text=fname, variable=var).grid(row=row_idx, column=col_idx, sticky="w", padx=12, pady=4)
                    self.selected_personnel[fname] = var
                    col_idx += 1
                    if col_idx > 1: col_idx = 0; row_idx += 1

        doc_frame = ttk.LabelFrame(scrollable_frame, text=" 4. Production Notes & Documents ", padding=12)
        doc_frame.pack(fill="x", padx=10, pady=8)
        self.txt_notes = tk.Text(doc_frame, height=4, font=("Helvetica", 9))
        self.txt_notes.pack(fill="x", pady=(0, 10))

        file_bar = ttk.Frame(doc_frame)
        file_bar.pack(fill="x")
        ttk.Button(file_bar, text="📎 Attach File", command=self.attach_doc_file).pack(side="left", padx=5)
        self.lbl_file_status = ttk.Label(file_bar, text="No file attached", font=("Helvetica", 9, "italic"))
        self.lbl_file_status.pack(side="left", padx=10)

        action_frame = ttk.Frame(scrollable_frame, padding=10)
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="💾 Save Production Batch", command=self.start_production).pack(side="right", padx=10)

    def attach_doc_file(self):
        file_path = filedialog.askopenfilename(title="Select File", filetypes=[("Documents", "*.docx *.xlsx *.doc *.xls")], parent=self)
        if file_path:
            self.attached_file_path = file_path
            self.lbl_file_status.config(text=f"Attached: {os.path.basename(file_path)}")

    def start_production(self):
        selected_product = self.product_combo.get().strip()
        if not selected_product:
            messagebox.showwarning("Warning", "Please select or add a product.", parent=self)
            return

        assigned_users = [user for user, var in self.selected_personnel.items() if var.get()]
        exp_date = self.entry_exp_date.get().strip()
        meeting_date = self.entry_meeting_date.get().strip()
        notes = self.txt_notes.get("1.0", tk.END).strip().replace("\n", " ")

        try:
            self.save_product_to_csv(selected_product)
            clean_prod = "".join(c for c in selected_product if c.isalnum() or c in (" ", "_", "-")).rstrip()
            batch_folder_path = os.path.join(self.new_prod_dir, f"{self.batch_number}_{clean_prod}")
            os.makedirs(batch_folder_path, exist_ok=True)

            copied_file_name = "None"
            if self.attached_file_path and os.path.exists(self.attached_file_path):
                shutil.copy(self.attached_file_path, batch_folder_path)
                copied_file_name = os.path.basename(self.attached_file_path)

            with open(os.path.join(batch_folder_path, "info.csv"), mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Batch_Number", "Product_Name", "Start_Date", "Expected_Completion_Date", "Meeting_Date", "Assigned_Personnel", "Attached_Document", "Notes", "Material_List"])
                writer.writerow([self.batch_number, selected_product, self.start_datetime_str, exp_date, meeting_date, ";".join(assigned_users), copied_file_name, notes, ""])

            messagebox.showinfo("Success", "Production Batch Saved Successfully!", parent=self)
            self.show_mode_selection()
        except Exception as e:
            messagebox.showerror("Save Error", f"{e}", parent=self)

    def open_add_product_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add New Product")
        dialog.geometry("360x160")
        entry_name = ttk.Entry(dialog, width=35)
        entry_name.pack(padx=15, pady=15)
        entry_name.focus_set()
        def save_product():
            p_name = entry_name.get().strip()
            if p_name:
                self.save_product_to_csv(p_name)
                self.product_combo["values"] = self.products
                self.product_combo.set(p_name)
                dialog.destroy()
        ttk.Button(dialog, text="Save", command=save_product).pack(pady=5)