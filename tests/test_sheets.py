"""Tests for writers.SheetsWriter using a mocked gspread Worksheet."""

import pytest
from unittest.mock import MagicMock, patch
import gspread

from writers.sheets_writer import SheetsWriter, _build_header_rows, _count_li_groups
from pdf_parser import HEADER_COLS, LI1_COLS, LI_COLS

_N_INV = len(HEADER_COLS)
_N_LI1 = len(LI1_COLS)
_N_LI  = len(LI_COLS)

# ── invoice fixtures ──────────────────────────────────────────────────────────

_INV_1 = {
    "invoice_num": "7573", "order_num": "1099173067", "adj_num": "9999",
    "adj_date": "2026-02-24", "inv_date": "2026-01-28", "po_date": "2026-01-26",
    "credit_debit": "C - Credit", "amount": 278.03, "handling": "A - Off Invoice",
    "store": "5089", "vendor_num": "000873237 / 580025", "dept": "28",
    "credit_line": {"adj_reason": "24", "sellers_inv": "7573",
                    "line_cd": "C - Credit", "item_total": 278.03},
    "debit_items": [
        {"sku": "175525", "vendor_pn": "900690", "adj_reason": "06",
         "sellers_inv": "7573", "line_cd": "D - Debit",
         "qty": 12, "unit": "EA", "unit_price": 3.34, "item_total": 40.08},
    ],
    "_file": "7573.pdf",
}

_INV_COMPACT = {
    "invoice_num": "8888", "order_num": "2222", "adj_num": "1",
    "adj_date": "2026-03-01", "inv_date": "2026-02-15", "po_date": "2026-02-10",
    "credit_debit": "D - Debit", "amount": 40.08, "handling": "A - Off Invoice",
    "store": "1001", "vendor_num": "000873237", "dept": "28",
    "credit_line": None,
    "debit_items": [
        {"sku": "175525", "vendor_pn": "900690", "adj_reason": "06",
         "sellers_inv": "8888", "line_cd": "D - Debit",
         "qty": 12, "unit": "EA", "unit_price": 3.34, "item_total": 40.08},
    ],
    "_file": "8888.pdf",
}


def _make_writer(all_rows=None):
    """Return a connected SheetsWriter with a mocked worksheet."""
    ws = MagicMock(spec=gspread.Worksheet)
    ws.id = 123
    ws.get_all_values.return_value = all_rows or []
    writer = SheetsWriter({"sheet_id": "x", "credentials_file": "x.json",
                            "worksheet_name": "Adjustments"})
    writer._worksheet = ws
    writer._all_rows = list(all_rows) if all_rows else []
    return writer, ws


# ── _build_header_rows helper ─────────────────────────────────────────────────

def test_build_header_rows_field_names():
    rows = _build_header_rows(0)
    assert rows[1][:_N_INV] == list(HEADER_COLS)
    assert "Adjustment #" not in rows[1][:_N_INV]


def test_build_header_rows_li1_label():
    rows = _build_header_rows(1)
    assert "LINE ITEM 1" in rows[0][_N_INV]
    assert rows[1][_N_INV:_N_INV + _N_LI1] == list(LI1_COLS)


def test_build_header_rows_li2_debit_cols():
    rows = _build_header_rows(1)
    li2_start = _N_INV + _N_LI1
    assert rows[1][li2_start:li2_start + _N_LI] == list(LI_COLS)


def test_build_header_rows_three_li_groups():
    rows = _build_header_rows(3)
    labels = [c for c in rows[0] if "LINE ITEM" in str(c)]
    assert len(labels) == 4  # LI1 + LI2 + LI3 + LI4


def test_count_li_groups_zero():
    rows = _build_header_rows(0)
    assert _count_li_groups(rows) == 1  # LI1 always present


def test_count_li_groups_three():
    rows = _build_header_rows(3)
    assert _count_li_groups(rows) == 4  # LI1 + 3 debit


# ── is_initialized ────────────────────────────────────────────────────────────

def test_not_initialized_when_empty():
    writer, _ = _make_writer([])
    assert not writer.is_initialized()


def test_initialized_after_initialize_headers():
    writer, ws = _make_writer([])
    ws.update = MagicMock()
    writer.initialize_headers(0)
    assert writer.is_initialized()


# ── initialize_headers ────────────────────────────────────────────────────────

def test_initialize_headers_calls_update(tmp_path):
    writer, ws = _make_writer([])
    writer.initialize_headers(1)
    ws.update.assert_called_once()
    written = ws.update.call_args[0][0]
    assert written[1][:_N_INV] == list(HEADER_COLS)


