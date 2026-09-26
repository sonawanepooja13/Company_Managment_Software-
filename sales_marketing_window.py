import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
import webbrowser
import crm_engine

class SalesMarketingView(ttk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.user_data = main_app.user_data

        self.sales_notebook = None
        self.material_calculator_data = {}
        self.material_tab_instance = None

        self.show_product_category_selector()

    def clear_internal_workspace(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_product_category_selector(self):
        self.clear_internal_workspace()

        container = ttk.Frame(self, padding=40)
        container.pack(expand=True)

        ttk.Label(
            container, text="Select Product Category", font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))

        category_frame = ttk.Frame(container)
        category_frame.pack()

        categories = [
            "Customer CRM & Leads",
            "Saark Product Sector",
            "Booster Pump Control Panel",
            "B2B Trading",
            "STP Panel",
            "Water Meter",
            "BMS",
            "Quotation"
        ]

        for category in categories:
            button_label = (
                "Booster Pump Control Panel Desing,Materil & Price Calculator"
                if category == "Booster Pump Control Panel"
                else "B2B Marketplace"
                if category == "B2B Trading"
                else category
            )
            btn = self.main_app.create_welcome_button(
                category_frame,
                button_label,
                lambda cat=category: self.show_category_content(cat),
            )
            btn.pack(pady=10)

    def show_category_content(self, category):
        try:
            from tabs import CrmTab, MaterialTab, PriceTab

            self.clear_internal_workspace()

            if category == "Saark Product Sector":
                self.show_saark_product_sector()

            elif category == "Customer CRM & Leads":
                if self.main_app.user_has_permission("allow_crm", False):
                    tab_crm = CrmTab(self)
                    tab_crm.pack(fill="both", expand=True)
                else:
                    messagebox.showwarning("Access Denied", "You do not have permission to access Customer CRM & Leads.", parent=self.main_app.root)
                    self.show_product_category_selector()

            elif category == "Booster Pump Control Panel":
                notebook = ttk.Notebook(self)
                notebook.pack(fill="both", expand=True, padx=5, pady=5)
                self.sales_notebook = notebook
                self.material_calculator_data = {}
                self.material_tab_instance = None

                if self.main_app.user_has_permission("allow_price", True):
                    tab_price = PriceTab(notebook, self.main_app)
                    notebook.add(tab_price, text=" Price List Search ")

                if self.main_app.user_has_permission("allow_material", True):
                    tab_material = MaterialTab(notebook, self.material_calculator_data)
                    notebook.add(tab_material, text=" Material & Labor Calculator ")
                    self.material_tab_instance = tab_material

            elif category == "B2B Trading":
                self.show_b2b_trading_view()

            elif category in ["STP Panel", "Water Meter", "BMS"]:
                placeholder_frame = ttk.Frame(self, padding=40)
                placeholder_frame.pack(expand=True)

                ttk.Label(
                    placeholder_frame,
                    text=f"{category}",
                    font=("Helvetica", 16, "bold")
                ).pack(pady=(0, 20))

                ttk.Label(
                    placeholder_frame,
                    text="This module is under development.",
                    font=("Helvetica", 12)
                ).pack(pady=10)

            elif category == "Quotation":
                self.show_quotation_dialog()

        except Exception as e:
            messagebox.showerror(
                "Error Loading Category", f"Could not load {category}:\n{e}"
            )

    def show_b2b_trading_view(self):
        b2b_frame = ttk.Frame(self, padding=20)
        b2b_frame.pack(expand=True, fill="both")

        ttk.Label(
            b2b_frame,
            text="B2B Trading Platform",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            b2b_frame,
            text="Manage your B2B products and trading operations",
            font=("Helvetica", 10)
        ).pack(pady=(0, 20))

        button_frame = ttk.Frame(b2b_frame)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Buy Product",
            command=lambda: self.show_b2b_buy_products()
        ).pack(side="left", padx=10)

        ttk.Button(
            button_frame,
            text="Add Product",
            command=lambda: self.open_b2b_product_manager()
        ).pack(side="left", padx=10)

        ttk.Button(
            button_frame,
            text="View My Products",
            command=lambda: self.view_my_b2b_products()
        ).pack(side="left", padx=10)

        product_list_frame = ttk.LabelFrame(b2b_frame, text="Available Products", padding=10)
        product_list_frame.pack(fill="both", expand=True, pady=10)

        self.load_b2b_products_list(product_list_frame)

    def open_b2b_product_manager(self):
        try:
            from b2b_product_manager import open_b2b_product_manager
            open_b2b_product_manager(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Product Manager: {e}")

    def show_b2b_buy_products(self):
        try:
            from b2b_buy_products import open_b2b_buy_products
            open_b2b_buy_products(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Buy Products: {e}")

    def view_my_b2b_products(self):
        try:
            from b2b_buy_products import open_b2b_buy_products
            open_b2b_buy_products(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Products: {e}")

    def load_b2b_products_list(self, parent_frame):
        csv_file = os.path.join(
            os.path.dirname(__file__),
            "csv_data",
            "b2b",
            "b2b_products.csv"
        )

        if not os.path.exists(csv_file):
            ttk.Label(
                parent_frame,
                text="No products available yet.\nClick 'Add Product' to list your products.",
                font=("Helvetica", 10),
                justify="center"
            ).pack(expand=True)
            return

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products = list(reader)

            if not products:
                ttk.Label(
                    parent_frame,
                    text="No products available yet.\nClick 'Add Product' to list your products.",
                    font=("Helvetica", 10),
                    justify="center"
                ).pack(expand=True)
                return

            columns = ("prod_id", "Title", "SKU", "Price", "Stock", "Status")
            tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

            tree.heading("prod_id", text="ID")
            tree.heading("Title", text="Product Title")
            tree.heading("SKU", text="SKU")
            tree.heading("Price", text="Price (₹)")
            tree.heading("Stock", text="Stock")
            tree.heading("Status", text="Status")

            tree.column("prod_id", width=100)
            tree.column("Title", width=300)
            tree.column("SKU", width=120)
            tree.column("Price", width=100)
            tree.column("Stock", width=80)
            tree.column("Status", width=80)

            tree.pack(fill="both", expand=True)

            for product in products:
                tree.insert("", "end", values=(
                    product.get('prod_id', ''),
                    product.get('title', ''),
                    product.get('sku', ''),
                    product.get('base_price', ''),
                    product.get('stock_qty', ''),
                    product.get('status', '')
                ))

            # Add Edit Button
            btn_edit = ttk.Button(
                parent_frame,
                text="📝 Edit Selected Product",
                command=lambda: self.edit_selected_product(tree)
            )
            btn_edit.pack(pady=10)

            vsb = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")

        except Exception as e:
            ttk.Label(parent_frame, text=f"Error loading products: {e}").pack(expand=True)

    def edit_selected_product(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product to edit first.")
            return

        prod_id = tree.item(selected[0])["values"][0]
        try:
            from b2b_product_manager import open_b2b_product_manager
            open_b2b_product_manager(self.main_app, prod_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Product Manager for editing: {e}")

    def show_saark_product_sector(self):
        self.clear_internal_workspace()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        sector_tab = ttk.Frame(notebook, padding=20)
        product_tab = ttk.Frame(notebook)
        promotion_tab = ttk.Frame(notebook, padding=16)
        notebook.add(sector_tab, text=" 1. Select / Add Sector ")
        notebook.add(product_tab, text=" 2. Basic Product Information ")
        notebook.add(promotion_tab, text=" 3. Promotion Material Management ")

        default_sectors = (
            "Booster Pump Control Panel", "STP Panel", "Water Meter", "BMS", "Other"
        )
        sector_file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sector_list.csv")
        selected_sector = tk.StringVar()
        new_sector_name = tk.StringVar()

        def get_sectors():
            sectors = list(default_sectors)
            if os.path.exists(sector_file_path):
                with open(sector_file_path, newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
                        sector_name = (row.get("sector_name") or "").strip()
                        if sector_name and sector_name not in sectors:
                            sectors.append(sector_name)
            return sectors

        crm_engine.init_crm_db()
        promo_sector = tk.StringVar()
        promo_title = tk.StringVar()
        promo_type = tk.StringVar(value="YouTube Video")
        promo_campaign = tk.StringVar()
        promo_platform = tk.StringVar(value="YouTube")
        promo_url = tk.StringVar()
        promo_attachment = tk.StringVar()

        ttk.Label(
            promotion_tab, text="Promotion Material Management",
            font=("Helvetica", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            promotion_tab,
            text="Maintain approved corporate marketing assets. Add each link or attachment as a separate item.",
        ).pack(anchor="w", pady=(4, 14))
        promo_form = ttk.LabelFrame(promotion_tab, text=" Add Promotion Material ", padding=14)
        promo_form.pack(fill="x")
        promo_form.columnconfigure(1, weight=1)

        def promo_row(row, label, widget):
            ttk.Label(promo_form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )
            widget.grid(row=row, column=1, sticky="ew", pady=5)

        promo_sector_combo = ttk.Combobox(
            promo_form, textvariable=promo_sector, values=get_sectors(), state="readonly"
        )
        promo_row(0, "Product Sector", promo_sector_combo)
        promo_row(1, "Material Title", ttk.Entry(promo_form, textvariable=promo_title))
        promo_row(2, "Material Type", ttk.Combobox(
            promo_form, textvariable=promo_type, state="readonly",
            values=("YouTube Video", "Instagram Reel", "Instagram Photo", "Product Photo",
                    "Product Video", "Brochure / Catalogue", "Datasheet", "Case Study", "Other"),
        ))
        promo_row(3, "Campaign / Product Name", ttk.Entry(promo_form, textvariable=promo_campaign))
        promo_row(4, "Platform", ttk.Combobox(
            promo_form, textvariable=promo_platform,
            values=("YouTube", "Instagram", "Website", "LinkedIn", "WhatsApp", "Internal", "Other"),
        ))
        promo_row(5, "Published / Upload Link", ttk.Entry(promo_form, textvariable=promo_url))

        attachment_box = ttk.Frame(promo_form)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=promo_attachment).grid(row=0, column=0, sticky="ew")

        def choose_promotion_attachment():
            path = filedialog.askopenfilename(
                parent=self.main_app.root, title="Attach promotion material",
                filetypes=(
                    ("Promotion files", "*.pdf *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.gif *.webp *.mp4 *.mov *.avi *.mkv *.webm"),
                    ("All files", "*.*"),
                ),
            )
            if path:
                promo_attachment.set(path)

        ttk.Button(attachment_box, text="Attach File", command=choose_promotion_attachment).grid(
            row=0, column=1, padx=(6, 0)
        )
        promo_row(6, "Attachment", attachment_box)
        ttk.Label(promo_form, text="Notes / Approval:").grid(
            row=7, column=0, sticky="nw", padx=(0, 12), pady=5
        )
        promo_notes = tk.Text(promo_form, height=3, wrap="word")
        promo_notes.grid(row=7, column=1, sticky="ew", pady=5)

        promo_table = ttk.LabelFrame(promotion_tab, text=" Saved Promotion Materials ", padding=8)
        promo_table.pack(fill="both", expand=True, pady=(14, 0))
        promo_columns = ("id", "product_sector", "material_type", "title", "platform", "url", "attachment_path", "created_at")
        promo_tree = ttk.Treeview(promo_table, columns=promo_columns, show="headings", height=11)
        promo_headings = ("ID", "Sector", "Type", "Title", "Platform", "Link", "Attachment", "Saved On")
        for column, heading, width in zip(promo_columns, promo_headings, (55, 165, 150, 205, 100, 240, 240, 145)):
            promo_tree.heading(column, text=heading)
            promo_tree.column(column, width=width, anchor="w")
        promo_scroll_y = ttk.Scrollbar(promo_table, orient="vertical", command=promo_tree.yview)
        promo_scroll_x = ttk.Scrollbar(promo_table, orient="horizontal", command=promo_tree.xview)
        promo_tree.configure(yscrollcommand=promo_scroll_y.set, xscrollcommand=promo_scroll_x.set)
        promo_tree.grid(row=0, column=0, sticky="nsew")
        promo_scroll_y.grid(row=0, column=1, sticky="ns")
        promo_scroll_x.grid(row=1, column=0, sticky="ew")
        promo_table.columnconfigure(0, weight=1)
        promo_table.rowconfigure(0, weight=1)

        def refresh_promotion_materials():
            for item in promo_tree.get_children():
                promo_tree.delete(item)
            for row in crm_engine.fetch_promotional_materials(promo_sector.get().strip() or None):
                promo_tree.insert("", "end", values=[row[column] or "" for column in promo_columns])

        def clear_promotion_form():
            promo_title.set("")
            promo_type.set("YouTube Video")
            promo_campaign.set("")
            promo_platform.set("YouTube")
            promo_url.set("")
            promo_attachment.set("")
            promo_notes.delete("1.0", tk.END)

        def save_promotion_material():
            sector = promo_sector.get().strip()
            title = promo_title.get().strip()
            if not sector or not title:
                messagebox.showwarning("Required Information", "Select a Product Sector and enter a Material Title.", parent=self.main_app.root)
                return
            if not promo_url.get().strip() and not promo_attachment.get().strip():
                messagebox.showwarning("Link or Attachment Required", "Add a published link or attach a file before saving.", parent=self.main_app.root)
                return
            crm_engine.add_promotional_material(
                sector, title, promo_type.get().strip(), promo_campaign.get().strip(),
                promo_platform.get().strip(), promo_url.get().strip(), promo_attachment.get().strip(),
                promo_notes.get("1.0", tk.END).strip(),
            )
            refresh_promotion_materials()
            clear_promotion_form()
            messagebox.showinfo("Saved", "Promotion material saved successfully.", parent=self.main_app.root)

        def selected_promotion_values():
            selected = promo_tree.selection()
            return promo_tree.item(selected[0], "values") if selected else None

        def open_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.main_app.root)
                return
            link, attachment = values[5], values[6]
            if link:
                webbrowser.open(link)
            elif attachment and os.path.exists(attachment):
                os.startfile(attachment)
            else:
                messagebox.showwarning("File Not Found", "The saved attachment is no longer available.", parent=self.main_app.root)

        def delete_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.main_app.root)
                return
            if messagebox.askyesno("Delete Material", f"Delete '{values[3]}' from the promotion library?", parent=self.main_app.root):
                crm_engine.delete_promotional_material(int(values[0]))
                refresh_promotion_materials()

        promo_actions = ttk.Frame(promotion_tab)
        promo_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(promo_actions, text="Save Material", command=save_promotion_material).pack(side="left")
        ttk.Button(promo_actions, text="Clear Form", command=clear_promotion_form).pack(side="left", padx=6)
        ttk.Button(promo_actions, text="Refresh List", command=refresh_promotion_materials).pack(side="left")
        ttk.Button(promo_actions, text="Open Link / Attachment", command=open_promotion_material).pack(side="right")
        ttk.Button(promo_actions, text="Delete Selected", command=delete_promotion_material).pack(side="right", padx=6)
        promo_sector_combo.bind("<<ComboboxSelected>>", lambda _event: refresh_promotion_materials())
        refresh_promotion_materials()

        ttk.Label(sector_tab, text="Product Sector Setup", font=("Helvetica", 15, "bold")).pack(anchor="w")
        ttk.Label(sector_tab, text="Select an existing sector or add a new sector before entering product details.").pack(anchor="w", pady=(4, 18))
        sector_setup = ttk.LabelFrame(sector_tab, text=" Sector ", padding=16)
        sector_setup.pack(fill="x", anchor="n")
        sector_setup.columnconfigure(1, weight=1)
        ttk.Label(sector_setup, text="Select Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        sector_selector = ttk.Combobox(sector_setup, textvariable=selected_sector, values=get_sectors(), state="readonly")
        sector_selector.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(sector_setup, text="New Sector Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(sector_setup, textvariable=new_sector_name).grid(row=1, column=1, sticky="ew", pady=7)

        form_canvas = tk.Canvas(product_tab, highlightthickness=0)
        form_scrollbar = ttk.Scrollbar(
            product_tab, orient="vertical", command=form_canvas.yview
        )
        form_canvas.configure(yscrollcommand=form_scrollbar.set)
        form_scrollbar.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)

        container = ttk.Frame(form_canvas, padding=20)
        form_window = form_canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind(
            "<Configure>",
            lambda _event: form_canvas.configure(scrollregion=form_canvas.bbox("all")),
        )
        form_canvas.bind(
            "<Configure>", lambda event: form_canvas.itemconfigure(form_window, width=event.width)
        )

        def scroll_product_form(event):
            form_canvas.yview_scroll(int(-event.delta / 120), "units")

        form_canvas.bind("<Enter>", lambda _event: form_canvas.bind_all("<MouseWheel>", scroll_product_form))
        form_canvas.bind("<Leave>", lambda _event: form_canvas.unbind_all("<MouseWheel>"))
        form = ttk.LabelFrame(container, text=" Basic Product Information ", padding=16)
        form.pack(fill="x", anchor="n")
        form.columnconfigure(1, weight=1)

        fields = {
            "product_sector": tk.StringVar(),
            "product_name": tk.StringVar(),
            "sku_model_number": tk.StringVar(),
            "product_category": tk.StringVar(),
            "short_description_file": tk.StringVar(),
            "detailed_description_file": tk.StringVar(),
            "target_applications_file": tk.StringVar(),
            "input_voltage": tk.StringVar(),
            "rated_frequency": tk.StringVar(),
            "min_power_rating": tk.StringVar(),
            "max_power_rating": tk.StringVar(),
            "power_rating_unit": tk.StringVar(value="HP"),
            "starter_drive_type": tk.StringVar(),
            "enclosure_ip_rating": tk.StringVar(),
            "pump_support_capacity": tk.StringVar(),
            "min_pressure": tk.StringVar(),
            "max_pressure": tk.StringVar(),
            "pressure_unit": tk.StringVar(value="bar"),
            "user_interface_display": tk.StringVar(),
            "product_images": tk.StringVar(),
            "datasheet_manual": tk.StringVar(),
            "wiring_sld": tk.StringVar(),
            "promotional_video": tk.StringVar(),
            "photo_name": tk.StringVar(),
            "photo_description": tk.StringVar(),
            "photo_attachment": tk.StringVar(),
            "setting_video_type": tk.StringVar(),
            "setting_video_details": tk.StringVar(),
            "setting_video_attachment": tk.StringVar(),
        }
        multi_selects = {}

        def refresh_sector_selectors():
            sectors = get_sectors()
            sector_selector["values"] = sectors
            basic_sector_combo["values"] = sectors
            promo_sector_combo["values"] = sectors

        def use_selected_sector(_event=None):
            fields["product_sector"].set(selected_sector.get())
            notebook.select(product_tab)

        def add_sector():
            sector_name = new_sector_name.get().strip()
            if not sector_name:
                messagebox.showwarning("Sector Name Required", "Enter a new sector name first.", parent=self.main_app.root)
                return
            sectors = get_sectors()
            if sector_name not in sectors:
                with open(sector_file_path, "a", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("sector_name",))
                    if os.path.getsize(sector_file_path) == 0:
                        writer.writeheader()
                    writer.writerow({"sector_name": sector_name})
            selected_sector.set(sector_name)
            fields["product_sector"].set(sector_name)
            new_sector_name.set("")
            refresh_sector_selectors()
            notebook.select(product_tab)

        sector_selector.bind("<<ComboboxSelected>>", use_selected_sector)
        ttk.Button(sector_setup, text="Add Sector", command=add_sector).grid(
            row=2, column=1, sticky="e", pady=(10, 0)
        )

        def add_text_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Entry(form, textvariable=fields[field]).grid(
                row=row, column=1, sticky="ew", pady=7
            )

        def add_attachment_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(form)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(
                row=0, column=0, sticky="ew"
            )

            def choose_file():
                path = filedialog.askopenfilename(
                    parent=self.main_app.root,
                    title=f"Attach {label}",
                    filetypes=(
                        ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                        ("All files", "*.*"),
                    ),
                )
                if path:
                    fields[field].set(path)

            ttk.Button(attachment_box, text="Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        def add_dropdown_field(section, row, label, field, values):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Combobox(
                section, textvariable=fields[field], values=values, state="readonly"
            ).grid(row=row, column=1, sticky="ew", pady=7)

        def add_checklist(section, row, label, field, options):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="nw", padx=(0, 12), pady=7
            )
            choice_box = ttk.Frame(section)
            choice_box.grid(row=row, column=1, sticky="ew", pady=4)
            selected_options = []
            for index, option in enumerate(options):
                option_var = tk.BooleanVar()
                ttk.Checkbutton(choice_box, text=option, variable=option_var).grid(
                    row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=2
                )
                selected_options.append((option, option_var))
            multi_selects[field] = selected_options

        def add_file_field(section, row, label, field, *, multiple=False, filetypes=None):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(section)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(row=0, column=0, sticky="ew")

            def choose_file():
                selected_filetypes = filetypes or (
                    ("Documents and images", "*.pdf *.doc *.docx *.jpg *.jpeg *.png *.bmp"),
                    ("All files", "*.*"),
                )
                if multiple:
                    paths = filedialog.askopenfilenames(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if paths:
                        fields[field].set(" | ".join(paths))
                else:
                    path = filedialog.askopenfilename(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if path:
                        fields[field].set(path)

            ttk.Button(attachment_box, text="Attach Files" if multiple else "Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        ttk.Label(form, text="Product Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        basic_sector_combo = ttk.Combobox(
            form, textvariable=fields["product_sector"], values=get_sectors(), state="readonly"
        )
        basic_sector_combo.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Name / Title:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["product_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="SKU / Model Number:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["sku_model_number"]).grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Category / Sub-category:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Combobox(
            form, textvariable=fields["product_category"],
            values=("Control Panel", "Pump", "Water Treatment", "Water Metering", "Automation", "Other")
        ).grid(row=3, column=1, sticky="ew", pady=7)
        add_attachment_field(4, "Short Description", "short_description_file")
        add_attachment_field(5, "Detailed Description / Features", "detailed_description_file")
        add_attachment_field(6, "Target Applications", "target_applications_file")

        electrical = ttk.LabelFrame(container, text=" 2. Electrical & Power Specifications ", padding=16)
        electrical.pack(fill="x", anchor="n", pady=(14, 0))
        electrical.columnconfigure(1, weight=1)
        add_dropdown_field(electrical, 0, "Input Voltage", "input_voltage", ("230V 1-Phase", "415V 3-Phase", "110V"))
        add_dropdown_field(electrical, 1, "Rated Frequency", "rated_frequency", ("50 Hz", "60 Hz", "50/60 Hz Dual"))
        ttk.Label(electrical, text="Power Rating Range:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        power_box = ttk.Frame(electrical)
        power_box.grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Entry(power_box, textvariable=fields["min_power_rating"], width=12).pack(side="left")
        ttk.Label(power_box, text=" to ").pack(side="left")
        ttk.Entry(power_box, textvariable=fields["max_power_rating"], width=12).pack(side="left")
        ttk.Combobox(power_box, textvariable=fields["power_rating_unit"], values=("HP", "kW"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_dropdown_field(electrical, 3, "Starter / Drive Type", "starter_drive_type", ("DOL", "Star-Delta", "Integrated VFD", "Soft Starter"))
        add_dropdown_field(electrical, 4, "Enclosure / IP Protection Rating", "enclosure_ip_rating", ("IP54", "IP55", "IP65", "NEMA 4X"))

        pump = ttk.LabelFrame(container, text=" 3. Pump Configuration & Control Parameters ", padding=16)
        pump.pack(fill="x", anchor="n", pady=(14, 0))
        pump.columnconfigure(1, weight=1)
        add_dropdown_field(pump, 0, "Pump Support Capacity", "pump_support_capacity", ("1 Pump", "2 Pumps [1W+1S]", "3 Pumps", "4+ Multi-Cascade"))
        add_checklist(pump, 1, "Control Modes", "control_modes", ("Constant Pressure", "Auto-Alternation", "Duty/Assist/Standby", "Manual Override"))
        add_checklist(pump, 2, "Pressure Sensor Compatibility", "pressure_sensor_compatibility", ("4-20 mA", "0-10V", "RS-485 Digital", "Pressure Switch"))
        ttk.Label(pump, text="Supported Pressure Range:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        pressure_box = ttk.Frame(pump)
        pressure_box.grid(row=3, column=1, sticky="ew", pady=7)
        ttk.Entry(pressure_box, textvariable=fields["min_pressure"], width=12).pack(side="left")
        ttk.Label(pressure_box, text=" to ").pack(side="left")
        ttk.Entry(pressure_box, textvariable=fields["max_pressure"], width=12).pack(side="left")
        ttk.Combobox(pressure_box, textvariable=fields["pressure_unit"], values=("bar", "PSI"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_checklist(pump, 4, "Level Sensor Inputs", "level_sensor_inputs", ("Float Switch", "Ultrasonic", "Conductive Probes", "Dry Run Float"))

        smart = ttk.LabelFrame(container, text=" 4. Smart Features, Display & Connectivity ", padding=16)
        smart.pack(fill="x", anchor="n", pady=(14, 0))
        smart.columnconfigure(1, weight=1)
        add_dropdown_field(smart, 0, "User Interface / Display", "user_interface_display", ("Touchscreen HMI", "Multi-line LCD", "7-Segment LED", "Indicator LEDs"))
        add_checklist(smart, 1, "Communication Protocols", "communication_protocols", ("RS-485 Modbus RTU", "Modbus TCP/IP", "BACnet", "Ethernet"))
        add_checklist(smart, 2, "IoT / Cloud Features", "iot_cloud_features", ("GSM/4G Remote Telemetry", "Wi-Fi Dashboard", "Mobile App Support", "SMS Alerts"))
        add_checklist(smart, 3, "Data Logging", "data_logging", ("Historical Fault Log", "Run-Hour Meter", "Pressure Trends"))

        protections = ttk.LabelFrame(container, text=" 5. Protections & Alarms ", padding=16)
        protections.pack(fill="x", anchor="n", pady=(14, 0))
        protections.columnconfigure(1, weight=1)
        add_checklist(protections, 0, "Electrical Protections", "electrical_protections", ("Overload", "Under/Over-Voltage", "Phase Failure", "Phase Reversal", "Short Circuit"))
        add_checklist(protections, 1, "Hydraulic Protections", "hydraulic_protections", ("Dry Run Protection (Auto-Reset)", "High/Low Pressure Cutoff", "Pipe Burst / Leakage Detection", "Anti-Seize Cycling"))

        media = ttk.LabelFrame(container, text=" 6. Media, Documents & Compliance ", padding=16)
        media.pack(fill="x", anchor="n", pady=(14, 0))
        media.columnconfigure(1, weight=1)
        add_file_field(media, 0, "Product Images", "product_images", multiple=True)
        add_file_field(media, 1, "Datasheet / Manual", "datasheet_manual")
        add_file_field(media, 2, "Wiring / Single Line Diagram (SLD)", "wiring_sld")
        add_checklist(media, 3, "Certifications", "certifications", ("CE", "RoHS", "ISO 9001", "CPRI Approved"))

        promotion = ttk.LabelFrame(container, text=" Promotional Material ", padding=16)
        promotion.pack(fill="x", anchor="n", pady=(14, 0))
        promotion.columnconfigure(1, weight=1)
        video_filetypes = (
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.webm"),
            ("All files", "*.*"),
        )
        add_file_field(promotion, 0, "Add Video", "promotional_video", filetypes=video_filetypes)
        ttk.Label(promotion, text="Photo Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(promotion, text="Photo Description:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_description"]).grid(row=2, column=1, sticky="ew", pady=7)
        add_file_field(
            promotion, 3, "Attach Photo", "photo_attachment",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All files", "*.*")),
        )
        add_dropdown_field(
            promotion, 4, "Setting Video", "setting_video_type",
            ("Installation / Setup", "Configuration", "Commissioning", "Operation", "Troubleshooting", "Other"),
        )
        ttk.Label(promotion, text="Setting Video Details:").grid(row=5, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["setting_video_details"]).grid(row=5, column=1, sticky="ew", pady=7)
        add_file_field(promotion, 6, "Attach Setting Video", "setting_video_attachment", filetypes=video_filetypes)

        saved_products = ttk.LabelFrame(container, text=" Saved Products — Select a row to edit ", padding=10)
        saved_products.pack(fill="both", expand=True, anchor="n", pady=(14, 0))
        product_columns = ("product_sector", "product_category", "product_name", "sku_model_number")
        products_tree = ttk.Treeview(saved_products, columns=product_columns, show="headings", height=8)
        for column, label in zip(product_columns, ("Sector", "Category", "Product Name", "SKU / Model No.")):
            products_tree.heading(column, text=label)
            products_tree.column(column, width=190, anchor="w")
        products_scrollbar = ttk.Scrollbar(saved_products, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=products_scrollbar.set)
        products_scrollbar.pack(side="right", fill="y")
        products_tree.pack(side="left", fill="both", expand=True)
        selected_record_index = {"value": None}

        def product_headers():
            return tuple(fields) + tuple(multi_selects)

        def read_product_records():
            file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sectors.csv")
            if not os.path.exists(file_path):
                return []
            with open(file_path, newline="", encoding="utf-8") as file:
                return list(csv.DictReader(file))

        def write_product_records(records):
            file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sectors.csv")
            with tempfile.NamedTemporaryFile(
                "w", newline="", encoding="utf-8", delete=False, dir=self.main_app.config.CSV_DIR
            ) as file:
                temporary_path = file.name
                writer = csv.DictWriter(file, fieldnames=product_headers(), extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
            os.replace(temporary_path, file_path)

        def current_product_record():
            product_name = fields["product_name"].get().strip()
            if not product_name:
                messagebox.showwarning(
                    "Product Name Required",
                    "Enter the Product Name / Title before saving.",
                    parent=self.main_app.root,
                )
                return None
            record = {key: value.get().strip() for key, value in fields.items()}
            record.update({
                key: "; ".join(option for option, value in options if value.get())
                for key, options in multi_selects.items()
            })
            return record

        def clear_product_sector_form():
            for value in fields.values():
                value.set("")
            fields["power_rating_unit"].set("HP")
            fields["pressure_unit"].set("bar")
            for options in multi_selects.values():
                for _option, value in options:
                    value.set(False)
            selected_record_index["value"] = None
            for item in products_tree.selection():
                products_tree.selection_remove(item)

        def load_saved_products():
            for item in products_tree.get_children():
                products_tree.delete(item)
            for index, record in enumerate(read_product_records()):
                products_tree.insert(
                    "", "end", iid=str(index), values=[record.get(column, "") for column in product_columns]
                )

        def load_selected_product(_event=None):
            selected = products_tree.selection()
            if not selected:
                return
            index = int(selected[0])
            records = read_product_records()
            if index >= len(records):
                return
            record = records[index]
            for key, value in fields.items():
                value.set(record.get(key, ""))
            for key, options in multi_selects.items():
                selected_options = {item.strip() for item in record.get(key, "").split(";") if item.strip()}
                for option, value in options:
                    value.set(option in selected_options)
            selected_record_index["value"] = index

        def add_product():
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            records.append(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Saved", "Product added successfully.", parent=self.main_app.root)

        def update_selected_product():
            index = selected_record_index["value"]
            if index is None:
                messagebox.showwarning("Select Product", "Select a saved product to edit first.", parent=self.main_app.root)
                return
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            if index >= len(records):
                messagebox.showwarning("Product Not Found", "Reload the saved product list and try again.", parent=self.main_app.root)
                return
            records[index].update(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Updated", "Product updated successfully.", parent=self.main_app.root)

        products_tree.bind("<<TreeviewSelect>>", load_selected_product)
        load_saved_products()

        actions = ttk.Frame(container)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="Clear / Add New", command=clear_product_sector_form).pack(
            side="right"
        )
        ttk.Button(actions, text="Update Selected Product", command=update_selected_product).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(actions, text="Add Product", command=add_product).pack(
            side="right", padx=(0, 8)
        )

    def add_text_field(self, row, label, field):
        ttk.Label(self, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        ttk.Entry(self, textvariable=field).grid(
            row=row, column=1, sticky="ew", pady=7
        )

    def add_attachment_field(self, row, label, field):
        ttk.Label(self, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        attachment_box = ttk.Frame(self)
        attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=field).grid(
            row=0, column=0, sticky="ew"
        )

        def choose_file():
            path = filedialog.askopenfilename(
                parent=self.main_app.root,
                title=f"Attach {label}",
                filetypes=(
                    ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                    ("All files", "*.*"),
                ),
            )
            if path:
                field.set(path)

        ttk.Button(attachment_box, text="Attach File", command=choose_file).grid(
            row=0, column=1, padx=(6, 0)
        )

    def add_dropdown_field(self, section, row, label, field, values):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        ttk.Combobox(
            section, textvariable=field, values=values, state="readonly"
        ).grid(row=row, column=1, sticky="ew", pady=7)

    def add_checklist(self, section, row, label, field, options):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 12), pady=7
        )
        choice_box = ttk.Frame(section)
        choice_box.grid(row=row, column=1, sticky="ew", pady=4)
        selected_options = []
        for index, option in enumerate(options):
            option_var = tk.BooleanVar()
            ttk.Checkbutton(choice_box, text=option, variable=option_var).grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=2
            )
            selected_options.append((option, option_var))
        return selected_options

    def add_file_field(self, section, row, label, field, *, multiple=False, filetypes=None):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        attachment_box = ttk.Frame(section)
        attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=field).grid(row=0, column=0, sticky="ew")

        def choose_file():
            selected_filetypes = filetypes or (
                ("Documents and images", "*.pdf *.doc *.docx *.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            )
            if multiple:
                paths = filedialog.askopenfilenames(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                if paths:
                    field.set(" | ".join(paths))
            else:
                path = filedialog.askopenfilename(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                if path:
                    field.set(path)

        ttk.Button(attachment_box, text="Attach Files" if multiple else "Attach File", command=choose_file).grid(
            row=0, column=1, padx=(6, 0)
        )

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import os
import webbrowser
from datetime import date, timedelta

import crm_engine
import quotation_manager

class SalesMarketingView(ttk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.user_data = main_app.user_data

        self.sales_notebook = None
        self.material_calculator_data = {}
        self.material_tab_instance = None

        self.show_product_category_selector()

    def clear_internal_workspace(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_product_category_selector(self):
        self.clear_internal_workspace()

        container = ttk.Frame(self, padding=40)
        container.pack(expand=True)

        ttk.Label(
            container, text="Select Product Category", font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))

        category_frame = ttk.Frame(container)
        category_frame.pack()

        categories = [
            "Customer CRM & Leads",
            "Saark Product Sector",
            "Booster Pump Control Panel",
            "B2B Trading",
            "STP Panel",
            "Water Meter",
            "BMS",
            "Quotation"
        ]

        for category in categories:
            button_label = (
                "Booster Pump Control Panel Desing,Materil & Price Calculator"
                if category == "Booster Pump Control Panel"
                else "B2B Marketplace"
                if category == "B2B Trading"
                else category
            )
            btn = self.main_app.create_welcome_button(
                category_frame,
                button_label,
                lambda cat=category: self.show_category_content(cat),
            )
            btn.pack(pady=10)

    def show_category_content(self, category):
        try:
            from tabs import CrmTab, MaterialTab, PriceTab

            self.clear_internal_workspace()

            if category == "Saark Product Sector":
                self.show_saark_product_sector()

            elif category == "Customer CRM & Leads":
                if self.main_app.user_has_permission("allow_crm", False):
                    tab_crm = CrmTab(self)
                    tab_crm.pack(fill="both", expand=True)
                else:
                    messagebox.showwarning("Access Denied", "You do not have permission to access Customer CRM & Leads.", parent=self.main_app.root)
                    self.show_product_category_selector()

            elif category == "Booster Pump Control Panel":
                notebook = ttk.Notebook(self)
                notebook.pack(fill="both", expand=True, padx=5, pady=5)
                self.sales_notebook = notebook
                self.material_calculator_data = {}
                self.material_tab_instance = None

                if self.main_app.user_has_permission("allow_price", True):
                    tab_price = PriceTab(notebook, self.main_app)
                    notebook.add(tab_price, text=" Price List Search ")

                if self.main_app.user_has_permission("allow_material", True):
                    tab_material = MaterialTab(notebook, self.material_calculator_data)
                    notebook.add(tab_material, text=" Material & Labor Calculator ")
                    self.material_tab_instance = tab_material

            elif category == "B2B Trading":
                self.show_b2b_trading_view()

            elif category in ["STP Panel", "Water Meter", "BMS"]:
                placeholder_frame = ttk.Frame(self, padding=40)
                placeholder_frame.pack(expand=True)

                ttk.Label(
                    placeholder_frame,
                    text=f"{category}",
                    font=("Helvetica", 16, "bold")
                ).pack(pady=(0, 20))

                ttk.Label(
                    placeholder_frame,
                    text="This module is under development.",
                    font=("Helvetica", 12)
                ).pack(pady=10)

            elif category == "Quotation":
                self.show_quotation_dialog()

        except Exception as e:
            messagebox.showerror(
                "Error Loading Category", f"Could not load {category}:\n{e}"
            )

    def show_b2b_trading_view(self):
        b2b_frame = ttk.Frame(self, padding=20)
        b2b_frame.pack(expand=True, fill="both")

        ttk.Label(
            b2b_frame,
            text="B2B Trading Platform",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            b2b_frame,
            text="Manage your B2B products and trading operations",
            font=("Helvetica", 10)
        ).pack(pady=(0, 20))

        button_frame = ttk.Frame(b2b_frame)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Buy Product",
            command=lambda: self.show_b2b_buy_products()
        ).pack(side="left", padx=10)

        ttk.Button(
            button_frame,
            text="Add Product",
            command=lambda: self.open_b2b_product_manager()
        ).pack(side="left", padx=10)

        ttk.Button(
            button_frame,
            text="View My Products",
            command=lambda: self.view_my_b2b_products()
        ).pack(side="left", padx=10)

        product_list_frame = ttk.LabelFrame(b2b_frame, text="Available Products", padding=10)
        product_list_frame.pack(fill="both", expand=True, pady=10)

        self.load_b2b_products_list(product_list_frame)

    def open_b2b_product_manager(self):
        try:
            from b2b_product_manager import open_b2b_product_manager
            open_b2b_product_manager(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Product Manager: {e}")

    def show_b2b_buy_products(self):
        try:
            from b2b_buy_products import open_b2b_buy_products
            open_b2b_buy_products(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Buy Products: {e}")

    def view_my_b2b_products(self):
        try:
            from b2b_buy_products import open_b2b_buy_products
            open_b2b_buy_products(self.main_app)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Products: {e}")

    def _add_quotation_window_controls(
        self, parent, window, normal_geometry, modal=False
    ):
        """Add minimize, maximize, and restore controls to a quotation window."""
        controls = ttk.Frame(parent)
        controls.pack(side="right")
        restore_geometry = {"value": normal_geometry}
        try:
            transient_master = window.master if window.wm_transient() else None
        except tk.TclError:
            transient_master = None

        def release_grab():
            if not modal:
                return
            try:
                window.grab_release()
            except tk.TclError:
                pass

        def restore_grab(event=None):
            if not modal or (event is not None and event.widget is not window):
                return
            try:
                if window.state() not in ("iconic", "withdrawn"):
                    window.grab_set()
            except tk.TclError:
                pass

        def restore_transient():
            if transient_master is None:
                return
            try:
                window.transient(transient_master)
            except tk.TclError:
                pass

        def minimize_window():
            release_grab()
            current_geometry = window.geometry()
            if current_geometry:
                restore_geometry["value"] = current_geometry
            try:
                # Windows Tkinter does not allow iconify() on transient windows.
                # Clear the relationship only while the window is minimized.
                if transient_master is not None:
                    window.wm_transient("")
                window.iconify()
            except tk.TclError:
                # Keep the control usable even if a Tk build still rejects
                # iconify(); Restore will use deiconify() to show the window.
                window.withdraw()

        def restore_window():
            try:
                # Deiconify before restoring the owner relationship. This is
                # required on Windows when the parent is temporarily hidden.
                if transient_master is not None:
                    window.wm_transient("")
                window.deiconify()
                window.state("normal")
                window.update_idletasks()
            except tk.TclError:
                pass
            try:
                if transient_master is not None and transient_master.winfo_ismapped():
                    window.transient(transient_master)
            except tk.TclError:
                pass
            if restore_geometry["value"]:
                window.geometry(restore_geometry["value"])
            try:
                window.lift()
            except tk.TclError:
                pass
            restore_grab()

        def maximize_window():
            try:
                if window.state() == "zoomed":
                    restore_grab()
                    return
                current_geometry = window.geometry()
                if current_geometry:
                    restore_geometry["value"] = current_geometry
                window.state("zoomed")
            except tk.TclError:
                # Fallback for platforms that do not support the zoomed state.
                window.geometry(
                    f"{window.winfo_screenwidth()}x{window.winfo_screenheight()}+0+0"
                )
            restore_grab()

        def handle_unmap(event=None):
            if event is not None and event.widget is not window:
                return
            try:
                if window.state() in ("iconic", "withdrawn"):
                    release_grab()
            except tk.TclError:
                pass

        # Native title-bar minimize actions must also release and restore the
        # modal grab; otherwise the quotation form can remain inaccessible.
        window.bind("<Map>", restore_grab)
        window.bind("<Unmap>", handle_unmap)

        ttk.Button(
            controls, text="Minimize", command=minimize_window
        ).pack(side="right", padx=(6, 0))
        ttk.Button(
            controls, text="Maximize", command=maximize_window
        ).pack(side="right", padx=(6, 0))
        ttk.Button(
            controls, text="Restore", command=restore_window
        ).pack(side="right")


    def show_quotation_dialog(self, quotation_no=None):
        """Create a quotation for a customer (or edit an existing one).

        Quotations are stored customer-wise in csv_data/quotation - one CSV
        file per customer, one row per quoted item - so the complete quotation
        history of a customer stays together.
        """
        existing = None
        if quotation_no:
            existing = quotation_manager.get_quotation(quotation_no)
            if existing is None:
                messagebox.showwarning("Edit Quotation",
                                       f"Quotation {quotation_no} was not found.",
                                       parent=self.main_app.root)
                return
        dialog = tk.Toplevel(self.main_app.root)
        dialog.title("Edit Quotation" if existing else "Create New Quotation")
        dialog.geometry("1320x900")
        dialog.minsize(1100, 760)
        dialog.resizable(True, True)
        dialog.transient(self.main_app.root)
        dialog.grab_set()

        # The quotation form is taller than a small screen, so the form body
        # scrolls.  The action bar is a sibling of the canvas (see below) and
        # stays pinned to the bottom, so Save / Print never scroll out of view.
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        page_canvas = tk.Canvas(dialog, highlightthickness=0, borderwidth=0)
        page_canvas.grid(row=0, column=0, sticky="nsew")
        page_scrollbar = ttk.Scrollbar(
            dialog, orient="vertical", command=page_canvas.yview
        )
        page_canvas.configure(yscrollcommand=page_scrollbar.set)
        page_scrollbar.grid(row=0, column=1, sticky="ns")

        main_frame = ttk.Frame(page_canvas, padding=16)
        main_frame_window = page_canvas.create_window(
            (0, 0), window=main_frame, anchor="nw"
        )
        main_frame.bind(
            "<Configure>",
            lambda _event: page_canvas.configure(scrollregion=page_canvas.bbox("all")),
        )
        page_canvas.bind(
            "<Configure>",
            lambda event: page_canvas.itemconfigure(
                main_frame_window, width=event.width
            ),
        )

        def scroll_quotation_page(event):
            try:
                page_canvas.yview_scroll(int(-event.delta / 120), "units")
            except tk.TclError:
                pass

        page_canvas.bind(
            "<Enter>",
            lambda _event: page_canvas.bind_all("<MouseWheel>", scroll_quotation_page),
        )
        page_canvas.bind(
            "<Leave>", lambda _event: page_canvas.unbind_all("<MouseWheel>")
        )

        title_header = ttk.Frame(main_frame)
        title_header.pack(fill="x", pady=(0, 12))
        ttk.Label(
            title_header,
            text="Edit Quotation" if existing else "Create New Quotation",
            font=("Helvetica", 16, "bold"),
        ).pack(side="left")
        self._add_quotation_window_controls(
            title_header, dialog, "1320x900", modal=True
        )

        header = existing or {}
        customer_name = tk.StringVar(value=header.get("customer_name", ""))
        customer_contact_person = tk.StringVar(
            value=header.get("customer_contact_person", "")
        )
        customer_email = tk.StringVar(value=header.get("customer_email", ""))
        customer_phone = tk.StringVar(value=header.get("customer_phone", ""))
        customer_gstin = tk.StringVar(value=header.get("customer_gstin", ""))
        customer_address = tk.StringVar(value=header.get("customer_address", ""))
        customer_type = tk.StringVar(value=header.get("customer_type", "Quotation"))
        quotation_no = tk.StringVar(
            value=header.get("quotation_no") or quotation_manager.next_quotation_number()
        )
        quotation_date = tk.StringVar(
            value=header.get("quotation_date") or date.today().isoformat()
        )
        valid_until = tk.StringVar(
            value=header.get("valid_until")
            or (date.today() + timedelta(days=quotation_manager.DEFAULT_VALIDITY_DAYS)).isoformat()
        )
        challan_no = tk.StringVar(value=header.get("challan_no", ""))
        challan_date = tk.StringVar(value=header.get("challan_date", ""))
        lr_no = tk.StringVar(value=header.get("lr_no", ""))
        delivery_mode = tk.StringVar(value=header.get("delivery_mode", ""))
        rev_charge = tk.StringVar(value=header.get("rev_charge", "No"))
        ship_to = tk.StringVar(value=header.get("ship_to", ""))
        distance_for_eway_bill = tk.StringVar(
            value=header.get("distance_for_eway_bill", "")
        )
        place_of_supply = tk.StringVar(value=header.get("place_of_supply", ""))
        status = tk.StringVar(value=header.get("status") or "Draft")
        tax_percent = tk.StringVar(
            value=str(header.get("tax_percent") or f"{quotation_manager.DEFAULT_TAX_PERCENT:g}")
        )

        def fill_customer_details(_event=None):
            """Fill the customer card from the saved CRM company record.

            The CRM stores the company tax id in its "GST Number" field and
            the quotation card shows the very same value as "GSTIN / PAN", so
            the CRM GST data is copied straight into GSTIN / PAN.  Values are
            only overwritten when the CRM actually holds one, so anything the
            user typed by hand is never discarded.
            """
            details = quotation_manager.load_customer_details(customer_name.get())
            if not details:
                return
            for key, variable in (
                ("customer_contact_person", customer_contact_person),
                ("customer_email", customer_email),
                ("customer_phone", customer_phone),
                ("customer_gstin", customer_gstin),
                ("customer_address", customer_address),
            ):
                value = details.get(key, "")
                if value:
                    variable.set(value)

        pending_fill = None

        def schedule_customer_fill(*_args):
            """Re-run the auto-fill shortly after the customer name stops changing."""
            nonlocal pending_fill
            if pending_fill is not None:
                try:
                    dialog.after_cancel(pending_fill)
                except Exception:
                    pass
            pending_fill = dialog.after(400, fill_customer_details)

        top_cards = ttk.Frame(main_frame)
        top_cards.pack(fill="x", pady=(0, 12))
        top_cards.columnconfigure(0, weight=1)
        top_cards.columnconfigure(1, weight=1)

        customer_card = ttk.LabelFrame(
            top_cards, text=" Customer Information ", padding=12
        )
        customer_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        customer_card.columnconfigure(1, weight=1)

        quotation_card = ttk.LabelFrame(
            top_cards, text=" Quotation Detail ", padding=12
        )
        quotation_card.grid(row=0, column=1, sticky="nsew")
        quotation_card.columnconfigure(1, weight=1)

        def add_card_field(parent, row, label, variable, width=26):
            ttk.Label(parent, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=5
            )
            ttk.Entry(parent, textvariable=variable, width=width).grid(
                row=row, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5
            )

        ttk.Label(customer_card, text="M/S. *:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        customer_combo = ttk.Combobox(
            customer_card, textvariable=customer_name, width=26,
            values=quotation_manager.load_customers(),
        )
        customer_combo.grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5
        )
        customer_combo.bind("<<ComboboxSelected>>", fill_customer_details)
        customer_combo.bind("<Return>", fill_customer_details)
        customer_combo.bind("<FocusOut>", fill_customer_details)
        # Also fill when the company name is typed instead of picked, so the
        # saved CRM GST data reaches GSTIN / PAN either way.
        customer_name.trace_add("write", schedule_customer_fill)
        add_card_field(customer_card, 1, "Address", customer_address)
        add_card_field(customer_card, 2, "Contact Person", customer_contact_person)
        add_card_field(customer_card, 3, "Phone No", customer_phone)
        add_card_field(customer_card, 4, "Email", customer_email)
        add_card_field(customer_card, 5, "GSTIN / PAN", customer_gstin)
        ttk.Label(customer_card, text="Rev. Charge:").grid(
            row=6, column=0, sticky="w", padx=(0, 8), pady=5
        )
        ttk.Combobox(
            customer_card, textvariable=rev_charge, values=("No", "Yes"),
            state="readonly", width=24,
        ).grid(row=6, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5)
        ttk.Label(customer_card, text="Ship To:").grid(
            row=7, column=0, sticky="w", padx=(0, 8), pady=5
        )
        ttk.Combobox(
            customer_card, textvariable=ship_to,
            values=("--", "Same as Customer", "Other"), width=24,
        ).grid(row=7, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5)
        add_card_field(customer_card, 8, "Distance for e-way bill (in km)", distance_for_eway_bill)
        add_card_field(customer_card, 9, "Place of Supply *", place_of_supply)

        ttk.Label(quotation_card, text="Type:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        ttk.Combobox(
            quotation_card, textvariable=customer_type,
            values=("Quotation", "Sales Quotation", "Service Quotation"),
            state="readonly", width=24,
        ).grid(row=0, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5)
        add_card_field(quotation_card, 1, "Quotation No. *", quotation_no, 18)
        add_card_field(quotation_card, 2, "Quotation Date *", quotation_date, 18)
        add_card_field(quotation_card, 3, "Challan No.", challan_no, 18)
        add_card_field(quotation_card, 4, "Challan Date", challan_date, 18)
        add_card_field(quotation_card, 5, "L.R. No.", lr_no, 18)
        ttk.Label(quotation_card, text="Delivery:").grid(
            row=6, column=0, sticky="w", padx=(0, 8), pady=5
        )
        ttk.Combobox(
            quotation_card, textvariable=delivery_mode,
            values=("Select Delivery Mode", "Door Delivery", "Pickup", "Courier"), width=24,
        ).grid(row=6, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5)
        add_card_field(quotation_card, 7, "Valid Until", valid_until, 18)
        ttk.Label(quotation_card, text="Status:").grid(
            row=8, column=0, sticky="w", padx=(0, 8), pady=5
        )
        ttk.Combobox(
            quotation_card, textvariable=status, state="readonly", width=24,
            values=list(quotation_manager.STATUSES),
        ).grid(row=8, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=5)
        add_card_field(quotation_card, 9, "Tax %", tax_percent, 18)

        items_frame = ttk.LabelFrame(main_frame, text=" Product Items ", padding=12)
        items_frame.pack(fill="both", expand=True, pady=(0, 12))

        # Products come from the price list; any custom item can be typed too.
        product_catalog = quotation_manager.load_products()
        product_labels = [product["label"] for product in product_catalog]
        product_choice = tk.StringVar()
        item_title = tk.StringVar()
        item_description = tk.StringVar()
        item_hsn = tk.StringVar()
        item_capacity = tk.StringVar()
        item_quantity = tk.StringVar(value="1")
        item_rate = tk.StringVar(value="0.00")
        item_discount = tk.StringVar(value="0")

        entry_row = ttk.Frame(items_frame)
        entry_row.pack(fill="x", pady=(0, 8))
        entry_row.columnconfigure(1, weight=1)
        entry_row.columnconfigure(3, weight=1)

        ttk.Label(entry_row, text="Existing Product:").grid(
            row=0, column=0, sticky="w", padx=(0, 6)
        )
        product_combo = ttk.Combobox(entry_row, textvariable=product_choice, values=product_labels)
        product_combo.grid(row=0, column=1, columnspan=4, sticky="ew", pady=(0, 6))

        ttk.Label(entry_row, text="Item:").grid(row=1, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(entry_row, textvariable=item_title).grid(
            row=1, column=1, sticky="ew", padx=(0, 12)
        )
        ttk.Label(entry_row, text="Description:").grid(row=1, column=2, sticky="w", padx=(0, 6))
        ttk.Entry(entry_row, textvariable=item_description).grid(
            row=1, column=3, sticky="ew", padx=(0, 12)
        )
        ttk.Label(entry_row, text="HSN Code:").grid(row=1, column=4, sticky="w", padx=(0, 6))
        ttk.Entry(entry_row, textvariable=item_hsn, width=16).grid(
            row=1, column=5, sticky="w"
        )

        ttk.Label(entry_row, text="Capacity / Unit:").grid(
            row=2, column=0, sticky="w", padx=(0, 6), pady=(6, 0)
        )
        ttk.Entry(entry_row, textvariable=item_capacity, width=16).grid(
            row=2, column=1, sticky="w", pady=(6, 0)
        )

        ttk.Label(entry_row, text="Quantity:").grid(
            row=2, column=2, sticky="w", padx=(0, 6), pady=(6, 0)
        )
        ttk.Entry(entry_row, textvariable=item_quantity, width=10).grid(
            row=2, column=3, sticky="w", pady=(6, 0)
        )
        ttk.Label(entry_row, text="Rate (₹):").grid(
            row=2, column=4, sticky="w", padx=(0, 6), pady=(6, 0)
        )
        ttk.Entry(entry_row, textvariable=item_rate, width=14).grid(
            row=2, column=5, sticky="w", pady=(6, 0)
        )
        ttk.Label(entry_row, text="Discount %:").grid(
            row=3, column=0, sticky="w", padx=(0, 6), pady=(6, 0)
        )
        ttk.Entry(entry_row, textvariable=item_discount, width=10).grid(
            row=3, column=1, sticky="w", pady=(6, 0)
        )
        item_buttons = ttk.Frame(entry_row)
        item_buttons.grid(row=3, column=4, columnspan=2, sticky="e", pady=(6, 0))

        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill="both", expand=True)
        columns = ("item", "hsn_code", "description", "capacity_unit", "quantity",
                   "unit_price", "discount_percent", "amount")
        items_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        for key, heading, width in (
            ("item", "Product / Other Charges", 190),
            ("hsn_code", "HSN/SAC Code", 90),
            ("description", "Description", 180),
            ("capacity_unit", "UOM", 90),
            ("quantity", "Qty.", 55),
            ("unit_price", "Price", 85),
            ("discount_percent", "Discount", 70),
            ("amount", "Total", 100),
        ):
            items_tree.heading(key, text=heading)
            items_tree.column(
                key, width=width,
                anchor="w" if key in ("item", "hsn_code", "description", "capacity_unit") else "center",
            )

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)
        items_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def collect_items():
            """Items currently listed in the tree, as dictionaries."""
            items = []
            for row_id in items_tree.get_children():
                values = items_tree.item(row_id, "values")
                items.append({
                    "item": values[0] if len(values) > 0 else "",
                    "hsn_code": values[1] if len(values) > 1 else "",
                    "description": values[2] if len(values) > 2 else "",
                    "capacity_unit": values[3] if len(values) > 3 else "",
                    "quantity": values[4] if len(values) > 4 else "0",
                    "unit_price": values[5] if len(values) > 5 else "0",
                    "discount_percent": values[6] if len(values) > 6 else "0",
                    "amount": values[7] if len(values) > 7 else "0",
                })
            return items

        def update_totals(*_args):
            totals = quotation_manager.calculate_totals(
                collect_items(), tax_percent.get()
            )
            subtotal_label.config(text=f"Subtotal: ₹{totals['subtotal']:,.2f}")
            if totals.get("discount_total"):
                discount_label.config(
                    text=f"Discount: -₹{totals['discount_total']:,.2f}"
                )
            else:
                discount_label.config(text="Discount: ₹0.00")
            tax_label.config(
                text=f"Tax ({tax_percent.get() or 0}%): ₹{totals['tax_amount']:,.2f}"
            )
            grand_total_label.config(
                text=f"Grand Total: ₹{totals['grand_total']:,.2f}"
            )

        def use_catalog_product(_event=None):
            """Fill item / capacity / rate from the selected price-list product."""
            chosen = product_choice.get().strip()
            for product in product_catalog:
                if product["label"] == chosen:
                    item_title.set(product["item"])
                    item_capacity.set(product["capacity_unit"])
                    if product["rate"]:
                        item_rate.set(f"{product['rate']:.2f}")
                    break

        def add_item():
            """Add the item typed above (or picked from the price list) to the tree."""
            title = item_title.get().strip()
            if not title and product_choice.get().strip():
                title = product_choice.get().split("  (Rs")[0].split(" | ")[0].strip()
                item_title.set(title)
            if not title:
                messagebox.showwarning("Add Item", "Enter or select an item first.", parent=dialog)
                return
            quantity = quotation_manager.try_float(item_quantity.get(), 0.0)
            rate = quotation_manager.try_float(item_rate.get(), 0.0)
            discount = quotation_manager.try_float(item_discount.get(), 0.0)
            line_amount = quantity * rate * (1.0 - discount / 100.0)
            items_tree.insert("", "end", values=(
                title,
                item_hsn.get().strip(),
                item_description.get().strip(),
                item_capacity.get().strip(),
                f"{quantity:g}",
                f"{rate:.2f}",
                f"{discount:g}",
                f"{line_amount:.2f}",
            ))
            for variable, reset in ((item_title, ""), (item_hsn, ""), (item_description, ""),
                                    (item_capacity, ""),
                                    (item_quantity, "1"), (item_rate, "0.00"),
                                    (item_discount, "0")):
                variable.set(reset)
            product_choice.set("")
            update_totals()

        def remove_item():
            for selected in items_tree.selection():
                items_tree.delete(selected)
            update_totals()

        def edit_selected_item():
            """Load the selected row back into the entry fields for correction."""
            selection = items_tree.selection()
            if not selection:
                messagebox.showwarning("Edit Item", "Select an item row first.", parent=dialog)
                return
            values = items_tree.item(selection[0], "values")
            item_title.set(values[0] if len(values) > 0 else "")
            item_hsn.set(values[1] if len(values) > 1 else "")
            item_description.set(values[2] if len(values) > 2 else "")
            item_capacity.set(values[3] if len(values) > 3 else "")
            item_quantity.set(values[4] if len(values) > 4 else "1")
            item_rate.set(values[5] if len(values) > 5 else "0.00")
            item_discount.set(values[6] if len(values) > 6 else "0")
            items_tree.delete(selection[0])
            update_totals()

        product_combo.bind("<<ComboboxSelected>>", use_catalog_product)
        ttk.Button(item_buttons, text="Add Item", command=add_item).pack(side="left", padx=4)
        ttk.Button(item_buttons, text="Remove Selected", command=remove_item).pack(side="left", padx=4)
        ttk.Button(item_buttons, text="Edit Selected", command=edit_selected_item).pack(side="left", padx=4)

        lower_panels = ttk.Frame(main_frame)
        lower_panels.pack(fill="both", expand=True, pady=(0, 12))
        lower_panels.columnconfigure(0, weight=3)
        lower_panels.columnconfigure(1, weight=2)

        notes_panel = ttk.LabelFrame(
            lower_panels, text=" Terms & Condition / Additional Note ", padding=10
        )
        notes_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        totals_panel = ttk.LabelFrame(
            lower_panels, text=" Quotation Summary ", padding=10
        )
        totals_panel.grid(row=0, column=1, sticky="nsew")

        bank_row = ttk.Frame(notes_panel)
        bank_row.pack(fill="x", pady=(0, 8))
        ttk.Label(bank_row, text="Bank:").pack(side="left", padx=(0, 8))
        bank_name = tk.StringVar(
            value=(quotation_manager.load_bank_details().get("bank_name") or "")
        )
        ttk.Combobox(
            bank_row, textvariable=bank_name, state="readonly", width=28,
            values=[bank_name.get()] if bank_name.get() else ["Select Bank"],
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            bank_row, text="Edit Bank Details", command=lambda: bank_details_dialog()
        ).pack(side="right", padx=(8, 0))

        totals_panel.columnconfigure(1, weight=1)
        summary_rows = (
            ("Taxable", "subtotal"),
            ("Discount", "discount"),
            ("Total Tax", "tax"),
            ("Grand Total", "grand"),
        )
        summary_labels = {}
        for row, (label, key) in enumerate(summary_rows):
            ttk.Label(totals_panel, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=4
            )
            value = ttk.Label(totals_panel, text="₹0.00", anchor="e")
            value.grid(row=row, column=1, sticky="ew", pady=4)
            summary_labels[key] = value

        grand_total_label = summary_labels["grand"]
        subtotal_label = summary_labels["subtotal"]
        discount_label = summary_labels["discount"]
        tax_label = summary_labels["tax"]
        tax_percent.trace_add("write", update_totals)
        update_totals()

        terms_frame = notes_panel

        term_entry_row = ttk.Frame(terms_frame)
        term_entry_row.pack(fill="x")
        term_entry_row.columnconfigure(1, weight=1)
        term_entry_row.columnconfigure(3, weight=2)
        term_title = tk.StringVar()
        term_detail = tk.StringVar()
        ttk.Label(term_entry_row, text="Title:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(term_entry_row, textvariable=term_title).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(term_entry_row, text="Detail:").grid(row=0, column=2, sticky="w", padx=(0, 6))
        ttk.Entry(term_entry_row, textvariable=term_detail).grid(row=0, column=3, sticky="ew", padx=(0, 12))
        terms_tree = ttk.Treeview(terms_frame, columns=("title", "detail"), show="headings", height=4)
        terms_tree.heading("title", text="Title")
        terms_tree.heading("detail", text="Detail")
        terms_tree.column("title", width=180, anchor="w")
        terms_tree.column("detail", width=480, anchor="w")
        terms_tree.pack(fill="x", pady=(8, 4))

        notes_row = ttk.Frame(terms_frame)
        notes_row.pack(fill="x", pady=(10, 0))
        ttk.Label(notes_row, text="Document Note / Remarks:").pack(
            side="left", anchor="nw", padx=(0, 8)
        )
        notes_text = tk.Text(notes_row, height=3, width=52)
        notes_text.pack(side="left", fill="both", expand=True)
        if header.get("notes"):
            notes_text.insert("1.0", header.get("notes", ""))

        def collect_terms():
            terms = []
            for row_id in terms_tree.get_children():
                values = terms_tree.item(row_id, "values")
                title = values[0] if len(values) > 0 else ""
                detail = values[1] if len(values) > 1 else ""
                if title.strip() or detail.strip():
                    terms.append({"title": title.strip(), "detail": detail.strip()})
            return terms

        def add_term():
            title = term_title.get().strip()
            detail = term_detail.get().strip()
            if not title and not detail:
                messagebox.showwarning("Add Note", "Enter a Title and/or Detail first.", parent=dialog)
                return
            terms_tree.insert("", "end", values=(title, detail))
            term_title.set("")
            term_detail.set("")

        def edit_selected_term():
            selection = terms_tree.selection()
            if not selection:
                messagebox.showwarning("Edit Note", "Select a note row first.", parent=dialog)
                return
            values = terms_tree.item(selection[0], "values")
            term_title.set(values[0] if len(values) > 0 else "")
            term_detail.set(values[1] if len(values) > 1 else "")
            terms_tree.delete(selection[0])

        def bank_details_dialog():
            """Add / edit the company bank details printed on every quotation."""
            saved = quotation_manager.load_bank_details()
            win = tk.Toplevel(dialog)
            win.title("Company Bank Details")
            win.geometry("430x400")
            win.transient(dialog)
            win.grab_set()
            body = ttk.Frame(win, padding=14)
            body.pack(fill="both", expand=True)
            ttk.Label(body, text="Bank Details (printed on quotation)",
                      font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 10))
            entries = {}
            for field in quotation_manager.BANK_DETAIL_FIELDS:
                row = ttk.Frame(body)
                row.pack(fill="x", pady=3)
                ttk.Label(row, text=f"{quotation_manager.BANK_DETAIL_LABELS.get(field, field)}:",
                          width=16, anchor="w").pack(side="left")
                var = tk.StringVar(value=saved.get(field, ""))
                ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
                entries[field] = var

            def save_bank():
                quotation_manager.save_bank_details(
                    {field: var.get() for field, var in entries.items()}
                )
                messagebox.showinfo("Saved", "Bank details saved.", parent=win)
                win.destroy()

            ttk.Button(body, text="Save Bank Details", command=save_bank).pack(pady=(12, 0))

        def add_previous_term():
            """Old terms: reuse previously saved Terms / Notes."""
            previous = quotation_manager.load_terms_library()
            if not previous:
                messagebox.showinfo("No Saved Terms",
                                    "No previously saved Terms / Notes found yet.\n"
                                    "Add a note with + ADD NOTE and it will be remembered.",
                                    parent=dialog)
                return
            picker = tk.Toplevel(dialog)
            picker.title("Add Previous Terms / Note")
            picker.geometry("520x380")
            picker.transient(dialog)
            picker.grab_set()
            body = ttk.Frame(picker, padding=12)
            body.pack(fill="both", expand=True)
            ttk.Label(body, text="Previously saved Terms & Conditions / Notes",
                      font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(0, 8))
            listbox = tk.Listbox(body, height=12, selectmode="extended")
            listbox.pack(fill="both", expand=True)
            for term in previous:
                listbox.insert("end", f"{term.get('title', '')} — {term.get('detail', '')}")

            def use_selected():
                for index in listbox.curselection():
                    term = previous[index]
                    terms_tree.insert("", "end", values=(term.get("title", ""), term.get("detail", "")))
                picker.destroy()

            ttk.Button(body, text="Add Selected Note(s)", command=use_selected).pack(pady=(10, 0))

        term_btn_row = ttk.Frame(terms_frame)
        term_btn_row.pack(fill="x")
        ttk.Button(term_btn_row, text="+ ADD NOTE", command=add_term).pack(side="left", padx=(0, 6))
        ttk.Button(term_btn_row, text="Edit Selected", command=edit_selected_term).pack(side="left", padx=(0, 6))
        ttk.Button(term_btn_row, text="Remove Selected",
                   command=lambda: [terms_tree.delete(s) for s in terms_tree.selection()]).pack(side="left", padx=(0, 6))
        ttk.Button(term_btn_row, text="Add Previous Term / Note",
                   command=lambda: add_previous_term()).pack(side="left", padx=(0, 6))
        ttk.Button(term_btn_row, text="Add Bank Details",
                   command=lambda: bank_details_dialog()).pack(side="left")

        def save_quotation(ask_print=True):
            """Validate the form and store the quotation for its customer."""
            items = collect_items()
            if not customer_name.get().strip():
                messagebox.showwarning("Required Field", "Customer name is required.", parent=dialog)
                return
            if not items:
                messagebox.showwarning("No Items", "Add at least one item to the quotation.", parent=dialog)
                return
            terms = collect_terms()

            try:
                result = quotation_manager.save_quotation(
                    customer_name=customer_name.get(),
                    items=items,
                    customer_email=customer_email.get(),
                    customer_phone=customer_phone.get(),
                    customer_gstin=customer_gstin.get(),
                    customer_address=customer_address.get(),
                    customer_contact_person=customer_contact_person.get(),
                    customer_type=customer_type.get(),
                    challan_no=challan_no.get(),
                    challan_date=challan_date.get(),
                    lr_no=lr_no.get(),
                    delivery_mode=delivery_mode.get(),
                    rev_charge=rev_charge.get(),
                    ship_to=ship_to.get(),
                    distance_for_eway_bill=distance_for_eway_bill.get(),
                    place_of_supply=place_of_supply.get(),
                    quotation_date=quotation_date.get(),
                    valid_until=valid_until.get(),
                    status=status.get(),
                    tax_percent=tax_percent.get(),
                    terms=terms,
                    notes=notes_text.get("1.0", tk.END).strip(),
                    quotation_no=quotation_no.get(),
                    created_by=(self.user_data or {}).get("username", ""),
                )
            except Exception as error:
                messagebox.showerror("Save Failed",
                                     f"Could not save the quotation:\n{error}", parent=dialog)
                return

            def do_print_saved(number):
                """Create the printable PDF / Excel copy of a saved quotation."""
                try:
                    exported = quotation_manager.export_quotation(number)
                    quotation_manager.open_path(exported["pdf"])
                except Exception as error:
                    messagebox.showerror("Print Failed",
                                         f"Could not create the print copy:\n{error}", parent=dialog)

            messagebox.showinfo(
                "Quotation Saved",
                f"Quotation {result['quotation_no']} saved for {customer_name.get().strip()}.\n\n"
                f"Customer file:\n{result['customer_file']}\n\n"
                f"Grand Total: ₹{result['grand_total']:,.2f}",
                parent=dialog,
            )
            if ask_print and messagebox.askyesno("Print Quotation",
                                   "Create the printable PDF / Excel copy now?", parent=dialog):
                do_print_saved(result["quotation_no"])
            if not ask_print:
                do_print_saved(result["quotation_no"])
            dialog.destroy()

        # Pinned below the scrolling form so these buttons are always on screen.
        button_frame = ttk.Frame(dialog, padding=(8, 4))
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(button_frame, text="⬅ Back", command=dialog.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(button_frame, text="View Quotations", command=self.show_quotations_list).pack(
            side="left", padx=4
        )
        ttk.Button(button_frame, text="Save & Print", command=lambda: save_quotation(ask_print=False)).pack(
            side="right", padx=4
        )
        ttk.Button(button_frame, text="Save", command=save_quotation).pack(
            side="right", padx=4
        )
        ttk.Button(button_frame, text="Save Draft", command=lambda: save_quotation(ask_print=True)).pack(
            side="right", padx=4
        )
    def show_quotations_list(self):
        """Quotation register: every saved quotation with status and value.

        The list is built from the customer-wise CSV files in
        csv_data/quotation by grouping their rows by quotation number.
        """
        window = tk.Toplevel(self.main_app.root)
        window.title("Quotation Register")
        window.geometry("1020x620")
        window.minsize(900, 520)
        window.resizable(True, True)
        window.transient(self.main_app.root)

        top = ttk.Frame(window, padding=12)
        top.pack(fill="both", expand=True)
        title_header = ttk.Frame(top)
        title_header.pack(fill="x", pady=(0, 8))
        ttk.Label(
            title_header, text="Saved Quotations", font=("Helvetica", 14, "bold")
        ).pack(side="left")
        self._add_quotation_window_controls(title_header, window, "1020x620")

        filters = ttk.Frame(top)
        filters.pack(fill="x", pady=(8, 8))
        ttk.Label(filters, text="Customer:").pack(side="left")
        customer_filter = tk.StringVar(value="All customers")
        ttk.Combobox(filters, textvariable=customer_filter, width=30,
                     values=["All customers"] + quotation_manager.load_customers()).pack(
            side="left", padx=(4, 14)
        )
        ttk.Label(filters, text="Status:").pack(side="left")
        status_filter = tk.StringVar(value="All")
        ttk.Combobox(filters, textvariable=status_filter, state="readonly", width=14,
                     values=["All"] + list(quotation_manager.STATUSES)).pack(side="left", padx=(4, 0))

        table_frame = ttk.Frame(top)
        table_frame.pack(fill="both", expand=True)
        columns = ("no", "date", "customer", "valid_until", "items", "total", "status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        for key, heading, width in (
            ("no", "Quotation No.", 110),
            ("date", "Date", 90),
            ("customer", "Customer", 230),
            ("valid_until", "Valid Until", 90),
            ("items", "Items", 60),
            ("total", "Grand Total (₹)", 120),
            ("status", "Status", 90),
        ):
            tree.heading(key, text=heading)
            tree.column(key, width=width, anchor="w" if key == "customer" else "center")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        summary_label = ttk.Label(top, text="", font=("Helvetica", 10))
        summary_label.pack(anchor="w", pady=(6, 0))

        def refresh(*_args):
            """Reload the table for the selected customer / status filters."""
            for row_id in tree.get_children():
                tree.delete(row_id)
            customer = customer_filter.get()
            rows = quotation_manager.list_quotations(
                customer_name="" if customer == "All customers" else customer,
                status="" if status_filter.get() == "All" else status_filter.get(),
            )
            for entry in rows:
                tree.insert("", "end", iid=entry["quotation_no"], values=(
                    entry["quotation_no"], entry["quotation_date"], entry["customer_name"],
                    entry["valid_until"], entry["items"], f"{entry['grand_total']:,.2f}",
                    entry["status"],
                ))
            total = sum(entry["grand_total"] for entry in rows)
            summary_label.config(text=f"{len(rows)} quotation(s)   |   Total value: ₹{total:,.2f}")

        def selected_number():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Select Quotation", "Select a quotation first.", parent=window)
                return None
            return selection[0]

        def print_selected():
            """Create the Excel + PDF copy of the selected quotation."""
            number = selected_number()
            if not number:
                return
            try:
                exported = quotation_manager.export_quotation(number)
            except Exception as error:
                messagebox.showerror("Print Failed", str(error), parent=window)
                return
            quotation_manager.open_path(exported["pdf"])
            messagebox.showinfo(
                "Quotation Exported",
                f"Excel copy:\n{exported['xlsx']}\n\nPDF copy:\n{exported['pdf']}",
                parent=window,
            )

        def mark_status(value):
            number = selected_number()
            if not number:
                return
            quotation_manager.update_status(number, value)
            refresh()

        def open_customer_file():
            number = selected_number()
            if not number:
                return
            entry = quotation_manager.get_quotation(number)
            if entry:
                quotation_manager.open_path(entry["file"])

        def convert_to_invoice():
            """Mark the quotation as converted and open the invoice entry."""
            number = selected_number()
            if not number:
                return
            quotation_manager.update_status(number, "Converted")
            refresh()
            if messagebox.askyesno(
                "Convert to Invoice",
                f"Quotation {number} is marked as Converted.\n\n"
                "Open the Sales / Income invoice entry now?",
                parent=window,
            ):
                window.destroy()
                self.main_app.show_sales_income_page()

        status_row = ttk.Frame(top)
        status_row.pack(fill="x", pady=(8, 0))
        ttk.Label(status_row, text="Mark selected as:").pack(side="left", padx=(0, 6))
        for value in quotation_manager.STATUSES:
            ttk.Button(status_row, text=value,
                       command=lambda v=value: mark_status(v)).pack(side="left", padx=3)

        actions = ttk.Frame(top)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Print / Export Selected",
                   command=print_selected).pack(side="left", padx=3)
        ttk.Button(actions, text="Convert to Invoice",
                   command=convert_to_invoice).pack(side="left", padx=3)
        ttk.Button(actions, text="Open Customer CSV",
                   command=open_customer_file).pack(side="left", padx=3)
        ttk.Button(actions, text="Open Quotation Folder",
                   command=lambda: quotation_manager.open_path(quotation_manager.QUOTATION_DIR)
                   ).pack(side="left", padx=3)
        ttk.Button(actions, text="Refresh", command=refresh).pack(side="left", padx=3)
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right", padx=3)

        customer_filter.trace_add("write", refresh)
        status_filter.trace_add("write", refresh)
        refresh()

    def load_b2b_products_list(self, parent_frame):
        csv_file = os.path.join(
            os.path.dirname(__file__),
            "csv_data",
            "b2b",
            "b2b_products.csv"
        )

        if not os.path.exists(csv_file):
            ttk.Label(
                parent_frame,
                text="No products available yet.\nClick 'Add Product' to list your products.",
                font=("Helvetica", 10),
                justify="center"
            ).pack(expand=True)
            return

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products = list(reader)

            if not products:
                ttk.Label(
                    parent_frame,
                    text="No products available yet.\nClick 'Add Product' to list your products.",
                    font=("Helvetica", 10),
                    justify="center"
                ).pack(expand=True)
                return

            columns = ("prod_id", "Title", "SKU", "Price", "Stock", "Status")
            tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

            tree.heading("prod_id", text="ID")
            tree.heading("Title", text="Product Title")
            tree.heading("SKU", text="SKU")
            tree.heading("Price", text="Price (₹)")
            tree.heading("Stock", text="Stock")
            tree.heading("Status", text="Status")

            tree.column("prod_id", width=100)
            tree.column("Title", width=300)
            tree.column("SKU", width=120)
            tree.column("Price", width=100)
            tree.column("Stock", width=80)
            tree.column("Status", width=80)

            tree.pack(fill="both", expand=True)

            for product in products:
                tree.insert("", "end", values=(
                    product.get('prod_id', ''),
                    product.get('title', ''),
                    product.get('sku', ''),
                    product.get('base_price', ''),
                    product.get('stock_qty', ''),
                    product.get('status', '')
                ))

            # Add Edit Button
            btn_edit = ttk.Button(
                parent_frame,
                text="📝 Edit Selected Product",
                command=lambda: self.edit_selected_product(tree)
            )
            btn_edit.pack(pady=10)

            vsb = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")

        except Exception as e:
            ttk.Label(parent_frame, text=f"Error loading products: {e}").pack(expand=True)

    def edit_selected_product(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product to edit first.")
            return

        prod_id = tree.item(selected[0])["values"][0]
        try:
            from b2b_product_manager import open_b2b_product_manager
            open_b2b_product_manager(self.main_app, prod_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Product Manager for editing: {e}")

    def show_saark_product_sector(self):
        self.clear_internal_workspace()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        sector_tab = ttk.Frame(notebook, padding=20)
        product_tab = ttk.Frame(notebook)
        promotion_tab = ttk.Frame(notebook, padding=16)
        notebook.add(sector_tab, text=" 1. Select / Add Sector ")
        notebook.add(product_tab, text=" 2. Basic Product Information ")
        notebook.add(promotion_tab, text=" 3. Promotion Material Management ")

        default_sectors = (
            "Booster Pump Control Panel", "STP Panel", "Water Meter", "BMS", "Other"
        )
        sector_file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sector_list.csv")
        selected_sector = tk.StringVar()
        new_sector_name = tk.StringVar()

        def get_sectors():
            sectors = list(default_sectors)
            if os.path.exists(sector_file_path):
                with open(sector_file_path, newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
                        sector_name = (row.get("sector_name") or "").strip()
                        if sector_name and sector_name not in sectors:
                            sectors.append(sector_name)
            return sectors

        crm_engine.init_crm_db()
        promo_sector = tk.StringVar()
        promo_title = tk.StringVar()
        promo_type = tk.StringVar(value="YouTube Video")
        promo_campaign = tk.StringVar()
        promo_platform = tk.StringVar(value="YouTube")
        promo_url = tk.StringVar()
        promo_attachment = tk.StringVar()

        ttk.Label(
            promotion_tab, text="Promotion Material Management",
            font=("Helvetica", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            promotion_tab,
            text="Maintain approved corporate marketing assets. Add each link or attachment as a separate item.",
        ).pack(anchor="w", pady=(4, 14))
        promo_form = ttk.LabelFrame(promotion_tab, text=" Add Promotion Material ", padding=14)
        promo_form.pack(fill="x")
        promo_form.columnconfigure(1, weight=1)

        def promo_row(row, label, widget):
            ttk.Label(promo_form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )
            widget.grid(row=row, column=1, sticky="ew", pady=5)

        promo_sector_combo = ttk.Combobox(
            promo_form, textvariable=promo_sector, values=get_sectors(), state="readonly"
        )
        promo_row(0, "Product Sector", promo_sector_combo)
        promo_row(1, "Material Title", ttk.Entry(promo_form, textvariable=promo_title))
        promo_row(2, "Material Type", ttk.Combobox(
            promo_form, textvariable=promo_type, state="readonly",
            values=("YouTube Video", "Instagram Reel", "Instagram Photo", "Product Photo",
                    "Product Video", "Brochure / Catalogue", "Datasheet", "Case Study", "Other"),
        ))
        promo_row(3, "Campaign / Product Name", ttk.Entry(promo_form, textvariable=promo_campaign))
        promo_row(4, "Platform", ttk.Combobox(
            promo_form, textvariable=promo_platform,
            values=("YouTube", "Instagram", "Website", "LinkedIn", "WhatsApp", "Internal", "Other"),
        ))
        promo_row(5, "Published / Upload Link", ttk.Entry(promo_form, textvariable=promo_url))

        attachment_box = ttk.Frame(promo_form)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=promo_attachment).grid(row=0, column=0, sticky="ew")

        def choose_promotion_attachment():
            path = filedialog.askopenfilename(
                parent=self.main_app.root, title="Attach promotion material",
                filetypes=(
                    ("Promotion files", "*.pdf *.doc *.docx *.ppt *.pptx *.jpg *.jpeg *.png *.gif *.webp *.mp4 *.mov *.avi *.mkv *.webm"),
                    ("All files", "*.*"),
                ),
            )
            if path:
                promo_attachment.set(path)

        ttk.Button(attachment_box, text="Attach File", command=choose_promotion_attachment).grid(
            row=0, column=1, padx=(6, 0)
        )
        promo_row(6, "Attachment", attachment_box)
        ttk.Label(promo_form, text="Notes / Approval:").grid(
            row=7, column=0, sticky="nw", padx=(0, 12), pady=5
        )
        promo_notes = tk.Text(promo_form, height=3, wrap="word")
        promo_notes.grid(row=7, column=1, sticky="ew", pady=5)

        promo_table = ttk.LabelFrame(promotion_tab, text=" Saved Promotion Materials ", padding=8)
        promo_table.pack(fill="both", expand=True, pady=(14, 0))
        promo_columns = ("id", "product_sector", "material_type", "title", "platform", "url", "attachment_path", "created_at")
        promo_tree = ttk.Treeview(promo_table, columns=promo_columns, show="headings", height=11)
        promo_headings = ("ID", "Sector", "Type", "Title", "Platform", "Link", "Attachment", "Saved On")
        for column, heading, width in zip(promo_columns, promo_headings, (55, 165, 150, 205, 100, 240, 240, 145)):
            promo_tree.heading(column, text=heading)
            promo_tree.column(column, width=width, anchor="w")
        promo_scroll_y = ttk.Scrollbar(promo_table, orient="vertical", command=promo_tree.yview)
        promo_scroll_x = ttk.Scrollbar(promo_table, orient="horizontal", command=promo_tree.xview)
        promo_tree.configure(yscrollcommand=promo_scroll_y.set, xscrollcommand=promo_scroll_x.set)
        promo_tree.grid(row=0, column=0, sticky="nsew")
        promo_scroll_y.grid(row=0, column=1, sticky="ns")
        promo_scroll_x.grid(row=1, column=0, sticky="ew")
        promo_table.columnconfigure(0, weight=1)
        promo_table.rowconfigure(0, weight=1)

        def refresh_promotion_materials():
            for item in promo_tree.get_children():
                promo_tree.delete(item)
            for row in crm_engine.fetch_promotional_materials(promo_sector.get().strip() or None):
                promo_tree.insert("", "end", values=[row[column] or "" for column in promo_columns])

        def clear_promotion_form():
            promo_title.set("")
            promo_type.set("YouTube Video")
            promo_campaign.set("")
            promo_platform.set("YouTube")
            promo_url.set("")
            promo_attachment.set("")
            promo_notes.delete("1.0", tk.END)

        def save_promotion_material():
            sector = promo_sector.get().strip()
            title = promo_title.get().strip()
            if not sector or not title:
                messagebox.showwarning("Required Information", "Select a Product Sector and enter a Material Title.", parent=self.main_app.root)
                return
            if not promo_url.get().strip() and not promo_attachment.get().strip():
                messagebox.showwarning("Link or Attachment Required", "Add a published link or attach a file before saving.", parent=self.main_app.root)
                return
            crm_engine.add_promotional_material(
                sector, title, promo_type.get().strip(), promo_campaign.get().strip(),
                promo_platform.get().strip(), promo_url.get().strip(), promo_attachment.get().strip(),
                promo_notes.get("1.0", tk.END).strip(),
            )
            refresh_promotion_materials()
            clear_promotion_form()
            messagebox.showinfo("Saved", "Promotion material saved successfully.", parent=self.main_app.root)

        def selected_promotion_values():
            selected = promo_tree.selection()
            return promo_tree.item(selected[0], "values") if selected else None

        def open_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.main_app.root)
                return
            link, attachment = values[5], values[6]
            if link:
                webbrowser.open(link)
            elif attachment and os.path.exists(attachment):
                os.startfile(attachment)
            else:
                messagebox.showwarning("File Not Found", "The saved attachment is no longer available.", parent=self.main_app.root)

        def delete_promotion_material():
            values = selected_promotion_values()
            if not values:
                messagebox.showwarning("Select Material", "Select a saved promotion material first.", parent=self.main_app.root)
                return
            if messagebox.askyesno("Delete Material", f"Delete '{values[3]}' from the promotion library?", parent=self.main_app.root):
                crm_engine.delete_promotional_material(int(values[0]))
                refresh_promotion_materials()

        promo_actions = ttk.Frame(promotion_tab)
        promo_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(promo_actions, text="Save Material", command=save_promotion_material).pack(side="left")
        ttk.Button(promo_actions, text="Clear Form", command=clear_promotion_form).pack(side="left", padx=6)
        ttk.Button(promo_actions, text="Refresh List", command=refresh_promotion_materials).pack(side="left")
        ttk.Button(promo_actions, text="Open Link / Attachment", command=open_promotion_material).pack(side="right")
        ttk.Button(promo_actions, text="Delete Selected", command=delete_promotion_material).pack(side="right", padx=6)
        promo_sector_combo.bind("<<ComboboxSelected>>", lambda _event: refresh_promotion_materials())
        refresh_promotion_materials()

        ttk.Label(sector_tab, text="Product Sector Setup", font=("Helvetica", 15, "bold")).pack(anchor="w")
        ttk.Label(sector_tab, text="Select an existing sector or add a new sector before entering product details.").pack(anchor="w", pady=(4, 18))
        sector_setup = ttk.LabelFrame(sector_tab, text=" Sector ", padding=16)
        sector_setup.pack(fill="x", anchor="n")
        sector_setup.columnconfigure(1, weight=1)
        ttk.Label(sector_setup, text="Select Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        sector_selector = ttk.Combobox(sector_setup, textvariable=selected_sector, values=get_sectors(), state="readonly")
        sector_selector.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(sector_setup, text="New Sector Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(sector_setup, textvariable=new_sector_name).grid(row=1, column=1, sticky="ew", pady=7)

        form_canvas = tk.Canvas(product_tab, highlightthickness=0)
        form_scrollbar = ttk.Scrollbar(
            product_tab, orient="vertical", command=form_canvas.yview
        )
        form_canvas.configure(yscrollcommand=form_scrollbar.set)
        form_scrollbar.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)

        container = ttk.Frame(form_canvas, padding=20)
        form_window = form_canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind(
            "<Configure>",
            lambda _event: form_canvas.configure(scrollregion=form_canvas.bbox("all")),
        )
        form_canvas.bind(
            "<Configure>", lambda event: form_canvas.itemconfigure(form_window, width=event.width)
        )

        def scroll_product_form(event):
            form_canvas.yview_scroll(int(-event.delta / 120), "units")

        form_canvas.bind("<Enter>", lambda _event: form_canvas.bind_all("<MouseWheel>", scroll_product_form))
        form_canvas.bind("<Leave>", lambda _event: form_canvas.unbind_all("<MouseWheel>"))
        form = ttk.LabelFrame(container, text=" Basic Product Information ", padding=16)
        form.pack(fill="x", anchor="n")
        form.columnconfigure(1, weight=1)

        fields = {
            "product_sector": tk.StringVar(),
            "product_name": tk.StringVar(),
            "sku_model_number": tk.StringVar(),
            "product_category": tk.StringVar(),
            "short_description_file": tk.StringVar(),
            "detailed_description_file": tk.StringVar(),
            "target_applications_file": tk.StringVar(),
            "input_voltage": tk.StringVar(),
            "rated_frequency": tk.StringVar(),
            "min_power_rating": tk.StringVar(),
            "max_power_rating": tk.StringVar(),
            "power_rating_unit": tk.StringVar(value="HP"),
            "starter_drive_type": tk.StringVar(),
            "enclosure_ip_rating": tk.StringVar(),
            "pump_support_capacity": tk.StringVar(),
            "min_pressure": tk.StringVar(),
            "max_pressure": tk.StringVar(),
            "pressure_unit": tk.StringVar(value="bar"),
            "user_interface_display": tk.StringVar(),
            "product_images": tk.StringVar(),
            "datasheet_manual": tk.StringVar(),
            "wiring_sld": tk.StringVar(),
            "promotional_video": tk.StringVar(),
            "photo_name": tk.StringVar(),
            "photo_description": tk.StringVar(),
            "photo_attachment": tk.StringVar(),
            "setting_video_type": tk.StringVar(),
            "setting_video_details": tk.StringVar(),
            "setting_video_attachment": tk.StringVar(),
        }
        multi_selects = {}

        def refresh_sector_selectors():
            sectors = get_sectors()
            sector_selector["values"] = sectors
            basic_sector_combo["values"] = sectors
            promo_sector_combo["values"] = sectors

        def use_selected_sector(_event=None):
            fields["product_sector"].set(selected_sector.get())
            notebook.select(product_tab)

        def add_sector():
            sector_name = new_sector_name.get().strip()
            if not sector_name:
                messagebox.showwarning("Sector Name Required", "Enter a new sector name first.", parent=self.main_app.root)
                return
            sectors = get_sectors()
            if sector_name not in sectors:
                with open(sector_file_path, "a", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("sector_name",))
                    if os.path.getsize(sector_file_path) == 0:
                        writer.writeheader()
                    writer.writerow({"sector_name": sector_name})
            selected_sector.set(sector_name)
            fields["product_sector"].set(sector_name)
            new_sector_name.set("")
            refresh_sector_selectors()
            notebook.select(product_tab)

        sector_selector.bind("<<ComboboxSelected>>", use_selected_sector)
        ttk.Button(sector_setup, text="Add Sector", command=add_sector).grid(
            row=2, column=1, sticky="e", pady=(10, 0)
        )

        def add_text_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Entry(form, textvariable=fields[field]).grid(
                row=row, column=1, sticky="ew", pady=7
            )

        def add_attachment_field(row, label, field):
            ttk.Label(form, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(form)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(
                row=0, column=0, sticky="ew"
            )

            def choose_file():
                path = filedialog.askopenfilename(
                    parent=self.main_app.root,
                    title=f"Attach {label}",
                    filetypes=(
                        ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                        ("All files", "*.*"),
                    ),
                )
                if path:
                    fields[field].set(path)

            ttk.Button(attachment_box, text="Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        def add_dropdown_field(section, row, label, field, values):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            ttk.Combobox(
                section, textvariable=fields[field], values=values, state="readonly"
            ).grid(row=row, column=1, sticky="ew", pady=7)

        def add_checklist(section, row, label, field, options):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="nw", padx=(0, 12), pady=7
            )
            choice_box = ttk.Frame(section)
            choice_box.grid(row=row, column=1, sticky="ew", pady=4)
            selected_options = []
            for index, option in enumerate(options):
                option_var = tk.BooleanVar()
                ttk.Checkbutton(choice_box, text=option, variable=option_var).grid(
                    row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=2
                )
                selected_options.append((option, option_var))
            multi_selects[field] = selected_options

        def add_file_field(section, row, label, field, *, multiple=False, filetypes=None):
            ttk.Label(section, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=7
            )
            attachment_box = ttk.Frame(section)
            attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
            attachment_box.columnconfigure(0, weight=1)
            ttk.Entry(attachment_box, textvariable=fields[field]).grid(row=0, column=0, sticky="ew")

            def choose_file():
                selected_filetypes = filetypes or (
                    ("Documents and images", "*.pdf *.doc *.docx *.jpg *.jpeg *.png *.bmp"),
                    ("All files", "*.*"),
                )
                if multiple:
                    paths = filedialog.askopenfilenames(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if paths:
                        fields[field].set(" | ".join(paths))
                else:
                    path = filedialog.askopenfilename(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                    if path:
                        fields[field].set(path)

            ttk.Button(attachment_box, text="Attach Files" if multiple else "Attach File", command=choose_file).grid(
                row=0, column=1, padx=(6, 0)
            )

        ttk.Label(form, text="Product Sector:").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=7)
        basic_sector_combo = ttk.Combobox(
            form, textvariable=fields["product_sector"], values=get_sectors(), state="readonly"
        )
        basic_sector_combo.grid(row=0, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Name / Title:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["product_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="SKU / Model Number:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(form, textvariable=fields["sku_model_number"]).grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Label(form, text="Product Category / Sub-category:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Combobox(
            form, textvariable=fields["product_category"],
            values=("Control Panel", "Pump", "Water Treatment", "Water Metering", "Automation", "Other")
        ).grid(row=3, column=1, sticky="ew", pady=7)
        add_attachment_field(4, "Short Description", "short_description_file")
        add_attachment_field(5, "Detailed Description / Features", "detailed_description_file")
        add_attachment_field(6, "Target Applications", "target_applications_file")

        electrical = ttk.LabelFrame(container, text=" 2. Electrical & Power Specifications ", padding=16)
        electrical.pack(fill="x", anchor="n", pady=(14, 0))
        electrical.columnconfigure(1, weight=1)
        add_dropdown_field(electrical, 0, "Input Voltage", "input_voltage", ("230V 1-Phase", "415V 3-Phase", "110V"))
        add_dropdown_field(electrical, 1, "Rated Frequency", "rated_frequency", ("50 Hz", "60 Hz", "50/60 Hz Dual"))
        ttk.Label(electrical, text="Power Rating Range:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        power_box = ttk.Frame(electrical)
        power_box.grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Entry(power_box, textvariable=fields["min_power_rating"], width=12).pack(side="left")
        ttk.Label(power_box, text=" to ").pack(side="left")
        ttk.Entry(power_box, textvariable=fields["max_power_rating"], width=12).pack(side="left")
        ttk.Combobox(power_box, textvariable=fields["power_rating_unit"], values=("HP", "kW"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_dropdown_field(electrical, 3, "Starter / Drive Type", "starter_drive_type", ("DOL", "Star-Delta", "Integrated VFD", "Soft Starter"))
        add_dropdown_field(electrical, 4, "Enclosure / IP Protection Rating", "enclosure_ip_rating", ("IP54", "IP55", "IP65", "NEMA 4X"))

        pump = ttk.LabelFrame(container, text=" 3. Pump Configuration & Control Parameters ", padding=16)
        pump.pack(fill="x", anchor="n", pady=(14, 0))
        pump.columnconfigure(1, weight=1)
        add_dropdown_field(pump, 0, "Pump Support Capacity", "pump_support_capacity", ("1 Pump", "2 Pumps [1W+1S]", "3 Pumps", "4+ Multi-Cascade"))
        add_checklist(pump, 1, "Control Modes", "control_modes", ("Constant Pressure", "Auto-Alternation", "Duty/Assist/Standby", "Manual Override"))
        add_checklist(pump, 2, "Pressure Sensor Compatibility", "pressure_sensor_compatibility", ("4-20 mA", "0-10V", "RS-485 Digital", "Pressure Switch"))
        ttk.Label(pump, text="Supported Pressure Range:").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=7)
        pressure_box = ttk.Frame(pump)
        pressure_box.grid(row=3, column=1, sticky="ew", pady=7)
        ttk.Entry(pressure_box, textvariable=fields["min_pressure"], width=12).pack(side="left")
        ttk.Label(pressure_box, text=" to ").pack(side="left")
        ttk.Entry(pressure_box, textvariable=fields["max_pressure"], width=12).pack(side="left")
        ttk.Combobox(pressure_box, textvariable=fields["pressure_unit"], values=("bar", "PSI"), state="readonly", width=7).pack(side="left", padx=(8, 0))
        add_checklist(pump, 4, "Level Sensor Inputs", "level_sensor_inputs", ("Float Switch", "Ultrasonic", "Conductive Probes", "Dry Run Float"))

        smart = ttk.LabelFrame(container, text=" 4. Smart Features, Display & Connectivity ", padding=16)
        smart.pack(fill="x", anchor="n", pady=(14, 0))
        smart.columnconfigure(1, weight=1)
        add_dropdown_field(smart, 0, "User Interface / Display", "user_interface_display", ("Touchscreen HMI", "Multi-line LCD", "7-Segment LED", "Indicator LEDs"))
        add_checklist(smart, 1, "Communication Protocols", "communication_protocols", ("RS-485 Modbus RTU", "Modbus TCP/IP", "BACnet", "Ethernet"))
        add_checklist(smart, 2, "IoT / Cloud Features", "iot_cloud_features", ("GSM/4G Remote Telemetry", "Wi-Fi Dashboard", "Mobile App Support", "SMS Alerts"))
        add_checklist(smart, 3, "Data Logging", "data_logging", ("Historical Fault Log", "Run-Hour Meter", "Pressure Trends"))

        protections = ttk.LabelFrame(container, text=" 5. Protections & Alarms ", padding=16)
        protections.pack(fill="x", anchor="n", pady=(14, 0))
        protections.columnconfigure(1, weight=1)
        add_checklist(protections, 0, "Electrical Protections", "electrical_protections", ("Overload", "Under/Over-Voltage", "Phase Failure", "Phase Reversal", "Short Circuit"))
        add_checklist(protections, 1, "Hydraulic Protections", "hydraulic_protections", ("Dry Run Protection (Auto-Reset)", "High/Low Pressure Cutoff", "Pipe Burst / Leakage Detection", "Anti-Seize Cycling"))

        media = ttk.LabelFrame(container, text=" 6. Media, Documents & Compliance ", padding=16)
        media.pack(fill="x", anchor="n", pady=(14, 0))
        media.columnconfigure(1, weight=1)
        add_file_field(media, 0, "Product Images", "product_images", multiple=True)
        add_file_field(media, 1, "Datasheet / Manual", "datasheet_manual")
        add_file_field(media, 2, "Wiring / Single Line Diagram (SLD)", "wiring_sld")
        add_checklist(media, 3, "Certifications", "certifications", ("CE", "RoHS", "ISO 9001", "CPRI Approved"))

        promotion = ttk.LabelFrame(container, text=" Promotional Material ", padding=16)
        promotion.pack(fill="x", anchor="n", pady=(14, 0))
        promotion.columnconfigure(1, weight=1)
        video_filetypes = (
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.webm"),
            ("All files", "*.*"),
        )
        add_file_field(promotion, 0, "Add Video", "promotional_video", filetypes=video_filetypes)
        ttk.Label(promotion, text="Photo Name:").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_name"]).grid(row=1, column=1, sticky="ew", pady=7)
        ttk.Label(promotion, text="Photo Description:").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["photo_description"]).grid(row=2, column=1, sticky="ew", pady=7)
        add_file_field(
            promotion, 3, "Attach Photo", "photo_attachment",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All files", "*.*")),
        )
        add_dropdown_field(
            promotion, 4, "Setting Video", "setting_video_type",
            ("Installation / Setup", "Configuration", "Commissioning", "Operation", "Troubleshooting", "Other"),
        )
        ttk.Label(promotion, text="Setting Video Details:").grid(row=5, column=0, sticky="w", padx=(0, 12), pady=7)
        ttk.Entry(promotion, textvariable=fields["setting_video_details"]).grid(row=5, column=1, sticky="ew", pady=7)
        add_file_field(promotion, 6, "Attach Setting Video", "setting_video_attachment", filetypes=video_filetypes)

        saved_products = ttk.LabelFrame(container, text=" Saved Products — Select a row to edit ", padding=10)
        saved_products.pack(fill="both", expand=True, anchor="n", pady=(14, 0))
        product_columns = ("product_sector", "product_category", "product_name", "sku_model_number")
        products_tree = ttk.Treeview(saved_products, columns=product_columns, show="headings", height=8)
        for column, label in zip(product_columns, ("Sector", "Category", "Product Name", "SKU / Model No.")):
            products_tree.heading(column, text=label)
            products_tree.column(column, width=190, anchor="w")
        products_scrollbar = ttk.Scrollbar(saved_products, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=products_scrollbar.set)
        products_scrollbar.pack(side="right", fill="y")
        products_tree.pack(side="left", fill="both", expand=True)
        selected_record_index = {"value": None}

        def product_headers():
            return tuple(fields) + tuple(multi_selects)

        def read_product_records():
            file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sectors.csv")
            if not os.path.exists(file_path):
                return []
            with open(file_path, newline="", encoding="utf-8") as file:
                return list(csv.DictReader(file))

        def write_product_records(records):
            file_path = os.path.join(self.main_app.config.CSV_DIR, "saark_product_sectors.csv")
            with tempfile.NamedTemporaryFile(
                "w", newline="", encoding="utf-8", delete=False, dir=self.main_app.config.CSV_DIR
            ) as file:
                temporary_path = file.name
                writer = csv.DictWriter(file, fieldnames=product_headers(), extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
            os.replace(temporary_path, file_path)

        def current_product_record():
            product_name = fields["product_name"].get().strip()
            if not product_name:
                messagebox.showwarning(
                    "Product Name Required",
                    "Enter the Product Name / Title before saving.",
                    parent=self.main_app.root,
                )
                return None
            record = {key: value.get().strip() for key, value in fields.items()}
            record.update({
                key: "; ".join(option for option, value in options if value.get())
                for key, options in multi_selects.items()
            })
            return record

        def clear_product_sector_form():
            for value in fields.values():
                value.set("")
            fields["power_rating_unit"].set("HP")
            fields["pressure_unit"].set("bar")
            for options in multi_selects.values():
                for _option, value in options:
                    value.set(False)
            selected_record_index["value"] = None
            for item in products_tree.selection():
                products_tree.selection_remove(item)

        def load_saved_products():
            for item in products_tree.get_children():
                products_tree.delete(item)
            for index, record in enumerate(read_product_records()):
                products_tree.insert(
                    "", "end", iid=str(index), values=[record.get(column, "") for column in product_columns]
                )

        def load_selected_product(_event=None):
            selected = products_tree.selection()
            if not selected:
                return
            index = int(selected[0])
            records = read_product_records()
            if index >= len(records):
                return
            record = records[index]
            for key, value in fields.items():
                value.set(record.get(key, ""))
            for key, options in multi_selects.items():
                selected_options = {item.strip() for item in record.get(key, "").split(";") if item.strip()}
                for option, value in options:
                    value.set(option in selected_options)
            selected_record_index["value"] = index

        def add_product():
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            records.append(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Saved", "Product added successfully.", parent=self.main_app.root)

        def update_selected_product():
            index = selected_record_index["value"]
            if index is None:
                messagebox.showwarning("Select Product", "Select a saved product to edit first.", parent=self.main_app.root)
                return
            record = current_product_record()
            if record is None:
                return
            records = read_product_records()
            if index >= len(records):
                messagebox.showwarning("Product Not Found", "Reload the saved product list and try again.", parent=self.main_app.root)
                return
            records[index].update(record)
            write_product_records(records)
            load_saved_products()
            clear_product_sector_form()
            messagebox.showinfo("Updated", "Product updated successfully.", parent=self.main_app.root)

        products_tree.bind("<<TreeviewSelect>>", load_selected_product)
        load_saved_products()

        actions = ttk.Frame(container)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="Clear / Add New", command=clear_product_sector_form).pack(
            side="right"
        )
        ttk.Button(actions, text="Update Selected Product", command=update_selected_product).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(actions, text="Add Product", command=add_product).pack(
            side="right", padx=(0, 8)
        )

    def add_text_field(self, row, label, field):
        ttk.Label(self, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        ttk.Entry(self, textvariable=field).grid(
            row=row, column=1, sticky="ew", pady=7
        )

    def add_attachment_field(self, row, label, field):
        ttk.Label(self, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        attachment_box = ttk.Frame(self)
        attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=field).grid(
            row=0, column=0, sticky="ew"
        )

        def choose_file():
            path = filedialog.askopenfilename(
                parent=self.main_app.root,
                title=f"Attach {label}",
                filetypes=(
                    ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                    ("All files", "*.*"),
                ),
            )
            if path:
                field.set(path)

        ttk.Button(attachment_box, text="Attach File", command=choose_file).grid(
            row=0, column=1, padx=(6, 0)
        )

    def add_dropdown_field(self, section, row, label, field, values):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        ttk.Combobox(
            section, textvariable=field, values=values, state="readonly"
        ).grid(row=row, column=1, sticky="ew", pady=7)

    def add_checklist(self, section, row, label, field, options):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="nw", padx=(0, 12), pady=7
        )
        choice_box = ttk.Frame(section)
        choice_box.grid(row=row, column=1, sticky="ew", pady=4)
        selected_options = []
        for index, option in enumerate(options):
            option_var = tk.BooleanVar()
            ttk.Checkbutton(choice_box, text=option, variable=option_var).grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=2
            )
            selected_options.append((option, option_var))
        return selected_options

    def add_file_field(self, section, row, label, field, *, multiple=False, filetypes=None):
        ttk.Label(section, text=f"{label}:").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=7
        )
        attachment_box = ttk.Frame(section)
        attachment_box.grid(row=row, column=1, sticky="ew", pady=7)
        attachment_box.columnconfigure(0, weight=1)
        ttk.Entry(attachment_box, textvariable=field).grid(row=0, column=0, sticky="ew")

        def choose_file():
            selected_filetypes = filetypes or (
                ("Documents and images", "*.pdf *.doc *.docx *.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            )
            if multiple:
                paths = filedialog.askopenfilenames(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                if paths:
                    field.set(" | ".join(paths))
            else:
                path = filedialog.askopenfilename(parent=self.main_app.root, title=f"Attach {label}", filetypes=selected_filetypes)
                if path:
                    field.set(path)

        ttk.Button(attachment_box, text="Attach Files" if multiple else "Attach File", command=choose_file).grid(
            row=0, column=1, padx=(6, 0)
        )
