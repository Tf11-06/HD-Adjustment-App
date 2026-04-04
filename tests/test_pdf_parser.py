import pytest
import pdf_parser as parser

# Full text extracted from a real Home Depot 812 adjustment PDF
SAMPLE_TEXT = """
Credit/Debit Adjustment
812
ADJUSTMENT NUMBER: 0
AMOUNT: 240.13
HANDLING: A - Off Invoice
CREDIT DEBIT: D - Debit
INVOICE NUMBER / ORDER NUMBER: 7573 / 1099173067
INVOICE DATE / PO DATE: 2026-01-28 / 2026-01-26
ADJUSTMENT DATE: 2026-02-24
VENDOR NUMBER: 000873237 / 580025
DEPARTMENT NUMBER: 28
BT - BILL TO:
KLEAR CONCEPTS LLC
NOTES/COMMENTS/SPECIAL INSTRUCTIONS:
ST - StoreNumber: 5089
RV: 500880949
"""


def test_parse_header_adjustment_number():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Adjustment #"] == "0"


def test_parse_header_adjustment_date():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Adjustment Date"] == "2026-02-24"


def test_parse_header_invoice_and_order():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Invoice #"] == "7573"
    assert h["Order #"] == "1099173067"


def test_parse_header_invoice_date_and_po_date():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Invoice Date"] == "2026-01-28"
    assert h["PO Date"] == "2026-01-26"


def test_parse_header_credit_debit():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Credit/Debit"] == "D - Debit"


def test_parse_header_total_amount():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Total Amount"] == "240.13"


def test_parse_header_handling():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Handling"] == "A - Off Invoice"


def test_parse_header_store_number():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Store #"] == "5089"


def test_parse_header_vendor_number():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Vendor #"] == "000873237 / 580025"


def test_parse_header_dept_number():
    h = parser._parse_header(SAMPLE_TEXT)
    assert h["Dept #"] == "28"


def test_parse_header_missing_field_returns_empty_string():
    h = parser._parse_header("ADJUSTMENT NUMBER: 5\n")
    assert h["Store #"] == ""
    assert h["Invoice #"] == ""


# Line item test data — mimics what pdfplumber.extract_table() returns
# Columns: LINE, SKU, VENDOR PN, UPC GTIN, ADJ REASON, DESC, SELLERS INV #, CREDIT DEBIT, QTY, UNIT PRICE, UNIT DIFF, ITEM TOTAL
SAMPLE_TABLE_ROWS = [
    ["LINE", "SKU", "VENDOR PN", "UPC GTIN", "ADJUSTMENT REASON",
     "DESCRIPTION", "SELLERS INVOICE #", "CREDIT DEBIT", "QTY",
     "UNIT PRICE RETAIL PRICE", "UNIT PRICE DIFFERENCE", "ITEM TOTAL"],
    # First row: credit-only — "24" is ADJUSTMENT REASON (index 4), not UPC (index 3)
    [None, None, None, None, "24", None, "7573", "C - Credit", None, None, None, "38.99"],
    [None, "175525", "900690", "06", None, None, "7573", "D - Debit",
     "CREDIT DEBIT QTY: 12 EA", "UCP: 3.34 / INV: 3.3399", None, "40.08"],
    [None, "588978", "900701", "06", None, None, "7573", "D - Debit",
     "CREDIT DEBIT QTY: 48 EA", "UCP: 4.98 / INV: 4.9801", None, "239.04"],
]

# Real-world PDF table rows: narrow columns cause numbers and text to wrap across lines
REAL_PDF_TABLE_ROWS = [
    ["LINE\nE", "SKU", "VENDOR\nPN", "UPC\nGTIN", "ADJUSTMENT\nREASON",
     "DESCRIPTION\nITEM\nCOMMENTS", "SELLERS INVOICE\n#", "CREDIT\nDEBIT", "QTY",
     "UNIT PRICE\nRETAIL PRICE", "UNIT PRICE\nDIFFERENCE", "ITEM\nTOTAL"],
    [None, None, None, None, "24", None, "7573", "C -\nCredit", None, None, None, "38.99"],
    [None, "17552\n5", "90069\n0", "06", None, None, "7573", "D -\nDebit",
     "CREDIT DEBIT QTY:  12  EA -\nEach", "UCP - Unit Cost Price: 3.\n34\nINV: 3.3399", None, "40.08"],
    [None, "58897\n8", "90070\n1", "06", None, None, "7573", "D -\nDebit",
     "CREDIT DEBIT QTY:  48  EA -\nEach", "UCP - Unit Cost Price: 4.\n98\nINV: 4.9801", None, "239.04"],
]

SAMPLE_TEXT_WITH_ITEMS = SAMPLE_TEXT + """
LINE SKU VENDOR PN UPC GTIN ADJUSTMENT REASON DESCRIPTION SELLERS INVOICE # CREDIT DEBIT QTY UNIT PRICE ITEM TOTAL
 175525 900690 06  7573 D - Debit CREDIT DEBIT QTY: 12 EA UCP: 3.34 / INV: 3.3399 40.08
 588978 900701 06  7573 D - Debit CREDIT DEBIT QTY: 48 EA UCP: 4.98 / INV: 4.9801 239.04
ALLOWANCE AND CHARGES INFORMATION:
"""


