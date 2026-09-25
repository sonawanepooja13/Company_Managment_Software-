"""
B2B Product Manager - Advanced PIM System
Implements a professional product information management workflow for white-labeling and sourcing.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
from datetime import datetime

# --- CSV CONFIGURATION ---
# Using a centralized directory for B2B data
DATA_DIR = os.path.join(os.path.dirname(__file__), "csv_data", "b2b")
FILES = {
    "suppliers": os.path.join(DATA_DIR, "b2b_suppliers.csv"),
    "categories": os.path.join(DATA_DIR, "b2b_categories.csv"),
    "products": os.path.join(DATA_DIR, "b2b_products.csv"),
    "variants": os.path.join(DATA_DIR, "b2b_variants.csv"),
    "white_label": os.path.join(DATA_DIR, "b2b_white_label.csv"),
    "financials": os.path.join(DATA_DIR, "b2b_financials.csv"),
    "media": os.path.join(DATA_DIR, "b2b_media.csv"),
}

HEADERS = {
    "suppliers": ["supplier_id", "name", "contact_person", "country", "moq", "sample_cost", "lead_time", "rating"],
    "categories": ["cat_id", "primary_category", "sub_category", "internal_tag"],
    "products": ["prod_id", "original_name", "original_model", "rebranded_name", "rebranded_model", "collection", "description", "material", "dimensions", "weight", "hs_code", "supplier_id", "cat_id", "status", "created_at"],
    "variants": ["variant_id", "prod_id", "sku", "color", "size", "package_type", "base_cost", "retail_price"],
    "white_label": ["prod_id", "logo_path", "insert_card_path", "pkg_dims", "printing_specs", "barcode_placement", "brand_copy", "seo_title", "seo_meta"],
    "financials": ["prod_id", "base_cost", "branding_fee", "sample_shipping", "freight_per_unit", "retail_price", "landed_cost", "margin_pct"],
    "media": ["media_id", "prod_id", "asset_type", "file_path", "description"],
}

def ensure_csv_files():
    """Initialize all required CSV files with headers if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for key, path in FILES.items():
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=HEADERS[key])
                writer.writeheader()

