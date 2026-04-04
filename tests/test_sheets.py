import pytest
from unittest.mock import MagicMock, patch, call
import sheets
from pdf_parser import HEADER_COLS, ITEM_COLS


@pytest.fixture
def mock_worksheet():
    ws = MagicMock()
    header_row1 = [""] * len(HEADER_COLS)
    header_row2 = list(HEADER_COLS)
    ws.get_all_values.return_value = [header_row1, header_row2]
    return ws


# ── _build_header_rows ─────────────────────────────────────────────────────

def test_build_header_rows_zero_items():
    rows = sheets._build_header_rows(0)
    assert len(rows) == 2
    assert rows[0] == [""] * len(HEADER_COLS)
    assert rows[1] == list(HEADER_COLS)


def test_build_header_rows_one_item():
    rows = sheets._build_header_rows(1)
    assert rows[0][len(HEADER_COLS)] == "LINE ITEM 1"
    assert rows[1][len(HEADER_COLS):] == list(ITEM_COLS)
    assert len(rows[0]) == len(HEADER_COLS) + len(ITEM_COLS)


def test_build_header_rows_three_items():
    rows = sheets._build_header_rows(3)
    item_labels = [c for c in rows[0] if c.startswith("LINE ITEM")]
    assert item_labels == ["LINE ITEM 1", "LINE ITEM 2", "LINE ITEM 3"]
    expected_len = len(HEADER_COLS) + 3 * len(ITEM_COLS)
    assert len(rows[0]) == expected_len
    assert len(rows[1]) == expected_len


# ── _get_max_items ─────────────────────────────────────────────────────────

def test_get_max_items_empty():
    assert sheets._get_max_items([]) == 0


def test_get_max_items_no_item_groups():
    header_rows = sheets._build_header_rows(0)
    assert sheets._get_max_items(header_rows) == 0


def test_get_max_items_three_groups():
    header_rows = sheets._build_header_rows(3)
    assert sheets._get_max_items(header_rows) == 3


# ── ensure_header ──────────────────────────────────────────────────────────

def test_ensure_header_writes_two_rows_when_empty(mock_worksheet):
    mock_worksheet.get_all_values.return_value = []
    sheets.ensure_header(mock_worksheet)
    mock_worksheet.update.assert_called_once()
    written = mock_worksheet.update.call_args[0][0]
    assert len(written) == 2
    assert written[1] == list(HEADER_COLS)


def test_ensure_header_skips_when_header_exists(mock_worksheet):
    sheets.ensure_header(mock_worksheet)
    mock_worksheet.update.assert_not_called()


def test_ensure_header_uses_all_rows_arg(mock_worksheet):
    header_rows = sheets._build_header_rows(0)
    sheets.ensure_header(mock_worksheet, all_rows=header_rows)
    mock_worksheet.update.assert_not_called()
    mock_worksheet.get_all_values.assert_not_called()


# ── ensure_capacity ────────────────────────────────────────────────────────

def test_ensure_capacity_expands_when_needed(mock_worksheet):
    all_rows = sheets._build_header_rows(0)
    result = sheets.ensure_capacity(mock_worksheet, 2, all_rows)
    mock_worksheet.update.assert_called_once()
    assert sheets._get_max_items(result) == 2


def test_ensure_capacity_no_op_when_sufficient(mock_worksheet):
    all_rows = sheets._build_header_rows(3)
    result = sheets.ensure_capacity(mock_worksheet, 2, all_rows)
    mock_worksheet.update.assert_not_called()
    assert result is all_rows


def test_ensure_capacity_returns_updated_cache(mock_worksheet):
    data_row = ["data"] * (len(HEADER_COLS) + len(ITEM_COLS))
    all_rows = sheets._build_header_rows(1) + [data_row]
    result = sheets.ensure_capacity(mock_worksheet, 3, all_rows)
    assert sheets._get_max_items(result) == 3
    assert result[2] == data_row


# ── find_duplicate ─────────────────────────────────────────────────────────

def test_find_duplicate_returns_true_when_invoice_exists(mock_worksheet):
    header_rows = sheets._build_header_rows(1)
    invoice_col = HEADER_COLS.index("Invoice #")
    data_row = [""] * (len(HEADER_COLS) + len(ITEM_COLS))
    data_row[invoice_col] = "7573"
    all_rows = header_rows + [data_row]
    assert sheets.find_duplicate(mock_worksheet, "7573", all_rows=all_rows) is True


def test_find_duplicate_returns_false_when_no_match(mock_worksheet):
    assert sheets.find_duplicate(mock_worksheet, "9999") is False


