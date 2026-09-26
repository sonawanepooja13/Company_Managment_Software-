import csv
import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import zlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
import locations
import company_file_import

try:
    import crm_engine
except ImportError:
    crm_engine = None

try:
    from .company_sorting import CompanySortingMixin
except ImportError:
    try:
        from tabs.company_sorting import CompanySortingMixin
    except ImportError:
        try:
            from company_sorting import CompanySortingMixin
        except ImportError:
            class CompanySortingMixin:
                def show_company_sorting(self):
                    from tkinter import messagebox
                    messagebox.showinfo("Info", "Company Sorting module not found.")

try:
    from .company_graph import CompanyGraphMixin
except ImportError:
    try:
        from tabs.company_graph import CompanyGraphMixin
    except ImportError:
        try:
            from company_graph import CompanyGraphMixin
        except ImportError:
            class CompanyGraphMixin:
                def show_company_graph(self):
                    from tkinter import messagebox
                    messagebox.showinfo("Info", "Graph module not found.")

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


class CrmTab(CompanySortingMixin, CompanyGraphMixin, ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.crm_csv_path = getattr(
            config,
            "CUSTOMERS_DETAILED_CSV",
            os.path.join(config.SCRIPT_DIR, "customers_detailed.csv"),
        )
        self.photos_base_dir = os.path.join(config.SCRIPT_DIR, "Customer_Photos")
        os.makedirs(self.photos_base_dir, exist_ok=True)
        
        # Audio recordings are stored inside csv_data, separated per customer folder.
        self.audio_base_dir = os.path.join(config.CSV_DIR, "Customer_Audio_Recordings")
        os.makedirs(self.audio_base_dir, exist_ok=True)

        self.selected_row_index = None
        self.location_fields_locked = False
        self._location_choices = {
            "country": tuple(locations.COUNTRY_NAMES),
            "state": (),
            "district": (),
        }
        self._location_popup_open = {
            "country": False,
            "state": False,
            "district": False,
        }
        self._location_post_scheduled = {
            "country": False,
            "state": False,
            "district": False,
        }
        self._location_suggestion_popups = {
            "country": None,
            "state": None,
            "district": None,
        }
        self._location_suggestion_listboxes = {
            "country": None,
            "state": None,
            "district": None,
        }
        self._location_suggestion_values = {
            "country": (),
            "state": (),
            "district": (),
        }
        self._location_preferences = self._read_location_preferences()
        self.all_rows = []
        self.selected_photo_paths = []
        self.selected_audio_paths = []
        self.status_summary_frame = None
        self.notified_meetings = set()
        # Per-company CSV folder: csv_data/Company_Wise/<Company>.csv
        self.company_wise_dir = os.path.join(config.CSV_DIR, "Company_Wise")
        os.makedirs(self.company_wise_dir, exist_ok=True)

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
        # background alarm: popup 15 min before next meeting
        try:
            self.start_meeting_reminder_thread()
        except Exception:
            pass

    def _read_location_preferences(self):
        """Read the last confirmed location selection from SQLite."""
        defaults = {"country": "India", "state": "", "district": ""}
        if crm_engine is None:
            return defaults
        try:
            crm_engine.init_crm_db()
            stored = crm_engine.get_location_preferences()
            return {
                key: (stored.get(key) or defaults[key])
                for key in defaults
            }
        except Exception as exc:
            print(f"Could not load location defaults: {exc}")
            return defaults

    def _save_location_preferences(self):
        """Persist the last confirmed location selection to SQLite."""
        if crm_engine is None or not hasattr(self, "crm_country"):
            return
        try:
            country = self.crm_country.get().strip()
            state = self.crm_state.get().strip()
            district = self.crm_district.get().strip()
            crm_engine.save_location_preferences(country, state, district)
            self._location_preferences = {
                "country": country,
                "state": state,
                "district": district,
            }
        except Exception as exc:
            print(f"Could not save location defaults: {exc}")

    def _load_default_location_values(self):
        """Apply the last confirmed location as the new-record default."""
        preferences = self._location_preferences
        self._set_location_values(
            preferences.get("country") or "India",
            preferences.get("state", ""),
            preferences.get("district", ""),
        )

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
            "valuable_customer_percentage",
            "customer_rating",
            "activity_count",
            "mobile_recording_count",
            "note",
            "call_conversion_time",
            "call_conversion_date",
            "company_data_sent",
            "data_type_name",
            "enquiry_received",
            "enquiry_type",
            "communication_details",
            "communication_date",
            "meeting_schedule_time",
            "next_meeting_datetime",
            "meeting_agenda",
            "meeting_completed_details",
            "photo_files",
            "audio_files",
            "country",
        ]

    # ---------- Company-wise CSV + reminder helpers ----------
    def _safe_company_filename(self, company_name):
        safe = "".join(
            c if (c.isalnum() or c in (" ", "-", "_")) else "_"
            for c in (company_name or "").strip()
        ).strip()
        safe = "_".join(safe.split())
        return safe[:80] if safe else "Unknown_Company"

    def get_company_csv_path(self, company_name):
        return os.path.join(
            self.company_wise_dir,
            f"{self._safe_company_filename(company_name)}.csv",
        )

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

    def save_company_wise_csv(self, row_dict):
        try:
            company = (row_dict.get("company_name") or "").strip() or "Unknown_Company"
            path = self.get_company_csv_path(company)
            headers = self.get_crm_headers()
            if os.path.exists(path):
                try:
                    with open(path, "r", newline="", encoding="utf-8-sig") as f:
                        reader = csv.DictReader(f)
                        existing = list(reader) if reader.fieldnames else []
                        old_fields = reader.fieldnames or []
                    key_new = (row_dict.get("company_name", ""), row_dict.get("contact_number", ""))
                    merged = False
                    for ex in existing:
                        key_ex = (ex.get("company_name", ""), ex.get("contact_number", ""))
                        if key_ex == key_new:
                            ex.update(row_dict)
                            merged = True
                            break
                    if not merged:
                        existing.append(row_dict)
                    all_fields = list(dict.fromkeys(list(old_fields) + headers + list(row_dict.keys())))
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        w = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
                        w.writeheader()
                        for ex in existing:
                            w.writerow({k: ex.get(k, "") for k in all_fields})
                    return path
                except Exception:
                    pass
            with open(path, "a", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                if f.tell() == 0:
                    w.writeheader()
                w.writerow({k: row_dict.get(k, "") for k in headers})
            return path
        except Exception as e:
            print(f"Company-wise CSV save failed: {e}")
            return None

    def parse_meeting_dt(self, s):
        s = (s or "").strip()
        if not s:
            return None
        fmts = ["%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M", "%d-%m-%Y %I:%M %p",
                "%d-%m-%Y %H:%M", "%Y/%m/%d %I:%M %p", "%Y-%m-%d", "%d-%m-%Y"]
        for fmt in fmts:
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def start_meeting_reminder_thread(self):
        def _loop():
            while True:
                try:
                    self.check_meeting_reminders()
                except Exception as e:
                    print(f"Reminder check failed: {e}")
                time.sleep(30)
        threading.Thread(target=_loop, daemon=True).start()

    def check_meeting_reminders(self):
        now = datetime.datetime.now()
        for row in list(self.all_rows):
            try:
                d = row if isinstance(row, dict) else dict(zip(self.get_crm_headers(), row))
            except Exception:
                continue
            nxt = d.get("next_meeting_datetime", "") or d.get("meeting_schedule_time", "")
            cname = d.get("company_name", "Unknown")
            if not nxt:
                continue
            mt = self.parse_meeting_dt(str(nxt))
            if not mt:
                continue
            delta_min = (mt - now).total_seconds() / 60.0
            key = f"{cname}|{nxt}"
            if 14.0 <= delta_min <= 16.5 and key not in self.notified_meetings:
                self.notified_meetings.add(key)
                msg = f"Meeting in ~15 minutes!\n\nCompany: {cname}\nAt: {nxt}"
                try:
                    self.after(0, lambda m=msg: messagebox.showwarning("Meeting Reminder", m))
                    self.after(0, lambda m=msg: self._flash_reminder_popup(m))
                except Exception:
                    pass

    def _flash_reminder_popup(self, msg):
        pop = tk.Toplevel(self)
        pop.title("Meeting Reminder - 15 min left")
        pop.geometry("380x200")
        pop.attributes("-topmost", True)
        try:
            pop.bell()
        except Exception:
            pass
        ttk.Label(pop, text="Next Meeting in 15 Minutes",
                  font=("Helvetica", 12, "bold"), foreground="red").pack(pady=10)
        ttk.Label(pop, text=msg, wraplength=340, justify="left").pack(pady=5, padx=12)
        ttk.Button(pop, text="OK", command=pop.destroy).pack(pady=10)

    def _get_date_str(self, widget, default_today=True):
        """DateEntry-safe getter: always returns YYYY-MM-DD string."""
        try:
            v = widget.get()
        except Exception:
            return datetime.date.today().strftime("%Y-%m-%d") if default_today else ""
        try:
            if hasattr(v, "strftime"):
                return v.strftime("%Y-%m-%d")
            return str(v).strip()
        except Exception:
            return datetime.date.today().strftime("%Y-%m-%d") if default_today else ""

    def sanitize_folder_name(self, name):
        return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()

    def get_company_photos_dir(self, company_name):
        clean_name = self.sanitize_folder_name(company_name)
        if not clean_name:
            clean_name = "Unnamed_Company"
        return os.path.join(self.photos_base_dir, clean_name)

    def get_company_audio_dir(self, company_name):
        clean_name = self.sanitize_folder_name(company_name)
        if not clean_name:
            clean_name = "Unnamed_Company"
        return os.path.join(self.audio_base_dir, clean_name)

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
                file_headers = next(reader, None) or []
                file_headers = [str(header).strip() for header in file_headers]
                needs_rewrite = file_headers != headers

                for row in reader:
                    if not row or not any(row):
                        continue

                    # Map by the header names so legacy files with a shorter
                    # schema (created by the BOM startup helper) are not shifted
                    # into the wrong CRM fields when the country column is added.
                    row_by_header = {
                        name: row[index]
                        for index, name in enumerate(file_headers)
                        if index < len(row)
                    }
                    migrated_row = [
                        "" if row_by_header.get(field) is None else row_by_header[field]
                        for field in headers
                    ]

                    for field in ("activity_count", "mobile_recording_count"):
                        index = headers.index(field)
                        if migrated_row[index] == "No" or (
                            field not in file_headers and not migrated_row[index]
                        ):
                            migrated_row[index] = "0"

                    if len(row) > len(file_headers):
                        needs_rewrite = True
                    updated_rows.append(migrated_row)

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
        ttk.Button(
            nav_frame, text="🏢 Company Sorting", command=self.show_company_sorting
        ).pack(side="left", padx=5)
        ttk.Button(
            nav_frame, text="📊 Graph", command=self.show_company_graph
        ).pack(side="left", padx=5)

        # Main container for different views
        self.view_container = ttk.Frame(self.content_frame)
        self.view_container.pack(fill="both", expand=True)

        # Build CRM Management view (default)
        self.build_crm_management()

    def on_data_sent_change(self, event=None):
        """Handle data sent combobox change."""
        if hasattr(self, 'crm_data_sent') and hasattr(self, 'crm_data_type_name'):
            if self.crm_data_sent.get() == "Yes":
                self.crm_data_type_name.config(state="normal")
            else:
                self.crm_data_type_name.config(state="disabled")
                self.crm_data_type_name.delete(0, tk.END)

    def on_enquiry_change(self, event=None):
        """Handle enquiry combobox change."""
        if hasattr(self, 'crm_enquiry') and hasattr(self, 'crm_enquiry_type'):
            if self.crm_enquiry.get() == "Yes":
                self.crm_enquiry_type.config(state="normal")
            else:
                self.crm_enquiry_type.config(state="disabled")
                self.crm_enquiry_type.delete(0, tk.END)

    @staticmethod
    def _with_saved_choice(options, saved_value):
        """Keep a historical value selectable when the data set changes."""
        saved_value = (saved_value or "").strip()
        if not saved_value or saved_value in options:
            return options
        return (saved_value, *options)

    def _update_location_suggestions(self, field, widget, values):
        """Refresh the visible suggestion list without taking focus."""
        values = tuple(values)
        self._location_suggestion_values[field] = values
        listbox = self._location_suggestion_listboxes.get(field)
        popup = self._location_suggestion_popups.get(field)
        if listbox is None or popup is None:
            return
        try:
            if not listbox.winfo_exists() or not popup.winfo_exists():
                return
            listbox.delete(0, tk.END)
            displayed = values or ("No matching location",)
            for value in displayed[:8]:
                listbox.insert(tk.END, value)
            height = min(180, max(32, len(displayed[:8]) * 23 + 6))
            width = max(180, widget.winfo_width())
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            popup.geometry(f"{width}x{height}+{x}+{y}")
            popup.deiconify()
            popup.lift()
        except tk.TclError:
            pass

    def _post_location_dropdown(self, field, widget):
        """Show or refresh a non-focus-stealing suggestion popup."""
        self._location_post_scheduled[field] = False
        if getattr(self, "location_fields_locked", False):
            return
        if str(widget.cget("state")) == "disabled":
            return

        popup = self._location_suggestion_popups.get(field)
        values = tuple(widget.cget("values") or ())
        if popup is not None:
            try:
                if popup.winfo_exists():
                    self._location_popup_open[field] = True
                    self._update_location_suggestions(field, widget, values)
                    return
            except tk.TclError:
                pass

        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        listbox = tk.Listbox(
            popup,
            height=6,
            width=24,
            exportselection=False,
            relief="solid",
            borderwidth=1,
            activestyle="none",
        )
        listbox.pack(fill="both", expand=True)
        listbox.bind(
            "<<ListboxSelect>>",
            lambda event, field=field: self._select_location_suggestion(field),
        )
        listbox.bind(
            "<Return>",
            lambda event, field=field: self._select_location_suggestion(field),
        )
        self._location_suggestion_popups[field] = popup
        self._location_suggestion_listboxes[field] = listbox
        self._location_popup_open[field] = True
        self._update_location_suggestions(field, widget, values)

    def _select_location_suggestion(self, field, event=None):
        """Apply a suggestion selected from the visible list."""
        listbox = self._location_suggestion_listboxes.get(field)
        values = self._location_suggestion_values.get(field, ())
        if listbox is None or not values:
            return "break"
        try:
            selection = listbox.curselection()
        except tk.TclError:
            return "break"
        if not selection or selection[0] >= len(values):
            return "break"
        value = values[selection[0]]
        self._close_location_dropdown(field)
        if field == "country":
            self._set_location_values(value)
        elif field == "state":
            self._set_location_values(self.crm_country.get(), value)
        else:
            self._set_location_values(
                self.crm_country.get(), self.crm_state.get(), value
            )
        self._save_location_preferences()
        return "break"

    def _close_location_dropdown(self, field, event=None):
        """Close the visible suggestions and allow them to reopen."""
        popup = self._location_suggestion_popups.get(field)
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass
        self._location_suggestion_popups[field] = None
        self._location_suggestion_listboxes[field] = None
        self._location_suggestion_values[field] = ()
        self._location_popup_open[field] = False
        self._location_post_scheduled[field] = False
        try:
            widget = getattr(self, f"crm_{field}")
            self.tk.call("ttk::combobox::Unpost", str(widget))
        except (AttributeError, tk.TclError):
            pass
        return "break"

    def _location_focus_in(self, field, event=None):
        """Reset popup state when the user returns to a location textbox."""
        if not getattr(self, "location_fields_locked", False):
            self._location_popup_open[field] = False
            self._location_post_scheduled[field] = False

    @staticmethod
    def _location_text_matches(choice, query):
        """Match full text or any combination of typed words."""
        tokens = query.casefold().split()
        normalized_choice = choice.casefold()
        return not tokens or all(token in normalized_choice for token in tokens)

    def _filter_location_dropdown(self, field, event=None):
        """Filter choices as the user types and show the matching popup."""
        widget = getattr(self, f"crm_{field}")
        if getattr(self, "location_fields_locked", False):
            return
        if str(widget.cget("state")) == "disabled":
            return

        query = widget.get().strip()
        choices = self._location_choices.get(field, ())
        if query:
            filtered = tuple(
                choice
                for choice in choices
                if self._location_text_matches(choice, query)
            )
        else:
            filtered = tuple(choices)
        widget.config(values=filtered)
        if not self._location_post_scheduled.get(field):
            self._location_post_scheduled[field] = True
            self.after_idle(
                lambda field=field, widget=widget: self._post_location_dropdown(
                    field, widget
                )
            )

    def _resolve_location_text(self, field):
        """Resolve a typed value to one unique available choice."""
        widget = getattr(self, f"crm_{field}")
        typed_value = widget.get().strip()
        current_choices = tuple(widget.cget("values") or ())
        choices = current_choices or self._location_choices.get(field, ())
        match = locations.canonical_name(typed_value, choices)
        if not match and typed_value:
            partial_matches = [
                choice
                for choice in choices
                if self._location_text_matches(choice, typed_value)
            ]
            if len(partial_matches) == 1:
                match = partial_matches[0]
        if match:
            widget.set(match)
        return match or typed_value

    def _commit_location_text(self, field, event=None):
        """Commit a typed location when Enter is pressed."""
        self._close_location_dropdown(field)
        value = self._resolve_location_text(field)
        if field == "country":
            self._set_location_values(value)
        elif field == "state":
            self._set_location_values(self.crm_country.get(), value)
        elif field == "district":
            self._set_location_values(
                self.crm_country.get(), self.crm_state.get(), value
            )
        self._save_location_preferences()
        return "break"

    def _refresh_location_dropdown_states(self):
        """Keep location fields editable while respecting parent selections."""
        if not hasattr(self, "crm_country"):
            return

        if getattr(self, "location_fields_locked", False):
            self.crm_country.config(state="disabled")
            self.crm_state.config(state="disabled")
            self.crm_district.config(state="disabled")
            return

        self.crm_country.config(state="normal")
        self.crm_state.config(
            state="normal" if self.crm_state.cget("values") else "disabled"
        )
        self.crm_district.config(
            state="normal" if self.crm_district.cget("values") else "disabled"
        )

    def _set_location_values(self, country="", state="", district=""):
        """Populate editable, dependent location dropdowns."""
        for field in self._location_popup_open:
            if self._location_suggestion_popups.get(field) is not None:
                self._close_location_dropdown(field)
            self._location_popup_open[field] = False
            self._location_post_scheduled[field] = False
        country = str(country or "").strip()
        state = str(state or "").strip()
        district = str(district or "").strip()

        country_options = locations.COUNTRY_NAMES
        if country and not locations.is_known_country(country):
            country_options = (country, *country_options)
        self._location_choices["country"] = tuple(country_options)
        self.crm_country.config(values=country_options)
        self.crm_country.set(country)

        state_options = locations.states_for_country(country)
        selected_state = locations.canonical_name(state, state_options)
        if not selected_state:
            selected_state = state
        state_choices = self._with_saved_choice(state_options, selected_state)
        self._location_choices["state"] = tuple(state_choices)
        self.crm_state.config(values=state_choices)
        self.crm_state.set(selected_state)

        district_options = locations.districts_for_country(country, selected_state)
        selected_district = locations.canonical_name(
            district, district_options
        )
        if not selected_district:
            selected_district = district
        district_choices = self._with_saved_choice(
            district_options, selected_district
        )
        self._location_choices["district"] = tuple(district_choices)
        self.crm_district.config(values=district_choices)
        self.crm_district.set(selected_district)
        self._refresh_location_dropdown_states()

    def on_country_change(self, event=None):
        """Reset state and district when a different country is selected."""
        self._location_popup_open["country"] = False
        self._set_location_values(self.crm_country.get())
        self._save_location_preferences()

    def on_state_change(self, event=None):
        """Reset district when a different state is selected."""
        self._location_popup_open["state"] = False
        self._set_location_values(
            self.crm_country.get(), self.crm_state.get()
        )
        self._save_location_preferences()

    def on_district_change(self, event=None):
        """Remember the last confirmed district selection."""
        self._location_popup_open["district"] = False
        self._save_location_preferences()

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
            text="Search Company / GST / Contact / Owner / Country / State / District / Location:",
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
            "Country",
            "State",
            "District",
            "Location",
            "Owner Name",
            "Products",
            "Valuable %",
            "Rating",
            "Activity",
            "Mobile Rec",
            "Data Sent",
            "Enquiry",
            "Call Time",
            "Conv Date",
            "Meeting Time",
            "Next Meeting",
        )
        self.crm_tree = ttk.Treeview(
            records_frame, columns=cols, show="headings", height=4
        )

        self.crm_tree.heading("#", text="#")
        self.crm_tree.column("#", width=25, anchor="center")

        for col in cols[1:]:
            self.crm_tree.heading(col, text=col)
            if col == "Valuable %":
                self.crm_tree.column(col, width=60, anchor="center")
            elif col == "Rating":
                self.crm_tree.column(col, width=50, anchor="center")
            elif col == "Activity":
                self.crm_tree.column(col, width=50, anchor="center")
            elif col == "Mobile Rec":
                self.crm_tree.column(col, width=60, anchor="center")
            else:
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
        ttk.Button(
            tbl_ctrl_frame,
            text="📥 Import Excel / CSV / PDF",
            command=self.import_company_data,
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
        self.crm_gst.bind("<FocusOut>", lambda e: self.on_gst_entered())
        self.crm_gst.bind("<Return>", lambda e: self.on_gst_entered())
        gst_btn = ttk.Button(left_info_frame, text="🔍",
            width=3, command=self.on_gst_entered)
        gst_btn.grid(row=1, column=2, padx=2)

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

        ttk.Label(left_info_frame, text="Country:").grid(
            row=7, column=0, sticky="w", pady=2
        )
        self.crm_country = ttk.Combobox(
            left_info_frame,
            values=locations.COUNTRY_NAMES,
            width=24,
            state="normal",
        )
        self.crm_country.grid(row=7, column=1, sticky="ew", pady=2, padx=4)
        self.crm_country.bind(
            "<<ComboboxSelected>>", self.on_country_change
        )
        self.crm_country.bind(
            "<FocusIn>",
            lambda event: self._location_focus_in("country", event),
        )
        self.crm_country.bind(
            "<KeyRelease>",
            lambda event: self._filter_location_dropdown("country", event),
        )
        self.crm_country.bind(
            "<Return>",
            lambda event: self._commit_location_text("country", event),
        )
        self.crm_country.bind(
            "<Escape>",
            lambda event: self._close_location_dropdown("country", event),
        )

        ttk.Label(left_info_frame, text="State:").grid(
            row=8, column=0, sticky="w", pady=2
        )
        self.crm_state = ttk.Combobox(
            left_info_frame, width=24, state="disabled"
        )
        self.crm_state.grid(row=8, column=1, sticky="ew", pady=2, padx=4)
        self.crm_state.bind("<<ComboboxSelected>>", self.on_state_change)
        self.crm_state.bind(
            "<FocusIn>",
            lambda event: self._location_focus_in("state", event),
        )
        self.crm_state.bind(
            "<KeyRelease>",
            lambda event: self._filter_location_dropdown("state", event),
        )
        self.crm_state.bind(
            "<Return>",
            lambda event: self._commit_location_text("state", event),
        )
        self.crm_state.bind(
            "<Escape>",
            lambda event: self._close_location_dropdown("state", event),
        )

        ttk.Label(left_info_frame, text="District:").grid(
            row=9, column=0, sticky="w", pady=2
        )
        self.crm_district = ttk.Combobox(
            left_info_frame, width=24, state="disabled"
        )
        self.crm_district.grid(row=9, column=1, sticky="ew", pady=2, padx=4)
        self.crm_district.bind(
            "<<ComboboxSelected>>", self.on_district_change
        )
        self.crm_district.bind(
            "<FocusIn>",
            lambda event: self._location_focus_in("district", event),
        )
        self.crm_district.bind(
            "<KeyRelease>",
            lambda event: self._filter_location_dropdown("district", event),
        )
        self.crm_district.bind(
            "<Return>",
            lambda event: self._commit_location_text("district", event),
        )
        self.crm_district.bind(
            "<Escape>",
            lambda event: self._close_location_dropdown("district", event),
        )

        ttk.Label(left_info_frame, text="Location:").grid(
            row=10, column=0, sticky="w", pady=2
        )
        self.crm_location = ttk.Entry(left_info_frame, width=24)
        self.crm_location.grid(row=10, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Company Turnover:").grid(
            row=11, column=0, sticky="w", pady=2
        )
        self.crm_turnover = ttk.Entry(left_info_frame, width=24)
        self.crm_turnover.grid(row=11, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Owner Name:").grid(
            row=12, column=0, sticky="w", pady=2
        )
        self.crm_owner_name = ttk.Entry(left_info_frame, width=24)
        self.crm_owner_name.grid(row=12, column=1, sticky="ew", pady=2, padx=4)

        ttk.Label(left_info_frame, text="Number of Staff:").grid(
            row=13, column=0, sticky="w", pady=2
        )
        self.crm_staff_count = ttk.Entry(left_info_frame, width=24)
        self.crm_staff_count.grid(row=13, column=1, sticky="ew", pady=2, padx=4)

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

        self.chk_booster = tk.Checkbutton(prod_frame, text="Booster Pump", variable=self.var_booster, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_booster.grid(row=0, column=0, sticky="w", padx=2)
        self.chk_stp = tk.Checkbutton(prod_frame, text="STP", variable=self.var_stp, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_stp.grid(row=0, column=1, sticky="w", padx=2)
        self.chk_water_meter = tk.Checkbutton(prod_frame, text="Water Meter", variable=self.var_water_meter, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_water_meter.grid(row=0, column=2, sticky="w", padx=2)

        self.chk_bms = tk.Checkbutton(prod_frame, text="BMS", variable=self.var_bms, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_bms.grid(row=1, column=0, sticky="w", padx=2)
        self.chk_wtp = tk.Checkbutton(prod_frame, text="WTP", variable=self.var_wtp, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_wtp.grid(row=1, column=1, sticky="w", padx=2)
        self.chk_ro = tk.Checkbutton(prod_frame, text="RO", variable=self.var_ro, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_ro.grid(row=1, column=2, sticky="w", padx=2)

        self.chk_fire_panel = tk.Checkbutton(prod_frame, text="Fire Panel", variable=self.var_fire_panel, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_fire_panel.grid(row=2, column=0, sticky="w", padx=2)
        self.chk_dewatering_panel = tk.Checkbutton(prod_frame, text="De-watering Panel", variable=self.var_dewatering_panel, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_dewatering_panel.grid(row=2, column=1, sticky="w", padx=2)
        self.chk_water_softener = tk.Checkbutton(prod_frame, text="Water Softener", variable=self.var_water_softener, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_water_softener.grid(row=2, column=2, sticky="w", padx=2)

        self.chk_choice_a = tk.Checkbutton(prod_frame, text="Choice A", variable=self.var_choice_a, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_choice_a.grid(row=3, column=0, sticky="w", padx=2)
        self.chk_pump_skid = tk.Checkbutton(prod_frame, text="Pump Skid", variable=self.var_pump_skid, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_pump_skid.grid(row=3, column=1, sticky="w", padx=2)
        self.chk_pump_sensor_panel = tk.Checkbutton(prod_frame, text="Sensor Panel", variable=self.var_pump_sensor_panel, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w")
        self.chk_pump_sensor_panel.grid(row=3, column=2, sticky="w", padx=2)

        # --- RIGHT COLUMN FIELDS ---
        # Photos Frame (small compact box)
        photos_frame = ttk.LabelFrame(right_column, text=" Photos ", padding="2")
        photos_frame.pack(fill="x", pady=(0, 4))

        self.photo_listbox = tk.Listbox(photos_frame, width=18, height=2)
        self.photo_listbox.pack(side="left", fill="both", expand=True, padx=(0, 4))

        photo_btn_frame = ttk.Frame(photos_frame)
        photo_btn_frame.pack(side="right")

        self.btn_add_photos = ttk.Button(
            photo_btn_frame, text="📷 Add", width=9, command=self.select_photos
        )
        self.btn_add_photos.pack(pady=1)
        self.btn_remove_photo = ttk.Button(
            photo_btn_frame, text="❌ Remove", width=9, command=self.remove_selected_photo
        )
        self.btn_remove_photo.pack(pady=1)
        self.btn_open_folder = ttk.Button(
            photo_btn_frame, text="📁 Open", width=9, command=self.open_company_photos_folder
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

        self.chk_val_vfd = tk.Checkbutton(
            val_chk_grid, text="Work in VFD Panel", variable=self.var_val_vfd, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w"
        )
        self.chk_val_vfd.grid(row=0, column=0, sticky="w", padx=2)

        self.chk_val_dewatering = tk.Checkbutton(
            val_chk_grid, text="Work in Dewatering", variable=self.var_val_dewatering, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w"
        )
        self.chk_val_dewatering.grid(row=0, column=1, sticky="w", padx=2)

        self.chk_val_distributor = tk.Checkbutton(
            val_chk_grid, text="Distributor", variable=self.var_val_distributor, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w"
        )
        self.chk_val_distributor.grid(row=1, column=0, sticky="w", padx=2)

        self.chk_val_dealer = tk.Checkbutton(
            val_chk_grid, text="Dealer", variable=self.var_val_dealer, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w"
        )
        self.chk_val_dealer.grid(row=1, column=1, sticky="w", padx=2)

        self.chk_val_serious_base = tk.Checkbutton(
            val_chk_grid, text="Serious Base", variable=self.var_val_serious_base, onvalue=True, offvalue=False, selectcolor="white", activebackground="#f0f0f0", anchor="w"
        )
        self.chk_val_serious_base.grid(row=2, column=0, sticky="w", padx=2)

        # Valuable Customer Percentage Field
        percentage_frame = ttk.Frame(val_chk_grid)
        percentage_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(percentage_frame, text="Valuable Customer %:").pack(side="left")
        self.crm_valuable_percentage = ttk.Entry(percentage_frame, width=6)
        self.crm_valuable_percentage.pack(side="left", padx=2)
        ttk.Label(percentage_frame, text="(0-100)", font=("Helvetica", 8)).pack(side="left")
        
        ttk.Button(percentage_frame, text="🧮 Auto-Calculate", width=12, 
                  command=self.auto_calculate_valuable_percentage).pack(side="left", padx=2)

        # Customer Rating Field
        rating_frame = ttk.Frame(val_chk_grid)
        rating_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(rating_frame, text="Customer Rating:").pack(side="left")
        self.crm_customer_rating = ttk.Entry(rating_frame, width=6)
        self.crm_customer_rating.pack(side="left", padx=2)
        ttk.Label(rating_frame, text="(0-100)", font=("Helvetica", 8)).pack(side="left")

        # Activity Count Field
        activity_frame = ttk.Frame(val_chk_grid)
        activity_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(activity_frame, text="Activity Count:").pack(side="left")
        self.crm_activity_count = ttk.Entry(activity_frame, width=6, state="readonly")
        self.crm_activity_count.pack(side="left", padx=2)
        ttk.Label(activity_frame, text="(Auto-increments on activity)", font=("Helvetica", 8)).pack(side="left")

        # Audio Recordings Field
        audio_frame = ttk.Frame(val_chk_grid)
        audio_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(audio_frame, text="Audio Recordings:").pack(side="left")
        self.audio_listbox = tk.Listbox(audio_frame, width=20, height=2)
        self.audio_listbox.pack(side="left", fill="both", expand=True, padx=(0, 4))

        audio_btn_frame = ttk.Frame(audio_frame)
        audio_btn_frame.pack(side="right")

        self.btn_add_audio = ttk.Button(
            audio_btn_frame, text="🎤 Upload", width=11, command=self.select_audio_recordings
        )
        self.btn_add_audio.pack(pady=1)
        self.btn_remove_audio = ttk.Button(
            audio_btn_frame, text="❌ Remove", width=11, command=self.remove_selected_audio
        )
        self.btn_remove_audio.pack(pady=1)
        self.btn_play_audio = ttk.Button(
            audio_btn_frame, text="▶️ Play", width=11, command=self.play_selected_audio
        )
        self.btn_play_audio.pack(pady=1)

        # Mobile Recording Count Field
        mobile_rec_frame = ttk.Frame(val_chk_grid)
        mobile_rec_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(mobile_rec_frame, text="Mobile Recording Count:").pack(side="left")
        self.crm_mobile_recording_count = ttk.Entry(
            mobile_rec_frame, width=6, state="readonly"
        )
        self.crm_mobile_recording_count.pack(side="left", padx=2)
        ttk.Label(
            mobile_rec_frame, text="(Auto-increments on recording)", font=("Helvetica", 8)
        ).pack(side="left")

        # Distributor Field Row (name entry enabled by Distributor checkbox above)
        dist_subframe = ttk.Frame(val_chk_grid)
        dist_subframe.grid(row=8, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(dist_subframe, text="Distributor Name:").pack(side="left")

        self.crm_distributor_name = ttk.Entry(
            dist_subframe, width=14, state="disabled"
        )
        self.crm_distributor_name.pack(side="left", padx=2)

        # Dealer Field Row (name entry enabled by Dealer checkbox above)
        dealer_subframe = ttk.Frame(val_chk_grid)
        dealer_subframe.grid(row=9, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(dealer_subframe, text="Dealer Name:").pack(side="left")

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

        # Date of Conversion (default today) — calendar selectable
        ttk.Label(row_act1, text="Conv. Date:").pack(side="left", padx=(10, 0))
        if HAS_TKCALENDAR:
            self.crm_conversion_date = DateEntry(
                row_act1, width=10, date_pattern="yyyy-mm-dd",
                background="darkblue", foreground="white",
            )
            self.crm_conversion_date.pack(side="left", padx=2)
        else:
            self.crm_conversion_date = ttk.Entry(row_act1, width=11)
            self.crm_conversion_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
            self.crm_conversion_date.pack(side="left", padx=2)

        ttk.Label(row_act1, text="Data Sent:").pack(side="left", padx=(10, 0))
        self.crm_data_sent = ttk.Combobox(
            row_act1, values=["Yes", "No"], width=5, state="readonly"
        )
        self.crm_data_sent.set("No")
        self.crm_data_sent.pack(side="left", padx=2)

        # Data Type Name (shown when Data Sent = Yes)
        ttk.Label(row_act1, text="Data Type:").pack(side="left", padx=(8, 0))
        self.crm_data_type_name = ttk.Entry(row_act1, width=10, state="disabled")
        self.crm_data_type_name.pack(side="left", padx=2)

        # Enquiry + Enquiry Type shifted to NEXT LINE (own row)
        row_act1b = ttk.Frame(activity_frame)
        row_act1b.pack(fill="x", pady=2)

        ttk.Label(row_act1b, text="Enquiry:").pack(side="left")
        self.crm_enquiry = ttk.Combobox(
            row_act1b, values=["Yes", "No"], width=5, state="readonly"
        )
        self.crm_enquiry.set("No")
        self.crm_enquiry.pack(side="left", padx=2)

        # Enquiry Type (shown when Enquiry = Yes)
        ttk.Label(row_act1b, text="Enquiry Type:").pack(side="left", padx=(8, 0))
        self.crm_enquiry_type = ttk.Entry(row_act1b, width=16, state="disabled")
        self.crm_enquiry_type.pack(side="left", padx=2)
        
        # Bind events to show/hide conditional fields
        self.crm_data_sent.bind("<<ComboboxSelected>>", lambda e: self.on_data_sent_change(e))
        self.crm_enquiry.bind("<<ComboboxSelected>>", lambda e: self.on_enquiry_change(e))

        # Meeting Schedule
        row_act2 = ttk.Frame(activity_frame)
        row_act2.pack(fill="x", pady=2)

        ttk.Label(row_act2, text="Meeting Time:").pack(side="left")
        self.crm_meeting_time = ttk.Entry(row_act2, width=16)
        self.crm_meeting_time.pack(side="left", padx=2)

        ttk.Button(
            row_act2, text="📅", width=3, command=self.open_datetime_picker
        ).pack(side="left")

        # Next Meeting date+time (selectable) with 15-min alarm popup
        row_act2b = ttk.Frame(activity_frame)
        row_act2b.pack(fill="x", pady=2)

        ttk.Label(row_act2b, text="Next Meeting:").pack(side="left")
        self.crm_next_meeting = ttk.Entry(row_act2b, width=16)
        self.crm_next_meeting.pack(side="left", padx=2)
        ttk.Button(
            row_act2b, text="📅", width=3,
            command=lambda: self.open_datetime_picker(target="next"),
        ).pack(side="left")
        self.crm_next_alarm = ttk.Label(
            row_act2b, text="🔔 alarm 15 min before",
            foreground="red", font=("Helvetica", 8, "bold"),
        )
        self.crm_next_alarm.pack(side="left", padx=(8, 0))

        # Saturday Alarm Indicator
        self.crm_saturday_alarm = ttk.Label(
            row_act2, text="", foreground="red", font=("Helvetica", 9, "bold")
        )
        self.crm_saturday_alarm.pack(side="left", padx=(10, 0))

        # Bind meeting time changes to check Saturday alarm
        self.crm_meeting_time.bind("<KeyRelease>", lambda e: self.check_saturday_alarm())

        ttk.Label(row_act2, text="Agenda:").pack(side="left", padx=(8, 0))
        self.crm_meeting_agenda = ttk.Entry(row_act2, width=15)
        self.crm_meeting_agenda.pack(side="left", padx=2)

        # Communication Date — calendar selectable
        comm_date_row = ttk.Frame(activity_frame)
        comm_date_row.pack(fill="x", pady=2)
        ttk.Label(comm_date_row, text="Conversation Date:").pack(side="left")
        if HAS_TKCALENDAR:
            self.crm_comm_date = DateEntry(
                comm_date_row, width=10, date_pattern="yyyy-mm-dd",
                background="darkblue", foreground="white",
            )
            self.crm_comm_date.pack(side="left", padx=2)
        else:
            self.crm_comm_date = ttk.Entry(comm_date_row, width=12)
            self.crm_comm_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
            self.crm_comm_date.pack(side="left", padx=2)
        ttk.Label(
            comm_date_row, text="(pick from calendar)",
            font=("Helvetica", 7), foreground="gray",
        ).pack(side="left", padx=4)

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

        self._load_default_location_values()
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

    def auto_calculate_valuable_percentage(self):
        """Automatically calculate valuable customer percentage based on combined factors."""
        try:
            percentage = 0
            
            # Factor 1: Company Turnover (0-25 points)
            turnover_str = self.crm_turnover.get().strip()
            if turnover_str:
                try:
                    turnover = float(turnover_str.replace(',', '').replace('L', '').replace('l', ''))
                    if turnover >= 100:  # 100L+ crore turnover
                        percentage += 25
                    elif turnover >= 50:  # 50-100L crore turnover
                        percentage += 20
                    elif turnover >= 10:  # 10-50L crore turnover
                        percentage += 15
                    elif turnover >= 5:   # 5-10L crore turnover
                        percentage += 10
                    elif turnover >= 1:   # 1-5L crore turnover
                        percentage += 5
                except (ValueError, AttributeError):
                    pass
            
            # Factor 2: Products Selected (0-20 points)
            selected_products = self.get_selected_products_str()
            product_count = len([p for p in selected_products.split(',') if p.strip()])
            if product_count >= 5:
                percentage += 20
            elif product_count >= 3:
                percentage += 15
            elif product_count >= 2:
                percentage += 10
            elif product_count >= 1:
                percentage += 5
            
            # Factor 3: Company Valuation (0-20 points)
            valuation_factors = 0
            if self.var_val_vfd.get():
                valuation_factors += 1
            if self.var_val_dewatering.get():
                valuation_factors += 1
            if self.var_val_serious_base.get():
                valuation_factors += 1
            if self.var_val_distributor.get():
                valuation_factors += 1
            if self.var_val_dealer.get():
                valuation_factors += 1
            
            if valuation_factors >= 4:
                percentage += 20
            elif valuation_factors >= 3:
                percentage += 15
            elif valuation_factors >= 2:
                percentage += 10
            elif valuation_factors >= 1:
                percentage += 5
            
            # Factor 4: Engagement Metrics (0-20 points)
            engagement_score = 0
            
            # Enquiry status
            if self.crm_enquiry.get() == "Yes":
                engagement_score += 8
            
            # Data sent
            if self.crm_data_sent.get() == "Yes":
                engagement_score += 7
            
            # Call duration
            call_hours = int(self.crm_call_hours.get())
            call_mins = int(self.crm_call_mins.get())
            total_call_mins = call_hours * 60 + call_mins
            if total_call_mins >= 30:
                engagement_score += 5
            elif total_call_mins >= 15:
                engagement_score += 3
            elif total_call_mins >= 5:
                engagement_score += 1
            
            percentage += engagement_score
            
            # Factor 5: Number of Staff (0-15 points)
            staff_str = self.crm_staff_count.get().strip()
            if staff_str:
                try:
                    staff_count = int(staff_str)
                    if staff_count >= 100:
                        percentage += 15
                    elif staff_count >= 50:
                        percentage += 12
                    elif staff_count >= 20:
                        percentage += 8
                    elif staff_count >= 10:
                        percentage += 5
                    elif staff_count >= 5:
                        percentage += 3
                except (ValueError, AttributeError):
                    pass
            
            # Cap at 100%
            percentage = min(percentage, 100)
            
            # Update the field
            self.crm_valuable_percentage.delete(0, tk.END)
            self.crm_valuable_percentage.insert(0, str(percentage))
            
            messagebox.showinfo("Auto-Calculation Complete", 
                              f"Valuable Customer Percentage calculated as {percentage}%\n\n"
                              f"Factors considered:\n"
                              f"- Company Turnover\n"
                              f"- Products Selected\n"
                              f"- Company Valuation\n"
                              f"- Engagement Metrics\n"
                              f"- Number of Staff")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to auto-calculate: {e}")

    def auto_increment_activity_count(self):
        """Auto-increment the activity count when communication details are updated."""
        try:
            current_count = self.crm_activity_count.get().strip()
            if not current_count or current_count == "No":
                current_count = "0"
            
            # Try to convert to int, handle any conversion errors
            try:
                current_count_int = int(current_count)
            except (ValueError, TypeError):
                current_count_int = 0
            
            new_count = current_count_int + 1
            self.crm_activity_count.config(state="normal")
            self.crm_activity_count.delete(0, tk.END)
            self.crm_activity_count.insert(0, str(new_count))
            self.crm_activity_count.config(state="readonly")
            
            return new_count
        except Exception as e:
            print(f"Failed to auto-increment activity count: {e}")
            return 0

    def increment_mobile_recording_count(self):
        """Increment the mobile recording count for the current customer."""
        try:
            current_count = self.crm_mobile_recording_count.get().strip()
            if not current_count or current_count == "No":
                current_count = "0"
            
            # Try to convert to int, handle any conversion errors
            try:
                current_count_int = int(current_count)
            except (ValueError, TypeError):
                current_count_int = 0
            
            new_count = current_count_int + 1
            self.crm_mobile_recording_count.config(state="normal")
            self.crm_mobile_recording_count.delete(0, tk.END)
            self.crm_mobile_recording_count.insert(0, str(new_count))
            self.crm_mobile_recording_count.config(state="readonly")
            
            messagebox.showinfo("Mobile Recording Count Updated", 
                              f"Mobile recording count incremented to {new_count}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to increment mobile recording count: {e}")

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

    def select_audio_recordings(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Audio Recordings",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                ("All Files", "*.*"),
            ],
        )
        if file_paths:
            for path in file_paths:
                filename = os.path.basename(path)
                if path not in self.selected_audio_paths:
                    self.selected_audio_paths.append(path)
                    self.audio_listbox.insert(tk.END, filename)

    def remove_selected_audio(self):
        selected_indices = self.audio_listbox.curselection()
        if not selected_indices:
            return
        idx = selected_indices[0]
        self.audio_listbox.delete(idx)
        if idx < len(self.selected_audio_paths):
            del self.selected_audio_paths[idx]

    def play_selected_audio(self):
        selected_indices = self.audio_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an audio file to play.")
            return
        
        idx = selected_indices[0]
        if idx < len(self.selected_audio_paths):
            audio_path = self.selected_audio_paths[idx]
            try:
                if sys.platform == "win32":
                    os.startfile(audio_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", audio_path])
                else:
                    subprocess.Popen(["xdg-open", audio_path])
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play audio file:\n{e}")

    def open_company_audio_folder(self):
        company_name = self.crm_company.get().strip()
        if not company_name:
            messagebox.showwarning(
                "Company Name Required",
                "Please enter or load a company name to open its audio folder.",
            )
            return

        folder_path = self.get_company_audio_dir(company_name)
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

    def process_and_save_audio(self, company_name):
        if not company_name:
            return ""

        target_dir = self.get_company_audio_dir(company_name)
        os.makedirs(target_dir, exist_ok=True)

        saved_filenames = []
        for src_path in self.selected_audio_paths:
            if os.path.exists(src_path):
                # If the file already lives in the customer's folder (loaded
                # from an existing record), keep it as-is.
                if os.path.abspath(os.path.dirname(src_path)) == os.path.abspath(target_dir):
                    saved_filenames.append(os.path.basename(src_path))
                    continue

                # Store each recording in the customer's folder using a
                # date-time based filename (YYYYMMDD_HHMMSS).
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(src_path)[1].lower()
                fname = f"{timestamp}{ext}"
                dest_path = os.path.join(target_dir, fname)

                # Avoid overwriting if multiple recordings share the same second.
                counter = 1
                while os.path.exists(dest_path):
                    fname = f"{timestamp}_{counter}{ext}"
                    dest_path = os.path.join(target_dir, fname)
                    counter += 1

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

    def check_saturday_alarm(self):
        if not hasattr(self, "crm_meeting_time") or not self.crm_meeting_time.winfo_exists():
            return
        meeting_time_str = self.crm_meeting_time.get().strip()
        if not meeting_time_str:
            try:
                self.crm_saturday_alarm.config(text="")
            except Exception:
                pass
            return
        try:
            parts = meeting_time_str.split()
            if len(parts) >= 3:
                date_str = parts[0]
                date_parts = date_str.split("-")
                if len(date_parts) == 3:
                    year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    import calendar
                    weekday = calendar.weekday(year, month, day)
                    if weekday == 5:
                        self.crm_saturday_alarm.config(
                            text="SATURDAY MEETING - Confirm availability!"
                        )
                        return
            self.crm_saturday_alarm.config(text="")
        except Exception:
            try:
                self.crm_saturday_alarm.config(text="")
            except Exception:
                pass

    def on_meeting_time_selected(self, datetime_str):
        self.crm_meeting_time.delete(0, tk.END)
        self.crm_meeting_time.insert(0, datetime_str)
        self.check_saturday_alarm()

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

    def open_datetime_picker(self, target="meeting"):
        if target == "next" and hasattr(self, "crm_next_meeting"):
            DateTimePickerPopup(
                self.winfo_toplevel(),
                initial_val=self.crm_next_meeting.get(),
                on_select_callback=self.set_next_meeting_value,
            )
            return
        DateTimePickerPopup(
            self.winfo_toplevel(),
            initial_val=self.crm_meeting_time.get(),
            on_select_callback=self.set_meeting_time_value,
        )

    def set_next_meeting_value(self, formatted_str):
        if hasattr(self, "crm_next_meeting"):
            self.crm_next_meeting.delete(0, tk.END)
            self.crm_next_meeting.insert(0, formatted_str)

    def set_meeting_time_value(self, formatted_str):
        self.crm_meeting_time.delete(0, tk.END)
        self.crm_meeting_time.insert(0, formatted_str)
        try:
            self.check_saturday_alarm()
        except Exception:
            pass

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
        self.location_fields_locked = state in ("disabled", "readonly")
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
        self._refresh_location_dropdown_states()
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
        self.crm_valuable_percentage.config(state=target_state)
        self.crm_customer_rating.config(state=target_state)
        self.crm_activity_count.config(state="readonly")
        self.crm_mobile_recording_count.config(state="readonly")

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
        # Enable activity & communication fields for editing
        self.crm_call_hours.config(state="normal")
        self.crm_call_mins.config(state="normal")
        try:
            self.crm_conversion_date.config(state="normal")
        except Exception:
            pass
        self.crm_meeting_time.config(state="normal")
        self.crm_meeting_agenda.config(state="normal")
        self.crm_comm_text.config(state="normal")
        self.crm_meeting_outcome_text.config(state="normal")
        self.crm_notes_text.config(state="normal")
        # Enable data type name if data sent is Yes
        if self.crm_data_sent.get() == "Yes":
            self.crm_data_type_name.config(state="normal")
        # Enable enquiry type if enquiry is Yes
        if self.crm_enquiry.get() == "Yes":
            self.crm_enquiry_type.config(state="normal")
        messagebox.showinfo(
            "Editing Unlocked",
            "Customer identity, details, and activity/communication fields are now editable.",
        )

    def get_form_data(self):
        company = self.crm_company.get().strip()
        if not company:
            messagebox.showwarning("Warning", "Company Name is required.")
            return None

        self._save_location_preferences()
        contact = self.crm_contact.get().strip()
        if contact and not contact.isdigit():
            messagebox.showwarning(
                "Input Error",
                "Contact Number must contain only numerical digits.",
            )
            return None

        photo_str = self.process_and_save_photos(company)
        audio_str = self.process_and_save_audio(company)

        call_time_str = (
            f"{self.crm_call_hours.get()} hrs {self.crm_call_mins.get()} mins"
        )

        # Validate and get valuable customer percentage
        percentage_str = self.crm_valuable_percentage.get().strip()
        if percentage_str:
            try:
                percentage = float(percentage_str)
                if percentage < 0 or percentage > 100:
                    messagebox.showwarning("Input Error", "Valuable Customer Percentage must be between 0 and 100.")
                    return None
                percentage_str = str(percentage)
            except ValueError:
                messagebox.showwarning("Input Error", "Valuable Customer Percentage must be a valid number.")
                return None
        else:
            percentage_str = "0"

        # Validate and get customer rating
        rating_str = self.crm_customer_rating.get().strip()
        if rating_str:
            try:
                rating = float(rating_str)
                if rating < 0 or rating > 100:
                    messagebox.showwarning("Input Error", "Customer Rating must be between 0 and 100.")
                    return None
                rating_str = str(rating)
            except ValueError:
                messagebox.showwarning("Input Error", "Customer Rating must be a valid number.")
                return None
        else:
            rating_str = "0"

        # Get activity count
        activity_count_str = self.crm_activity_count.get().strip()
        if not activity_count_str:
            activity_count_str = "0"

        # Get mobile recording count
        mobile_recording_count_str = self.crm_mobile_recording_count.get().strip()
        if not mobile_recording_count_str:
            mobile_recording_count_str = "0"

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
            percentage_str,
            rating_str,
            activity_count_str,
            mobile_recording_count_str,
            self.crm_notes_text.get("1.0", tk.END).strip(),
            call_time_str,
            self._get_date_str(self.crm_conversion_date) if hasattr(self, "crm_conversion_date") else "",
            self.crm_data_sent.get(),
            self.crm_data_type_name.get().strip() if hasattr(self, "crm_data_type_name") else "",
            self.crm_enquiry.get(),
            self.crm_enquiry_type.get().strip() if hasattr(self, "crm_enquiry_type") else "",
            self.crm_comm_text.get("1.0", tk.END).strip(),
            self._get_date_str(self.crm_comm_date) if hasattr(self, "crm_comm_date") else "",
            self.crm_meeting_time.get().strip(),
            self.crm_next_meeting.get().strip() if hasattr(self, "crm_next_meeting") else "",
            self.crm_meeting_agenda.get().strip(),
            self.crm_meeting_outcome_text.get("1.0", tk.END).strip(),
            photo_str,
            audio_str,
            self.crm_country.get().strip(),
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
        saved_state = r[7] if len(r) > 7 else ""
        saved_district = r[8] if len(r) > 8 else ""
        headers = self.get_crm_headers()
        country_index = headers.index("country")
        saved_country = r[country_index] if len(r) > country_index else ""
        self._set_location_values(
            saved_country or "India", saved_state, saved_district
        )
        self.crm_location.insert(0, r[9] if len(r) > 9 else "")
        self.crm_turnover.insert(0, r[10] if len(r) > 10 else "")
        self.crm_owner_name.insert(0, r[11] if len(r) > 11 else "")
        self.crm_staff_count.insert(0, r[12] if len(r) > 12 else "")
        self.set_products_from_str(r[13] if len(r) > 13 else "")
        self.set_company_valuation_from_str(r[14] if len(r) > 14 else "")
        self.crm_valuable_percentage.insert(0, r[15] if len(r) > 15 else "0")
        self.crm_customer_rating.insert(0, r[16] if len(r) > 16 else "0")
        self.crm_activity_count.config(state="normal")
        activity_val = r[17] if len(r) > 17 else "0"
        # Handle "No" or other non-numeric values in activity count
        if activity_val == "No" or not activity_val.strip():
            activity_val = "0"
        self.crm_activity_count.insert(0, activity_val)
        self.crm_activity_count.config(state="readonly")
        self.crm_mobile_recording_count.config(state="normal")
        mobile_val = r[18] if len(r) > 18 else "0"
        # Handle "No" or other non-numeric values in mobile recording count
        if mobile_val == "No" or not mobile_val.strip():
            mobile_val = "0"
        self.crm_mobile_recording_count.insert(0, mobile_val)
        self.crm_mobile_recording_count.config(state="readonly")
        self.crm_notes_text.insert("1.0", r[19] if len(r) > 19 else "")
        self.set_call_time_from_str(r[20] if len(r) > 20 else "")
        # Load conversion date (index 21) — DateEntry-safe
        conv_date = r[21] if len(r) > 21 and r[21] else ""
        try:
            self.crm_conversion_date.delete(0, tk.END)
            self.crm_conversion_date.insert(
                0, conv_date if conv_date else datetime.date.today().strftime("%Y-%m-%d")
            )
        except Exception:
            pass
        self.crm_data_sent.set(r[22] if len(r) > 22 and r[22] else "No")
        # Load data type name (index 23)
        data_type = r[23] if len(r) > 23 and r[23] else ""
        if data_type:
            self.crm_data_type_name.config(state="normal")
            self.crm_data_type_name.delete(0, tk.END)
            self.crm_data_type_name.insert(0, data_type)
            self.crm_data_type_name.config(state="disabled")
        self.crm_enquiry.set(r[24] if len(r) > 24 and r[24] else "No")
        # Load enquiry type (index 25)
        enquiry_type = r[25] if len(r) > 25 and r[25] else ""
        if enquiry_type:
            self.crm_enquiry_type.config(state="normal")
            self.crm_enquiry_type.delete(0, tk.END)
            self.crm_enquiry_type.insert(0, enquiry_type)
            self.crm_enquiry_type.config(state="disabled")
        self.crm_comm_text.insert("1.0", r[26] if len(r) > 26 else "")
        # Conversation date (index 27), Meeting time (28), Next meeting (29)
        try:
            self.crm_comm_date.delete(0, tk.END)
            self.crm_comm_date.insert(0, r[27] if len(r) > 27 else "")
        except Exception:
            pass
        self.crm_meeting_time.insert(0, r[28] if len(r) > 28 else "")
        try:
            if hasattr(self, "crm_next_meeting"):
                self.crm_next_meeting.delete(0, tk.END)
                self.crm_next_meeting.insert(0, r[29] if len(r) > 29 else "")
        except Exception:
            pass
        self.crm_meeting_agenda.insert(0, r[30] if len(r) > 30 else "")
        self.crm_meeting_outcome_text.insert("1.0", r[31] if len(r) > 31 else "")

        photo_str = r[32] if len(r) > 32 else ""
        if photo_str:
            photo_dir = self.get_company_photos_dir(company_name)
            for fname in photo_str.split("|"):
                if fname:
                    full_path = os.path.join(photo_dir, fname)
                    self.selected_photo_paths.append(full_path)
                    self.photo_listbox.insert(tk.END, fname)

        audio_str = r[33] if len(r) > 33 else ""
        if audio_str:
            audio_dir = self.get_company_audio_dir(company_name)
            for fname in audio_str.split("|"):
                if fname:
                    full_path = os.path.join(audio_dir, fname)
                    self.selected_audio_paths.append(full_path)
                    self.audio_listbox.insert(tk.END, fname)

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

        # Check if communication details have changed
        current_comm = self.crm_comm_text.get("1.0", tk.END).strip()
        old_comm = self.all_rows[self.selected_row_index][23] if len(self.all_rows[self.selected_row_index]) > 23 else ""
        
        row_data = self.get_form_data()
        if not row_data:
            return

        # Auto-increment activity count if communication details changed
        if current_comm != old_comm and current_comm:
            new_count = self.auto_increment_activity_count()
            # Update the activity count in the row data (index 17 is activity_count)
            if len(row_data) > 17:
                row_data[17] = str(new_count)
            print(f"Activity count auto-incremented to {new_count} due to communication update")

        self.all_rows[self.selected_row_index] = row_data
        self.save_all_rows_to_csv()
        # also update company-wise file
        try:
            headers = self.get_crm_headers()
            self.save_company_wise_csv(dict(zip(headers, row_data)))
        except Exception:
            pass
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

        # Auto-increment activity count if communication details are present
        current_comm = self.crm_comm_text.get("1.0", tk.END).strip()
        if current_comm:
            new_count = self.auto_increment_activity_count()
            # Update the activity count in the row data (index 17 is activity_count)
            if len(row_data) > 17:
                row_data[17] = str(new_count)
            print(f"Activity count auto-incremented to {new_count} for new entry")

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
            # also save into company-wise CSV file
            try:
                headers = self.get_crm_headers()
                self.save_company_wise_csv(dict(zip(headers, row_data)))
            except Exception as e:
                print(f"Company-wise save failed: {e}")
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

    def _empty_import_row(self):
        """Create a CRM row with safe defaults for imported records."""
        headers = self.get_crm_headers()
        row = [""] * len(headers)
        defaults = {
            "activity_count": "0",
            "mobile_recording_count": "0",
            "company_data_sent": "No",
            "enquiry_received": "No",
        }
        for field, value in defaults.items():
            row[headers.index(field)] = value
        return row

    def _append_imported_records(self, mapped_records):
        """Append only new companies and persist them in CRM order."""
        headers = self.get_crm_headers()
        existing_keys = {
            company_file_import.company_key(row[0])
            for row in self.all_rows
            if row and company_file_import.company_key(row[0])
        }
        added_rows = []
        skipped_count = 0

        for mapped in mapped_records:
            company_name = company_file_import.stringify_value(
                mapped.get("company_name", "")
            )
            key = company_file_import.company_key(company_name)
            if not key or key in existing_keys:
                skipped_count += 1
                continue

            row = self._empty_import_row()
            for field, value in mapped.items():
                if field in headers:
                    row[headers.index(field)] = company_file_import.stringify_value(
                        value
                    )
            self.all_rows.append(row)
            added_rows.append(row)
            existing_keys.add(key)

        if not added_rows:
            return 0, skipped_count

        self.save_all_rows_to_csv()
        for row in added_rows:
            try:
                self.save_company_wise_csv(dict(zip(headers, row)))
            except Exception as exc:
                print(f"Company-wise import save failed: {exc}")

        if self.mqtt_manager and self.mqtt_manager.is_connected():
            for row in added_rows:
                try:
                    self.mqtt_manager.publish_customer_update(
                        dict(zip(headers, row)), "upsert"
                    )
                except Exception as exc:
                    print(f"MQTT import sync failed: {exc}")

        self.load_crm_data()
        self.clear_crm_entries()
        return len(added_rows), skipped_count

    def import_company_data(self):
        """Import Excel, CSV, or text-PDF company data by column name."""
        file_path = filedialog.askopenfilename(
            title="Import Company Data",
            filetypes=[
                (
                    "Supported files",
                    "*.xlsx *.xls *.csv *.pdf",
                ),
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("PDF", "*.pdf"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            records = company_file_import.read_import_records(file_path)
            mapped_records = company_file_import.map_records_to_crm(
                records, self.get_crm_headers()
            )
            if not mapped_records:
                raise ValueError("The selected file contains no data rows.")

            added_count, skipped_count = self._append_imported_records(
                mapped_records
            )
            if added_count:
                messagebox.showinfo(
                    "Import Complete",
                    f"Added {added_count} new company record(s).\n"
                    f"Skipped {skipped_count} empty or duplicate record(s).",
                )
            else:
                messagebox.showinfo(
                    "Import Complete",
                    "No new records were added. All company names were "
                    "already present or the rows had no company name.",
                )
        except PermissionError:
            messagebox.showerror(
                "File Lock Error",
                "Close customers_detailed.csv if it is open in Excel.",
            )
        except Exception as exc:
            messagebox.showerror(
                "Import Error",
                f"Could not import the selected file:\n{exc}",
            )

    def import_csv_data(self):
        """Backward-compatible alias for older callers."""
        self.import_company_data()

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
        self.selected_audio_paths = []
        self.form_frame.config(text=" Customer Details & Data Entry ")

        self.set_identity_fields_state("normal")

        self.crm_company.delete(0, tk.END)
        self.crm_gst.delete(0, tk.END)
        self.crm_contact_person.delete(0, tk.END)
        self.crm_designation.delete(0, tk.END)
        self.crm_website.delete(0, tk.END)
        self.crm_contact.delete(0, tk.END)
        self.crm_address.delete(0, tk.END)
        self._load_default_location_values()
        self.crm_location.delete(0, tk.END)
        self.crm_turnover.delete(0, tk.END)
        self.crm_owner_name.delete(0, tk.END)
        self.crm_staff_count.delete(0, tk.END)
        self.photo_listbox.delete(0, tk.END)
        self.audio_listbox.delete(0, tk.END)

        self.set_products_from_str("")
        self.set_company_valuation_from_str("")
        self.crm_valuable_percentage.delete(0, tk.END)
        self.crm_customer_rating.delete(0, tk.END)
        self.crm_activity_count.config(state="normal")
        self.crm_activity_count.delete(0, tk.END)
        self.crm_activity_count.config(state="readonly")
        self.crm_mobile_recording_count.config(state="normal")
        self.crm_mobile_recording_count.delete(0, tk.END)
        self.crm_mobile_recording_count.config(state="readonly")

        self.crm_call_hours.set("00")
        self.crm_call_mins.set("00")
        try:
            self.crm_conversion_date.delete(0, tk.END)
            self.crm_conversion_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        except Exception:
            pass
        self.crm_meeting_time.delete(0, tk.END)
        try:
            if hasattr(self, "crm_next_meeting"):
                self.crm_next_meeting.delete(0, tk.END)
        except Exception:
            pass
        self.crm_meeting_agenda.delete(0, tk.END)
        self.crm_data_sent.set("No")
        self.crm_data_type_name.config(state="normal")
        self.crm_data_type_name.delete(0, tk.END)
        self.crm_data_type_name.config(state="disabled")
        self.crm_enquiry.set("No")
        self.crm_enquiry_type.config(state="normal")
        self.crm_enquiry_type.delete(0, tk.END)
        self.crm_enquiry_type.config(state="disabled")
        self.crm_comm_text.delete("1.0", tk.END)
        self.crm_meeting_outcome_text.delete("1.0", tk.END)
        self.crm_notes_text.delete("1.0", tk.END)
        try:
            self.crm_comm_date.delete(0, tk.END)
        except Exception:
            pass
        self.crm_saturday_alarm.config(text="")

    def _convert_row_to_dict(self, row_data):
        """Convert CRM row data to dictionary for MQTT syncing."""
        headers = self.get_crm_headers()
        return dict(zip(headers, row_data))

    def on_gst_entered(self):
        """Auto-fill Company/Address/State/District/Owner from saved GST record."""
        if not hasattr(self, "crm_gst") or not self.crm_gst.winfo_exists():
            return
        gst = self.crm_gst.get().strip().upper()
        if not gst:
            return
        self.crm_gst.delete(0, tk.END)
        self.crm_gst.insert(0, gst)
        if len(gst) != 15:
            return
        try:
            self._reload_all_rows_silent()
        except Exception:
            pass
        headers = self.get_crm_headers()
        try:
            gi = headers.index("gst_number")
        except ValueError:
            return
        match = None
        for r in list(getattr(self, "all_rows", [])):
            if len(r) > gi and (r[gi] or "").strip().upper() == gst:
                match = r
                break
        if not match:
            try:
                from tkinter import messagebox as _mb
                _mb.showinfo("GST Lookup",
                    "GST '%s' not found in saved records.\n"
                    "Fill details manually - it will be saved." % gst)
            except Exception:
                pass
            return
        d = dict(zip(headers, match))
        company = (d.get("company_name") or "").strip()
        if not company:
            return
        try:
            cur_company = self.crm_company.get().strip()
        except Exception:
            cur_company = ""
        if cur_company and cur_company.lower() != company.lower():
            try:
                from tkinter import messagebox as _mb2
                ok = _mb2.askyesno("GST Found",
                    "Found saved record for:\n%s\n\nFill its details?" % company)
                if not ok:
                    return
            except Exception:
                pass
        def _set(entry, val):
            try:
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, val or "")
            except Exception:
                pass
        _set(self.crm_company, d.get("company_name", ""))
        _set(self.crm_address, d.get("address", ""))
        self._set_location_values(
            d.get("country") or ("India" if d.get("state") else ""),
            d.get("state", ""),
            d.get("district", ""),
        )
        _set(self.crm_location, d.get("location", ""))
        _set(self.crm_owner_name, d.get("owner_name", ""))
        _set(self.crm_contact_person, d.get("contact_person", ""))
        _set(self.crm_contact, d.get("contact_number", ""))
        _set(self.crm_website, d.get("website", ""))
        try:
            from tkinter import messagebox as _mb3
            _mb3.showinfo("GST Auto-Fill",
                "Filled from saved record:\n%s" % company)
        except Exception:
            pass

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
        except Exception as e:
            messagebox.showerror(
                "Load Error",
                f"Could not load customer CRM & lead data:\n{str(e)}",
            )
            print(f"Error loading CRM data: {e}")

    def populate_tree(self, rows_to_show):
        for item in self.crm_tree.get_children():
            self.crm_tree.delete(item)

        headers = self.get_crm_headers()
        indices = {name: index for index, name in enumerate(headers)}

        def value(row, field, default=""):
            index = indices.get(field, -1)
            return row[index] if 0 <= index < len(row) else default

        for r in rows_to_show:
            orig_idx = self.all_rows.index(r)
            state = value(r, "state")
            country = value(r, "country") or ("India" if state else "")
            activity_count = value(r, "activity_count", "0")
            if str(activity_count).strip() in ("", "No"):
                activity_count = "0"
            mobile_recording_count = value(r, "mobile_recording_count", "0")
            if str(mobile_recording_count).strip() in ("", "No"):
                mobile_recording_count = "0"
            self.crm_tree.insert(
                "",
                tk.END,
                values=(
                    orig_idx + 1,
                    value(r, "company_name"),
                    value(r, "gst_number"),
                    value(r, "contact_person"),
                    value(r, "designation"),
                    value(r, "contact_number"),
                    country,
                    state,
                    value(r, "district"),
                    value(r, "location"),
                    value(r, "owner_name"),
                    value(r, "products_selected"),
                    value(r, "valuable_customer_percentage", "0"),
                    value(r, "customer_rating", "0"),
                    activity_count,
                    mobile_recording_count,
                    value(r, "company_data_sent", "No"),
                    value(r, "enquiry_received", "No"),
                    value(r, "call_conversion_time"),
                    value(r, "call_conversion_date"),
                    value(r, "meeting_schedule_time"),
                    value(r, "next_meeting_datetime"),
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
            if any(query in str(cell).casefold() for cell in r)
        ]
        self.populate_tree(filtered)

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.populate_tree(self.all_rows)