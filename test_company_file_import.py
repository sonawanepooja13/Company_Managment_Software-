"""Tests for CRM file import parsing and column-name mapping."""

import csv
import os
import tempfile
import unittest

from company_file_import import map_records_to_crm, read_import_records
from tabs.crm_tab import CrmTab


EXPECTED_HEADERS = [
    "company_name",
    "gst_number",
    "contact_person",
    "contact_number",
    "state",
    "district",
    "country",
]


class CompanyFileImportTests(unittest.TestCase):
    def test_csv_headers_are_mapped_by_name_not_position(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "companies.csv")
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["District", "Company Name", "GST Number", "Unknown Column"]
                )
                writer.writerow(["Pune", "Acme Pumps", "27ABCDE1234F1Z5", "ignore"])

            records = read_import_records(path)
            mapped = map_records_to_crm(records, EXPECTED_HEADERS)

        self.assertEqual(mapped[0]["company_name"], "Acme Pumps")
        self.assertEqual(mapped[0]["gst_number"], "27ABCDE1234F1Z5")
        self.assertEqual(mapped[0]["district"], "Pune")
        self.assertNotIn("Unknown Column", mapped[0])

    def test_excel_headers_are_mapped_by_name(self):
        pandas = __import__("pandas")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "companies.xlsx")
            pandas.DataFrame(
                [
                    {
                        "State": "Maharashtra",
                        "Company": "Excel Company",
                        "Contact Number": "9876543210",
                    }
                ]
            ).to_excel(path, index=False)
            records = read_import_records(path)
            mapped = map_records_to_crm(records, EXPECTED_HEADERS)

        self.assertEqual(mapped[0]["company_name"], "Excel Company")
        self.assertEqual(mapped[0]["state"], "Maharashtra")
        self.assertEqual(mapped[0]["contact_number"], "9876543210")

    def test_text_pdf_key_value_data_is_read(self):
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "companies.pdf")
            pdf = canvas.Canvas(path)
            pdf.drawString(72, 760, "Company Name: PDF Company")
            pdf.drawString(72, 735, "State: Karnataka")
            pdf.drawString(72, 710, "District: Bengaluru Urban")
            pdf.save()

            records = read_import_records(path)
            mapped = map_records_to_crm(records, EXPECTED_HEADERS)

        self.assertEqual(mapped[0]["company_name"], "PDF Company")
        self.assertEqual(mapped[0]["state"], "Karnataka")
        self.assertEqual(mapped[0]["district"], "Bengaluru Urban")
    def test_duplicate_company_names_are_skipped(self):
        view = CrmTab.__new__(CrmTab)
        view.all_rows = [view._empty_import_row()]
        view.all_rows[0][0] = "Acme Pumps"
        view.mqtt_manager = None
        view.save_all_rows_to_csv = lambda: None
        view.save_company_wise_csv = lambda row: None
        view.load_crm_data = lambda: None
        view.clear_crm_entries = lambda: None

        records = [
            {"company_name": "Acme Pumps", "state": "Maharashtra"},
            {"company_name": "New Company", "state": "Karnataka"},
            {"company_name": " new   company ", "state": "Karnataka"},
        ]
        added, skipped = view._append_imported_records(records)

        self.assertEqual(added, 1)
        self.assertEqual(skipped, 2)
        self.assertEqual(len(view.all_rows), 2)
        self.assertEqual(view.all_rows[1][0], "New Company")


if __name__ == "__main__":
    unittest.main()