def test_find_duplicate_returns_false_on_empty_sheet(mock_worksheet):
    assert sheets.find_duplicate(mock_worksheet, "7573", all_rows=[]) is False


def test_find_duplicate_skips_both_header_rows(mock_worksheet):
    header_rows = sheets._build_header_rows(0)
    assert sheets.find_duplicate(mock_worksheet, "Invoice #", all_rows=header_rows) is False


# ── append_invoice ─────────────────────────────────────────────────────────

def test_append_invoice_writes_exactly_one_row(mock_worksheet):
    all_rows = sheets._build_header_rows(0)
    invoice_data = {
        "header": {col: "h" for col in HEADER_COLS},
        "items": [{col: "x" for col in ITEM_COLS}],
    }
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    assert mock_worksheet.append_rows.call_count == 1
    written = mock_worksheet.append_rows.call_args[0][0]
    assert len(written) == 1


def test_append_invoice_row_header_fields_in_order(mock_worksheet):
    all_rows = sheets._build_header_rows(1)
    header_data = {col: f"h{i}" for i, col in enumerate(HEADER_COLS)}
    invoice_data = {"header": header_data, "items": [{col: "" for col in ITEM_COLS}]}
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    row = mock_worksheet.append_rows.call_args[0][0][0]
    assert row[:len(HEADER_COLS)] == [f"h{i}" for i in range(len(HEADER_COLS))]


def test_append_invoice_row_item_fields_after_header(mock_worksheet):
    all_rows = sheets._build_header_rows(1)
    item_data = {col: f"it{j}" for j, col in enumerate(ITEM_COLS)}
    invoice_data = {"header": {col: "" for col in HEADER_COLS}, "items": [item_data]}
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    row = mock_worksheet.append_rows.call_args[0][0][0]
    item_slice = row[len(HEADER_COLS):len(HEADER_COLS) + len(ITEM_COLS)]
    assert item_slice == [f"it{j}" for j in range(len(ITEM_COLS))]


def test_append_invoice_pads_unused_item_slots(mock_worksheet):
    all_rows = sheets._build_header_rows(3)
    invoice_data = {
        "header": {col: "" for col in HEADER_COLS},
        "items": [{col: "x" for col in ITEM_COLS}],
    }
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    row = mock_worksheet.append_rows.call_args[0][0][0]
    expected_len = len(HEADER_COLS) + 3 * len(ITEM_COLS)
    assert len(row) == expected_len
    unused = row[len(HEADER_COLS) + len(ITEM_COLS):]
    assert all(v == "" for v in unused)


def test_append_invoice_empty_items_list(mock_worksheet):
    all_rows = sheets._build_header_rows(0)
    invoice_data = {"header": {col: "v" for col in HEADER_COLS}, "items": []}
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    written = mock_worksheet.append_rows.call_args[0][0]
    assert len(written) == 1
    assert len(written[0]) == len(HEADER_COLS)


def test_append_invoice_expands_header_when_needed(mock_worksheet):
    all_rows = sheets._build_header_rows(1)
    invoice_data = {
        "header": {col: "" for col in HEADER_COLS},
        "items": [{col: "" for col in ITEM_COLS} for _ in range(3)],
    }
    sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    mock_worksheet.update.assert_called_once()


def test_append_invoice_returns_updated_all_rows(mock_worksheet):
    all_rows = sheets._build_header_rows(1)
    invoice_data = {
        "header": {col: "" for col in HEADER_COLS},
        "items": [{col: "" for col in ITEM_COLS}],
    }
    result = sheets.append_invoice(mock_worksheet, invoice_data, all_rows)
    assert len(result) == 3


# ── connect_sheet (unchanged) ───────────────────────────────────────────────

def test_connect_sheet_raises_on_missing_credentials(tmp_path):
    cfg = {
        "sheet_id": "abc",
        "credentials_file": str(tmp_path / "nonexistent.json"),
        "worksheet_name": "Adjustments",
    }
    with pytest.raises(FileNotFoundError, match="Credentials file not found"):
        sheets.connect_sheet(cfg)


def test_connect_sheet_raises_on_bad_sheet_id(tmp_path):
    import gspread
    creds_file = tmp_path / "sa.json"
    creds_file.write_text('{"type":"service_account"}')
    cfg = {
        "sheet_id": "bad_id",
        "credentials_file": str(creds_file),
        "worksheet_name": "Adjustments",
    }
    with patch("sheets.gspread.service_account") as mock_sa:
        mock_client = MagicMock()
        mock_sa.return_value = mock_client
        mock_client.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound
        with pytest.raises(ValueError, match="Could not find the Google Sheet"):
            sheets.connect_sheet(cfg)
