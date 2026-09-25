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

    def show_quotation_dialog(self):
        dialog = tk.Toplevel(self.main_app.root)
        dialog.title("Create New Quotation")
        dialog.geometry("800x600")
        dialog.transient(self.main_app.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(
            main_frame,
            text="Create New Quotation",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))

        form_frame = ttk.LabelFrame(main_frame, text="Quotation Details", padding=15)
        form_frame.pack(fill="x", pady=(0, 15))

        customer_name = tk.StringVar()
        customer_email = tk.StringVar()
        customer_phone = tk.StringVar()
        quotation_date = tk.StringVar()
        valid_until = tk.StringVar()
        notes = tk.StringVar()

        def add_field(row, label, variable):
            ttk.Label(form_frame, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=8
            )
            ttk.Entry(form_frame, textvariable=variable, width=40).grid(
                row=row, column=1, sticky="w", pady=8
            )

        add_field(0, "Customer Name", customer_name)
        add_field(1, "Customer Email", customer_email)
        add_field(2, "Customer Phone", customer_phone)
        add_field(3, "Quotation Date", quotation_date)
        add_field(4, "Valid Until", valid_until)

        ttk.Label(form_frame, text="Notes:").grid(
            row=5, column=0, sticky="nw", padx=(0, 10), pady=8
        )
        notes_text = tk.Text(form_frame, height=4, width=50)
        notes_text.grid(row=5, column=1, sticky="w", pady=8)

        items_frame = ttk.LabelFrame(main_frame, text="Quotation Items", padding=15)
        items_frame.pack(fill="both", expand=True, pady=(0, 15))

        columns = ("item", "description", "quantity", "unit_price", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=8)

        items_tree.heading("item", text="Item")
        items_tree.heading("description", text="Description")
        items_tree.heading("quantity", text="Quantity")
        items_tree.heading("unit_price", text="Unit Price (₹)")
        items_tree.heading("total", text="Total (₹)")

        items_tree.column("item", width=100)
        items_tree.column("description", width=250)
        items_tree.column("quantity", width=80)
        items_tree.column("unit_price", width=100)
        items_tree.column("total", width=100)

        items_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        def add_item():
            item_name = simpledialog.askstring("Add Item", "Enter item name:", parent=dialog)
            if not item_name:
                return
            description = simpledialog.askstring("Add Item", "Enter description:", parent=dialog)
            if not description:
                description = ""
            quantity = simpledialog.askinteger("Add Item", "Enter quantity:", parent=dialog, minvalue=1)
            if not quantity:
                return
            unit_price = simpledialog.askfloat("Add Item", "Enter unit price:", parent=dialog, minvalue=0.0)
            if unit_price is None:
                return

            total = quantity * unit_price
            items_tree.insert("", "end", values=(item_name, description, quantity, f"{unit_price:.2f}", f"{total:.2f}"))

        def remove_item():
            selected = items_tree.selection()
            if selected:
                items_tree.delete(selected[0])

        def calculate_grand_total():
            total = 0.0
            for item in items_tree.get_children():
                values = items_tree.item(item, "values")
                if len(values) > 4:
                    try:
                        total += float(values[4])
                    except ValueError:
                        pass
            return total

        item_buttons = ttk.Frame(items_frame)
        item_buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(item_buttons, text="Add Item", command=add_item).pack(side="left", padx=5)
        ttk.Button(item_buttons, text="Remove Selected", command=remove_item).pack(side="left", padx=5)

        total_frame = ttk.Frame(main_frame)
        total_frame.pack(fill="x", pady=(0, 15))
        grand_total_label = ttk.Label(total_frame, text="Grand Total: ₹0.00", font=("Helvetica", 12, "bold"))
        grand_total_label.pack(side="right")

        def update_total():
            grand_total = calculate_grand_total()
            grand_total_label.config(text=f"Grand Total: ₹{grand_total:.2f}")

        items_tree.bind("<<TreeviewInsert>>", lambda e: update_total())
        items_tree.bind("<<TreeviewDelete>>", lambda e: update_total())

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")

        def save_quotation():
            if not customer_name.get().strip():
                messagebox.showwarning("Required Field", "Customer name is required.", parent=dialog)
                return

            items = []
            for item in items_tree.get_children():
                values = items_tree.item(item, "values")
                if len(values) >= 5:
                    items.append({
                        "item": values[0],
                        "description": values[1],
                        "quantity": values[2],
                        "unit_price": values[3],
                        "total": values[4]
                    })

            if not items:
                messagebox.showwarning("No Items", "Add at least one item to the quotation.", parent=dialog)
                return

            quotation_data = {
                "customer_name": customer_name.get().strip(),
                "customer_email": customer_email.get().strip(),
                "customer_phone": customer_phone.get().strip(),
                "quotation_date": quotation_date.get().strip(),
                "valid_until": valid_until.get().strip(),
                "notes": notes_text.get("1.0", tk.END).strip(),
                "items": items,
                "grand_total": calculate_grand_total()
            }

            csv_file = os.path.join(self.main_app.config.CSV_DIR, "quotations.csv")
            file_exists = os.path.exists(csv_file)

            import json
            if file_exists:
                with open(csv_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    quotation_num = sum(1 for _ in reader) + 1
            else:
                quotation_num = 1

            quotation_id = f"QT-{quotation_num:04d}"

            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["quotation_id", "customer_name", "customer_email", "customer_phone",
                                   "quotation_date", "valid_until", "notes", "items_json", "grand_total"])

                writer.writerow([
                    quotation_id,
                    quotation_data["customer_name"],
                    quotation_data["customer_email"],
                    quotation_data["customer_phone"],
                    quotation_data["quotation_date"],
                    quotation_data["valid_until"],
                    quotation_data["notes"],
                    json.dumps(quotation_data["items"]),
                    f"{quotation_data['grand_total']:.2f}"
                ])

            messagebox.showinfo("Success", f"Quotation {quotation_id} saved successfully!", parent=dialog)
            dialog.destroy()

        ttk.Button(button_frame, text="Save Quotation", command=save_quotation).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

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
