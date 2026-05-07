"""
Google Sheets writer for HD Adjustment invoices.
Adapts the existing gspread logic to the Writer ABC.
"""

import os
import re
import gspread

import config
from pdf_parser import HEADER_COLS, LI_COLS
from .base import Writer

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_N_INV = len(HEADER_COLS)  # 12
_N_LI  = len(LI_COLS)      # 9


def _build_header_rows(max_li: int) -> list[list]:
    """Build the 2-row header: [group-label row, field-name row]."""
    row1 = ["Invoice Details"] + [""] * (_N_INV - 1)
    row2 = list(HEADER_COLS)

    # LI1 always present (slot 0 = credit, slots 1..n = debit)
    for li in range(max_li + 1):
        label = "LINE ITEM 1 · Credit" if li == 0 else f"LINE ITEM {li + 1} · Debit"
        row1.append(label)
        row1.extend([""] * (_N_LI - 1))
        row2.extend(LI_COLS)

    return [row1, row2]


def _count_li_groups(all_rows: list) -> int:
    """Count LI groups from the group-label row (row index 0)."""
    if not all_rows:
        return 0
    return sum(1 for cell in all_rows[0] if re.match(r'^LINE ITEM \d+', str(cell)))


class SheetsWriter(Writer):
    """Appends invoices to a Google Sheet worksheet."""

    def __init__(self, config: dict):
        self._config = config
        self._worksheet: gspread.Worksheet | None = None
        self._all_rows: list | None = None

    # ── connection ────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Authenticate and open the worksheet. Raises on failure."""
        creds_path = config.resolve_credentials_path(self._config.get("credentials_file", ""))

        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Credentials file not found: {creds_path}. Check the path in Settings."
            )

        try:
            client = gspread.service_account(filename=creds_path, scopes=SCOPES)
        except Exception as e:
            raise ConnectionError(f"Could not authenticate with Google: {e}") from e

        try:
            spreadsheet = client.open_by_key(self._config["sheet_id"])
        except gspread.exceptions.SpreadsheetNotFound:
            raise ValueError("Could not find the Google Sheet. Verify the Sheet ID in Settings.")
        except Exception as e:
            raise ConnectionError(f"Could not connect to Google Sheets: {e}") from e

        name = self._config.get("worksheet_name", "Adjustments")
        try:
            self._worksheet = spreadsheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            self._worksheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=300)

        self._all_rows = self._worksheet.get_all_values()

    def _require_connected(self):
        if self._worksheet is None:
            raise RuntimeError("SheetsWriter.connect() must be called before use.")

    # ── Writer interface ─────────────────────────────────────────────────

    def is_initialized(self) -> bool:
        self._require_connected()
        if not self._all_rows or len(self._all_rows) < 2:
            return False
        return bool(self._all_rows[0]) and str(self._all_rows[1][0]) == HEADER_COLS[0]

    def initialize_headers(self, max_line_items: int = 0) -> None:
        self._require_connected()
        header = _build_header_rows(max_line_items)
        self._worksheet.update(header, "A1")
        self._all_rows = header

    def find_duplicate(self, invoice_num: str) -> bool:
        self._require_connected()
        if not self._all_rows:
            return False
        for row in self._all_rows[2:]:
            if row and row[0] == invoice_num:
                return True
        return False

    def expand_columns_if_needed(self, num_debit_items: int) -> None:
        self._require_connected()
        current = _count_li_groups(self._all_rows)
        needed = num_debit_items + 1  # +1 for LI1 (credit slot always present)
        if needed <= current:
            return
        new_header = _build_header_rows(num_debit_items)
        self._worksheet.update(new_header, "A1")
        data_rows = self._all_rows[2:] if len(self._all_rows) >= 2 else []
        self._all_rows = new_header + data_rows

    def append_invoice(self, invoice: dict) -> None:
        self._require_connected()

        if not self.is_initialized():
            self.initialize_headers(len(invoice.get('debit_items', [])))
        else:
            self.expand_columns_if_needed(len(invoice.get('debit_items', [])))

        current_li = _count_li_groups(self._all_rows)

        # Build flat row
        row = self.invoice_header_row(invoice)

        # LI1 — credit summary
        row.extend(self.li1_row(invoice.get('credit_line')))

        # LI2+ — debit items
        for item in invoice.get('debit_items', []):
            row.extend(self.debit_row(item))

        # Pad to full width
        total_li = current_li
        used_li = len(invoice.get('debit_items', [])) + 1  # +1 for LI1
        if used_li < total_li:
            row.extend([''] * (total_li - used_li) * _N_LI)

        self._worksheet.append_rows([row], value_input_option='RAW')
        self._all_rows.append(row)

    # ── convenience ──────────────────────────────────────────────────────

    @property
    def all_rows(self) -> list:
        return self._all_rows or []
