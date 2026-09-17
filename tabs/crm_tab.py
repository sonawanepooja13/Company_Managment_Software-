import csv
import datetime
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config

# Try to import MQTT components (optional - for centralized data)
try:
    from mqtt_data_manager import CentralDataManager
    from mqtt_config import MQTT_BROKER, MQTT_PORT, CLIENT_ID
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

# Try importing tkcalendar; fallback to manual input if not available
try:
    from tkcalendar import DateEntry

    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False


class DateTimePickerPopup(tk.Toplevel):
    """Popup for selecting Date and Time."""

    def __init__(self, parent, initial_val="", on_select_callback=None):
        super().__init__(parent)
        self.title("Select Date & Time")
        self.geometry("320x240")
        self.minsize(320, 240)
        self.resizable(True, True)
        self.grab_set()

        self.on_select_callback = on_select_callback

        ttk.Label(
            self,
            text="Select Meeting Schedule Time",
            font=("Helvetica", 10, "bold"),
        ).pack(pady=10)

        date_frame = ttk.Frame(self)
        date_frame.pack(pady=5)

        ttk.Label(date_frame, text="Date:").pack(side="left", padx=5)
        if HAS_TKCALENDAR:
            self.cal = DateEntry(
                date_frame,
                width=12,
                background="darkblue",
                foreground="white",
                date_pattern="yyyy-mm-dd",
            )
            self.cal.pack(side="left", padx=5)
        else:
            self.entry_date = ttk.Entry(date_frame, width=12)
            self.entry_date.insert(
                0, datetime.date.today().strftime("%Y-%m-%d")
            )
            self.entry_date.pack(side="left", padx=5)
            ttk.Label(
                self, text="(Format: YYYY-MM-DD)", font=("Helvetica", 8)
            ).pack()

        time_frame = ttk.Frame(self)
        time_frame.pack(pady=10)

        ttk.Label(time_frame, text="Time:").pack(side="left", padx=5)
        self.spin_hour = ttk.Spinbox(
            time_frame, from_=1, to=12, width=3, format="%02.0f"
        )
        self.spin_hour.set("10")
        self.spin_hour.pack(side="left")

        ttk.Label(time_frame, text=":").pack(side="left")

        self.spin_min = ttk.Spinbox(
            time_frame, from_=0, to=59, width=3, format="%02.0f"
        )
        self.spin_min.set("00")
        self.spin_min.pack(side="left")

        self.combo_ampm = ttk.Combobox(
            time_frame, values=["AM", "PM"], width=4, state="readonly"
        )
        self.combo_ampm.set("AM")
        self.combo_ampm.pack(side="left", padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)

        ttk.Button(
            btn_frame, text="✅ Set Schedule", command=self.confirm_selection
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="❌ Cancel", command=self.destroy
        ).pack(side="left", padx=5)

    def confirm_selection(self):
        if HAS_TKCALENDAR:
            selected_date = self.cal.get_date().strftime("%Y-%m-%d")
        else:
            selected_date = self.entry_date.get().strip()

        hour = self.spin_hour.get().zfill(2)
        minute = self.spin_min.get().zfill(2)
        ampm = self.combo_ampm.get()

        formatted_datetime = f"{selected_date} {hour}:{minute} {ampm}"

        if self.on_select_callback:
            self.on_select_callback(formatted_datetime)
        self.destroy()


