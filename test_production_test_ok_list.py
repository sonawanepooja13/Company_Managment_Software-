import csv
import os

from production_window import (
    extract_tested_ok_product_ids,
    get_dispatch_log_path,
    get_products_list_path,
)


def test_csv_data_production_paths_are_used(tmp_path):
    dispatch_path = get_dispatch_log_path(str(tmp_path))
    products_path = get_products_list_path(str(tmp_path))

    assert dispatch_path == os.path.join(str(tmp_path), "tested_ok_dispatch_log.csv")
    assert products_path == os.path.join(str(tmp_path), "products_list.csv")


def test_extract_tested_ok_product_ids_filters_yes_rows(tmp_path):
    csv_path = tmp_path / "product_testing_log.csv"
    rows = [
        {"Product_ID": "P001", "Tested_OK": "Yes"},
        {"Product_ID": "P002", "Tested_OK": "No - Fault"},
        {"Product_ID": "P003", "Tested_OK": "yes"},
        {"Product_ID": "P004", "Tested_OK": ""},
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Product_ID", "Tested_OK"])
        writer.writeheader()
        writer.writerows(rows)

    ids = extract_tested_ok_product_ids(csv_path)

    assert ids == ["P001", "P003"]
