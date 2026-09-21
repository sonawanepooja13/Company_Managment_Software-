"""Canonical category ordering for panel price lists.

Whenever an Excel/CSV price list is uploaded, the rows are arranged
category-wise using the order defined in ``CATEGORY_ORDER`` below.
Categories that are not listed are placed after the known ones,
sorted alphabetically, so nothing is ever lost.
"""

# Preferred display / arrangement order for panel material categories.
CATEGORY_ORDER = [
    "MCB",
    "MCCB",
    "RCCB",
    "MPCB",
    "Contactor",
    "OLR",
    "VFD",
    "Controller",
    "CT Coil",
    "Power Supply",
    "Switch",
    "Terminal",
    "Din Rail",
    "Cable Tray",
    "Metal Box",
    "Fan",
    "Filter / Air Filter",
    "Tube",
    "Wire",
    "Lugs",
    "Spiral",
    "Cable Tie",
    "Gasket",
    "Screw",
    "Label / Panel Stickers / Sticker",
    "Lock",
    "Key",
    "Ferrule",
    "Sensor",
    "Relay",
    "Fuse",
    "Add On Block",
    "PG Gland",
    "RSPP",
    "Timer",
    "Z Clamp",
    "Busbar",
    "Modbus Pin",
    "Insulator",
    "Sleeve",
    "Socket",
    "Nuts",
    "Washer",
    "Board",
    "ATS",
    "CT",
    "Transformer",
    "Soft Starter",
    "STP Metal Box",
    "Fire",
    "Packaging",
    "DVM",
    "Stop Button / Push Button",
    "Choke / VFD Choke",
    "SFU",
    "Fuses",
    "MFM",
    "Panel Box",
]

# Fast lookup: normalised category name -> position in the preferred order.
_CATEGORY_RANK = {
    name.strip().lower(): index for index, name in enumerate(CATEGORY_ORDER)
}


def category_rank(category):
    """Return the sort rank for a category name.

    Known categories get their configured position. Unknown categories are
    ranked after every known category so they still appear in the list.
    """
    normalised = str(category or "").strip().lower()
    return _CATEGORY_RANK.get(normalised, len(CATEGORY_ORDER))


def sort_rows_by_category(rows, category_column="Category"):
    """Arrange tabular rows category-wise, keeping the header row first.

    ``rows`` may be a list of lists (CSV/Excel rows) or a list of dicts
    (``csv.DictReader`` output). The header row is always kept at the top.
    Rows are ordered by the preferred category order, then by the original
    row order so items inside a category stay stable.
    """
    if not rows:
        return rows

    first = rows[0]

    # Dict rows (e.g. csv.DictReader) -------------------------------------
    if isinstance(first, dict):
        header = list(first.keys())
        data_rows = [row for row in rows if any(str(value).strip() for value in row.values())]
        data_rows.sort(
            key=lambda row: (
                category_rank(row.get(category_column, "")),
                str(row.get(category_column, "")).strip().lower(),
            )
        )
        return data_rows

    # List/tuple rows (CSV reader or Excel iter_rows) ---------------------
    header = list(first)
    category_index = None
    for index, column in enumerate(header):
        if str(column).strip().lower() == category_column.strip().lower():
            category_index = index
            break

    if category_index is None:
        return rows

    data_rows = [
        row for row in rows[1:] if any(str(value).strip() for value in row)
    ]
    data_rows.sort(
        key=lambda row: (
            category_rank(row[category_index] if category_index < len(row) else ""),
            str(row[category_index] if category_index < len(row) else "").strip().lower(),
        )
    )
    return [header] + data_rows
