"""Company Sorting for CrmTab."""
import csv
import datetime
import os
import tkinter as tk
from tkinter import messagebox, ttk
try:
    from tkcalendar import DateEntry
    HAS_CAL = True
except ImportError:
    HAS_CAL = False


class CompanySortingMixin:
    def show_company_sorting(self):
        for w in self.view_container.winfo_children():
            w.destroy()
        ttk.Label(self.view_container,
            text="Company Sorting - Filter / Sort Companies",
            font=("Helvetica", 12, "bold")).pack(pady=4)
        filt = ttk.LabelFrame(self.view_container,
            text=" Sorting Filters ", padding="8")
        filt.pack(fill="x", padx=10, pady=5)
        r1 = ttk.Frame(filt)
        r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Product & System:").pack(side="left")
        self.sort_product_var = tk.StringVar(value="All")
        ttk.Combobox(r1, textvariable=self.sort_product_var,
            values=["All", "Booster Pump System", "STP",
                "Water Meter", "BMS", "WTP", "RO",
                "FIRE PANEL", "De-watering Panel",
                "Water Softener", "Choice A",
                "Pump Skid", "Pump Sensor Panel"],
            width=20, state="readonly").pack(side="left", padx=(2, 12))
        ttk.Label(r1, text="Company Valuation:").pack(side="left")
        self.sort_valuation_var = tk.StringVar(value="All")
        ttk.Combobox(r1, textvariable=self.sort_valuation_var,
            values=["All", "Work in VFD Panel",
                "Work in Dewatering", "Distributor",
                "Dealer", "Serious Base"],
            width=18, state="readonly").pack(side="left", padx=(2, 12))
        ttk.Label(r1, text="Activity & Comm:").pack(side="left")
        self.sort_activity_var = tk.StringVar(value="All")
        ttk.Combobox(r1, textvariable=self.sort_activity_var,
            values=["All", "With Activity (count>0)",
                "High Activity (>=5)", "No Activity",
                "With Communication", "Without Communication"],
            width=24, state="readonly").pack(side="left", padx=2)
        r2 = ttk.Frame(filt)
        r2.pack(fill="x", pady=4)
        self.sort_date_enable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r2, text="Next Meeting between:",
            variable=self.sort_date_enable_var,
            selectcolor="white").pack(side="left")
        today = datetime.date.today()
        if HAS_CAL:
            self.sort_from_date = DateEntry(r2, width=10,
                date_pattern="yyyy-mm-dd",
                background="darkblue", foreground="white")
            self.sort_from_date.pack(side="left", padx=2)
            ttk.Label(r2, text="to").pack(side="left")
            self.sort_to_date = DateEntry(r2, width=10,
                date_pattern="yyyy-mm-dd",
                background="darkblue", foreground="white")
            self.sort_to_date.pack(side="left", padx=2)
        else:
            self.sort_from_date = ttk.Entry(r2, width=11)
            self.sort_from_date.insert(0, today.strftime("%Y-%m-%d"))
            self.sort_from_date.pack(side="left", padx=2)
            ttk.Label(r2, text="to").pack(side="left")
            self.sort_to_date = ttk.Entry(r2, width=11)
            self.sort_to_date.insert(0, today.strftime("%Y-%m-%d"))
            self.sort_to_date.pack(side="left", padx=2)
        ttk.Label(r2, text="Enquiry:").pack(side="left", padx=(12, 0))
        self.sort_enquiry_var = tk.StringVar(value="All")
        ttk.Combobox(r2, textvariable=self.sort_enquiry_var,
            values=["All", "Yes", "No"],
            width=6, state="readonly").pack(side="left", padx=2)
        ttk.Label(r2, text="Enquiry Type:").pack(side="left", padx=(8, 0))
        self.sort_enquiry_type_entry = ttk.Entry(r2, width=14)
        self.sort_enquiry_type_entry.pack(side="left", padx=2)
        # Row 2b : Website | State | District | Rating | Distributor | Dealer
        r2b = ttk.Frame(filt)
        r2b.pack(fill="x", pady=3)
        ttk.Label(r2b, text="Website:").pack(side="left")
        self.sort_website_var = tk.StringVar(value="All")
        ttk.Combobox(r2b, textvariable=self.sort_website_var,
            values=["All", "Available", "Not Available"],
            width=12, state="readonly").pack(side="left", padx=(2, 8))
        ttk.Label(r2b, text="State:").pack(side="left")
        self.sort_state_entry = ttk.Entry(r2b, width=12)
        self.sort_state_entry.pack(side="left", padx=(2, 8))
        ttk.Label(r2b, text="District:").pack(side="left")
        self.sort_district_entry = ttk.Entry(r2b, width=12)
        self.sort_district_entry.pack(side="left", padx=(2, 8))
        ttk.Label(r2b, text="Rating above >").pack(side="left")
        self.sort_rating_entry = ttk.Entry(r2b, width=6)
        self.sort_rating_entry.insert(0, "")
        self.sort_rating_entry.pack(side="left", padx=2)
        ttk.Label(r2b, text="Distributor:").pack(side="left", padx=(8, 0))
        self.sort_distributor_entry = ttk.Entry(r2b, width=12)
        self.sort_distributor_entry.pack(side="left", padx=2)
        ttk.Label(r2b, text="Dealer:").pack(side="left", padx=(8, 0))
        self.sort_dealer_entry = ttk.Entry(r2b, width=12)
        self.sort_dealer_entry.pack(side="left", padx=2)
        r3 = ttk.Frame(filt)
        r3.pack(fill="x", pady=3)
        ttk.Label(r3, text="Sort By:").pack(side="left")
        self.sort_by_var = tk.StringVar(value="Company Name (A-Z)")
        ttk.Combobox(r3, textvariable=self.sort_by_var,
            values=["Company Name (A-Z)", "Company Name (Z-A)",
                "Next Meeting (Earliest)", "Next Meeting (Latest)",
                "Valuable % (High-Low)", "Rating (High-Low)",
                "Activity (High-Low)"],
            width=24, state="readonly").pack(side="left", padx=2)
        ttk.Button(r3, text="Apply Filter",
            command=self.apply_company_sorting).pack(side="left", padx=8)
        ttk.Button(r3, text="Reset",
            command=self.reset_company_sorting).pack(side="left", padx=3)
        self.sort_count_label = ttk.Label(r3, text="Total: 0",
            font=("Helvetica", 10, "bold"))
        self.sort_count_label.pack(side="right", padx=10)
        res_frame = ttk.LabelFrame(self.view_container,
            text=" Sorted Company List ", padding="6")
        res_frame.pack(fill="both", expand=True, padx=10, pady=5)
        sort_cols = ("#", "Company Name", "Contact Person",
            "Contact Number", "Website", "State", "District",
            "Product & System", "Valuation", "Rating",
            "Activity", "Communication Date", "Next Meeting",
            "Enquiry", "Enquiry Type")
        self.sort_tree = ttk.Treeview(res_frame, columns=sort_cols,
            show="headings", height=10)
        self.sort_tree.heading("#", text="#")
        self.sort_tree.column("#", width=30, anchor="center")
        widths = {"Company Name": 130, "Contact Person": 100,
            "Contact Number": 90, "Website": 110, "State": 80,
            "District": 90, "Product & System": 140,
            "Valuation": 130, "Rating": 55, "Activity": 55,
            "Communication Date": 95, "Next Meeting": 120,
            "Enquiry": 55, "Enquiry Type": 100}
        for col in sort_cols[1:]:
            self.sort_tree.heading(col, text=col)
            self.sort_tree.column(col, width=widths.get(col, 90))
        vsb = ttk.Scrollbar(res_frame, orient="vertical",
            command=self.sort_tree.yview)
        hsb = ttk.Scrollbar(res_frame, orient="horizontal",
            command=self.sort_tree.xview)
        self.sort_tree.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.sort_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        res_frame.grid_rowconfigure(0, weight=1)
        res_frame.grid_columnconfigure(0, weight=1)
        try:
            self.ensure_crm_csv_exists()
            self._reload_all_rows_silent()
        except Exception:
            pass
        self.apply_company_sorting()

    def _reload_all_rows_silent(self):
        if not os.path.exists(self.crm_csv_path):
            return
        expected = len(self.get_crm_headers())
        rows = []
        with open(self.crm_csv_path, mode="r",
                  encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)
            for r in reader:
                if r and any(r):
                    if len(r) < expected:
                        r.extend([""] * (expected - len(r)))
                    rows.append(r)
        self.all_rows = rows

    def _parse_date_only(self, s):
        s = (s or "").strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y",
                    "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(
                    s[:10], fmt).date()
            except ValueError:
                continue
        try:
            mt = self.parse_meeting_dt(s)
            return mt.date() if mt else None
        except Exception:
            return None

    def _get_sort_widget_date(self, widget):
        try:
            v = widget.get()
        except Exception:
            return None
        if hasattr(v, "strftime"):
            try:
                return v.strftime("%Y-%m-%d")
            except Exception:
                return None
        return str(v).strip()

    def _sort_val(self, row, idx, key, default=""):
        i = idx.get(key, -1)
        if 0 <= i < len(row):
            return row[i]
        return default

    def apply_company_sorting(self):
        if not hasattr(self, "sort_tree"):
            return
        try:
            if not self.sort_tree.winfo_exists():
                return
        except Exception:
            return
        try:
            self._reload_all_rows_silent()
        except Exception:
            pass
        headers = self.get_crm_headers()
        idx = {}
        for h in headers:
            try:
                idx[h] = headers.index(h)
            except Exception:
                pass
        fp = self.sort_product_var.get()
        fv = self.sort_valuation_var.get()
        fa = self.sort_activity_var.get()
        fe = self.sort_enquiry_var.get()
        fet = self.sort_enquiry_type_entry.get().strip().lower()
        fw = self.sort_website_var.get() if hasattr(
            self, "sort_website_var") else "All"
        fst = self.sort_state_entry.get().strip().lower() if hasattr(
            self, "sort_state_entry") else ""
        fdi = self.sort_district_entry.get().strip().lower() if hasattr(
            self, "sort_district_entry") else ""
        frat = self.sort_rating_entry.get().strip() if hasattr(
            self, "sort_rating_entry") else ""
        fdist = self.sort_distributor_entry.get().strip().lower() \
            if hasattr(self, "sort_distributor_entry") else ""
        fdea = self.sort_dealer_entry.get().strip().lower() \
            if hasattr(self, "sort_dealer_entry") else ""
        try:
            frat_n = float(frat) if frat else None
        except Exception:
            frat_n = None
        use_date = bool(self.sort_date_enable_var.get())
        from_d = to_d = None
        if use_date:
            from_d = self._parse_date_only(
                self._get_sort_widget_date(self.sort_from_date))
            to_d = self._parse_date_only(
                self._get_sort_widget_date(self.sort_to_date))
            if from_d and to_d and from_d > to_d:
                from_d, to_d = to_d, from_d
        filtered = []
        for row in list(self.all_rows):
            prods = str(self._sort_val(
                row, idx, "products_selected", ""))
            valu = str(self._sort_val(
                row, idx, "company_valuation", ""))
            enq = str(self._sort_val(
                row, idx, "enquiry_received", "No")).strip()
            enq_t = str(self._sort_val(row, idx, "enquiry_type", ""))
            if fp != "All" and fp.lower() not in prods.lower():
                continue
            if fv != "All" and fv.lower() not in valu.lower():
                continue
            act_raw = str(self._sort_val(
                row, idx, "activity_count", "0")).strip()
            try:
                if act_raw in ("", "No", "None"):
                    act_n = 0
                else:
                    act_n = int(float(act_raw))
            except Exception:
                act_n = 0
            comm = str(self._sort_val(
                row, idx, "communication_details", "")).strip()
            if fa == "With Activity (count>0)" and not act_n > 0:
                continue
            if fa == "High Activity (>=5)" and not act_n >= 5:
                continue
            if fa == "No Activity" and not act_n <= 0:
                continue
            if fa == "With Communication" and not comm:
                continue
            if fa == "Without Communication" and comm:
                continue
            if use_date and (from_d or to_d):
                nxt0 = str(self._sort_val(
                    row, idx, "next_meeting_datetime", "")
                    or self._sort_val(
                        row, idx, "meeting_schedule_time", "")).strip()
                mt0 = self.parse_meeting_dt(nxt0) if nxt0 else None
                if not mt0:
                    continue
                md0 = mt0.date()
                if from_d and md0 < from_d:
                    continue
                if to_d and md0 > to_d:
                    continue
            if fe != "All" and enq != fe:
                continue
            if fet and fet not in enq_t.lower():
                continue
            web = str(self._sort_val(row, idx, "website", "")).strip()
            if fw == "Available" and not web:
                continue
            if fw == "Not Available" and web:
                continue
            st = str(self._sort_val(row, idx, "state", "")).strip().lower()
            if fst and fst not in st:
                continue
            di = str(self._sort_val(
                row, idx, "district", "")).strip().lower()
            if fdi and fdi not in di:
                continue
            if frat_n is not None:
                try:
                    rv = float(str(self._sort_val(
                        row, idx, "customer_rating",
                        "0") or "0").strip() or 0)
                except Exception:
                    rv = 0.0
                if not rv > frat_n:
                    continue
            if fdist and fdist not in valu.lower():
                continue
            if fdea and fdea not in valu.lower():
                continue
            filtered.append(row)
        self._sort_and_fill(filtered, idx)

    def _sort_and_fill(self, filtered, idx):
        sort_by = self.sort_by_var.get()

        def _num(r, key):
            try:
                return float(str(self._sort_val(
                    r, idx, key, "0") or "0").strip() or 0)
            except Exception:
                return 0.0

        def _meet(r):
            nxt = str(self._sort_val(
                r, idx, "next_meeting_datetime", "")
                or self._sort_val(
                    r, idx, "meeting_schedule_time", "")).strip()
            mt = self.parse_meeting_dt(nxt) if nxt else None
            if mt:
                return mt
            return datetime.datetime.max

        try:
            if sort_by == "Company Name (A-Z)":
                filtered.sort(key=lambda r: str(
                    self._sort_val(
                        r, idx, "company_name", "")).lower())
            elif sort_by == "Company Name (Z-A)":
                filtered.sort(key=lambda r: str(
                    self._sort_val(
                        r, idx, "company_name", "")).lower(),
                    reverse=True)
            elif sort_by == "Next Meeting (Earliest)":
                filtered.sort(key=_meet)
            elif sort_by == "Next Meeting (Latest)":
                wm = [r for r in filtered
                      if _meet(r) != datetime.datetime.max]
                wom = [r for r in filtered
                       if _meet(r) == datetime.datetime.max]
                wm.sort(key=_meet, reverse=True)
                filtered = wm + wom
            elif sort_by == "Valuable % (High-Low)":
                filtered.sort(
                    key=lambda r: _num(
                        r, "valuable_customer_percentage"),
                    reverse=True)
            elif sort_by == "Rating (High-Low)":
                filtered.sort(
                    key=lambda r: _num(r, "customer_rating"),
                    reverse=True)
            elif sort_by == "Activity (High-Low)":
                filtered.sort(
                    key=lambda r: _num(r, "activity_count"),
                    reverse=True)
        except Exception:
            pass
        self.sort_tree.delete(*self.sort_tree.get_children())
        for i, row in enumerate(filtered, 1):
            nxt = str(self._sort_val(
                row, idx, "next_meeting_datetime", "")
                or self._sort_val(
                    row, idx, "meeting_schedule_time", ""))
            act_raw = str(self._sort_val(
                row, idx, "activity_count", "0")).strip()
            if act_raw in ("", "No", "None"):
                act_raw = "0"
            self.sort_tree.insert("", "end", values=(
                i, self._sort_val(row, idx, "company_name", ""),
                self._sort_val(row, idx, "contact_person", ""),
                self._sort_val(row, idx, "contact_number", ""),
                self._sort_val(row, idx, "website", ""),
                self._sort_val(row, idx, "state", ""),
                self._sort_val(row, idx, "district", ""),
                self._sort_val(row, idx, "products_selected", ""),
                self._sort_val(row, idx, "company_valuation", ""),
                self._sort_val(row, idx, "customer_rating", ""),
                act_raw,
                self._sort_val(row, idx, "communication_date", ""),
                nxt,
                self._sort_val(row, idx, "enquiry_received", ""),
                self._sort_val(row, idx, "enquiry_type", "")))
        try:
            self.sort_count_label.config(
                text="Total: %d / %d" % (
                    len(filtered), len(self.all_rows)))
        except Exception:
            pass

    def reset_company_sorting(self):
        try:
            self.sort_product_var.set("All")
            self.sort_valuation_var.set("All")
            self.sort_activity_var.set("All")
            self.sort_enquiry_var.set("All")
            self.sort_website_var.set("All")
            self.sort_by_var.set("Company Name (A-Z)")
            self.sort_enquiry_type_entry.delete(0, tk.END)
            self.sort_state_entry.delete(0, tk.END)
            self.sort_district_entry.delete(0, tk.END)
            self.sort_rating_entry.delete(0, tk.END)
            self.sort_distributor_entry.delete(0, tk.END)
            self.sort_dealer_entry.delete(0, tk.END)
            self.sort_date_enable_var.set(False)
            self.apply_company_sorting()
        except Exception as e:
            messagebox.showerror(
                "Reset Error",
                "Failed to reset filters:\n%s" % e)





