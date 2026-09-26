"""Tests for the CRM GST data that fills the quotation GSTIN / PAN field."""

import csv
import os
import tempfile
import unittest

import quotation_manager


CRM_HEADERS = [
    "company_name",
    "gst_number",
    "contact_person",
    "contact_number",
    "address",
]


def write_crm_csv(path, rows, headers=None):
    """Write a minimal customers_detailed.csv for the tests to read back."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers or CRM_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class CustomerGstFillTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.original_path = quotation_manager.CUSTOMERS_DETAILED_CSV
        self.path = os.path.join(self.directory.name, "customers_detailed.csv")
        quotation_manager.CUSTOMERS_DETAILED_CSV = self.path
        self.addCleanup(self._restore_path)

    def _restore_path(self):
        quotation_manager.CUSTOMERS_DETAILED_CSV = self.original_path

    def test_crm_gst_number_fills_gstin_pan(self):
        write_crm_csv(
            self.path,
            [
                {
                    "company_name": "Acme Pumps",
                    "gst_number": "27ABCDE1234F1Z5",
                    "contact_person": "Asha",
                    "contact_number": "9876543210",
                    "address": "Pune",
                }
            ],
        )

        details = quotation_manager.load_customer_details("Acme Pumps")

        self.assertEqual(details["customer_gstin"], "27ABCDE1234F1Z5")
        self.assertEqual(
            quotation_manager.load_customer_gstin("Acme Pumps"), "27ABCDE1234F1Z5"
        )

    def test_company_name_match_ignores_case_and_extra_spaces(self):
        write_crm_csv(
            self.path,
            [{"company_name": "Acme  Pumps", "gst_number": "27ABCDE1234F1Z5"}],
        )

        self.assertEqual(
            quotation_manager.load_customer_gstin("  acme pumps "), "27ABCDE1234F1Z5"
        )

    def test_pan_column_is_used_when_no_gst_number_exists(self):
        write_crm_csv(
            self.path,
            [{"company_name": "Beta Systems", "pan": "ABCDE1234F"}],
            headers=["company_name", "pan"],
        )

        self.assertEqual(quotation_manager.load_customer_gstin("Beta Systems"), "ABCDE1234F")

    def test_first_non_empty_gst_wins_across_duplicate_company_rows(self):
        write_crm_csv(
            self.path,
            [
                {"company_name": "Acme Pumps", "gst_number": ""},
                {"company_name": "Acme Pumps", "gst_number": "27ABCDE1234F1Z5"},
            ],
        )

        self.assertEqual(
            quotation_manager.load_customer_gstin("Acme Pumps"), "27ABCDE1234F1Z5"
        )

    def test_unknown_company_has_no_gst(self):
        write_crm_csv(
            self.path,
            [{"company_name": "Acme Pumps", "gst_number": "27ABCDE1234F1Z5"}],
        )

        self.assertEqual(quotation_manager.load_customer_gstin("Nobody Ltd"), "")
        self.assertEqual(quotation_manager.load_customer_gstin(""), "")


if __name__ == "__main__":
    unittest.main()
