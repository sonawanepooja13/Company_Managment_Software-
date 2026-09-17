import csv
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
import config


class DateTimePicker(ttk.Frame):
    """Reusable widget for selecting Date (YYYY-MM-DD) and Time (HH:MM AM/PM)."""

    def __init__(self, parent):
        super().__init__(parent)

        # Date pickers
        now = datetime.now()
        self.year_var = tk.StringVar(value=str(now.year))
        self.month_var = tk.StringVar(value=f"{now.month:02d}")
        self.day_var = tk.StringVar(value=f"{now.day:02d}")

        years = [str(y) for y in range(now.year, now.year + 5)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]

        ttk.Combobox(self, textvariable=self.year_var, values=years, width=5, state="readonly").pack(side="left", padx=1)
        ttk.Label(self, text="-").pack(side="left")
        ttk.Combobox(self, textvariable=self.month_var, values=months, width=3, state="readonly").pack(side="left", padx=1)
        ttk.Label(self, text="-").pack(side="left")
        ttk.Combobox(self, textvariable=self.day_var, values=days, width=3, state="readonly").pack(side="left", padx=1)

        # Time pickers
        self.hour_var = tk.StringVar(value="10")
        self.min_var = tk.StringVar(value="00")
        self.ampm_var = tk.StringVar(value="AM")

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]

        ttk.Label(self, text="  ").pack(side="left")
        ttk.Combobox(self, textvariable=self.hour_var, values=hours, width=3, state="readonly").pack(side="left", padx=1)
        ttk.Label(self, text=":").pack(side="left")
        ttk.Combobox(self, textvariable=self.min_var, values=minutes, width=3, state="readonly").pack(side="left", padx=1)
        ttk.Combobox(self, textvariable=self.ampm_var, values=["AM", "PM"], width=4, state="readonly").pack(side="left", padx=2)

    def get_datetime_str(self):
        """Returns string formatted as 'YYYY-MM-DD HH:MM AM/PM'."""
        return f"{self.year_var.get()}-{self.month_var.get()}-{self.day_var.get()} {self.hour_var.get()}:{self.min_var.get()} {self.ampm_var.get()}"

    def set_datetime_str(self, dt_str):
        """Parses 'YYYY-MM-DD HH:MM AM/PM' and sets the combobox values."""
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
            self.year_var.set(str(dt.year))
            self.month_var.set(f"{dt.month:02d}")
            self.day_var.set(f"{dt.day:02d}")
            hour12 = dt.strftime("%I")
            self.hour_var.set(hour12)
            self.min_var.set(f"{dt.minute:02d}")
            self.ampm_var.set(dt.strftime("%p"))
        except Exception:
            pass


