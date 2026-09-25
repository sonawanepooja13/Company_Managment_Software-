"""Vendor registration form and vendor master CSV database."""

import csv
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import config
from tkcalendar import DateEntry


VENDOR_CSV = os.path.join(config.CSV_DIR, "vendors.csv")
VENDOR_HEADERS = ["vendor_code", "vendor_legal_name", "vendor_category", "constitution", "contact_person", "phone_mobile", "official_email", "registered_city", "factory_location", "registered_office_location", "gstin", "pan", "msme_status", "bank_name", "account_number", "ifsc_code", "credit_terms", "approval_status", "onboarding_date"]
VENDOR_LABELS = ["Vendor Code", "Vendor Legal Name", "Vendor Category", "Constitution", "Contact Person", "Phone / Mobile", "Official Email", "Registered City", "Factory / Works Location", "Registered Office Location", "GSTIN", "PAN", "MSME Status", "Bank Name", "Account Number", "IFSC Code", "Credit Terms", "Approval Status", "Onboarding Date"]


def ensure_vendor_file():
    if not os.path.exists(VENDOR_CSV):
        with open(VENDOR_CSV, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=VENDOR_HEADERS).writeheader()


def next_vendor_code():
    ensure_vendor_file()
    with open(VENDOR_CSV, newline="", encoding="utf-8") as file:
        count = sum(1 for _ in csv.DictReader(file)) + 1
    return f"VND-{date.today().year}-{count:03d}"


class VendorRegistrationWindow(ttk.Frame):
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.on_complete = on_complete or (lambda: None)
        self.vars = {key: tk.StringVar() for key in VENDOR_HEADERS}
        self.vars["vendor_code"].set(next_vendor_code())
        self.vars["approval_status"].set("Pending Review")
        self.vars["onboarding_date"].set(date.today().isoformat())
        self._build()

    def _build(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Vendor Registration", font=("Helvetica", 16, "bold")).pack(anchor="w")
        ttk.Label(container, text="Add the vendor once here, then select it in a new inward invoice.").pack(anchor="w", pady=(2, 10))

        form = ttk.Frame(container)
        form.pack(fill="both", expand=True)
        for column in (1, 3):
            form.columnconfigure(column, weight=1)

        sections = (
            ("Basic Details", ("vendor_code", "vendor_legal_name", "vendor_category", "constitution", "contact_person", "phone_mobile", "official_email")),
            ("Registration & Location", ("registered_city", "factory_location", "registered_office_location", "gstin", "pan", "msme_status")),
            ("Bank & Approval", ("bank_name", "account_number", "ifsc_code", "credit_terms", "approval_status", "onboarding_date")),
        )
        labels = dict(zip(VENDOR_HEADERS, VENDOR_LABELS))
        for section_index, (title, fields) in enumerate(sections):
            section = ttk.LabelFrame(form, text=f" {title} ", padding=10)
            section.grid(row=section_index, column=0, columnspan=4, sticky="ew", pady=(0, 10))
            for column in (1, 3):
                section.columnconfigure(column, weight=1)
            for row, key in enumerate(fields):
                row_number, group = divmod(row, 2)
                column = group * 2
                ttk.Label(section, text=f"{labels[key]}:").grid(row=row_number, column=column, sticky="w", padx=(0, 10), pady=5)
                if key == "vendor_category":
                    widget = ttk.Combobox(section, textvariable=self.vars[key], values=("Manufacturer", "Trader / Stockist", "Authorized Distributor / Dealer", "Service Provider"), state="readonly")
                elif key == "approval_status":
                    widget = ttk.Combobox(section, textvariable=self.vars[key], values=("Pending Review", "Approved", "Conditionally Approved", "Rejected"), state="readonly")
                elif key == "onboarding_date":
                    widget = DateEntry(section, textvariable=self.vars[key], date_pattern="yyyy-mm-dd")
                else:
                    widget = ttk.Entry(section, textvariable=self.vars[key])
                    if key == "vendor_code":
                        widget.configure(state="readonly")
                widget.grid(row=row_number, column=column + 1, sticky="ew", padx=(0, 14) if group == 0 else (0, 0), pady=5)

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Back", command=self.on_complete).pack(side="right")
        ttk.Button(actions, text="Save Vendor", command=self.save).pack(side="right", padx=(0, 8))

    def save(self):
        if not self.vars["vendor_legal_name"].get().strip() or not self.vars["phone_mobile"].get().strip():
            messagebox.showwarning("Vendor Details", "Vendor legal name and phone/mobile are required.", parent=self)
            return
        ensure_vendor_file()
        with open(VENDOR_CSV, "a", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=VENDOR_HEADERS).writerow({key: value.get().strip() for key, value in self.vars.items()})
        messagebox.showinfo("Saved", f"Vendor {self.vars['vendor_code'].get()} saved successfully.", parent=self)
        self.on_complete()