def test_parse_line_items_from_tables_count():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert len(items) == 3


def test_parse_line_items_from_tables_sku():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[0]["SKU"] == ""         # credit-only row, no SKU
    assert items[1]["SKU"] == "175525"
    assert items[2]["SKU"] == "588978"


def test_parse_line_items_from_tables_vendor_pn():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[1]["Vendor PN"] == "900690"


def test_parse_line_items_from_tables_upc():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[0]["UPC/GTIN"] == ""   # credit-only row — no UPC
    assert items[1]["UPC/GTIN"] == "06"


def test_parse_line_items_from_tables_line_cd():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[0]["Line C/D"] == "C - Credit"
    assert items[1]["Line C/D"] == "D - Debit"


def test_parse_line_items_from_tables_qty_and_unit():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[1]["QTY"] == "12"
    assert items[1]["Unit"] == "EA"
    assert items[0]["QTY"] == ""        # blank qty on credit-only row


def test_parse_line_items_from_tables_unit_price():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[1]["Unit Price"] == "3.34"
    assert items[2]["Unit Price"] == "4.98"


def test_parse_line_items_from_tables_item_total():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[0]["Item Total"] == "38.99"
    assert items[1]["Item Total"] == "40.08"
    assert items[2]["Item Total"] == "239.04"


def test_parse_line_items_from_tables_sellers_invoice():
    items = parser._parse_line_items_from_tables(SAMPLE_TABLE_ROWS)
    assert items[1]["Sellers Inv #"] == "7573"


def test_parse_line_items_from_tables_empty_input():
    items = parser._parse_line_items_from_tables([])
    assert items == []


def test_parse_line_items_from_tables_no_header_row():
    items = parser._parse_line_items_from_tables([["foo", "bar"]])
    assert items == []


def test_parse_line_items_from_text_fallback_count():
    items = parser._parse_line_items_from_text(SAMPLE_TEXT_WITH_ITEMS)
    assert len(items) == 2


def test_parse_line_items_from_text_fallback_sku():
    items = parser._parse_line_items_from_text(SAMPLE_TEXT_WITH_ITEMS)
    assert items[0]["SKU"] == "175525"
    assert items[1]["SKU"] == "588978"


REAL_VENDOR_TEXT = """
VENDOR NUMBER:
000873237
580025
DEPARTMENT NUMBER: 28
"""


def test_parse_header_vendor_number_two_line():
    """Real PDFs put vendor # on two separate lines."""
    h = parser._parse_header(REAL_VENDOR_TEXT)
    assert h["Vendor #"] == "000873237 / 580025"


def test_real_pdf_table_sku_rejoins_split_number():
    items = parser._parse_line_items_from_tables(REAL_PDF_TABLE_ROWS)
    assert items[1]["SKU"] == "175525"
    assert items[2]["SKU"] == "588978"


def test_real_pdf_table_vendor_pn_rejoins_split_number():
    items = parser._parse_line_items_from_tables(REAL_PDF_TABLE_ROWS)
    assert items[1]["Vendor PN"] == "900690"
    assert items[2]["Vendor PN"] == "900701"


def test_real_pdf_table_line_cd_normalized():
    items = parser._parse_line_items_from_tables(REAL_PDF_TABLE_ROWS)
    assert items[0]["Line C/D"] == "C - Credit"
    assert items[1]["Line C/D"] == "D - Debit"


def test_real_pdf_table_ucp_extracted_from_full_label():
    items = parser._parse_line_items_from_tables(REAL_PDF_TABLE_ROWS)
    assert items[1]["Unit Price"] == "3.34"
    assert items[2]["Unit Price"] == "4.98"


def test_real_pdf_table_credit_row_has_blank_sku_and_upc():
    items = parser._parse_line_items_from_tables(REAL_PDF_TABLE_ROWS)
    assert items[0]["SKU"] == ""
    assert items[0]["UPC/GTIN"] == ""
    assert items[0]["Item Total"] == "38.99"


from unittest.mock import MagicMock, patch


def test_parse_pdf_merges_header_into_rows():
    """parse_pdf() returns {"header": dict, "items": list[dict]}."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = SAMPLE_TEXT
    mock_page.extract_table.return_value = SAMPLE_TABLE_ROWS

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdf_parser.pdfplumber.open", return_value=mock_pdf):
        result = parser.parse_pdf("fake.pdf")

    assert isinstance(result, dict)
    assert "header" in result
    assert "items" in result
    assert result["header"]["Invoice #"] == "7573"
    assert result["header"]["Adjustment Date"] == "2026-02-24"
    assert len(result["items"]) == 3
    assert result["items"][1]["SKU"] == "175525"
    assert result["items"][2]["SKU"] == "588978"
    for item in result["items"]:
        assert "Item Total" in item
        assert "SKU" in item
        assert "Invoice #" not in item   # header fields NOT duplicated into items
