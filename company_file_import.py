"""File readers and header mapping for CRM company imports.

Supported inputs: CSV, Excel .xlsx/.xls, and text-based PDF files.
The importer returns dictionaries first so the CRM layer can arrange values
by column name instead of relying on file column order.
"""

import base64
import io
import os
import re
import zlib


ALIASES = {
    "company": "company_name", "companyname": "company_name",
    "company_name": "company_name", "gst": "gst_number",
    "gstno": "gst_number", "gst_number": "gst_number",
    "contact": "contact_person", "contactname": "contact_person",
    "contact_person": "contact_person", "phone": "contact_number",
    "mobile": "contact_number", "contactno": "contact_number",
    "contact_number": "contact_number", "country_name": "country",
    "country": "country", "state_name": "state", "state": "state",
    "district_name": "district", "district": "district",
    "location_name": "location", "location": "location",
    "owner": "owner_name", "ownername": "owner_name",
    "owner_name": "owner_name", "staff": "number_of_staff",
    "number_of_staff": "number_of_staff", "products": "products_selected",
    "product": "products_selected", "products_selected": "products_selected",
    "valuation": "company_valuation", "company_valuation": "company_valuation",
    "valuable_customer_percentage": "valuable_customer_percentage",
    "customer_rating": "customer_rating", "activity_count": "activity_count",
    "mobile_recording_count": "mobile_recording_count", "note": "note",
    "notes": "note", "call_conversion_time": "call_conversion_time",
    "call_conversion_date": "call_conversion_date",
    "company_data_sent": "company_data_sent", "data_type_name": "data_type_name",
    "enquiry_received": "enquiry_received", "enquiry_type": "enquiry_type",
    "communication_details": "communication_details",
    "communication_date": "communication_date",
    "meeting_schedule_time": "meeting_schedule_time",
    "next_meeting_datetime": "next_meeting_datetime",
    "meeting_agenda": "meeting_agenda",
    "meeting_completed_details": "meeting_completed_details",
    "photo_files": "photo_files", "audio_files": "audio_files",
}


def normalize_header(value):
    """Return a stable snake_case header name."""
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold())
    text = text.strip("_")
    return ALIASES.get(text, text)


def stringify_value(value):
    """Convert spreadsheet/PDF values to clean CRM text values."""
    if value is None:
        return ""
    try:
        import pandas as pd
        if pd.isna(value):
            return ""
    except (ImportError, TypeError, ValueError):
        pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value).strip()


def company_key(value):
    """Return a duplicate-safe company name key."""
    return re.sub(r"\s+", " ", stringify_value(value)).strip().casefold()


def _decode_pdf_token(token):
    """Decode a simple PDF literal or hexadecimal string token."""
    if token.startswith(b"<"):
        digits = re.sub(rb"\s+", b"", token[1:-1])
        if len(digits) % 2:
            digits += b"0"
        try:
            return bytes.fromhex(digits.decode("ascii")).decode(
                "utf-8", errors="ignore"
            )
        except (ValueError, UnicodeDecodeError):
            return ""
    body = token[1:-1]
    replacements = {
        rb"\\n": b"\n", rb"\\r": b"\r", rb"\\t": b"\t",
        rb"\(": b"(", rb"\)": b")", rb"\\": b"\\",
    }
    for escaped, replacement in replacements.items():
        body = body.replace(escaped, replacement)
    return body.decode("utf-8", errors="ignore")


def _fallback_pdf_text(file_path):
    """Extract simple text operators from text-based PDFs."""
    with open(file_path, "rb") as file:
        data = file.read()
    output = []
    stream_pattern = re.compile(rb"stream\s*(.*?)\s*endstream", re.S)
    token_pattern = re.compile(rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]+>")
    for match in stream_pattern.finditer(data):
        stream = match.group(1)
        header = data[max(0, match.start() - 300):match.start()]
        if b"/ASCII85Decode" in header:
            try:
                stream = base64.a85decode(stream, adobe=True)
            except (ValueError, TypeError):
                continue
        if b"/FlateDecode" in header:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                continue
        for token in token_pattern.findall(stream):
            decoded = _decode_pdf_token(token).strip()
            if decoded:
                output.append(decoded)
    return "\n".join(output)


def _pdf_text(file_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return _fallback_pdf_text(file_path)
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _pdf_key_value_records(text):
    records = []
    current = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        match = re.match(r"^([^:]{2,60})\s*[:=]\s*(.*)$", line)
        if not match:
            continue
        key = normalize_header(match.group(1))
        value = stringify_value(match.group(2))
        if key == "company_name" and current.get("company_name"):
            records.append(current)
            current = {}
        current[key] = value
    if current:
        records.append(current)
    return records


def _pdf_table_records(text):
    try:
        import pandas as pd
    except ImportError:
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    for separator in ("\t", ",", r"\s{2,}"):
        try:
            frame = pd.read_csv(
                io.StringIO("\n".join(lines)),
                sep=separator,
                engine="python",
            )
        except Exception:
            continue
        if frame.empty:
            continue
        records = frame.to_dict(orient="records")
        if any(
            normalize_header(column) == "company_name"
            for column in frame.columns
        ):
            return records
    return []


def read_import_records(file_path):
    """Read a supported file and return a list of column dictionaries."""
    extension = os.path.splitext(file_path)[1].casefold()
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "Excel and CSV import requires pandas."
        ) from exc

    if extension == ".csv":
        try:
            frame = pd.read_csv(file_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            frame = pd.read_csv(file_path, encoding="latin1")
        return frame.to_dict(orient="records")

    if extension in (".xlsx", ".xls"):
        try:
            frame = pd.read_excel(file_path, sheet_name=0)
        except ImportError as exc:
            raise RuntimeError(
                "Legacy .xls import requires the xlrd package."
            ) from exc
        return frame.to_dict(orient="records")

    if extension == ".pdf":
        text = _pdf_text(file_path)
        records = _pdf_key_value_records(text)
        if not records:
            records = _pdf_table_records(text)
        if not records:
            raise ValueError(
                "No readable company rows were found in the PDF. "
                "The PDF must contain text, not only a scanned image."
            )
        return records

    raise ValueError("Supported files are .xlsx, .xls, .csv, and .pdf.")


def map_records_to_crm(records, expected_headers):
    """Arrange source columns into the CRM's fixed header order by name."""
    expected_by_name = {
        normalize_header(header): header for header in expected_headers
    }
    mapped_records = []
    for record in records:
        mapped = {header: "" for header in expected_headers}
        for source_column, value in record.items():
            canonical = normalize_header(source_column)
            target = expected_by_name.get(canonical, canonical)
            if target in mapped:
                mapped[target] = stringify_value(value)
        mapped_records.append(mapped)
    return mapped_records
