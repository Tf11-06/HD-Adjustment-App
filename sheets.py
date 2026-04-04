import os
import sys
import gspread
from pdf_parser import HEADER_COLS, ITEM_COLS


def _get_app_dir() -> str:
    """Return the directory containing the running app (exe dir when frozen, script dir otherwise)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def _build_header_rows(num_items: int) -> list[list]:
    """Build the 2-row header: [section-label row, column-name row].

    Row 1: blank for invoice columns; "LINE ITEM N" in first cell of each item group.
    Row 2: HEADER_COLS + ITEM_COLS repeated num_items times.
    """
    row1 = [""] * len(HEADER_COLS)
    row2 = list(HEADER_COLS)
    for i in range(1, num_items + 1):
        row1.append(f"LINE ITEM {i}")
        row1.extend([""] * (len(ITEM_COLS) - 1))
        row2.extend(ITEM_COLS)
    return [row1, row2]


def _get_max_items(all_rows: list) -> int:
    """Count how many LINE ITEM column groups exist in the header label row."""
    if not all_rows:
        return 0
    return sum(1 for cell in all_rows[0] if str(cell).startswith("LINE ITEM"))


def connect_sheet(config: dict) -> gspread.Worksheet:
    """Connect to the Google Sheet worksheet. Raises on bad credentials or sheet ID."""
    creds_path = config["credentials_file"]
    if not os.path.isabs(creds_path):
        creds_path = os.path.join(_get_app_dir(), creds_path)

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file not found: {creds_path}. Check the path in Settings."
        )

    try:
        client = gspread.service_account(filename=creds_path, scopes=SCOPES)
    except Exception as e:
        raise ConnectionError(f"Could not authenticate with Google: {e}") from e

    try:
        spreadsheet = client.open_by_key(config["sheet_id"])
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(
            "Could not find the Google Sheet. Verify the Sheet ID in Settings."
        )
    except Exception as e:
        raise ConnectionError(f"Could not connect to Google Sheets: {e}") from e

    try:
        worksheet = spreadsheet.worksheet(config["worksheet_name"])
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=config["worksheet_name"], rows=1000, cols=200
        )

    return worksheet


def get_all_rows(worksheet: gspread.Worksheet) -> list:
    """Fetch and return all rows from the worksheet."""
    return worksheet.get_all_values()


def ensure_header(worksheet: gspread.Worksheet, all_rows=None) -> None:
    """Write the 2-row header if the sheet is empty."""
    existing = all_rows if all_rows is not None else worksheet.get_all_values()
    if not existing:
        worksheet.update(_build_header_rows(0), "A1")


def ensure_capacity(worksheet: gspread.Worksheet, num_items: int, all_rows: list) -> list:
    """Expand the header to support num_items line item groups if needed.

    Returns updated all_rows with the new header in positions [0] and [1].
    """
    current_max = _get_max_items(all_rows)
    if num_items <= current_max:
        return all_rows
    new_header = _build_header_rows(num_items)
    worksheet.update(new_header, "A1")
    if len(all_rows) >= 2:
        return new_header + list(all_rows[2:])
    return new_header


def find_duplicate(worksheet: gspread.Worksheet, invoice_number: str, all_rows=None) -> bool:
    """Return True if any data row has this Invoice # value."""
    rows = all_rows if all_rows is not None else worksheet.get_all_values()
    invoice_col = HEADER_COLS.index("Invoice #")
    for row in rows[2:]:  # skip 2 header rows
        if len(row) > invoice_col and row[invoice_col] == invoice_number:
            return True
    return False


def append_invoice(worksheet: gspread.Worksheet, invoice_data: dict, all_rows: list) -> list:
    """Append one flat row for the invoice. Expands header if needed.

    Args:
        invoice_data: {"header": dict, "items": list[dict]}
        all_rows: current cached sheet rows.

    Returns:
        Updated all_rows with the new invoice row appended.
    """
    header = invoice_data.get("header", {})
    items = invoice_data.get("items", [])

    all_rows = ensure_capacity(worksheet, len(items), all_rows)
    current_max = _get_max_items(all_rows)

    row = [header.get(col, "") for col in HEADER_COLS]
    for item in items:
        row.extend([item.get(col, "") for col in ITEM_COLS])
    row.extend([""] * ((current_max - len(items)) * len(ITEM_COLS)))

    worksheet.append_rows([row], value_input_option='RAW')
    all_rows.append(row)
    return all_rows
