import os
import gspread
from pdf_parser import COLUMNS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def connect_sheet(config: dict) -> gspread.Worksheet:
    """Connect to the Google Sheet worksheet. Raises on bad credentials or sheet ID."""
    creds_path = config["credentials_file"]
    if not os.path.isabs(creds_path):
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), creds_path)

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
            title=config["worksheet_name"], rows=1000, cols=len(COLUMNS)
        )

    return worksheet


def get_all_rows(worksheet: gspread.Worksheet) -> list:
    """Fetch and return all rows from the worksheet."""
    return worksheet.get_all_values()


def ensure_header(worksheet: gspread.Worksheet, all_rows=None) -> None:
    """Write header row if the sheet is empty."""
    existing = all_rows if all_rows is not None else worksheet.get_all_values()
    if not existing:
        worksheet.append_row(COLUMNS)


def find_duplicate(worksheet: gspread.Worksheet, invoice_number: str, all_rows=None) -> bool:
    """Return True if any row has this Invoice # (col index 2, 0-based)."""
    rows = all_rows if all_rows is not None else worksheet.get_all_values()
    invoice_col = COLUMNS.index("Invoice #")
    for row in rows[1:]:  # skip header
        if len(row) > invoice_col and row[invoice_col] == invoice_number:
            return True
    return False


def append_rows(worksheet: gspread.Worksheet, rows: list[dict]) -> int:
    """Append rows to the worksheet in column order. Returns number of rows added."""
    if not rows:
        return 0
    all_values = [[row.get(col, "") for col in COLUMNS] for row in rows]
    worksheet.append_rows(all_values, value_input_option='RAW')
    return len(rows)