class CrmTab(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.crm_csv_path = getattr(
            config,
            "CUSTOMERS_DETAILED_CSV",
            os.path.join(config.SCRIPT_DIR, "customers_detailed.csv"),
        )
        self.photos_base_dir = os.path.join(config.SCRIPT_DIR, "Customer_Photos")
        os.makedirs(self.photos_base_dir, exist_ok=True)

        self.selected_row_index = None
        self.all_rows = []
        self.selected_photo_paths = []
        self.status_summary_frame = None

        # Initialize MQTT data manager if available
        self.mqtt_manager = None
        if HAS_MQTT:
            try:
                self.mqtt_manager = CentralDataManager(
                    mqtt_broker=MQTT_BROKER,
                    mqtt_port=MQTT_PORT,
                    db_path=os.path.join(config.SCRIPT_DIR, "central_database.db"),
                    client_id=f"crm_{CLIENT_ID}"
                )
                print("MQTT data manager initialized successfully")
            except Exception as e:
                print(f"Failed to initialize MQTT manager: {e}")
                self.mqtt_manager = None

        self.ensure_crm_csv_exists()
        self.migrate_and_align_csv()

        self.setup_scrollable_container()
        self.build_ui()

    def get_crm_headers(self):
        """Returns row 1 header structure exactly matching get_form_data() output index order."""
        return [
            "company_name",
            "gst_number",
            "contact_person",
            "designation",
            "website",
            "contact_number",
            "address",
            "state",
            "district",
            "location",
            "company_turnover",
            "owner_name",
            "number_of_staff",
            "products_selected",
            "company_valuation",
            "note",
            "call_conversion_time",
            "company_data_sent",
            "enquiry_received",
            "communication_details",
            "meeting_schedule_time",
            "meeting_agenda",
            "meeting_completed_details",
            "photo_files",
        ]

    def setup_scrollable_container(self):
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.content_frame = ttk.Frame(self.canvas)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width - 20)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def sanitize_folder_name(self, name):
        return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()

    def get_company_photos_dir(self, company_name):
        clean_name = self.sanitize_folder_name(company_name)
        if not clean_name:
            clean_name = "Unnamed_Company"
        return os.path.join(self.photos_base_dir, clean_name)

    def ensure_crm_csv_exists(self):
        headers = self.get_crm_headers()
        if not os.path.exists(self.crm_csv_path):
            try:
                with open(
                    self.crm_csv_path, mode="w", newline="", encoding="utf-8-sig"
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            except Exception as e:
                messagebox.showerror(
                    "Initialization Error",
                    f"Failed to initialize CRM CSV file: {e}",
                )

    def migrate_and_align_csv(self):
        """Fixes and updates Row 1 headers to guarantee CSV column order matches Python UI."""
        if not os.path.exists(self.crm_csv_path):
            return

        headers = self.get_crm_headers()

        try:
            updated_rows = []
            needs_rewrite = False

            with open(self.crm_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                file_headers = next(reader, None)

                # Check if headers match the correct layout
                if file_headers != headers:
                    needs_rewrite = True

                for row in reader:
                    if not row or not any(row):
                        continue

                    # Adjust row data length if columns were added or removed
                    if len(row) < len(headers):
                        row.extend([""] * (len(headers) - len(row)))
                        needs_rewrite = True
                    elif len(row) > len(headers):
                        row = row[: len(headers)]
                        needs_rewrite = True

                    updated_rows.append(row)

            if needs_rewrite:
                with open(
                    self.crm_csv_path, mode="w", newline="", encoding="utf-8-sig"
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(updated_rows)

        except Exception as e:
            print(f"Error executing CSV migration/realignment: {e}")

    def build_ui(self):
        # Navigation buttons
        nav_frame = ttk.Frame(self.content_frame)
        nav_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            nav_frame, text="📋 CRM Management", command=self.show_crm_management
        ).pack(side="left", padx=5)
        ttk.Button(
            nav_frame, text="❓ Enquiry Management", command=self.show_enquiry_management
        ).pack(side="left", padx=5)

        # Main container for different views
        self.view_container = ttk.Frame(self.content_frame)
        self.view_container.pack(fill="both", expand=True)

        # Build CRM Management view (default)
        self.build_crm_management()

    def build_crm_management(self):
        """Build the main CRM management view."""
        # Clear view container
        for widget in self.view_container.winfo_children():
            widget.destroy()

        title = ttk.Label(
            self.view_container,
            text="Customer Management & Lead Tracker",
            font=("Helvetica", 12, "bold"),
        )
        title.pack(pady=4)

        # SECTION 1: SEARCH BAR
        search_frame = ttk.LabelFrame(
            self.view_container, text=" Search & Select Company ", padding="4"
        )
        search_frame.pack(fill="x", padx=10, pady=2)

        ttk.Label(
            search_frame,
            text="Search Company / GST / Contact / Owner / Product / State / District / Location:",
            font=("Helvetica", 9, "bold"),
        ).pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind(
            "<Return>", lambda event: self.filter_crm_data()
        )

        ttk.Button(
            search_frame, text="🔎 Search", command=self.filter_crm_data
        ).pack(side="left", padx=3)
        ttk.Button(
            search_frame, text="🔄 Reset", command=self.reset_search
        ).pack(side="left", padx=3)

        # SECTION 2: TABLE
        records_frame = ttk.LabelFrame(
            self.view_container, text=" Customer Interaction History ", padding="4"
        )
        records_frame.pack(fill="x", padx=10, pady=2)

        cols = (
            "#",
            "Company Name",
            "GST Number",
            "Contact Person",
            "Designation",
            "Contact Number",
            "State",
            "District",
            "Location",
            "Owner Name",
            "Products",
            "Data Sent",
            "Enquiry",
            "Call Time",
            "Meeting Time",
        )
        self.crm_tree = ttk.Treeview(
            records_frame, columns=cols, show="headings", height=4
        )

        self.crm_tree.heading("#", text="#")
        self.crm_tree.column("#", width=25, anchor="center")

        for col in cols[1:]:
            self.crm_tree.heading(col, text=col)
            self.crm_tree.column(col, width=80)

        vsb_crm = ttk.Scrollbar(
            records_frame, orient="vertical", command=self.crm_tree.yview
        )
        self.crm_tree.configure(yscrollcommand=vsb_crm.set)

        self.crm_tree.pack(side="left", fill="both", expand=True)
        vsb_crm.pack(side="right", fill="y")

        self.crm_tree.bind(
            "<Double-1>", lambda event: self.open_selected_customer()
        )

        tbl_ctrl_frame = ttk.Frame(self.view_container, padding="2")
        tbl_ctrl_frame.pack(fill="x", padx=10)

        ttk.Button(
            tbl_ctrl_frame,
            text="📂 Open Company Data",
            command=self.open_selected_customer,
        ).pack(side="left", padx=3)
        ttk.Button(
            tbl_ctrl_frame,
            text="🗑️ Delete Selected Record",
            command=self.delete_crm_customer,
        ).pack(side="left", padx=3)

        # SECTION 3: FORM (2-COLUMN LAYOUT)
        self.form_frame = ttk.LabelFrame(
            self.view_container,
            text=" Customer Details & Data Entry ",
            padding="6",
        )
        self.form_frame.pack(fill="x", padx=10, pady=4)

        columns_wrapper = ttk.Frame(self.form_frame)
        columns_wrapper.pack(fill="x", expand=True)

        left_column = ttk.Frame(columns_wrapper)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_column = ttk.Frame(columns_wrapper)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # --- LEFT COLUMN FIELDS ---
        left_info_frame = ttk.LabelFrame(
            left_column, text=" Company Identity & Details ", padding="4"
        )
        left_info_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(left_info_frame, text="Company Name:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.crm_company = ttk.Entry(left_info_frame, width=24)
        self.crm_company.grid(row=0, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="GST Number:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.crm_gst = ttk.Entry(left_info_frame, width=24)
        self.crm_gst.grid(row=1, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Contact Person:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.crm_contact_person = ttk.Entry(left_info_frame, width=24)
        self.crm_contact_person.grid(row=2, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Designation:").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.crm_designation = ttk.Entry(left_info_frame, width=24)
        self.crm_designation.grid(row=3, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Website:").grid(
            row=4, column=0, sticky="w", pady=2
        )
        self.crm_website = ttk.Entry(left_info_frame, width=24)
        self.crm_website.grid(row=4, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Contact Number:").grid(
            row=5, column=0, sticky="w", pady=2
        )
        self.crm_contact = ttk.Entry(left_info_frame, width=24)
        self.crm_contact.grid(row=5, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Address:").grid(
            row=6, column=0, sticky="w", pady=2
        )
        self.crm_address = ttk.Entry(left_info_frame, width=24)
        self.crm_address.grid(row=6, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="State:").grid(
            row=7, column=0, sticky="w", pady=2
        )
        self.crm_state = ttk.Entry(left_info_frame, width=24)
        self.crm_state.grid(row=7, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="District:").grid(
            row=8, column=0, sticky="w", pady=2
        )
        self.crm_district = ttk.Entry(left_info_frame, width=24)
        self.crm_district.grid(row=8, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Location:").grid(
            row=9, column=0, sticky="w", pady=2
        )
        self.crm_location = ttk.Entry(left_info_frame, width=24)
        self.crm_location.grid(row=9, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Company Turnover:").grid(
            row=10, column=0, sticky="w", pady=2
        )
        self.crm_turnover = ttk.Entry(left_info_frame, width=24)
        self.crm_turnover.grid(row=10, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Owner Name:").grid(
            row=11, column=0, sticky="w", pady=2
        )
        self.crm_owner_name = ttk.Entry(left_info_frame, width=24)
        self.crm_owner_name.grid(row=11, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Number of Staff:").grid(
            row=12, column=0, sticky="w", pady=2
        )
        self.crm_staff_count = ttk.Entry(left_info_frame, width=24)
        self.crm_staff_count.grid(row=12, column=1, sticky="ew", pady=2, padx=4)

        left_info_frame.columnconfigure(1, weight=1)

        # Products Frame (Left Column)
        prod_frame = ttk.LabelFrame(
            left_column, text=" Products & Systems ", padding="4"
        )
        prod_frame.pack(fill="x")

        self.var_booster = tk.BooleanVar()
        self.var_stp = tk.BooleanVar()
        self.var_water_meter = tk.BooleanVar()
        self.var_bms = tk.BooleanVar()
        self.var_wtp = tk.BooleanVar()
        self.var_ro = tk.BooleanVar()
        self.var_fire_panel = tk.BooleanVar()
        self.var_dewatering_panel = tk.BooleanVar()
        self.var_water_softener = tk.BooleanVar()
        self.var_choice_a = tk.BooleanVar()
        self.var_pump_skid = tk.BooleanVar()
        self.var_pump_sensor_panel = tk.BooleanVar()

        self.chk_booster = ttk.Checkbutton(prod_frame, text="Booster Pump", variable=self.var_booster)
        self.chk_booster.grid(row=0, column=0, sticky="w", padx=2)
        self.chk_stp = ttk.Checkbutton(prod_frame, text="STP", variable=self.var_stp)
        self.chk_stp.grid(row=0, column=1, sticky="w", padx=2)
        self.chk_water_meter = ttk.Checkbutton(prod_frame, text="Water Meter", variable=self.var_water_meter)
        self.chk_water_meter.grid(row=0, column=2, sticky="w", padx=2)

        self.chk_bms = ttk.Checkbutton(prod_frame, text="BMS", variable=self.var_bms)
        self.chk_bms.grid(row=1, column=0, sticky="w", padx=2)
        self.chk_wtp = ttk.Checkbutton(prod_frame, text="WTP", variable=self.var_wtp)
        self.chk_wtp.grid(row=1, column=1, sticky="w", padx=2)
        self.chk_ro = ttk.Checkbutton(prod_frame, text="RO", variable=self.var_ro)
        self.chk_ro.grid(row=1, column=2, sticky="w", padx=2)

        self.chk_fire_panel = ttk.Checkbutton(prod_frame, text="Fire Panel", variable=self.var_fire_panel)
        self.chk_fire_panel.grid(row=2, column=0, sticky="w", padx=2)
        self.chk_dewatering_panel = ttk.Checkbutton(prod_frame, text="De-watering Panel", variable=self.var_dewatering_panel)
        self.chk_dewatering_panel.grid(row=2, column=1, sticky="w", padx=2)
        self.chk_water_softener = ttk.Checkbutton(prod_frame, text="Water Softener", variable=self.var_water_softener)
        self.chk_water_softener.grid(row=2, column=2, sticky="w", padx=2)

        self.chk_choice_a = ttk.Checkbutton(prod_frame, text="Choice A", variable=self.var_choice_a)
        self.chk_choice_a.grid(row=3, column=0, sticky="w", padx=2)
        self.chk_pump_skid = ttk.Checkbutton(prod_frame, text="Pump Skid", variable=self.var_pump_skid)
        self.chk_pump_skid.grid(row=3, column=1, sticky="w", padx=2)
        self.chk_pump_sensor_panel = ttk.Checkbutton(prod_frame, text="Sensor Panel", variable=self.var_pump_sensor_panel)
        self.chk_pump_sensor_panel.grid(row=3, column=2, sticky="w", padx=2)

        # --- RIGHT COLUMN FIELDS ---
        # Photos Frame
        photos_frame = ttk.LabelFrame(right_column, text=" Photos ", padding="4")
        photos_frame.pack(fill="x", pady=(0, 4))

        self.photo_listbox = tk.Listbox(photos_frame, width=20, height=3)
        self.photo_listbox.pack(side="left", fill="both", expand=True, padx=(0, 4))

        photo_btn_frame = ttk.Frame(photos_frame)
        photo_btn_frame.pack(side="right")

        self.btn_add_photos = ttk.Button(
            photo_btn_frame, text="📷 Add", width=11, command=self.select_photos
        )
        self.btn_add_photos.pack(pady=1)
        self.btn_remove_photo = ttk.Button(
            photo_btn_frame, text="❌ Remove", width=11, command=self.remove_selected_photo
        )
        self.btn_remove_photo.pack(pady=1)
        self.btn_open_folder = ttk.Button(
            photo_btn_frame, text="📁 Open", width=11, command=self.open_company_photos_folder
        )
        self.btn_open_folder.pack(pady=1)

        # Company Valuation Frame
        valuation_frame = ttk.LabelFrame(
            right_column, text=" Company Valuation ", padding="4"
        )
        valuation_frame.pack(fill="x", pady=2)

        self.var_val_vfd = tk.BooleanVar()
        self.var_val_dewatering = tk.BooleanVar()
        self.var_val_distributor = tk.BooleanVar()
        self.var_val_dealer = tk.BooleanVar()
        self.var_val_serious_base = tk.BooleanVar()

        val_chk_grid = ttk.Frame(valuation_frame)
        val_chk_grid.pack(fill="x")

        self.chk_val_vfd = ttk.Checkbutton(
            val_chk_grid, text="Work in VFD Panel", variable=self.var_val_vfd
        )
        self.chk_val_vfd.grid(row=0, column=0, sticky="w", padx=2)

        self.chk_val_dewatering = ttk.Checkbutton(
            val_chk_grid, text="Work in Dewatering", variable=self.var_val_dewatering
        )
        self.chk_val_dewatering.grid(row=0, column=1, sticky="w", padx=2)

        self.chk_val_serious_base = ttk.Checkbutton(
            val_chk_grid, text="Serious Base", variable=self.var_val_serious_base
        )
        self.chk_val_serious_base.grid(row=1, column=0, sticky="w", padx=2)

        # Distributor Field Row
        dist_subframe = ttk.Frame(val_chk_grid)
        dist_subframe.grid(row=1, column=1, sticky="w", padx=2)

        self.chk_val_distributor = ttk.Checkbutton(
            dist_subframe,
            text="Distributor:",
            variable=self.var_val_distributor,
            command=self.toggle_distributor_field,
        )
        self.chk_val_distributor.pack(side="left")

        self.crm_distributor_name = ttk.Entry(
            dist_subframe, width=14, state="disabled"
        )
        self.crm_distributor_name.pack(side="left", padx=2)

        # Dealer Field Row
        dealer_subframe = ttk.Frame(val_chk_grid)
        dealer_subframe.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=2)

        self.chk_val_dealer = ttk.Checkbutton(
            dealer_subframe,
            text="Dealer:",
            variable=self.var_val_dealer,
            command=self.toggle_dealer_field,
        )
        self.chk_val_dealer.pack(side="left")

        self.crm_dealer_name = ttk.Entry(
            dealer_subframe, width=14, state="disabled"
        )
        self.crm_dealer_name.pack(side="left", padx=2)

        # Activity & Interaction Frame
        activity_frame = ttk.LabelFrame(
            right_column, text=" Activity & Communication ", padding="4"
        )
        activity_frame.pack(fill="x", pady=2)

        # Call duration & Data sent
        row_act1 = ttk.Frame(activity_frame)
        row_act1.pack(fill="x", pady=2)

        ttk.Label(row_act1, text="Call Time:").pack(side="left")
        hours_list = [f"{i:02d}" for i in range(24)]
        mins_list = [f"{i:02d}" for i in range(60)]

        self.crm_call_hours = ttk.Combobox(
            row_act1, values=hours_list, width=3, state="readonly"
        )
        self.crm_call_hours.set("00")
        self.crm_call_hours.pack(side="left", padx=(2, 0))
        ttk.Label(row_act1, text="h").pack(side="left")

        self.crm_call_mins = ttk.Combobox(
            row_act1, values=mins_list, width=3, state="readonly"
        )
        self.crm_call_mins.set("00")
        self.crm_call_mins.pack(side="left", padx=(2, 0))
        ttk.Label(row_act1, text="m").pack(side="left", padx=(0, 10))

        ttk.Label(row_act1, text="Data Sent:").pack(side="left")
        self.crm_data_sent = ttk.Combobox(
            row_act1, values=["Yes", "No"], width=5, state="readonly"
        )
        self.crm_data_sent.set("No")
        self.crm_data_sent.pack(side="left", padx=2)

        ttk.Label(row_act1, text="Enquiry:").pack(side="left", padx=(8, 0))
        self.crm_enquiry = ttk.Combobox(
            row_act1, values=["Yes", "No"], width=5, state="readonly"
        )
        self.crm_enquiry.set("No")
        self.crm_enquiry.pack(side="left", padx=2)

        # Meeting Schedule
        row_act2 = ttk.Frame(activity_frame)
        row_act2.pack(fill="x", pady=2)

        ttk.Label(row_act2, text="Meeting Time:").pack(side="left")
        self.crm_meeting_time = ttk.Entry(row_act2, width=16)
        self.crm_meeting_time.pack(side="left", padx=2)

        ttk.Button(
            row_act2, text="📅", width=3, command=self.open_datetime_picker
        ).pack(side="left")

        ttk.Label(row_act2, text="Agenda:").pack(side="left", padx=(8, 0))
        self.crm_meeting_agenda = ttk.Entry(row_act2, width=15)
        self.crm_meeting_agenda.pack(side="left", padx=2)

        # Text Notes Areas
        notes_grid = ttk.Frame(activity_frame)
        notes_grid.pack(fill="x", pady=2)

        ttk.Label(notes_grid, text="Communication Details:").grid(
            row=0, column=0, sticky="nw"
        )
        self.crm_comm_text = tk.Text(notes_grid, width=18, height=2)
        self.crm_comm_text.grid(row=0, column=1, sticky="ew", padx=2, pady=1)

        ttk.Label(notes_grid, text="Meeting Outcome:").grid(
            row=1, column=0, sticky="nw"
        )
        self.crm_meeting_outcome_text = tk.Text(notes_grid, width=18, height=2)
        self.crm_meeting_outcome_text.grid(
            row=1, column=1, sticky="ew", padx=2, pady=1
        )

        ttk.Label(notes_grid, text="General Notes:").grid(
            row=2, column=0, sticky="nw"
        )
        self.crm_notes_text = tk.Text(notes_grid, width=18, height=2)
        self.crm_notes_text.grid(row=2, column=1, sticky="ew", padx=2, pady=1)

        notes_grid.columnconfigure(1, weight=1)

        # BOTTOM BUTTON BAR
        btn_box = ttk.Frame(self.form_frame)
        btn_box.pack(fill="x", pady=(6, 0))

        ttk.Button(
            btn_box, text="🔓 Enable Editing", command=self.enable_editing
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_box,
            text="💾 Update Selected Record",
            command=self.update_existing_entry,
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_box,
            text="⏱️ Stamp Date in Log",
            command=self.add_timestamp_to_comm,
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_box, text="➕ Save as New Entry", command=self.save_new_entry
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_box, text="🧹 Clear Form", command=self.clear_crm_entries
        ).pack(side="left", padx=2)

        self.load_crm_data()

    def show_crm_management(self):
        """Show the CRM management view."""
        self.build_crm_management()

    def show_enquiry_management(self):
        """Show the enquiry management view."""
        # Clear view container
        for widget in self.view_container.winfo_children():
            widget.destroy()

        title = ttk.Label(
            self.view_container,
            text="Enquiry Management - Customers with Enquiry: Yes",
            font=("Helvetica", 12, "bold"),
        )
        title.pack(pady=4)

        # Status summary
        status_frame = ttk.LabelFrame(
            self.view_container, text=" Enquiry Status Summary ", padding="10"
        )
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_summary_frame = status_frame
        self.load_enquiry_status_summary(status_frame)

        # Enquiry list with status management
        enquiry_frame = ttk.LabelFrame(
            self.view_container, text=" Enquiry List & Status Management ", padding="10"
        )
        enquiry_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for enquiry customers
        enquiry_cols = (
            "#",
            "Company Name",
            "Contact Person",
            "Contact Number",
            "Enquiry Date",
            "Status",
        )
        self.enquiry_tree = ttk.Treeview(
            enquiry_frame, columns=enquiry_cols, show="headings", height=8
        )

        self.enquiry_tree.heading("#", text="#")
        self.enquiry_tree.column("#", width=30, anchor="center")

        for col in enquiry_cols[1:]:
            self.enquiry_tree.heading(col, text=col)
            self.enquiry_tree.column(col, width=100)

        vsb_enquiry = ttk.Scrollbar(
            enquiry_frame, orient="vertical", command=self.enquiry_tree.yview
        )
        self.enquiry_tree.configure(yscrollcommand=vsb_enquiry.set)

        self.enquiry_tree.pack(side="left", fill="both", expand=True)
        vsb_enquiry.pack(side="right", fill="y")

        # Status control buttons
        status_ctrl_frame = ttk.Frame(self.view_container, padding="5")
        status_ctrl_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(
            status_ctrl_frame, text="Mark Selected as:", font=("Helvetica", 10, "bold")
        ).pack(side="left", padx=5)

        ttk.Button(
            status_ctrl_frame,
            text="✅ Complete",
            command=lambda: self.update_enquiry_status("Complete"),
        ).pack(side="left", padx=5)
        ttk.Button(
            status_ctrl_frame,
            text="❌ Not Complete",
            command=lambda: self.update_enquiry_status("Not Complete"),
        ).pack(side="left", padx=5)
        ttk.Button(
            status_ctrl_frame,
            text="🔄 Refresh List",
            command=self.load_enquiry_customers,
        ).pack(side="left", padx=5)

        # Load enquiry customers
        self.load_enquiry_customers()

    def load_enquiry_status_summary(self, parent_frame):
        """Load and display enquiry status summary."""
        try:
            enquiry_status_file = os.path.join(config.SCRIPT_DIR, "enquiry_status.csv")
            status_map = {}
            
            if os.path.exists(enquiry_status_file):
                with open(enquiry_status_file, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        status_map[row.get("company_name", "")] = row.get("status", "Pending")
            
            total_enquiries = 0
            completed = 0
            not_completed = 0
            pending = 0

            with open(self.crm_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("enquiry_received", "No") == "Yes":
                        total_enquiries += 1
                        company_name = row.get("company_name", "")
                        status = status_map.get(company_name, "Pending")
                        if status == "Complete":
                            completed += 1
                        elif status == "Not Complete":
                            not_completed += 1
                        else:
                            pending += 1

            summary_grid = ttk.Frame(parent_frame)
            summary_grid.pack(fill="x")

            ttk.Label(summary_grid, text=f"Total Enquiries: {total_enquiries}", font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=20, pady=5)
            ttk.Label(summary_grid, text=f"✅ Complete: {completed}", font=("Helvetica", 10), foreground="green").grid(row=0, column=1, padx=20, pady=5)
            ttk.Label(summary_grid, text=f"❌ Not Complete: {not_completed}", font=("Helvetica", 10), foreground="red").grid(row=0, column=2, padx=20, pady=5)
            ttk.Label(summary_grid, text=f"⏳ Pending: {pending}", font=("Helvetica", 10), foreground="orange").grid(row=0, column=3, padx=20, pady=5)

        except Exception as e:
            ttk.Label(parent_frame, text=f"Error loading summary: {e}", font=("Helvetica", 9), foreground="red").pack()

    def load_enquiry_customers(self):
        """Load customers with enquiry=yes into the enquiry tree."""
        self.enquiry_tree.delete(*self.enquiry_tree.get_children())
        
        try:
            enquiry_status_file = os.path.join(config.SCRIPT_DIR, "enquiry_status.csv")
            status_map = {}
            
            if os.path.exists(enquiry_status_file):
                with open(enquiry_status_file, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        status_map[row.get("company_name", "")] = row.get("status", "Pending")
            
            with open(self.crm_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, 1):
                    if row.get("enquiry_received", "No") == "Yes":
                        company_name = row.get("company_name", "")
                        status = status_map.get(company_name, "Pending")
                        self.enquiry_tree.insert(
                            "",
                            "end",
                            values=(
                                idx,
                                company_name,
                                row.get("contact_person", ""),
                                row.get("contact_number", ""),
                                row.get("call_conversion_time", ""),
                                status,
                            ),
                        )
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load enquiry customers:\n{e}")

    def update_enquiry_status(self, new_status):
        """Update the status of selected enquiry customers."""
        selected_items = self.enquiry_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one customer to update status.")
            return

        try:
            enquiry_status_file = os.path.join(config.SCRIPT_DIR, "enquiry_status.csv")
            status_map = {}
            
            if os.path.exists(enquiry_status_file):
                with open(enquiry_status_file, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        status_map[row.get("company_name", "")] = row.get("status", "Pending")
            
            updated_count = 0
            for item in selected_items:
                values = self.enquiry_tree.item(item)["values"]
                company_name = values[1]
                status_map[company_name] = new_status
                updated_count += 1

            with open(enquiry_status_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["company_name", "status"])
                writer.writeheader()
                for company_name, status in status_map.items():
                    writer.writerow({"company_name": company_name, "status": status})

            messagebox.showinfo("Success", f"Updated {updated_count} customer(s) to '{new_status}'")
            self.load_enquiry_customers()
            
            if hasattr(self, 'status_summary_frame') and self.status_summary_frame:
                for child in self.status_summary_frame.winfo_children():
                    child.destroy()
                self.load_enquiry_status_summary(self.status_summary_frame)
            
            # Sync with MQTT if available
            if self.mqtt_manager and self.mqtt_manager.is_connected():
                for item in selected_items:
                    values = self.enquiry_tree.item(item)["values"]
                    company_name = values[1]
                    status_dict = {
                        'company_name': company_name,
                        'status': new_status
                    }
                    self.mqtt_manager.publish_enquiry_status_update(status_dict, 'upsert')
                print("Enquiry status synced via MQTT")

        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update enquiry status:\n{e}")

    def toggle_distributor_field(self):
        if self.var_val_distributor.get():
            self.crm_distributor_name.config(state="normal")
        else:
            self.crm_distributor_name.delete(0, tk.END)
            self.crm_distributor_name.config(state="disabled")

    def toggle_dealer_field(self):
        if self.var_val_dealer.get():
            self.crm_dealer_name.config(state="normal")
        else:
            self.crm_dealer_name.delete(0, tk.END)
            self.crm_dealer_name.config(state="disabled")

    def select_photos(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Photos",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All Files", "*.*"),
            ],
        )
        if file_paths:
            for path in file_paths:
                filename = os.path.basename(path)
                if path not in self.selected_photo_paths:
                    self.selected_photo_paths.append(path)
                    self.photo_listbox.insert(tk.END, filename)

    def remove_selected_photo(self):
        selected_indices = self.photo_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        self.photo_listbox.delete(idx)
        if idx < len(self.selected_photo_paths):
            del self.selected_photo_paths[idx]

    def open_company_photos_folder(self):
        company_name = self.crm_company.get().strip()
        if not company_name:
            messagebox.showwarning(
                "Company Name Required",
                "Please enter or load a company name to open its photos folder.",
            )
            return

        folder_path = self.get_company_photos_dir(company_name)
        os.makedirs(folder_path, exist_ok=True)

        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror(
                "Folder Error", f"Could not open folder:\n{e}"
            )

    def process_and_save_photos(self, company_name):
        if not company_name:
            return ""

        target_dir = self.get_company_photos_dir(company_name)
        os.makedirs(target_dir, exist_ok=True)

        saved_filenames = []
        for src_path in self.selected_photo_paths:
            if os.path.exists(src_path):
                fname = os.path.basename(src_path)
                dest_path = os.path.join(target_dir, fname)
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    shutil.copy2(src_path, dest_path)
                saved_filenames.append(fname)
            else:
                saved_filenames.append(os.path.basename(src_path))

        return "|".join(saved_filenames)

    def get_selected_products_str(self):
        selected = []
        if self.var_booster.get():
            selected.append("Booster Pump System")
        if self.var_stp.get():
            selected.append("STP")
        if self.var_water_meter.get():
            selected.append("Water Meter")
        if self.var_bms.get():
            selected.append("BMS")
        if self.var_wtp.get():
            selected.append("WTP")
        if self.var_ro.get():
            selected.append("RO")
        if self.var_fire_panel.get():
            selected.append("FIRE PANEL")
        if self.var_dewatering_panel.get():
            selected.append("De-watering Panel")
        if self.var_water_softener.get():
            selected.append("Water Softener")
        if self.var_choice_a.get():
            selected.append("Choice A")
        if self.var_pump_skid.get():
            selected.append("Pump Skid")
        if self.var_pump_sensor_panel.get():
            selected.append("Pump Sensor Panel")
        return ", ".join(selected)

    def set_products_from_str(self, products_str):
        self.var_booster.set("Booster Pump System" in products_str)
        self.var_stp.set("STP" in products_str)
        self.var_water_meter.set("Water Meter" in products_str)
        self.var_bms.set("BMS" in products_str)
        self.var_wtp.set("WTP" in products_str)
        self.var_ro.set("RO" in products_str)
        self.var_fire_panel.set("FIRE PANEL" in products_str)
        self.var_dewatering_panel.set("De-watering Panel" in products_str)
        self.var_water_softener.set("Water Softener" in products_str)
        self.var_choice_a.set("Choice A" in products_str)
        self.var_pump_skid.set("Pump Skid" in products_str)
        self.var_pump_sensor_panel.set("Pump Sensor Panel" in products_str)

    def get_company_valuation_str(self):
        selected = []
        if self.var_val_vfd.get():
            selected.append("Work in VFD Panel")
        if self.var_val_dewatering.get():
            selected.append("Work in Dewatering")
        if self.var_val_distributor.get():
            dist_name = self.crm_distributor_name.get().strip()
            if dist_name:
                selected.append(f"Distributor ({dist_name})")
            else:
                selected.append("Distributor")
        if self.var_val_dealer.get():
            dealer_name = self.crm_dealer_name.get().strip()
            if dealer_name:
                selected.append(f"Dealer ({dealer_name})")
            else:
                selected.append("Dealer")
        if self.var_val_serious_base.get():
            selected.append("Serious Base")
        return ", ".join(selected)

    def set_company_valuation_from_str(self, valuation_str):
        self.var_val_vfd.set("Work in VFD Panel" in valuation_str)
        self.var_val_dewatering.set("Work in Dewatering" in valuation_str)
        self.var_val_serious_base.set("Serious Base" in valuation_str)

        if "Distributor" in valuation_str:
            self.var_val_distributor.set(True)
            self.crm_distributor_name.config(state="normal")
            if "Distributor (" in valuation_str:
                try:
                    dist_name = valuation_str.split("Distributor (")[1].split(")")[0]
                    self.crm_distributor_name.delete(0, tk.END)
                    self.crm_distributor_name.insert(0, dist_name)
                except Exception:
                    self.crm_distributor_name.delete(0, tk.END)
            else:
                self.crm_distributor_name.delete(0, tk.END)
        else:
            self.var_val_distributor.set(False)
            self.crm_distributor_name.delete(0, tk.END)
            self.crm_distributor_name.config(state="disabled")

        if "Dealer" in valuation_str:
            self.var_val_dealer.set(True)
            self.crm_dealer_name.config(state="normal")
            if "Dealer (" in valuation_str:
                try:
                    dealer_name = valuation_str.split("Dealer (")[1].split(")")[0]
                    self.crm_dealer_name.delete(0, tk.END)
                    self.crm_dealer_name.insert(0, dealer_name)
                except Exception:
                    self.crm_dealer_name.delete(0, tk.END)
            else:
                self.crm_dealer_name.delete(0, tk.END)
        else:
            self.var_val_dealer.set(False)
            self.crm_dealer_name.delete(0, tk.END)
            self.crm_dealer_name.config(state="disabled")

    def set_call_time_from_str(self, time_str):
        if not time_str:
            self.crm_call_hours.set("00")
            self.crm_call_mins.set("00")
            return

        try:
            parts = time_str.split()
            hrs = parts[0].zfill(2) if len(parts) > 0 else "00"
            mins = parts[2].zfill(2) if len(parts) > 2 else "00"

            if hrs in self.crm_call_hours["values"]:
                self.crm_call_hours.set(hrs)
            if mins in self.crm_call_mins["values"]:
                self.crm_call_mins.set(mins)
        except Exception:
            self.crm_call_hours.set("00")
            self.crm_call_mins.set("00")

    def open_datetime_picker(self):
        DateTimePickerPopup(
            self.winfo_toplevel(),
            initial_val=self.crm_meeting_time.get(),
            on_select_callback=self.set_meeting_time_value,
        )

    def set_meeting_time_value(self, formatted_str):
        self.crm_meeting_time.delete(0, tk.END)
        self.crm_meeting_time.insert(0, formatted_str)

    def add_timestamp_to_comm(self):
        if not hasattr(self, 'crm_comm_text') or not self.crm_comm_text.winfo_exists():
            messagebox.showwarning(
                "View Error",
                "Please switch to CRM Management view first.",
            )
            return

        now_str = datetime.datetime.now().strftime("[%Y-%m-%d %I:%M %p]\n")
        current_text = self.crm_comm_text.get("1.0", tk.END).strip()
        if current_text:
            self.crm_comm_text.insert(
                tk.END, f"\n\n------------------------------\n{now_str}"
            )
        else:
            self.crm_comm_text.insert(tk.END, now_str)

    def set_identity_fields_state(self, state="normal"):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            return

        target_state = (
            "readonly" if state in ["disabled", "readonly"] else "normal"
        )
        chk_state = (
            "disabled" if state in ["disabled", "readonly"] else "normal"
        )

        self.crm_company.config(state=target_state)
        self.crm_gst.config(state=target_state)
        self.crm_contact_person.config(state=target_state)
        self.crm_designation.config(state=target_state)
        self.crm_website.config(state=target_state)
        self.crm_contact.config(state=target_state)
        self.crm_address.config(state=target_state)
        self.crm_state.config(state=target_state)
        self.crm_district.config(state=target_state)
        self.crm_location.config(state=target_state)
        self.crm_turnover.config(state=target_state)
        self.crm_owner_name.config(state=target_state)
        self.crm_staff_count.config(state=target_state)

        self.chk_booster.config(state=chk_state)
        self.chk_stp.config(state=chk_state)
        self.chk_water_meter.config(state=chk_state)
        self.chk_bms.config(state=chk_state)
        self.chk_wtp.config(state=chk_state)
        self.chk_ro.config(state=chk_state)
        self.chk_fire_panel.config(state=chk_state)
        self.chk_dewatering_panel.config(state=chk_state)
        self.chk_water_softener.config(state=chk_state)
        self.chk_choice_a.config(state=chk_state)
        self.chk_pump_skid.config(state=chk_state)
        self.chk_pump_sensor_panel.config(state=chk_state)

        self.chk_val_vfd.config(state=chk_state)
        self.chk_val_dewatering.config(state=chk_state)
        self.chk_val_distributor.config(state=chk_state)
        self.chk_val_dealer.config(state=chk_state)
        self.chk_val_serious_base.config(state=chk_state)

        if self.var_val_distributor.get() and state == "normal":
            self.crm_distributor_name.config(state="normal")
        else:
            self.crm_distributor_name.config(state=target_state)

        if self.var_val_dealer.get() and state == "normal":
            self.crm_dealer_name.config(state="normal")
        else:
            self.crm_dealer_name.config(state=target_state)

        self.crm_call_hours.config(
            state="readonly" if state == "normal" else "disabled"
        )
        self.crm_call_mins.config(
            state="readonly" if state == "normal" else "disabled"
        )

        self.btn_add_photos.config(state=chk_state)
        self.btn_remove_photo.config(state=chk_state)

    def enable_editing(self):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            messagebox.showwarning(
                "View Error",
                "Please switch to CRM Management view first.",
            )
            return

        self.set_identity_fields_state("normal")
        messagebox.showinfo(
            "Editing Unlocked",
            "Customer identity and details fields are now editable.",
        )

    def get_form_data(self):
        company = self.crm_company.get().strip()
        if not company:
            messagebox.showwarning("Warning", "Company Name is required.")
            return None

        contact = self.crm_contact.get().strip()
        if contact and not contact.isdigit():
            messagebox.showwarning(
                "Input Error",
                "Contact Number must contain only numerical digits.",
            )
            return None

        photo_str = self.process_and_save_photos(company)

        call_time_str = (
            f"{self.crm_call_hours.get()} hrs {self.crm_call_mins.get()} mins"
        )

        data = [
            company,
            self.crm_gst.get().strip(),
            self.crm_contact_person.get().strip(),
            self.crm_designation.get().strip(),
            self.crm_website.get().strip(),
            contact,
            self.crm_address.get().strip(),
            self.crm_state.get().strip(),
            self.crm_district.get().strip(),
            self.crm_location.get().strip(),
            self.crm_turnover.get().strip(),
            self.crm_owner_name.get().strip(),
            self.crm_staff_count.get().strip(),
            self.get_selected_products_str(),
            self.get_company_valuation_str(),
            self.crm_notes_text.get("1.0", tk.END).strip(),
            call_time_str,
            self.crm_data_sent.get(),
            self.crm_enquiry.get(),
            self.crm_comm_text.get("1.0", tk.END).strip(),
            self.crm_meeting_time.get().strip(),
            self.crm_meeting_agenda.get().strip(),
            self.crm_meeting_outcome_text.get("1.0", tk.END).strip(),
            photo_str,
        ]
        return data

    def open_selected_customer(self):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            messagebox.showwarning(
                "View Error",
                "Please switch to CRM Management view first.",
            )
            return

        selected_items = self.crm_tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Selection Warning",
                "Please select a company from the list above to open.",
            )
            return

        item_values = self.crm_tree.item(selected_items[0])["values"]
        if not item_values:
            return

        row_id = int(item_values[0]) - 1
        r = self.all_rows[row_id]

        self.clear_crm_entries()
        self.selected_row_index = row_id

        self.set_identity_fields_state("normal")

        company_name = r[0] if len(r) > 0 else ""
        self.crm_company.insert(0, company_name)
        self.crm_gst.insert(0, r[1] if len(r) > 1 else "")
        self.crm_contact_person.insert(0, r[2] if len(r) > 2 else "")
        self.crm_designation.insert(0, r[3] if len(r) > 3 else "")
        self.crm_website.insert(0, r[4] if len(r) > 4 else "")
        self.crm_contact.insert(0, r[5] if len(r) > 5 else "")
        self.crm_address.insert(0, r[6] if len(r) > 6 else "")
        self.crm_state.insert(0, r[7] if len(r) > 7 else "")
        self.crm_district.insert(0, r[8] if len(r) > 8 else "")
        self.crm_location.insert(0, r[9] if len(r) > 9 else "")
        self.crm_turnover.insert(0, r[10] if len(r) > 10 else "")
        self.crm_owner_name.insert(0, r[11] if len(r) > 11 else "")
        self.crm_staff_count.insert(0, r[12] if len(r) > 12 else "")
        self.set_products_from_str(r[13] if len(r) > 13 else "")
        self.set_company_valuation_from_str(r[14] if len(r) > 14 else "")
        self.crm_notes_text.insert("1.0", r[15] if len(r) > 15 else "")
        self.set_call_time_from_str(r[16] if len(r) > 16 else "")
        self.crm_data_sent.set(r[17] if len(r) > 17 and r[17] else "No")
        self.crm_enquiry.set(r[18] if len(r) > 18 and r[18] else "No")
        self.crm_comm_text.insert("1.0", r[19] if len(r) > 19 else "")
        self.crm_meeting_time.insert(0, r[20] if len(r) > 20 else "")
        self.crm_meeting_agenda.insert(0, r[21] if len(r) > 21 else "")
        self.crm_meeting_outcome_text.insert("1.0", r[22] if len(r) > 22 else "")

        photo_str = r[23] if len(r) > 23 else ""
        if photo_str:
            photo_dir = self.get_company_photos_dir(company_name)
            for fname in photo_str.split("|"):
                if fname:
                    full_path = os.path.join(photo_dir, fname)
                    self.selected_photo_paths.append(full_path)
                    self.photo_listbox.insert(tk.END, fname)

        self.set_identity_fields_state("readonly")

        self.form_frame.config(
            text=f" Customer Data Entry (Opened: {r[0]}) "
        )
        messagebox.showinfo(
            "Company Loaded",
            f"Loaded '{r[0]}'. Fields are Read-Only (Ctrl+C to copy). Click '🔓 Enable Editing' to modify.",
        )

    def update_existing_entry(self):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            messagebox.showwarning(
                "View Error",
                "Please switch to CRM Management view first.",
            )
            return

        if self.selected_row_index is None:
            messagebox.showwarning(
                "No Record Selected",
                "Please select and open a record from the table first before updating.",
            )
            return

        row_data = self.get_form_data()
        if not row_data:
            return

        self.all_rows[self.selected_row_index] = row_data
        self.save_all_rows_to_csv()
        messagebox.showinfo(
            "Updated",
            f"Record for '{row_data[0]}' has been updated successfully!",
        )
        self.clear_crm_entries()
        self.load_crm_data()

    def save_new_entry(self):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            messagebox.showwarning(
                "View Error",
                "Please switch to CRM Management view first.",
            )
            return

        row_data = self.get_form_data()
        if not row_data:
            return

        try:
            with open(
                self.crm_csv_path, mode="a", newline="", encoding="utf-8-sig"
            ) as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

            # Sync with MQTT if available
            if self.mqtt_manager and self.mqtt_manager.is_connected():
                customer_dict = self._convert_row_to_dict(row_data)
                self.mqtt_manager.publish_customer_update(customer_dict, 'upsert')
                print("Customer data synced via MQTT")

            messagebox.showinfo(
                "Saved", f"New log entry saved for '{row_data[0]}'!"
            )
            self.clear_crm_entries()
            self.load_crm_data()

        except PermissionError:
            messagebox.showerror(
                "File Lock Error",
                "Close 'customers_detailed.csv' if open in Excel.",
            )

    def delete_crm_customer(self):
        selected_items = self.crm_tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Selection Warning",
                "Please select a customer record from the list to delete.",
            )
            return

        item_values = self.crm_tree.item(selected_items[0])["values"]
        row_id = int(item_values[0]) - 1
        company_name = self.all_rows[row_id][0]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete entry #{row_id + 1} for '{company_name}'?",
        )
        if confirm:
            del self.all_rows[row_id]
            self.save_all_rows_to_csv()
            messagebox.showinfo("Deleted", "Record deleted successfully.")
            self.clear_crm_entries()
            self.load_crm_data()

    def save_all_rows_to_csv(self):
        headers = self.get_crm_headers()
        try:
            with open(
                self.crm_csv_path, mode="w", newline="", encoding="utf-8-sig"
            ) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(self.all_rows)
        except PermissionError:
            messagebox.showerror(
                "File Lock Error",
                "Close 'customers_detailed.csv' if open in Excel.",
            )

    def clear_crm_entries(self):
        if not hasattr(self, 'crm_company') or not self.crm_company.winfo_exists():
            return

        self.selected_row_index = None
        self.selected_photo_paths = []
        self.form_frame.config(text=" Customer Details & Data Entry ")

        self.set_identity_fields_state("normal")

        self.crm_company.delete(0, tk.END)
        self.crm_gst.delete(0, tk.END)
        self.crm_contact_person.delete(0, tk.END)
        self.crm_designation.delete(0, tk.END)
        self.crm_website.delete(0, tk.END)
        self.crm_contact.delete(0, tk.END)
        self.crm_address.delete(0, tk.END)
        self.crm_state.delete(0, tk.END)
        self.crm_district.delete(0, tk.END)
        self.crm_location.delete(0, tk.END)
        self.crm_turnover.delete(0, tk.END)
        self.crm_owner_name.delete(0, tk.END)
        self.crm_staff_count.delete(0, tk.END)
        self.photo_listbox.delete(0, tk.END)

        self.set_products_from_str("")
        self.set_company_valuation_from_str("")

        self.crm_call_hours.set("00")
        self.crm_call_mins.set("00")
        self.crm_meeting_time.delete(0, tk.END)
        self.crm_meeting_agenda.delete(0, tk.END)
        self.crm_data_sent.set("No")
        self.crm_enquiry.set("No")
        self.crm_comm_text.delete("1.0", tk.END)
        self.crm_meeting_outcome_text.delete("1.0", tk.END)
        self.crm_notes_text.delete("1.0", tk.END)

    def _convert_row_to_dict(self, row_data):
        """Convert CRM row data to dictionary for MQTT syncing."""
        headers = self.get_crm_headers()
        return dict(zip(headers, row_data))

        if self.crm_tree.selection():
            self.crm_tree.selection_remove(self.crm_tree.selection())

    def load_crm_data(self):
        self.all_rows = []
        if not os.path.exists(self.crm_csv_path):
            return

        expected_count = len(self.get_crm_headers())

        try:
            with open(
                self.crm_csv_path, mode="r", encoding="utf-8-sig"
            ) as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for r in reader:
                    if r and any(r):
                        if len(r) < expected_count:
                            r.extend([""] * (expected_count - len(r)))
                        self.all_rows.append(r)

            self.populate_tree(self.all_rows)
        except PermissionError:
            messagebox.showerror(
                "File Error",
                "Could not load customer records. Close Excel if open.",
            )

    def populate_tree(self, rows_to_show):
        for item in self.crm_tree.get_children():
            self.crm_tree.delete(item)

        for r in rows_to_show:
            orig_idx = self.all_rows.index(r)
            company = r[0] if len(r) > 0 else ""
            gst_no = r[1] if len(r) > 1 else ""
            contact_person = r[2] if len(r) > 2 else ""
            designation = r[3] if len(r) > 3 else ""
            contact = r[5] if len(r) > 5 else ""
            state = r[7] if len(r) > 7 else ""
            district = r[8] if len(r) > 8 else ""
            location = r[9] if len(r) > 9 else ""
            owner = r[11] if len(r) > 11 else ""
            products = r[13] if len(r) > 13 else ""
            data_sent = r[17] if len(r) > 17 else "No"
            enquiry = r[18] if len(r) > 18 else "No"
            call_time = r[16] if len(r) > 16 else ""
            meeting_time = r[20] if len(r) > 20 else ""

            self.crm_tree.insert(
                "",
                tk.END,
                values=(
                    orig_idx + 1,
                    company,
                    gst_no,
                    contact_person,
                    designation,
                    contact,
                    state,
                    district,
                    location,
                    owner,
                    products,
                    data_sent,
                    enquiry,
                    call_time,
                    meeting_time,
                ),
            )

    def filter_crm_data(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.populate_tree(self.all_rows)
            return

        filtered = [
            r
            for r in self.all_rows
            if (len(r) > 0 and query in r[0].lower())
            or (len(r) > 1 and query in r[1].lower())
            or (len(r) > 2 and query in r[2].lower())
            or (len(r) > 3 and query in r[3].lower())
            or (len(r) > 5 and query in r[5].lower())
            or (len(r) > 7 and query in r[7].lower())
            or (len(r) > 8 and query in r[8].lower())
            or (len(r) > 9 and query in r[9].lower())
            or (len(r) > 11 and query in r[11].lower())
            or (len(r) > 13 and query in r[13].lower())
            or (len(r) > 14 and query in r[14].lower())
        ]
        self.populate_tree(filtered)

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.populate_tree(self.all_rows)