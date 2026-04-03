import pytest
from unittest.mock import MagicMock, patch, call
import sheets
from pdf_parser import COLUMNS


@pytest.fixture
def mock_worksheet():
    ws = MagicMock()
    ws.row_values.return_value = []
    ws.get_all_values.return_value = [COLUMNS]  # only header row
    return ws


def test_ensure_header_writes_header_when_sheet_empty(mock_worksheet):
    mock_worksheet.get_all_values.return_value = []
    sheets.ensure_header(mock_worksheet)
    mock_worksheet.append_row.assert_called_once_with(COLUMNS)


def test_ensure_header_skips_when_header_exists(mock_worksheet):
    sheets.ensure_header(mock_worksheet)
    mock_worksheet.append_row.assert_not_called()


def test_find_duplicate_returns_true_when_invoice_exists(mock_worksheet):
    mock_worksheet.get_all_values.return_value = [
        COLUMNS,
        ["0", "2026-02-24", "7573", "1099173067"] + [""] * 18,
    ]
    assert sheets.find_duplicate(mock_worksheet, "7573") is True


def test_find_duplicate_returns_false_when_no_match(mock_worksheet):
    assert sheets.find_duplicate(mock_worksheet, "9999") is False


def test_find_duplicate_returns_false_on_empty_sheet(mock_worksheet):
    mock_worksheet.get_all_values.return_value = []
    assert sheets.find_duplicate(mock_worksheet, "7573") is False


def test_append_rows_calls_batch_append(mock_worksheet):
    rows = [
        {col: "" for col in COLUMNS},
        {col: "" for col in COLUMNS},
    ]
    rows[0]["Invoice #"] = "7573"
    rows[1]["Invoice #"] = "7573"
    count = sheets.append_rows(mock_worksheet, rows)
    assert mock_worksheet.append_rows.call_count == 1
    called_values = mock_worksheet.append_rows.call_args[0][0]
    assert len(called_values) == 2
    assert count == 2


def test_append_rows_values_in_column_order(mock_worksheet):
    row = {col: f"val_{i}" for i, col in enumerate(COLUMNS)}
    sheets.append_rows(mock_worksheet, [row])
    expected = [f"val_{i}" for i in range(len(COLUMNS))]
    mock_worksheet.append_rows.assert_called_once_with([expected], value_input_option='RAW')


def test_append_rows_empty_list(mock_worksheet):
    count = sheets.append_rows(mock_worksheet, [])
    assert count == 0
    mock_worksheet.append_rows.assert_not_called()


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
