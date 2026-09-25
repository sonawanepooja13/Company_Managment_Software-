"""
B2B Product Viewer / Buyer Interface
Allows users to browse and view published white-label products.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv

# --- CSV CONFIGURATION ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "csv_data", "b2b")
PRODUCTS_FILE = os.path.join(DATA_DIR, "b2b_products.csv")
FINANCIALS_FILE = os.path.join(DATA_DIR, "b2b_financials.csv")

class B2BProductViewer:
    def __init__(self, parent):
        self.parent = parent
        self.create_gui()

    def create_gui(self):
        # Robustly find the root window to avoid 'MainApp object has no attribute tk' error
        if hasattr(self.parent, 'root') and isinstance(self.parent.root, (tk.Tk, tk.Toplevel)):
            root_window = self.parent.root
        elif isinstance(self.parent, (tk.Tk, tk.Toplevel)):
            root_window = self.parent
        elif isinstance(self.parent, (tk.Frame, ttk.Frame)):
            root_window = self.parent
        else:
            root_window = self.parent

        try:
            self.window = tk.Toplevel(root_window)
        except tk.TclError:
            try:
                root_window = self.parent.root if hasattr(self.parent, 'root') else self.parent
                self.window = tk.Toplevel(root_window)
            except:
                messagebox.showerror("System Error", "Could not initialize the Product Viewer window. Please restart the application.")
                return

        self.window.title("My Published Products - B2B Catalog")
        self.window.geometry("1000x600")

        # Header
        header = ttk.Frame(self.window, padding="15")
        header.pack(fill="x")
        ttk.Label(header, text="📦 Published Product Catalog", font=("Helvetica", 16, "bold")).pack(side="left")

        ttk.Button(header, text="Close", command=self.window.destroy).pack(side="right")

        # Search Bar
        search_frame = ttk.Frame(self.window, padding="10")
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search Products:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.refresh_list)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=5)

        # --- Autocomplete Suggestion List ---
        self.suggestion_frame = tk.Frame(self.window, bg="white", highlightthickness=1, highlightbackground="gray")
        self.suggestion_list = tk.Listbox(self.suggestion_frame, width=40, height=6, borderwidth=0, highlightthickness=0)
        self.suggestion_list.pack(fill="both", expand=True)
        self.suggestion_list.bind("<<ListboxSelect>>", self.on_suggestion_select)

        # Position the suggestion frame relative to the entry
        self.window.update_idletasks()
        x = self.search_entry.winfo_rootx() - self.window.winfo_rootx()
        y = self.search_entry.winfo_rooty() - self.window.winfo_rooty() + self.search_entry.winfo_height()
        self.suggestion_frame.place(x=x, y=y)
        self.suggestion_frame.place_forget() # Hide by default

        # Product Table
        self.tree_frame = ttk.Frame(self.window, padding="15")
        self.tree_frame.pack(fill="both", expand=True)

        cols = ("ID", "Rebranded Name", "Model", "Category", "Retail Price", "Status")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.column("Rebranded Name", width=300)
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Action Buttons
        btn_frame = ttk.Frame(self.window, padding="15")
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="🔍 View Detailed Specifications", command=self.show_details).pack(side="right", padx=5)

        self.refresh_list()

    def refresh_list(self, *args):
        # Clear existing table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear suggestions
        self.suggestion_list.delete(0, tk.END)

        search_term = self.search_var.get().lower()

        try:
            if not os.path.exists(PRODUCTS_FILE):
                return

            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                matches = []
                for row in reader:
                    # Only show 'published' products
                    if row.get("status") == "published":
                        name = row.get("rebranded_name", "")
                        model = row.get("rebranded_model", "")
                        if search_term in name.lower() or search_term in model.lower():
                            matches.append(row)

                # Update Table
                for row in matches:
                    price = self.get_retail_price(row["prod_id"])
                    self.tree.insert("", "end", values=(
                        row["prod_id"],
                        row.get("rebranded_name", ""),
                        row.get("rebranded_model", ""),
                        row.get("cat_id", ""),
                        f"₹{price}",
                        row["status"]
                    ))

                # Update Suggestions (only if typing)
                if search_term and matches:
                    for row in matches:
                        display_text = f"{row.get('rebranded_name', '')} ({row.get('rebranded_model', '')})"
                        self.suggestion_list.insert(tk.END, display_text)
                    self.suggestion_frame.place() # Show dropdown
                else:
                    self.suggestion_frame.place_forget() # Hide if no matches or empty search

        except Exception as e:
            print(f"Error refreshing list: {e}")

    def on_suggestion_select(self, event):
        selection = self.suggestion_list.curselection()
        if selection:
            selected_text = self.suggestion_list.get(selection[0])
            # Extract the product name (everything before the '(')
            product_name = selected_text.split(" (")[0]
            self.search_var.set(product_name)
            self.suggestion_frame.place_forget()
            self.refresh_list()

    def get_retail_price(self, prod_id):
        try:
            with open(FINANCIALS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["prod_id"] == prod_id:
                        return row.get("retail_price", "0.00")
        except Exception:
            pass
        return "0.00"

    def show_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product to view details.")
            return

        prod_id = self.tree.item(selected[0])["values"][0]

        # Open the Product Manager in READ-ONLY mode (simulated)
        try:
            from b2b_product_manager import open_b2b_product_manager
            open_b2b_product_manager(self.parent, prod_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open details: {e}")

def open_b2b_buy_products(parent):
    """Open the product viewer window"""
    return B2BProductViewer(parent)
