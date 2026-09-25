"""Quick checks for the category-wise arrangement helper."""

import csv

import category_order


def check_list_rows():
    rows = [
        ["SKU", "Category", "Item Name"],
        ["1", "Wire", "Wire 1.5 sqmm"],
        ["2", "MCB", "MCB 16A"],
        ["3", "VFD", "VFD 7.5kW"],
        ["4", "Contactor", "Contactor 25A"],
        ["5", "Unknown Thing", "Mystery item"],
        ["6", "Contactor", "Contactor 32A"],
    ]
    arranged = category_order.sort_rows_by_category(rows)
    categories = [row[1] for row in arranged[1:]]
    print("list rows ->", categories)
    assert arranged[0] == rows[0], "header must stay first"
    # MCB (0) < Contactor (4) < VFD (6) < Wire (28) < unknown
    assert categories == ["MCB", "Contactor", "Contactor", "VFD", "Wire", "Unknown Thing"], categories


def check_dict_rows():
    with open("csv_data/Product Price Calculator/price_list.csv", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    arranged = category_order.sort_rows_by_category(rows)
    ranks = [category_order.category_rank(row.get("Category", "")) for row in arranged]
    assert ranks == sorted(ranks), "dict rows must be category-ordered"
    print("dict rows -> first categories:", [row.get("Category") for row in arranged[:8]])
    print("dict rows total:", len(arranged), "of", len(rows))


if __name__ == "__main__":
    check_list_rows()
    check_dict_rows()
    print("category_order tests passed")