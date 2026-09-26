"""Regression checks for CRM location dropdown data and CSV migration."""

import csv
import os
import tempfile
import unittest

import locations
from tabs.crm_tab import CrmTab


class LocationDropdownTests(unittest.TestCase):
    def test_country_choices_are_available(self):
        self.assertGreaterEqual(len(locations.COUNTRY_NAMES), 249)
        self.assertIn("India", locations.COUNTRY_NAMES)
        self.assertIn("United States of America", locations.COUNTRY_NAMES)
        self.assertEqual(len(locations.COUNTRY_NAMES), len(set(locations.COUNTRY_NAMES)))

    def test_india_hierarchy_is_populated(self):
        states = locations.states_for_country("India")
        self.assertEqual(len(states), 36)
        self.assertIn("Maharashtra", states)
        self.assertIn("Pune", locations.districts_for_country("India", "Maharashtra"))
        self.assertEqual(
            locations.canonical_name("maharashtra", states), "Maharashtra"
        )

    def test_country_is_appended_to_crm_csv_schema(self):
        headers = CrmTab.get_crm_headers(None)
        self.assertEqual(headers[-1], "country")

    def test_existing_csv_rows_keep_location_values(self):
        headers = CrmTab.get_crm_headers(None)
        old_headers = headers[:-1]
        old_row = [f"value-{index}" for index in range(len(old_headers))]
        old_row[headers.index("state")] = "Maharashtra"
        old_row[headers.index("district")] = "Pune"

        with tempfile.TemporaryDirectory() as directory:
            csv_path = os.path.join(directory, "customers_detailed.csv")
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(old_headers)
                writer.writerow(old_row)

            instance = CrmTab.__new__(CrmTab)
            instance.crm_csv_path = csv_path
            instance.migrate_and_align_csv()

            with open(csv_path, newline="", encoding="utf-8-sig") as file:
                migrated = list(csv.DictReader(file))

        self.assertEqual(migrated[0]["state"], "Maharashtra")
        self.assertEqual(migrated[0]["district"], "Pune")
        self.assertEqual(migrated[0]["country"], "")

    def test_short_legacy_schema_is_mapped_by_header_name(self):
        from config import CUSTOMERS_DETAILED_HEADERS

        legacy_row = [
            "Acme Pumps",
            "https://acme.example",
            "9876543210",
            "Address",
            "Location",
            "Notes",
            "10:00",
            "Yes",
            "No",
            "Communication",
            "Meeting",
            "Agenda",
            "Completed",
        ]
        with tempfile.TemporaryDirectory() as directory:
            csv_path = os.path.join(directory, "customers_detailed.csv")
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(CUSTOMERS_DETAILED_HEADERS[:-1])
                writer.writerow(legacy_row)

            instance = CrmTab.__new__(CrmTab)
            instance.crm_csv_path = csv_path
            instance.migrate_and_align_csv()

            with open(csv_path, newline="", encoding="utf-8-sig") as file:
                migrated = list(csv.DictReader(file))[0]

        self.assertEqual(migrated["company_name"], "Acme Pumps")
        self.assertEqual(migrated["website"], "https://acme.example")
        self.assertEqual(migrated["contact_number"], "9876543210")
        self.assertEqual(migrated["state"], "")
        self.assertEqual(migrated["country"], "")
        self.assertEqual(migrated["activity_count"], "0")
    def test_location_preferences_round_trip(self):
        import tabs.crm_tab as crm_module

        crm_engine = crm_module.crm_engine
        original_db_file = crm_engine.DB_FILE
        try:
            with tempfile.TemporaryDirectory() as directory:
                crm_engine.DB_FILE = os.path.join(directory, "crm_database.db")
                crm_engine.init_crm_db()
                crm_engine.save_location_preferences(
                    "India", "Maharashtra", "Pune"
                )
                self.assertEqual(
                    crm_engine.get_location_preferences(),
                    {
                        "country": "India",
                        "state": "Maharashtra",
                        "district": "Pune",
                    },
                )
        finally:
            crm_engine.DB_FILE = original_db_file

    def test_typed_location_values_filter_and_commit(self):
        import tkinter as tk
        import config
        import tabs.crm_tab as crm_module

        original_script_dir = config.SCRIPT_DIR
        original_csv_dir = config.CSV_DIR
        original_crm_path = config.CUSTOMERS_DETAILED_CSV
        original_has_mqtt = crm_module.HAS_MQTT
        original_db_file = crm_module.crm_engine.DB_FILE
        root = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                config.SCRIPT_DIR = directory
                config.CSV_DIR = os.path.join(directory, "csv_data")
                os.makedirs(config.CSV_DIR, exist_ok=True)
                config.CUSTOMERS_DETAILED_CSV = os.path.join(
                    config.CSV_DIR, "customers_detailed.csv"
                )
                crm_module.crm_engine.DB_FILE = os.path.join(
                    directory, "crm_database.db"
                )
                crm_module.HAS_MQTT = False
                root = tk.Tk()
                root.withdraw()
                view = CrmTab(root)
                view._set_location_values("India")

                view.crm_country.set("united")
                view._filter_location_dropdown("country")
                root.update()
                self.assertIn(
                    "United States of America",
                    tuple(view.crm_country.cget("values")),
                )
                self.assertIsNotNone(
                    view._location_suggestion_popups["country"]
                )
                self.assertIn(
                    "United States of America",
                    tuple(
                        view._location_suggestion_listboxes["country"].get(
                            0, tk.END
                        )
                    ),
                )

                view.crm_country.set("states america")
                view._filter_location_dropdown("country")
                root.update()
                self.assertIn(
                    "United States of America",
                    tuple(view.crm_country.cget("values")),
                )

                view.crm_country.set("ind")
                view._filter_location_dropdown("country")
                root.update()
                self.assertIn("India", tuple(view.crm_country.cget("values")))
                view.crm_country.set("india")
                view._commit_location_text("country")
                self.assertEqual(view.crm_country.get(), "India")

                view.crm_state.set("maha")
                view._filter_location_dropdown("state")
                root.update()
                self.assertIn(
                    "Maharashtra", tuple(view.crm_state.cget("values"))
                )
                view._commit_location_text("state")
                self.assertEqual(view.crm_state.get(), "Maharashtra")

                view.crm_district.set("pun")
                view._filter_location_dropdown("district")
                root.update()
                self.assertIn("Pune", tuple(view.crm_district.cget("values")))
                view._commit_location_text("district")
                self.assertEqual(view.crm_district.get(), "Pune")
                self.assertEqual(
                    crm_module.crm_engine.get_location_preferences(),
                    {
                        "country": "India",
                        "state": "Maharashtra",
                        "district": "Pune",
                    },
                )
                view.clear_crm_entries()
                self.assertEqual(view.crm_country.get(), "India")
                self.assertEqual(view.crm_state.get(), "Maharashtra")
                self.assertEqual(view.crm_district.get(), "Pune")
        finally:
            if root is not None:
                root.destroy()
            crm_module.HAS_MQTT = original_has_mqtt
            crm_module.crm_engine.DB_FILE = original_db_file
            config.SCRIPT_DIR = original_script_dir
            config.CSV_DIR = original_csv_dir
            config.CUSTOMERS_DETAILED_CSV = original_crm_path


if __name__ == "__main__":
    unittest.main()
