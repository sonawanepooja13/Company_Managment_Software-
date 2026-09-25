import csv
import math
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk

import bom_engine
import config
import views


class PriceTab(ttk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.products_csv_path = config.PRODUCTS_CSV
        self.customers_csv_path = config.CUSTOMERS_CSV
        self.customer_data = {}
        self.current_search_params = {}  # Store current search parameters
        self.product_price_csv = os.path.join(
            config.CSV_DIR, "Product Price Calculator", "price_list.csv"
        )
        self.vfd_make_values = self.load_price_list_makes("VFD", use_subcategory=True)
        self.switch_gear_make_values = self.load_price_list_makes("MCB")

        self.build_ui()
        self.refresh_customer_list()

    def build_ui(self):
        title = ttk.Label(self, text="Product Price Lookup", font=("Helvetica", 15, "bold"))
        title.pack(pady=10)

        # Create scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        form_frame = ttk.Frame(scrollable_frame, padding="10")
        form_frame.pack(fill="both", expand=True)

        row = 0

        ttk.Label(form_frame, text="Select Customer:", font=("Helvetica", 10, "bold")).grid(row=row, column=0, sticky="w", pady=4)
        cust_frame = ttk.Frame(form_frame)
        cust_frame.grid(row=row, column=1, sticky="e", pady=4)

        self.customer_combo = ttk.Combobox(cust_frame, width=17, state="readonly")
        self.customer_combo.pack(side="left", padx=(0, 5))

        add_cust_btn = ttk.Button(cust_frame, text="+ Add Customer", command=self.open_add_customer_window)
        add_cust_btn.pack(side="left", padx=(0, 5))

        open_csv_btn = ttk.Button(cust_frame, text="📊 Open Price List", command=self.open_csv_viewer)
        open_csv_btn.pack(side="left")

        row += 1
        ttk.Separator(form_frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        ttk.Label(form_frame, text="Pump Type:").grid(row=row, column=0, sticky="w", pady=4)
        self.pump_type_combo = ttk.Combobox(form_frame, values=["3 Phase", "1 Phase"], width=23, state="readonly")
        self.pump_type_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.pump_type_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Pump Current (A):").grid(row=row, column=0, sticky="w", pady=4)
        self.current_entry = ttk.Entry(form_frame, width=25)
        self.current_entry.grid(row=row, column=1, sticky="e", pady=4)
        ttk.Label(form_frame, text="Switch Gear Make:").grid(row=row, column=2, sticky="w", padx=(30, 0), pady=4)
        self.switch_gear_make_combo = ttk.Combobox(
            form_frame, values=self.switch_gear_make_values, width=23, state="readonly"
        )
        self.switch_gear_make_combo.grid(row=row, column=3, sticky="e", pady=4)
        if self.switch_gear_make_values:
            self.switch_gear_make_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Number of Pumps:").grid(row=row, column=0, sticky="w", pady=4)
        self.pumps_combo = ttk.Combobox(form_frame, values=["1", "2", "3", "4", "5"], width=23, state="readonly")
        self.pumps_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.pumps_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Number of VFD:").grid(row=row, column=0, sticky="w", pady=4)
        self.vfd_combo = ttk.Combobox(form_frame, values=["0", "1", "2", "3", "4"], width=23, state="readonly")
        self.vfd_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.vfd_combo.current(0)
        ttk.Label(form_frame, text="VFD Make:").grid(row=row, column=2, sticky="w", padx=(30, 0), pady=4)
        self.vfd_make_combo = ttk.Combobox(
            form_frame, values=self.vfd_make_values, width=23, state="readonly"
        )
        self.vfd_make_combo.grid(row=row, column=3, sticky="e", pady=4)
        if self.vfd_make_values:
            self.vfd_make_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Bypass:").grid(row=row, column=0, sticky="w", pady=4)
        self.bypass_combo = ttk.Combobox(form_frame, values=["With Bypass", "Without Bypass"], width=23, state="readonly")
        self.bypass_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.bypass_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Panel Type:").grid(row=row, column=0, sticky="w", pady=4)
        self.panel_type_combo = ttk.Combobox(form_frame, values=["Indoor", "Outdoor"], width=23, state="readonly")
        self.panel_type_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.panel_type_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Panel Size:").grid(row=row, column=0, sticky="w", pady=4)
        self.size_combo = ttk.Combobox(form_frame, values=["400x300", "600x400", "800x600", "1000x800", "1200x800"], width=23, state="readonly")
        self.size_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.size_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Panel Class:").grid(row=row, column=0, sticky="w", pady=4)
        self.panel_class_combo = ttk.Combobox(form_frame, values=["Industrial", "Domestic"], width=23, state="readonly")
        self.panel_class_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.panel_class_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Main Incomer:").grid(row=row, column=0, sticky="w", pady=4)
        self.main_incomer_combo = ttk.Combobox(form_frame, values=["Yes", "No"], width=23, state="readonly")
        self.main_incomer_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.main_incomer_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="OLR Requirement:").grid(row=row, column=0, sticky="w", pady=4)
        self.olr_combo = ttk.Combobox(form_frame, values=["Yes", "No"], width=23, state="readonly")
        self.olr_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.olr_combo.current(0)
        row += 1

        ttk.Label(form_frame, text="Indicator Light Required:").grid(row=row, column=0, sticky="w", pady=4)
        self.light_combo = ttk.Combobox(form_frame, values=["Yes", "No"], width=23, state="readonly")
        self.light_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.light_combo.current(0)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        search_btn = ttk.Button(btn_frame, text="Search Price", command=self.search_price)
        search_btn.pack(side="left", padx=5)

        reload_btn = ttk.Button(btn_frame, text="📁 Reload File Path", command=self.show_file_info)
        reload_btn.pack(side="left", padx=5)

        calc_switch_btn = ttk.Button(btn_frame, text="Open Material Calculator ->", command=lambda: self.main_app.switch_tab(1))
        calc_switch_btn.pack(side="left", padx=5)

        self.result_label = ttk.Label(self, text="Select parameters and click 'Search Price'", font=("Helvetica", 12, "italic"))
        self.result_label.pack(pady=5)

        self.breakdown_label = ttk.Label(self, text="", font=("Helvetica", 9), foreground="gray")
        self.breakdown_label.pack(pady=2)

    def show_file_info(self):
        messagebox.showinfo(
            "Active CSV Storage Folder",
            f"All CSV files are stored in:\n\n{config.CSV_DIR}\n\n"
            f"Active Products CSV:\n{self.products_csv_path}"
        )

    def load_price_list_makes(self, category, use_subcategory=False):
        makes = []
        try:
            with open(self.product_price_csv, newline="", encoding="utf-8-sig") as file:
                for row in csv.DictReader(file):
                    if str(row.get("Category", "")).strip().lower() != category.lower():
                        continue
                    make = str(row.get("make", "")).strip()
                    if not make and use_subcategory:
                        make = str(row.get("SUB Category Type 1", "")).strip()
                    if make and make.lower() not in {value.lower() for value in makes}:
                        makes.append(make)
        except (OSError, csv.Error):
            pass
        return makes or ["Not specified"]

    def open_csv_viewer(self):
        views.CSVViewerWindow(self.winfo_toplevel())

    def refresh_customer_list(self):
        customers = bom_engine.read_csv_data(self.customers_csv_path)
        self.customer_data = {}
        names = []

        for c in customers:
            name = c.get("customer_name")
            try:
                pct = float(c.get("percentage", 0.0))
            except ValueError:
                pct = 0.0
            if name:
                self.customer_data[name] = pct
                names.append(name)

        if names:
            self.customer_combo["values"] = names
            self.customer_combo.current(0)
        
    def open_add_customer_window(self):
        views.AddCustomerWindow(self.winfo_toplevel(), self.refresh_customer_list)

    def search_price(self):
        raw_current = self.current_entry.get().strip()
        if not raw_current:
            messagebox.showwarning("Input Warning", "Please enter the Pump Current value.")
            return

        try:
            pump_current = float(raw_current)
        except ValueError:
            messagebox.showwarning("Input Warning", "Pump Current must be a valid number.")
            return

        def flexible_normalize(val):
            if val is None:
                return ""
            s = str(val).strip().lower()
            if s.endswith(".0"):
                s = s[:-2]
            
            if s in ["1", "true", "yes", "with bypass", "with_bypass", "withbypass"]:
                return "yes_or_with"
            if s in ["0", "false", "no", "without bypass", "without_bypass", "withoutbypass"]:
                return "no_or_without"
            
            return re.sub(r"[^a-z0-9]", "", s)

        pump_type = flexible_normalize(self.pump_type_combo.get())
        num_pumps = flexible_normalize(self.pumps_combo.get())
        num_vfd = flexible_normalize(self.vfd_combo.get())
        switch_gear_make = flexible_normalize(self.switch_gear_make_combo.get())
        vfd_make = flexible_normalize(self.vfd_make_combo.get())
        bypass = flexible_normalize(self.bypass_combo.get())
        panel_type = flexible_normalize(self.panel_type_combo.get())
        panel_size = flexible_normalize(self.size_combo.get())
        panel_class = flexible_normalize(self.panel_class_combo.get())
        main_incomer = flexible_normalize(self.main_incomer_combo.get())
        olr_required = flexible_normalize(self.olr_combo.get())
        indicator_light = flexible_normalize(self.light_combo.get())

        # Store current search parameters for Material Calculator
        self.current_search_params = {
            'pump_type': self.pump_type_combo.get(),
            'pump_current': pump_current,
            'switch_gear_make': self.switch_gear_make_combo.get(),
            'num_pumps': self.pumps_combo.get(),
            'num_vfd': self.vfd_combo.get(),
            'vfd_make': self.vfd_make_combo.get(),
            'bypass': self.bypass_combo.get(),
            'panel_type': self.panel_type_combo.get(),
            'panel_size': self.size_combo.get(),
            'panel_class': self.panel_class_combo.get(),
            'main_incomer': self.main_incomer_combo.get(),
            'olr_required': self.olr_combo.get(),
            'indicator_light': self.light_combo.get()
        }

        found_base_price = None

        print(f"DEBUG: Searching in CSV: {self.products_csv_path}")
        print(f"DEBUG: CSV exists: {os.path.exists(self.products_csv_path)}")

        if os.path.exists(self.products_csv_path):
            try:
                with open(self.products_csv_path, mode="r", encoding="utf-8-sig") as f:
                    reader = list(csv.reader(f))
                    print(f"DEBUG: CSV has {len(reader)} rows")
                    
                    if reader:
                        header_map = {}
                        first_row_norm = [re.sub(r"[^a-z0-9]", "", str(c).lower()) for c in reader[0]]
                        print(f"DEBUG: First row: {reader[0]}")
                        print(f"DEBUG: Normalized: {first_row_norm}")

                        has_header = any(
                            k in first_row_norm
                            for k in ["pumpcurrent", "current", "price", "numpumps", "pumps"]
                        )
                        print(f"DEBUG: Has header: {has_header}")

                        if has_header:
                            for idx, col_norm in enumerate(first_row_norm):
                                header_map[col_norm] = idx
                            data_rows = reader[1:]
                            print(f"DEBUG: Header map: {header_map}")
                        else:
                            data_rows = reader
                            print(f"DEBUG: No header, using all rows as data")

                        def get_val(row, aliases, default_idx):
                            for alias in aliases:
                                norm_alias = re.sub(r"[^a-z0-9]", "", alias.lower())
                                if norm_alias in header_map:
                                    idx = header_map[norm_alias]
                                    if idx < len(row):
                                        return row[idx].strip()
                            if 0 <= default_idx < len(row):
                                return row[default_idx].strip()
                            return ""

                        for r in data_rows:
                            if not r or not any(r):
                                continue

                            # Some saved rows omit pump_type even though the header includes it.
                            # Restore the missing leading field before applying header positions.
                            if (
                                has_header
                                and len(r) == len(reader[0]) - 1
                                and "pumptype" in header_map
                                and r
                                and not flexible_normalize(r[0]) in {"3phase", "1phase"}
                            ):
                                r = [""] + r

                            print(f"DEBUG: Processing row: {r}")

                            # Handle both old format (10 columns) and new format (11+ columns with pump_type)
                            if len(r) >= 11:  # New format with pump_type
                                try:
                                    csv_current_val = get_val(r, ["pump_current", "current", "pump current", "amp"], 1)
                                    csv_current = float(csv_current_val)
                                except (ValueError, TypeError):
                                    continue

                                csv_pump_type = flexible_normalize(get_val(r, ["pump_type", "type", "pump type"], 0))
                                csv_switch_gear_make = flexible_normalize(get_val(r, ["switch_gear_make", "switch gear make"], -1))
                                csv_pumps = flexible_normalize(get_val(r, ["num_pumps", "pumps", "num pumps"], 2))
                                csv_vfd = flexible_normalize(get_val(r, ["num_vfd", "vfd", "num vfd"], 3))
                                csv_vfd_make = flexible_normalize(get_val(r, ["vfd_make", "vfd make"], -1))
                                csv_bypass = flexible_normalize(get_val(r, ["bypass"], 4))
                                csv_type = flexible_normalize(get_val(r, ["panel_type", "type", "panel type"], 5))
                                csv_size = flexible_normalize(get_val(r, ["panel_size", "size", "panel size"], 6))
                                csv_class = flexible_normalize(get_val(r, ["panel_class", "class", "panel class"], 7) or "industrial")
                                csv_incomer = flexible_normalize(get_val(r, ["main_incomer", "incomer", "main incomer"], 8) or "yes")
                                csv_olr = flexible_normalize(get_val(r, ["olr_required", "olr", "olr required"], 9) or "no")
                                csv_light = flexible_normalize(get_val(r, ["indicator_light", "indicator", "light"], 10) or "no")

                                price_str = get_val(r, ["price", "base_price", "cost"], len(r) - 1)

                                print(f"DEBUG: New format - csv_current: {csv_current}, search: {pump_current}")
                                print(f"DEBUG: csv_pumps: {csv_pumps}, search: {num_pumps}")
                                print(f"DEBUG: price_str: {price_str}")

                                # Check if pump_type matches (if CSV has it)
                                pump_type_match = True
                                if csv_pump_type and pump_type:
                                    pump_type_match = csv_pump_type == pump_type
                                
                                if (
                                    pump_type_match
                                    and math.isclose(csv_current, pump_current, rel_tol=1e-5)
                                    and csv_pumps == num_pumps
                                    and csv_vfd == num_vfd
                                    and ("switchgearmake" not in header_map or csv_switch_gear_make == switch_gear_make)
                                    and ("vfdmake" not in header_map or csv_vfd_make == vfd_make)
                                    and csv_bypass == bypass
                                    and csv_type == panel_type
                                    and csv_size == panel_size
                                    and csv_class == panel_class
                                    and csv_incomer == main_incomer
                                    and csv_olr == olr_required
                                    and csv_light == indicator_light
                                ):
                                    try:
                                        found_base_price = float(price_str)
                                        print(f"DEBUG: Found match! Price: {found_base_price}")
                                    except (ValueError, TypeError):
                                        found_base_price = None
                                    break
                            
                            elif len(r) >= 10:  # Old format without pump_type
                                try:
                                    csv_current_val = get_val(r, ["pump_current", "current", "pump current", "amp"], 0)
                                    csv_current = float(csv_current_val)
                                except (ValueError, TypeError):
                                    continue

                                csv_pumps = flexible_normalize(get_val(r, ["num_pumps", "pumps", "num pumps"], 1))
                                csv_vfd = flexible_normalize(get_val(r, ["num_vfd", "vfd", "num vfd"], 2))
                                csv_bypass = flexible_normalize(get_val(r, ["bypass"], 3))
                                csv_type = flexible_normalize(get_val(r, ["panel_type", "type", "panel type"], 4))
                                csv_size = flexible_normalize(get_val(r, ["panel_size", "size", "panel size"], 5))
                                csv_class = flexible_normalize(get_val(r, ["panel_class", "class", "panel class"], 6) or "industrial")
                                csv_incomer = flexible_normalize(get_val(r, ["main_incomer", "incomer", "main incomer"], 7) or "yes")
                                csv_olr = flexible_normalize(get_val(r, ["olr_required", "olr", "olr required"], 8) or "no")
                                csv_light = flexible_normalize(get_val(r, ["indicator_light", "indicator", "light"], 9) or "no")

                                price_str = get_val(r, ["price", "base_price", "cost"], len(r) - 1)

                                print(f"DEBUG: Old format - csv_current: {csv_current}, search: {pump_current}")
                                print(f"DEBUG: csv_pumps: {csv_pumps}, search: {num_pumps}")
                                print(f"DEBUG: price_str: {price_str}")
                                
                                if (
                                    math.isclose(csv_current, pump_current, rel_tol=1e-5)
                                    and csv_pumps == num_pumps
                                    and csv_vfd == num_vfd
                                    and csv_bypass == bypass
                                    and csv_type == panel_type
                                    and csv_size == panel_size
                                    and csv_class == panel_class
                                    and csv_incomer == main_incomer
                                    and csv_olr == olr_required
                                    and csv_light == indicator_light
                                ):
                                    try:
                                        found_base_price = float(price_str)
                                        print(f"DEBUG: Found match! Price: {found_base_price}")
                                    except (ValueError, TypeError):
                                        found_base_price = None
                                    break
            except PermissionError:
                messagebox.showerror("File Reading Error", "Cannot read 'products.csv'. Please close Excel if it is open.")
                return

        if found_base_price is not None:
            selected_customer = self.customer_combo.get()
            pct_adj = self.customer_data.get(selected_customer, 0.0)
            final_price = found_base_price + (found_base_price * (pct_adj / 100.0))

            self.result_label.config(
                text=f"Final Price: Rs.{final_price:,.2f}",
                foreground="green",
                font=("Helvetica", 14, "bold"),
            )
            sign_str = f"+{pct_adj}%" if pct_adj >= 0 else f"{pct_adj}%"
            self.breakdown_label.config(
                text=f"(Base Price: Rs.{found_base_price:,.2f} | Customer Adj: {sign_str})"
            )
        else:
            self.result_label.config(
                text="Product does not exist",
                foreground="red",
                font=("Helvetica", 13, "bold"),
            )
            self.breakdown_label.config(text="")

            # Create custom dialog with 3 options
            choice_dialog = tk.Toplevel(self.winfo_toplevel())
            choice_dialog.title("Product Not Found")
            choice_dialog.geometry("400x200")
            choice_dialog.transient(self.winfo_toplevel())
            choice_dialog.grab_set()

            message = tk.Label(
                choice_dialog,
                text="Product does not exist in database.\n\nChoose an option:",
                font=("Helvetica", 11),
                justify="left"
            )
            message.pack(pady=20)

            button_frame = tk.Frame(choice_dialog)
            button_frame.pack(pady=10)

            def add_price_action():
                choice_dialog.destroy()
                # Create a custom dialog that stays on top
                price_dialog = tk.Toplevel(self.winfo_toplevel())
                price_dialog.title("Enter Price")
                price_dialog.geometry("400x150")
                price_dialog.transient(self.winfo_toplevel())
                price_dialog.grab_set()
                price_dialog.attributes('-topmost', True)  # Keep window on top
                
                # Make sure it stays on top
                price_dialog.lift()
                price_dialog.focus_force()
                
                message = tk.Label(
                    price_dialog,
                    text="Enter base price for this new configuration:",
                    font=("Helvetica", 11),
                    justify="left"
                )
                message.pack(pady=15)
                
                price_entry = ttk.Entry(price_dialog, width=25, font=("Helvetica", 12))
                price_entry.pack(pady=10)
                price_entry.focus()
                
                def on_submit():
                    new_price_str = price_entry.get().strip()
                    price_dialog.destroy()
                    
                    if new_price_str:
                        try:
                            new_price = float(new_price_str)

                            row_to_add = [
                                self.pump_type_combo.get().strip(),
                                f"{pump_current:g}",
                                self.switch_gear_make_combo.get().strip(),
                                self.pumps_combo.get().strip(),
                                self.vfd_combo.get().strip(),
                                self.vfd_make_combo.get().strip(),
                                self.bypass_combo.get().strip(),
                                self.panel_type_combo.get().strip(),
                                self.size_combo.get().strip(),
                                self.panel_class_combo.get().strip(),
                                self.main_incomer_combo.get().strip(),
                                self.olr_combo.get().strip(),
                                self.light_combo.get().strip(),
                                f"{new_price:.2f}"
                            ]

                            file_exists = os.path.exists(self.products_csv_path)
                            file_is_empty = not file_exists or os.path.getsize(self.products_csv_path) == 0

                            last_char = b"\n"
                            if file_exists and not file_is_empty:
                                with open(self.products_csv_path, mode="rb") as check_f:
                                    check_f.seek(-1, os.SEEK_END)
                                    last_char = check_f.read(1)

                            with open(self.products_csv_path, mode="a", newline="", encoding="utf-8-sig") as file:
                                if last_char not in (b"\n", b"\r"):
                                    file.write("\n")

                                writer = csv.writer(file)
                                if file_is_empty:
                                    writer.writerow(config.PRODUCTS_HEADERS)

                                writer.writerow(row_to_add)

                            selected_customer = self.customer_combo.get()
                            pct_adj = self.customer_data.get(selected_customer, 0.0)
                            final_price = new_price + (new_price * (pct_adj / 100.0))
                            sign_str = f"+{pct_adj}%" if pct_adj >= 0 else f"{pct_adj}%"

                            self.result_label.config(
                                text=f"Final Price: Rs.{final_price:,.2f}",
                                foreground="green",
                                font=("Helvetica", 14, "bold"),
                            )
                            self.breakdown_label.config(
                                text=f"(Base Price: Rs.{new_price:,.2f} | Customer Adj: {sign_str})"
                            )
                            messagebox.showinfo("Success", "New product saved successfully!")

                        except PermissionError:
                            messagebox.showerror(
                                "Permission Error",
                                "Cannot write to 'products.csv'.\nPlease close Excel before saving."
                            )
                        except ValueError:
                            messagebox.showerror("Invalid Input", "Please enter a valid numeric price.")
                
                def on_cancel():
                    price_dialog.destroy()
                
                # Enter key to submit
                price_entry.bind("<Return>", lambda event: on_submit())
                
                button_frame = tk.Frame(price_dialog)
                button_frame.pack(pady=10)
                
                submit_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=on_submit,
                    width=10,
                    bg="#4CAF50",
                    fg="white",
                    font=("Helvetica", 10, "bold")
                )
                submit_btn.pack(side="left", padx=5)
                
                cancel_btn = tk.Button(
                    button_frame,
                    text="Cancel",
                    command=on_cancel,
                    width=10,
                    bg="#f44336",
                    fg="white",
                    font=("Helvetica", 10, "bold")
                )
                cancel_btn.pack(side="left", padx=5)

            def calculate_price_action():
                choice_dialog.destroy()
                # Store search parameters for Material Calculator
                search_data = {
                    'pump_type': self.pump_type_combo.get(),
                    'pump_current': pump_current,
                    'num_pumps': self.pumps_combo.get(),
                    'num_vfd': self.vfd_combo.get(),
                    'bypass': self.bypass_combo.get(),
                    'panel_type': self.panel_type_combo.get(),
                    'panel_size': self.size_combo.get(),
                    'panel_class': self.panel_class_combo.get(),
                    'main_incomer': self.main_incomer_combo.get(),
                    'olr_required': self.olr_combo.get(),
                    'indicator_light': self.light_combo.get()
                }
                
                # Pass data to main app for Material Calculator
                self.main_app.material_calculator_data = search_data
                
                # Switch to Material & Labor Calculator tab (index 1)
                self.main_app.switch_tab(1)

            def cancel_action():
                choice_dialog.destroy()

            add_btn = tk.Button(
                button_frame,
                text="Enter Price",
                command=add_price_action,
                width=15,
                bg="#4CAF50",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            add_btn.pack(side="left", padx=5)

            calc_btn = tk.Button(
                button_frame,
                text="Calculate Price",
                command=calculate_price_action,
                width=15,
                bg="#2196F3",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            calc_btn.pack(side="left", padx=5)

            cancel_btn = tk.Button(
                button_frame,
                text="Cancel",
                command=cancel_action,
                width=15,
                bg="#f44336",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            cancel_btn.pack(side="left", padx=5)