class CSVViewerWindow(tk.Toplevel):
    """Simple CSV viewer for product/customer tables."""

    def __init__(self, parent, csv_path=None, title="CSV Viewer"):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x520")
        self.transient(parent)
        self.grab_set()

        csv_path = csv_path or config.PRODUCTS_CSV
        self.csv_path = csv_path
        self.create_widgets()
        self.load_csv_data()

    def create_widgets(self):
        toolbar = ttk.Frame(self, padding=(10, 10, 10, 5))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Refresh", command=self.load_csv_data).pack(side="left")

        table = ttk.Frame(self)
        table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(table, show="headings", selectmode="browse")
        ysb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        table.grid_rowconfigure(0, weight=1)
        table.grid_columnconfigure(0, weight=1)

    def load_csv_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(self.csv_path):
            messagebox.showwarning("File Missing", f"CSV file not found:\n{self.csv_path}", parent=self)
            return

        with open(self.csv_path, newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            rows = list(reader)
            if not rows:
                return

            headers = rows[0]
            self.tree["columns"] = headers
            for header in headers:
                self.tree.heading(header, text=header.replace("_", " ").title())
                self.tree.column(header, width=120, anchor="w")

            for row in rows[1:]:
                self.tree.insert("", "end", values=row[:len(headers)])


class AddCustomerWindow(tk.Toplevel):
    """Window to add a new customer percentage record."""

    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.title("Add Customer")
        self.geometry("420x220")
        self.transient(parent)
        self.grab_set()
        self.callback = callback

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Customer Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Percentage:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.percentage_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.percentage_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Save", command=self.save_customer).grid(row=2, column=0, columnspan=2, pady=(12, 0), sticky="ew")

    def save_customer(self):
        name = self.name_var.get().strip()
        percentage = self.percentage_var.get().strip()

        if not name:
            messagebox.showwarning("Input Missing", "Customer name is required.", parent=self)
            return

        try:
            pct_value = float(percentage)
        except ValueError:
            messagebox.showwarning("Input Error", "Percentage must be a number.", parent=self)
            return

        file_path = config.CUSTOMERS_CSV
        existing_rows = []
        if os.path.exists(file_path):
            with open(file_path, newline="", encoding="utf-8-sig") as file:
                reader = csv.reader(file)
                rows = list(reader)
                if rows:
                    existing_rows = rows

        if not existing_rows:
            existing_rows = [["customer_name", "percentage"]]

        header = existing_rows[0]
        if header != ["customer_name", "percentage"]:
            existing_rows = [["customer_name", "percentage"]] + existing_rows[1:]

        updated = False
        for i, row in enumerate(existing_rows[1:], start=1):
            if row and row[0].strip().lower() == name.lower():
                existing_rows[i] = [name, str(pct_value)]
                updated = True
                break

        if not updated:
            existing_rows.append([name, str(pct_value)])

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(existing_rows)

        messagebox.showinfo("Saved", f"Customer '{name}' saved successfully.", parent=self)
        if self.callback:
            self.callback()
        self.destroy()


class CRMManagerWindow(tk.Toplevel):
    """Window to view all CRM customers, search, and edit individual details."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("CRM Lead Manager")
        self.geometry("950x500")
        self.transient(parent)

        self.create_widgets()
        self.load_crm_data()

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill="x")

        ttk.Button(top_frame, text="+ Add New Lead", command=self.add_lead).pack(side="left", padx=5)
        ttk.Button(top_frame, text="✏️ Edit Selected Lead", command=self.edit_lead).pack(side="left", padx=5)
        ttk.Button(top_frame, text="🔄 Refresh Table", command=self.load_crm_data).pack(side="left", padx=5)

        table_frame = ttk.Frame(self, padding="10")
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def load_crm_data(self):
        crm_csv = getattr(config, "CUSTOMERS_DETAILED_CSV", os.path.join(config.SCRIPT_DIR, "customers_detailed.csv"))
        if not os.path.exists(crm_csv):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        with open(crm_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                self.tree["columns"] = headers
                for h in headers:
                    self.tree.heading(h, text=h.replace("_", " ").title())
                    self.tree.column(h, width=130, anchor="w")

                for row in reader:
                    self.tree.insert("", "end", values=row)

    def add_lead(self):
        AddOrEditCRMWindow(self, callback_refresh=self.load_crm_data)

    def edit_lead(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Customer", "Please select a customer from the table to edit.", parent=self)
            return

        item_values = self.tree.item(selected[0], "values")
        row_index = self.tree.index(selected[0])
        AddOrEditCRMWindow(self, callback_refresh=self.load_crm_data, edit_row_index=row_index, edit_values=item_values)


class AddOrEditCRMWindow(tk.Toplevel):
    """Window to create or edit customer details with Date/Time pickers."""

    def __init__(self, parent, callback_refresh=None, edit_row_index=None, edit_values=None):
        super().__init__(parent)
        self.callback_refresh = callback_refresh
        self.edit_row_index = edit_row_index
        self.is_edit = edit_row_index is not None

        title_str = "Edit Lead Details" if self.is_edit else "Add New Lead Details"
        self.title(title_str)
        self.geometry("560x650")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if self.is_edit and edit_values:
            self.populate_existing_values(edit_values)

    def create_widgets(self):
        ttk.Label(self, text="Customer / Lead Details", font=("Helvetica", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)

        # Standard Text Entries
        fields = [
            ("Company Name*", "company_name"),
            ("Website", "website"),
            ("Contact Number", "contact_number"),
            ("Address", "address"),
            ("Location", "location"),
        ]

        self.entries = {}
        row_idx = 0
        for label_text, key in fields:
            ttk.Label(frame, text=f"{label_text}:").grid(row=row_idx, column=0, sticky="w", pady=4)
            ent = ttk.Entry(frame, width=38)
            ent.grid(row=row_idx, column=1, sticky="w", pady=4)
            self.entries[key] = ent
            row_idx += 1

        # Date & Time Pickers
        ttk.Label(frame, text="Call Conversion Time:").grid(row=row_idx, column=0, sticky="w", pady=4)
        self.call_time_picker = DateTimePicker(frame)
        self.call_time_picker.grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        ttk.Label(frame, text="Meeting Schedule Time:").grid(row=row_idx, column=0, sticky="w", pady=4)
        self.meeting_time_picker = DateTimePicker(frame)
        self.meeting_time_picker.grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        # Meeting Agenda
        ttk.Label(frame, text="Meeting Agenda:").grid(row=row_idx, column=0, sticky="w", pady=4)
        self.entries["meeting_agenda"] = ttk.Entry(frame, width=38)
        self.entries["meeting_agenda"].grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        # Comboboxes
        ttk.Label(frame, text="Company Data Sent:").grid(row=row_idx, column=0, sticky="w", pady=4)
        self.data_sent_combo = ttk.Combobox(frame, values=["Yes", "No"], width=35, state="readonly")
        self.data_sent_combo.set("No")
        self.data_sent_combo.grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        ttk.Label(frame, text="Enquiry Received:").grid(row=row_idx, column=0, sticky="w", pady=4)
        self.enquiry_combo = ttk.Combobox(frame, values=["Yes", "No"], width=35, state="readonly")
        self.enquiry_combo.set("No")
        self.enquiry_combo.grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        # Text Area Inputs
        ttk.Label(frame, text="Communication Details:").grid(row=row_idx, column=0, sticky="nw", pady=4)
        self.comm_text = tk.Text(frame, width=29, height=3)
        self.comm_text.grid(row=row_idx, column=1, sticky="w", pady=4)
        row_idx += 1

        ttk.Label(frame, text="Notes:").grid(row=row_idx, column=0, sticky="nw", pady=4)
        self.notes_text = tk.Text(frame, width=29, height=3)
        self.notes_text.grid(row=row_idx, column=1, sticky="w", pady=4)

        save_btn = ttk.Button(self, text="Save Lead Profile", command=self.save_lead)
        save_btn.pack(pady=15)

    def populate_existing_values(self, vals):
        """Pre-fill fields when editing an existing customer."""
        try:
            self.entries["company_name"].insert(0, vals[0])
            self.entries["website"].insert(0, vals[1])
            self.entries["contact_number"].insert(0, vals[2])
            self.entries["address"].insert(0, vals[3])
            self.entries["location"].insert(0, vals[4])
            self.notes_text.insert("1.0", vals[5])
            self.call_time_picker.set_datetime_str(vals[6])
            self.data_sent_combo.set(vals[7] if vals[7] in ["Yes", "No"] else "No")
            self.enquiry_combo.set(vals[8] if vals[8] in ["Yes", "No"] else "No")
            self.comm_text.insert("1.0", vals[9])
            self.meeting_time_picker.set_datetime_str(vals[10])
            self.entries["meeting_agenda"].insert(0, vals[11])
        except IndexError:
            pass

    def save_lead(self):
        company = self.entries["company_name"].get().strip()
        if not company:
            messagebox.showwarning("Input Error", "Company Name is required.", parent=self)
            return

        crm_csv = getattr(config, "CUSTOMERS_DETAILED_CSV", os.path.join(config.SCRIPT_DIR, "customers_detailed.csv"))

        row = [
            company,
            self.entries["website"].get().strip(),
            self.entries["contact_number"].get().strip(),
            self.entries["address"].get().strip(),
            self.entries["location"].get().strip(),
            self.notes_text.get("1.0", tk.END).strip(),
            self.call_time_picker.get_datetime_str(),
            self.data_sent_combo.get(),
            self.enquiry_combo.get(),
            self.comm_text.get("1.0", tk.END).strip(),
            self.meeting_time_picker.get_datetime_str(),
            self.entries["meeting_agenda"].get().strip(),
            ""
        ]

        # Load all rows and update or append
        rows = []
        if os.path.exists(crm_csv):
            with open(crm_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)

        if self.is_edit and self.edit_row_index is not None:
            # Row index + 1 accounts for header row
            rows[self.edit_row_index + 1] = row
        else:
            rows.append(row)

        try:
            with open(crm_csv, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            messagebox.showinfo("Success", f"Lead details for '{company}' saved!", parent=self)
            if self.callback_refresh:
                self.callback_refresh()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {e}", parent=self)