class B2BProductManager:
    def __init__(self, parent, product_id=None):
        self.parent = parent
        ensure_csv_files()

        # State management
        self.current_prod_id = product_id
        self.product_images = []
        self.is_dirty = False # Track unsaved changes

        self.create_gui()

        if product_id:
            self.load_product_data(product_id)

        if product_id:
            self.load_product_data(product_id)

    def create_gui(self):
        # Robustly find the root window to avoid 'MainApp object has no attribute tk' error
        if hasattr(self.parent, 'root') and isinstance(self.parent.root, (tk.Tk, tk.Toplevel)):
            root_window = self.parent.root
        elif isinstance(self.parent, (tk.Tk, tk.Toplevel)):
            root_window = self.parent
        elif isinstance(self.parent, (tk.Frame, ttk.Frame)):
            # If parent is a frame, we can use it as master or get its root
            root_window = self.parent
        else:
            # Fallback: Try to find any tkinter root
            try:
                root_window = tk.Tk().withdraw() # This is a hack, not ideal
                # Better: just use the parent if we have no choice, but we'll wrap in try-except
                root_window = self.parent
            except:
                root_window = self.parent

        try:
            self.window = tk.Toplevel(root_window)
        except tk.TclError:
            # If the above failed, it means root_window is still not a widget.
            # Try to find the actual root of the application.
            try:
                # This is a common way to get the root window in a complex app
                root_window = self.parent.root if hasattr(self.parent, 'root') else self.parent
                self.window = tk.Toplevel(root_window)
            except:
                messagebox.showerror("System Error", "Could not initialize the Product Manager window. Please restart the application.")
                return

        self.window.title("B2B Product Intelligence Manager")
        self.window.geometry("1100x850")

        # Intercept window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Header
        header = ttk.Frame(self.window, padding="15")
        header.pack(fill="x")
        ttk.Label(header, text="📦 Product Sourcing & White-Labeling Workflow", font=("Helvetica", 16, "bold")).pack(side="left")

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="📝 Edit Draft", command=self.open_draft_selector).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 Save Draft", command=self.save_product).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🚀 Publish Product", command=self.publish_product).pack(side="left", padx=5)

        # Multi-step Notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.create_tab_1_taxonomy()
        self.create_tab_2_suppliers()
        self.create_tab_3_specs()
        self.create_tab_4_branding()
        self.create_tab_5_financials()
        self.create_tab_6_media()
        self.create_tab_7_review()

    def mark_dirty(self, *args):
        """Set the dirty flag to True when any input is modified.
        Accepts *args to handle various Tkinter event arguments."""
        self.is_dirty = True

    def load_product_data(self, prod_id):
        """Loads existing product data from CSVs into the GUI."""
        try:
            # Ensure prod_id is a string and stripped
            prod_id = str(prod_id).strip()

            # 1. Load Main Product Data
            with open(FILES["products"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                prod_row = next((row for row in reader if str(row.get("prod_id", "")).strip() == prod_id), None)


            if not prod_row:
                messagebox.showerror("Error", "Product data not found.")
                return

            # --- Clear All Fields First ---
            self.orig_name.delete(0, tk.END)
            self.orig_model.delete(0, tk.END)
            self.rebrand_name.delete(0, tk.END)
            self.rebrand_model.delete(0, tk.END)
            self.collection.delete(0, tk.END)
            self.prod_desc.delete("1.0", tk.END)

            for entry in self.core_specs.values():
                entry.delete(0, tk.END)

            for entry in self.fin_inputs.values():
                entry.delete(0, tk.END)

            self.pkg_notes.delete("1.0", tk.END)
            self.brand_title.delete(0, tk.END)
            self.seo_meta.delete(0, tk.END)

            # Tab 1: Taxonomy & Mapping
            self.primary_cat.set(prod_row.get("cat_id", ""))
            self.orig_name.insert(0, prod_row.get("original_name", ""))
            self.orig_model.insert(0, prod_row.get("original_model", ""))
            self.rebrand_name.insert(0, prod_row.get("rebranded_name", ""))
            self.rebrand_model.insert(0, prod_row.get("rebranded_model", ""))
            self.collection.insert(0, prod_row.get("collection", ""))
            self.prod_desc.insert("1.0", prod_row.get("description", ""))

            # Tab 2: Supplier
            self.supplier_combo.set(self.get_supplier_name_by_id(prod_row.get("supplier_id", "")))
            self.show_supplier_details()

            # Tab 3: Specs & Variants
            self.core_specs["material"].insert(0, prod_row.get("material", ""))
            self.core_specs["dims"].insert(0, prod_row.get("dimensions", ""))
            self.core_specs["weight"].insert(0, prod_row.get("weight", ""))
            self.core_specs["hs_code"].insert(0, prod_row.get("hs_code", ""))

            self.var_tree.delete(*self.var_tree.get_children())
            with open(FILES["variants"], "r", encoding="utf-8") as f:
                v_reader = csv.DictReader(f)
                for v_row in v_reader:
                    if str(v_row.get("prod_id", "")).strip() == prod_id:
                        self.var_tree.insert("", "end", values=(
                            v_row["sku"], v_row["color"], v_row["size"],
                            v_row["package_type"], v_row["base_cost"], v_row["retail_price"]
                        ))

            # Tab 4: Branding
            with open(FILES["white_label"], "r", encoding="utf-8") as f:
                wl_reader = csv.DictReader(f)
                wl_row = next((row for row in wl_reader if str(row.get("prod_id", "")).strip() == prod_id), {})
                self.logo_path.set(wl_row.get("logo_path", "Not selected"))
                self.insert_path.set(wl_row.get("insert_card_path", "Not selected"))
                self.pkg_notes.insert("1.0", wl_row.get("pkg_dims", ""))
                self.brand_title.insert(0, wl_row.get("brand_copy", ""))
                self.seo_meta.insert(0, wl_row.get("seo_meta", ""))

            # Tab 5: Financials
            with open(FILES["financials"], "r", encoding="utf-8") as f:
                fin_reader = csv.DictReader(f)
                fin_row = next((row for row in fin_reader if str(row.get("prod_id", "")).strip() == prod_id), {})
                self.fin_inputs["base"].insert(0, fin_row.get("base_cost", ""))
                self.fin_inputs["brand_fee"].insert(0, fin_row.get("branding_fee", ""))
                self.fin_inputs["pkg_fee"].insert(0, fin_row.get("sample_shipping", ""))
                self.fin_inputs["freight"].insert(0, fin_row.get("freight_per_unit", ""))
                self.fin_inputs["retail"].insert(0, fin_row.get("retail_price", ""))
                self.calculate_margins()

            # Tab 6: Media & Docs
            self.media_list.delete(*self.media_list.get_children())
            for type_key in self.doc_types:
                self.doc_lists[type_key].delete(*self.doc_lists[type_key].get_children())

            with open(FILES["media"], "r", encoding="utf-8") as f:
                m_reader = csv.DictReader(f)
                for m_row in m_reader:
                    if str(m_row.get("prod_id", "")).strip() == prod_id:
                        if m_row["asset_type"] in self.doc_types:
                            self.doc_lists[m_row["asset_type"]].insert("", "end", values=(m_row["file_path"],))
                        else:
                            self.media_list.insert("", "end", values=(m_row["asset_type"], m_row["file_path"]))

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load product data: {e}")

        self.is_dirty = False # Reset dirty flag after loading data

    def get_csv_column(self, file_key, column_name):
        try:
            with open(FILES[file_key], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return [row[column_name] for row in reader if row[column_name]]
        except Exception:
            return []

    def get_supplier_id_by_name(self, name):
        """Helper to find the supplier_id for a given supplier name."""
        try:
            with open(FILES["suppliers"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["name"] == name:
                        return row["supplier_id"]
        except Exception:
            pass
        return None

    def get_supplier_name_by_id(self, supplier_id):
        """Helper to find the supplier name for a given supplier_id."""
        try:
            with open(FILES["suppliers"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get("supplier_id", "")).strip() == str(supplier_id).strip():
                        return row["name"]
        except Exception:
            pass
        return "Unknown Supplier"

    # --------------------------------------------------------------------------
    # TAB 1: CATEGORIZATION & TAXONOMY
    # --------------------------------------------------------------------------
    def create_tab_1_taxonomy(self):
        # ... (rest of the method remains same as in Read output)
        # I will replace the method and add the helpers below it
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 1. Taxonomy & Mapping ")

        ttk.Label(frame, text="Product Classification", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        tax_grid = ttk.Frame(frame)
        tax_grid.pack(fill="x")

        ttk.Label(tax_grid, text="Primary Category:").grid(row=0, column=0, sticky="w", pady=5)
        cat_frame = ttk.Frame(tax_grid)
        cat_frame.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.primary_cat = ttk.Combobox(cat_frame, values=self.get_csv_column("categories", "primary_category"), width=37)
        self.primary_cat.pack(side="left")
        self.primary_cat.bind("<<ComboboxSelected>>", self.update_subcategories)
        self.primary_cat.bind("<<ComboboxSelected>>", self.mark_dirty)

        ttk.Button(cat_frame, text="➕", width=3, command=lambda: self.open_category_dialog("primary")).pack(side="left", padx=5)

        ttk.Label(tax_grid, text="Sub-Category:").grid(row=1, column=0, sticky="w", pady=5)
        sub_cat_frame = ttk.Frame(tax_grid)
        sub_cat_frame.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.sub_cat = ttk.Combobox(sub_cat_frame, width=37, state="readonly")
        self.sub_cat.pack(side="left")
        self.sub_cat.bind("<<ComboboxSelected>>", self.on_subcat_selected)
        self.sub_cat.bind("<<ComboboxSelected>>", self.mark_dirty)

        ttk.Button(sub_cat_frame, text="➕", width=3, command=lambda: self.open_category_dialog("sub")).pack(side="left", padx=5)

        ttk.Label(tax_grid, text="Internal Tags (comma separated):").grid(row=2, column=0, sticky="w", pady=5)
        self.internal_tags = ttk.Entry(tax_grid, width=43)
        self.internal_tags.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.internal_tags.bind("<KeyRelease>", self.mark_dirty)

        ttk.Label(frame, text="Product Identification Mapping", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(25, 15))

        map_main_frame = ttk.Frame(frame)
        map_main_frame.pack(fill="x")

        left_col = ttk.LabelFrame(map_main_frame, text=" Supplier / Original Details ", padding=15)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(left_col, text="Original Product Name:").pack(anchor="w", pady=(0, 5))
        self.orig_name = ttk.Entry(left_col)
        self.orig_name.pack(fill="x", pady=(0, 15))
        self.orig_name.bind("<KeyRelease>", self.mark_dirty)

        ttk.Label(left_col, text="Original Model Number:").pack(anchor="w", pady=(0, 5))
        self.orig_model = ttk.Entry(left_col)
        self.orig_model.pack(fill="x", pady=(0, 15))
        self.orig_model.bind("<KeyRelease>", self.mark_dirty)

        right_col = ttk.LabelFrame(map_main_frame, text=" Your Brand / Rebranded Details ", padding=15)
        right_col.pack(side="left", fill="both", expand=True)

        ttk.Label(right_col, text="Rebranded Product Name:").pack(anchor="w", pady=(0, 5))
        self.rebrand_name = ttk.Entry(right_col)
        self.rebrand_name.pack(fill="x", pady=(0, 15))
        self.rebrand_name.bind("<KeyRelease>", self.mark_dirty)

        ttk.Label(right_col, text="Rebranded Model Number:").pack(anchor="w", pady=(0, 5))
        self.rebrand_model = ttk.Entry(right_col)
        self.rebrand_model.pack(fill="x", pady=(0, 15))
        self.rebrand_model.bind("<KeyRelease>", self.mark_dirty)

        coll_frame = ttk.Frame(frame)
        coll_frame.pack(fill="x", pady=(20, 0))
        ttk.Label(coll_frame, text="Collection / Brand Assignment:").pack(side="left", padx=(0, 10))
        self.collection = ttk.Entry(coll_frame, width=40)
        self.collection.pack(side="left")
        self.collection.bind("<KeyRelease>", self.mark_dirty)

        ttk.Label(frame, text="Detailed Product Description", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(25, 10))
        self.prod_desc = tk.Text(frame, width=80, height=6, wrap="word")
        self.prod_desc.pack(fill="x")
        self.prod_desc.bind("<KeyRelease>", self.mark_dirty)

    def on_subcat_selected(self, event):
        pass

    def update_subcategories(self, event=None):
        """Filter sub-categories based on the selected primary category."""
        primary = self.primary_cat.get()
        if not primary:
            self.sub_cat["values"] = []
            return

        try:
            with open(FILES["categories"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                sub_cats = [row["sub_category"] for row in reader if row["primary_category"] == primary and row["sub_category"]]

            sub_cats = sorted(list(set(sub_cats)))
            self.sub_cat["values"] = sub_cats
            self.sub_cat.set("")
        except Exception:
            self.sub_cat["values"] = []

    def open_draft_selector(self):
        """Opens a dialog to select a saved draft for editing."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Select Draft to Edit")
        dialog.geometry("600x400")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Available Drafts", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Drafts Table
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill="both", expand=True)

        cols = ("ID", "Rebranded Name", "Model", "Created At")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.column("Rebranded Name", width=200)
        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Load Drafts
        try:
            with open(FILES["products"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status") == "Draft":
                        tree.insert("", "end", values=(
                            row.get("prod_id", ""),
                            row.get("rebranded_name", ""),
                            row.get("rebranded_model", ""),
                            row.get("created_at", "")
                        ))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load drafts: {e}")

        def load_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Please select a draft to edit.")
                return

            prod_id = tree.item(selected[0])["values"][0]
            dialog.destroy()
            self.load_product_data(prod_id)

        ttk.Button(dialog, text="Load Selected Draft", command=load_selected).pack(pady=15)

    def open_category_dialog(self, cat_type):
        """Dialog to add a new primary or sub-category."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add New Category")
        dialog.geometry("350x200")
        dialog.transient(self.window)
        dialog.grab_set()

        label_text = "Enter Primary Category:" if cat_type == "primary" else "Enter Sub-Category:"
        ttk.Label(dialog, text=label_text, font=("Helvetica", 10, "bold")).pack(pady=(20, 10))

        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=5)
        entry.focus_set()

        def save_cat():
            val = entry.get().strip()
            if not val:
                messagebox.showwarning("Input Error", "Category name is required.")
                return

            cat_id = datetime.now().strftime("%Y%m%d%H%M%S")
            if cat_type == "primary":
                data = {
                    "cat_id": cat_id,
                    "primary_category": val,
                    "sub_category": "",
                    "internal_tag": ""
                }
            else:
                # For sub-category, we need the selected primary category
                primary = self.primary_cat.get()
                if not primary:
                    messagebox.showwarning("Error", "Please select a Primary Category first.")
                    return
                data = {
                    "cat_id": cat_id,
                    "primary_category": primary,
                    "sub_category": val,
                    "internal_tag": ""
                }

            with open(FILES["categories"], "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=HEADERS["categories"])
                writer.writerow(data)

            # Refresh the dropdowns
            self.primary_cat["values"] = self.get_csv_column("categories", "primary_category")
            dialog.destroy()

        ttk.Button(dialog, text="Save Category", command=save_cat).pack(pady=20)

    # --------------------------------------------------------------------------
    # TAB 2: SUPPLIER DATA ENTRY
    # --------------------------------------------------------------------------
    def create_tab_2_suppliers(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 2. Supplier ")

        ttk.Label(frame, text="Supplier Profiling", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        # Selection Area
        sup_frame = ttk.LabelFrame(frame, text=" Select or Create Supplier ", padding=15)
        sup_frame.pack(fill="x", pady=5)

        self.supplier_combo = ttk.Combobox(sup_frame, values=self.get_csv_column("suppliers", "name"), width=40)
        self.supplier_combo.pack(side="left", padx=5)
        self.supplier_combo.bind("<<ComboboxSelected>>", self.show_supplier_details)
        self.supplier_combo.bind("<<ComboboxSelected>>", self.mark_dirty)

        ttk.Button(sup_frame, text="➕ New Supplier", command=self.open_supplier_dialog).pack(side="left", padx=5)

        # Supplier Details Preview (The "Select Supplier" improvement)
        self.sup_details_frame = ttk.LabelFrame(frame, text=" Selected Supplier Information ", padding=15)
        self.sup_details_frame.pack(fill="x", pady=10)

        self.sup_info_label = ttk.Label(self.sup_details_frame, text="Please select a supplier to see details...", foreground="gray")
        self.sup_info_label.pack(anchor="w")

        # Logistics
        log_frame = ttk.Frame(frame)
        log_frame.pack(fill="x", pady=20)

        log_fields = [
            ("MOQ (Minimum Order Qty):", "moq"),
            ("Sample Cost (₹):", "sample_cost"),
            ("Lead Time (Days):", "lead_time"),
            ("Factory Rating (1-5):", "rating"),
        ]

        self.sup_logistics = {}
        for i, (label, key) in enumerate(log_fields):
            ttk.Label(log_frame, text=label).grid(row=i//2, column=(i%2)*2, sticky="w", pady=5)
            entry = ttk.Entry(log_frame, width=15)
            entry.grid(row=i//2, column=(i%2)*2+1, sticky="w", padx=10, pady=5)
            entry.bind("<KeyRelease>", self.mark_dirty)
            self.sup_logistics[key] = entry

    def show_supplier_details(self, event=None):
        """Fetch and display details of the selected supplier."""
        name = self.supplier_combo.get()
        try:
            with open(FILES["suppliers"], "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["name"] == name:
                        details = (f"Company: {row['name']} | Contact: {row['contact_person']} | "
                                   f"Country: {row['country']} | Rating: {row['rating']}⭐")
                        self.sup_info_label.config(text=details, foreground="black")
                        return
            self.sup_info_label.config(text="Supplier details not found.", foreground="red")
        except Exception as e:
            self.sup_info_label.config(text=f"Error loading details: {e}", foreground="red")

    def open_supplier_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add New Supplier")
        dialog.geometry("400x300")

        fields = ["Name", "Contact Person", "Country", "MOQ", "Sample Cost", "Lead Time", "Rating"]
        entries = {}
        for i, f in enumerate(fields):
            ttk.Label(dialog, text=f+":").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = ttk.Entry(dialog)
            e.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[f] = e

        def save_sup():
            data = {
                "supplier_id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": entries["Name"].get(),
                "contact_person": entries["Contact Person"].get(),
                "country": entries["Country"].get(),
                "moq": entries["MOQ"].get(),
                "sample_cost": entries["Sample Cost"].get(),
                "lead_time": entries["Lead Time"].get(),
                "rating": entries["Rating"].get(),
            }
            with open(FILES["suppliers"], "a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=HEADERS["suppliers"]).writerow(data)
            self.supplier_combo["values"] = self.get_csv_column("suppliers", "name")
            dialog.destroy()

        ttk.Button(dialog, text="Save Supplier", command=save_sup).grid(row=len(fields), column=0, columnspan=2, pady=20)

    # --------------------------------------------------------------------------
    # TAB 3: CORE PRODUCT SPECS & VARIANTS
    # --------------------------------------------------------------------------
    def create_tab_3_specs(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 3. Specifications ")

        ttk.Label(frame, text="Technical Specifications", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        spec_grid = ttk.Frame(frame)
        spec_grid.pack(fill="x")

        specs = [
            ("Material:", "material"),
            ("Dimensions:", "dims"),
            ("Weight (kg):", "weight"),
            ("HS Code (Customs):", "hs_code"),
        ]
        self.core_specs = {}
        for i, (lbl, key) in enumerate(specs):
            ttk.Label(spec_grid, text=lbl).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(spec_grid, width=40)
            e.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            e.bind("<KeyRelease>", self.mark_dirty)
            self.core_specs[key] = e

        ttk.Label(frame, text="Product Variants (SKUs)", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(20, 10))

        var_frame = ttk.Frame(frame)
        var_frame.pack(fill="both", expand=True)

        cols = ("SKU", "Color", "Size", "Pkg Type", "Base Cost", "Retail Price")
        self.var_tree = ttk.Treeview(var_frame, columns=cols, show="headings", height=8)
        for c in cols:
            self.var_tree.heading(c, text=c)
            self.var_tree.column(c, width=100)
        self.var_tree.pack(side="left", fill="x", expand=True)

        add_var_frame = ttk.LabelFrame(frame, text=" Add Variant ", padding=10)
        add_var_frame.pack(fill="x", pady=10)

        self.var_inputs = {}
        for i, col in enumerate(cols):
            ttk.Label(add_var_frame, text=col+":").grid(row=0, column=i*2, padx=5)
            e = ttk.Entry(add_var_frame, width=10)
            e.grid(row=0, column=i*2+1, padx=5)
            e.bind("<KeyRelease>", self.mark_dirty)
            self.var_inputs[col] = e

        ttk.Button(add_var_frame, text="➕ Add Variant", command=self.add_variant).grid(row=0, column=12, padx=10)

    def add_variant(self):
        vals = [self.var_inputs[c].get() for c in self.var_inputs]
        if not vals[0]:
            messagebox.showwarning("Error", "SKU is required")
            return
        self.var_tree.insert("", "end", values=vals)
        self.mark_dirty()
        for e in self.var_inputs.values(): e.delete(0, tk.END)

    # --------------------------------------------------------------------------
    # TAB 4: WHITE-LABELING & BRANDING
    # --------------------------------------------------------------------------
    def create_tab_4_branding(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 4. Branding ")

        asset_frame = ttk.LabelFrame(frame, text=" Brand Assets ", padding=15)
        asset_frame.pack(fill="x", pady=5)

        self.logo_path = tk.StringVar(value="Not selected")
        self.insert_path = tk.StringVar(value="Not selected")
        self.logo_path.trace_add("write", self.mark_dirty)
        self.insert_path.trace_add("write", self.mark_dirty)

        ttk.Label(asset_frame, text="Brand Logo:").grid(row=0, column=0, sticky="w")
        ttk.Label(asset_frame, textvariable=self.logo_path, foreground="gray").grid(row=0, column=1, padx=10)
        ttk.Button(asset_frame, text="Upload", command=lambda: self.upload_file(self.logo_path)).grid(row=0, column=2)

        ttk.Label(asset_frame, text="Insert Card:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(asset_frame, textvariable=self.insert_path, foreground="gray").grid(row=1, column=1, padx=10)
        ttk.Button(asset_frame, text="Upload", command=lambda: self.upload_file(self.insert_path)).grid(row=1, column=2)

        pkg_frame = ttk.LabelFrame(frame, text=" Packaging Specifications ", padding=15)
        pkg_frame.pack(fill="x", pady=10)
        self.pkg_notes = tk.Text(pkg_frame, height=4, width=60)
        self.pkg_notes.pack(fill="x")
        self.pkg_notes.bind("<KeyRelease>", self.mark_dirty)

        copy_frame = ttk.LabelFrame(frame, text=" Brand-Specific Copy ", padding=15)
        copy_frame.pack(fill="x", pady=10)

        ttk.Label(copy_frame, text="Rewritten Sales Title:").pack(anchor="w")
        self.brand_title = ttk.Entry(copy_frame, width=80)
        self.brand_title.pack(fill="x", pady=5)
        self.brand_title.bind("<KeyRelease>", self.mark_dirty)

        ttk.Label(copy_frame, text="SEO Metadata / Keywords:").pack(anchor="w")
        self.seo_meta = ttk.Entry(copy_frame, width=80)
        self.seo_meta.pack(fill="x", pady=5)
        self.seo_meta.bind("<KeyRelease>", self.mark_dirty)

    def upload_file(self, var):
        path = filedialog.askopenfilename()
        if path: var.set(path)

    # --------------------------------------------------------------------------
    # TAB 5: COSTING & MARGINS
    # --------------------------------------------------------------------------
    def create_tab_5_financials(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 5. Financials ")

        ttk.Label(frame, text="Landed Cost Calculator", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        calc_grid = ttk.Frame(frame)
        calc_grid.pack(fill="x")

        fields = [
            ("Unit Purchase Cost (₹):", "base"),
            ("Branding/Customization Fee per Unit (₹):", "brand_fee"),
            ("Packaging Cost per Unit (₹):", "pkg_fee"),
            ("Freight/Shipping Cost per Unit (₹):", "freight"),
            ("Target Retail Selling Price (₹):", "retail"),
        ]
        self.fin_inputs = {}
        for i, (lbl, key) in enumerate(fields):
            ttk.Label(calc_grid, text=lbl).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(calc_grid, width=20)
            e.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            e.bind("<KeyRelease>", self.calculate_margins)
            e.bind("<KeyRelease>", self.mark_dirty)
            self.fin_inputs[key] = e

        res_frame = ttk.LabelFrame(frame, text=" Results ", padding=15)
        res_frame.pack(fill="x", pady=20)

        self.res_landed = tk.StringVar(value="₹0.00")
        self.res_margin = tk.StringVar(value="0.00%")

        ttk.Label(res_frame, text="Estimated Landed Cost:").grid(row=0, column=0, sticky="w")
        ttk.Label(res_frame, textvariable=self.res_landed, font=("Helvetica", 14, "bold")).grid(row=0, column=1, padx=10, sticky="w")

        ttk.Label(res_frame, text="Estimated Gross Margin:").grid(row=1, column=0, sticky="w")
        ttk.Label(res_frame, textvariable=self.res_margin, font=("Helvetica", 14, "bold"), foreground="green").grid(row=1, column=1, padx=10, sticky="w")

    def calculate_margins(self):
        try:
            base = float(self.fin_inputs["base"].get() or 0)
            brand = float(self.fin_inputs["brand_fee"].get() or 0)
            pkg = float(self.fin_inputs["pkg_fee"].get() or 0)
            freight = float(self.fin_inputs["freight"].get() or 0)
            retail = float(self.fin_inputs["retail"].get() or 0)

            landed = base + brand + pkg + freight
            self.res_landed.set(f"₹{landed:.2f}")

            if retail > 0:
                margin = ((retail - landed) / retail) * 100
                self.res_margin.set(f"{margin:.2f}%")
            else:
                self.res_margin.set("0.00%")
        except ValueError:
            pass

    # --------------------------------------------------------------------------
    # TAB 6: MEDIA & DOCUMENT VAULT
    # --------------------------------------------------------------------------
    def create_tab_6_media(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 6. Media & Docs ")

        # --- Section 1: PDF Document Vault ---
        ttk.Label(frame, text="Document Vault (PDFs)", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        doc_container = ttk.Frame(frame)
        doc_container.pack(fill="x", pady=(0, 25))

        # Defined Document Types
        self.doc_types = {
            "SPEC_SHEET": "📄 Spec Sheets & Datasheets",
            "USER_MANUAL": "📘 User / Operation Manuals",
            "CERTIFICATE": "📜 Quality & Safety Certs (CE/RoHS)",
            "INVOICE": "💰 Supplier Invoices / POs",
            "ARTWORK": "🎨 Packaging / Printing Artworks"
        }

        self.doc_lists = {} # Store Treeviews for each type

        # Create a grid of upload buckets
        doc_grid = ttk.Frame(doc_container)
        doc_grid.pack(fill="both", expand=True)

        for i, (type_key, label) in enumerate(self.doc_types.items()):
            bucket = ttk.LabelFrame(doc_grid, text=label, padding=10)
            bucket.grid(row=i//2, column=i%2, sticky="nsew", padx=5, pady=5)
            doc_grid.columnconfigure(i%2, weight=1)

            # List of files for this category
            tree = ttk.Treeview(bucket, columns=("Path"), show="headings", height=3)
            tree.heading("Path", text="File Path")
            tree.column("Path", width=200)
            tree.pack(fill="x", pady=5)
            self.doc_lists[type_key] = tree

            btn_frame = ttk.Frame(bucket)
            btn_frame.pack(fill="x")
            ttk.Button(btn_frame, text="Upload PDF",
                       command=lambda tk=type_key: self.upload_categorized_pdf(tk)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="X", width=3,
                       command=lambda tk=type_key: self.remove_doc(tk)).pack(side="right", padx=2)

        # --- Section 2: Image Gallery ---
        ttk.Label(frame, text="Product Image Gallery", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(15, 15))

        img_frame = ttk.Frame(frame)
        img_frame.pack(fill="x")

        ttk.Button(img_frame, text="📸 Upload Product Photos",
                   command=lambda: self.upload_media("Photo")).pack(side="left", padx=5)
        ttk.Button(img_frame, text="📦 Upload Mockups",
                   command=lambda: self.upload_media("Mockup")).pack(side="left", padx=5)

        self.media_list = ttk.Treeview(frame, columns=("Type", "Path"), show="headings")
        self.media_list.heading("Type", text="Asset Type")
        self.media_list.heading("Path", text="File Path")
        self.media_list.pack(fill="both", expand=True, pady=10)

    def upload_categorized_pdf(self, doc_type):
        path = filedialog.askopenfilename(
            title=f"Select {self.doc_types[doc_type]}",
            filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            # Add to the specific Treeview for this category
            self.doc_lists[doc_type].insert("", "end", values=(path,))
            self.mark_dirty()

    def remove_doc(self, doc_type):
        selected = self.doc_lists[doc_type].selection()
        if not selected:
            return
        for item in selected:
            self.doc_lists[doc_type].delete(item)
        self.mark_dirty()

    def upload_media(self, asset_type):
        path = filedialog.askopenfilename()
        if path:
            self.media_list.insert("", "end", values=(asset_type, path))
            self.mark_dirty()

    # --------------------------------------------------------------------------
    # TAB 7: REVIEW & EXPORT
    # --------------------------------------------------------------------------
    def create_tab_7_review(self):
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text=" 7. Review ")

        ttk.Label(frame, text="Final Product Review", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 15))

        self.review_text = tk.Text(frame, height=20, width=80, state="disabled", bg="#f0f0f0")
        self.review_text.pack(fill="both", expand=True)

        ttk.Button(frame, text="🔄 Refresh Review Summary", command=self.update_review_summary).pack(pady=10)

    def update_review_summary(self):
        self.review_text.config(state="normal")
        self.review_text.delete("1.0", tk.END)

        summary = f"Original Product: {self.orig_name.get()} ({self.orig_model.get()})\n"
        summary += f"Rebranded Product: {self.rebrand_name.get()} ({self.rebrand_model.get()})\n"
        summary += f"Collection: {self.collection.get()}\n"
        summary += f"Category: {self.primary_cat.get()} -> {self.sub_cat.get()}\n"
        summary += f"Supplier: {self.supplier_combo.get()}\n"
        summary += f"Landed Cost: {self.res_landed.get()}\n"
        summary += f"Gross Margin: {self.res_margin.get()}\n"

        # Document Summary
        doc_summary = []
        for type_key, label in self.doc_types.items():
            count = len(self.doc_lists[type_key].get_children())
            doc_summary.append(f"{label}: {count}")

        summary += f"Documents: {', '.join(doc_summary)}\n"
        summary += f"Variants: {len(self.var_tree.get_children())} SKUs listed\n"
        summary += f"Assets: {len(self.media_list.get_children())} files attached\n"

        self.review_text.insert(tk.END, summary)
        self.review_text.config(state="disabled")

    # --------------------------------------------------------------------------
    # DATA PERSISTENCE
    # --------------------------------------------------------------------------
    def save_product(self, status="Draft"):
        if not self.rebrand_name.get():
            messagebox.showwarning("Missing Info", "Rebranded Product Name is required before saving.")
            return

        prod_id = self.current_prod_id or datetime.now().strftime("%Y%m%d%H%M%S")
        self.current_prod_id = prod_id

        # 1. Main Product (Updated for Mapping)
        prod_data = {
            "prod_id": prod_id,
            "original_name": self.orig_name.get(),
            "original_model": self.orig_model.get(),
            "rebranded_name": self.rebrand_name.get(),
            "rebranded_model": self.rebrand_model.get(),
            "collection": self.collection.get(),
            "description": self.prod_desc.get("1.0", tk.END).strip(),
            "material": self.core_specs["material"].get(),
            "dimensions": self.core_specs["dims"].get(),
            "weight": self.core_specs["weight"].get(),
            "hs_code": self.core_specs["hs_code"].get(),
            "supplier_id": self.get_supplier_id_by_name(self.supplier_combo.get()),
            "cat_id": self.primary_cat.get(),
            "status": status,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.write_to_csv("products", prod_data)

        # ... (rest of the save logic)
        # 2. Variants
        for child in self.var_tree.get_children():
            v = self.var_tree.item(child)["values"]
            var_data = {
                "variant_id": f"{prod_id}_{v[0]}",
                "prod_id": prod_id,
                "sku": v[0], "color": v[1], "size": v[2], "package_type": v[3],
                "base_cost": v[4], "retail_price": v[5]
            }
            self.write_to_csv("variants", var_data)

        # 3. White Labeling
        wl_data = {
            "prod_id": prod_id,
            "logo_path": self.logo_path.get(),
            "insert_card_path": self.insert_path.get(),
            "pkg_dims": self.pkg_notes.get("1.0", tk.END).strip(),
            "printing_specs": "", "barcode_placement": "",
            "brand_copy": self.brand_title.get(),
            "seo_title": "", "seo_meta": self.seo_meta.get()
        }
        self.write_to_csv("white_label", wl_data)

        # 4. Financials (Updated to match new Professional Calculator)
        fin_data = {
            "prod_id": prod_id,
            "base_cost": self.fin_inputs["base"].get(),
            "branding_fee": self.fin_inputs["brand_fee"].get(),
            "sample_shipping": self.fin_inputs["pkg_fee"].get(), # Mapping pkg_fee to this slot for CSV compatibility
            "freight_per_unit": self.fin_inputs["freight"].get(),
            "retail_price": self.fin_inputs["retail"].get(),
            "landed_cost": self.res_landed.get(),
            "margin_pct": self.res_margin.get()
        }
        self.write_to_csv("financials", fin_data)

        # 5. Media & Documents
        # Save images/mockups
        for child in self.media_list.get_children():
            m = self.media_list.item(child)["values"]
            media_data = {
                "media_id": f"m_{datetime.now().strftime('%S%f')}",
                "prod_id": prod_id,
                "asset_type": m[0], "file_path": m[1], "description": ""
            }
            self.write_to_csv("media", media_data)

        # Save categorized PDFs
        for type_key, tree in self.doc_lists.items():
            for child in tree.get_children():
                path = tree.item(child)["values"][0]
                doc_data = {
                    "media_id": f"d_{datetime.now().strftime('%S%f')}",
                    "prod_id": prod_id,
                    "asset_type": type_key, "file_path": path, "description": ""
                }
                self.write_to_csv("media", doc_data)

        self.is_dirty = False
        messagebox.showinfo("Success", f"Product {prod_id} saved as draft successfully!")

    def publish_product(self):
        # Final Validation before publishing
        missing = []
        if not self.rebrand_name.get(): missing.append("Rebranded Product Name")
        if not self.rebrand_model.get(): missing.append("Rebranded Model Number")
        if not self.fin_inputs["retail"].get(): missing.append("Retail Price")
        if not self.supplier_combo.get(): missing.append("Supplier")

        if missing:
            messagebox.showerror("Publishing Error", f"Please complete the following critical fields before publishing:\n\n" + "\n".join(missing))
            return

        self.save_product(status="published")
        messagebox.showinfo("Published", "Product has been published to the B2B Catalog!")

    def write_to_csv(self, key, data):
        with open(FILES[key], "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS[key])
            writer.writerow(data)

    def on_closing(self):
        """Handle window closing event and prompt to save if changes were made."""
        if self.is_dirty:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save them before closing?"
            )
            if response is True: # Save and close
                self.save_product()
                self.window.destroy()
            elif response is False: # Don't save and close
                self.window.destroy()
            else: # Cancel closing
                pass
        else:
            self.window.destroy()

def open_b2b_product_manager(parent, product_id=None):
    """Open the B2B Product Manager window"""
    return B2BProductManager(parent, product_id)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_b2b_product_manager(root)
    root.mainloop()