def test_initialize_headers_applies_formatting():
    writer, ws = _make_writer([])
    writer.initialize_headers(1)
    formatted_ranges = [item["range"] for item in ws.batch_format.call_args[0][0]]
    assert "A1:K1" in formatted_ranges
    assert "A2:K2" in formatted_ranges
    assert "A3:K1000" in formatted_ranges
    assert "L1:O1" in formatted_ranges
    assert "L3:O1000" in formatted_ranges
    assert "P1:X1" in formatted_ranges
    assert "P3:X1000" in formatted_ranges
    ws.freeze.assert_called_once_with(rows=2)
    ws.merge_cells.assert_any_call("A1:K1")
    ws.merge_cells.assert_any_call("L1:O1")
    ws.merge_cells.assert_any_call("P1:X1")


# ── find_duplicate ────────────────────────────────────────────────────────────

def test_find_duplicate_false_on_empty():
    writer, _ = _make_writer([])
    assert not writer.find_duplicate("7573")


def test_find_duplicate_true_after_row_exists():
    header = _build_header_rows(1)
    data_row = ["7573"] + [""] * (_N_INV - 1 + _N_LI1 + _N_LI)
    writer, _ = _make_writer(header + [data_row])
    assert writer.find_duplicate("7573")


def test_find_duplicate_false_for_different_invoice():
    header = _build_header_rows(1)
    data_row = ["7573"] + [""] * (_N_INV - 1 + _N_LI1 + _N_LI)
    writer, _ = _make_writer(header + [data_row])
    assert not writer.find_duplicate("9999")


# ── expand_columns_if_needed ──────────────────────────────────────────────────

def test_expand_calls_update_when_needed():
    header = _build_header_rows(0)
    writer, ws = _make_writer(header)
    writer.expand_columns_if_needed(3)
    ws.update.assert_called_once()
    assert ws.batch_format.called
    assert _count_li_groups(writer._all_rows) >= 4


def test_expand_no_op_when_sufficient():
    header = _build_header_rows(5)
    writer, ws = _make_writer(header)
    writer.expand_columns_if_needed(2)
    ws.update.assert_not_called()


# ── append_invoice ────────────────────────────────────────────────────────────

def test_append_invoice_calls_append_rows():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    ws.append_rows.assert_called_once()


def test_append_invoice_formats_existing_sheet_once():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    formatted_ranges = [item["range"] for item in ws.batch_format.call_args[0][0]]
    assert "A3:K1000" in formatted_ranges
    assert "L3:O1000" in formatted_ranges
    assert "P3:X1000" in formatted_ranges


def test_append_invoice_does_not_reformat_headers_for_every_row():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    writer.append_invoice(_INV_1)
    assert ws.batch_format.call_count == 1
    assert ws.append_rows.call_count == 2


def test_append_invoice_row_starts_with_invoice_num():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    row = ws.append_rows.call_args[0][0][0]
    assert row[0] == "7573"


def test_rule1_li1_adj_reason_populated():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    row = ws.append_rows.call_args[0][0][0]
    li1_start = _N_INV
    assert row[li1_start] == "24"        # Adj Reason


def test_rule1_li1_has_no_sku_vendor_qty_unit_price_columns():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    row = ws.append_rows.call_args[0][0][0]
    li1_start = _N_INV
    assert row[li1_start:li1_start + _N_LI1] == ["24", "7573", "C - Credit", 278.03]
    assert row[li1_start + _N_LI1] == "175525"


def test_rule3_compact_li1_all_blank():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_COMPACT)
    row = ws.append_rows.call_args[0][0][0]
    li1_start = _N_INV
    for offset in range(_N_LI1):
        assert row[li1_start + offset] == ""


def test_debit_items_start_at_li2():
    header = _build_header_rows(1)
    writer, ws = _make_writer(header)
    writer.append_invoice(_INV_1)
    row = ws.append_rows.call_args[0][0][0]
    li2_start = _N_INV + _N_LI1
    assert row[li2_start] == "175525"        # SKU of first debit item


# ── connect() error paths ─────────────────────────────────────────────────────

def test_connect_raises_on_missing_credentials(tmp_path):
    writer = SheetsWriter({
        "sheet_id": "abc",
        "credentials_file": str(tmp_path / "nonexistent.json"),
        "worksheet_name": "Adjustments",
    })
    with pytest.raises(FileNotFoundError, match="Credentials file not found"):
        writer.connect()


def test_connect_raises_on_bad_sheet_id(tmp_path):
    creds = tmp_path / "sa.json"
    creds.write_text('{"type":"service_account"}')
    writer = SheetsWriter({
        "sheet_id": "bad_id",
        "credentials_file": str(creds),
        "worksheet_name": "Adjustments",
    })
    with patch("writers.sheets_writer.gspread.service_account") as mock_sa:
        mock_client = MagicMock()
        mock_sa.return_value = mock_client
        mock_client.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound
        with pytest.raises(ValueError, match="Could not find the Google Sheet"):
            writer.connect()
