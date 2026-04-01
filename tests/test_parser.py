import pytest
import parser

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
