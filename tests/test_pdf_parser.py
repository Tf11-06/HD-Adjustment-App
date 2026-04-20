"""Tests for pdf_parser.parse_pdf() using mock pdfplumber tables."""

import pytest
from unittest.mock import MagicMock, patch, call
import pdf_parser as parser


def _make_pdf(tables):
    """Build a mock pdfplumber PDF that returns the given list of tables."""
    page = MagicMock()
    page.extract_tables.return_value = tables
    pdf = MagicMock()
    pdf.pages = [page]
    pdf.__enter__ = lambda s: pdf
    pdf.__exit__ = MagicMock(return_value=False)
    return pdf


# ── Table fixtures ─────────────────────────────────────────────────────────────

# Table 0 — main invoice body
_T0 = [
    # row 0: header text blob
    [
        "Credit/Debit Adjustment 812\n"
        "ADJUSTMENT NUMBER: 9999\n"
        "AMOUNT: 278.03\n"
        "HANDLING: A - Off Invoice\n"
        "CREDIT DEBIT: C - Credit\n"
        "INVOICE NUMBER / ORDER NUMBER: 7573 / 1099173067\n"
        "INVOICE DATE / PO DATE: 2026-01-28 / 2026-01-26\n",
        None, None,
    ],
    # line-item header row
    ["LINE", "SKU", "VENDOR PN", "UPC GTIN", "ADJUSTMENT REASON",
     "DESCRIPTION", "SELLERS INVOICE #", "CREDIT DEBIT", "QTY",
     "UNIT PRICE", "UNIT DIFF", "ITEM TOTAL"],
    # credit summary row (adj_reason=24, Rule 1) — col 4 = ADJUSTMENT REASON
    [None, None, None, None, "24", None, "7573", "C - Credit", None, None, None, "278.03"],
    # debit row 1 — "06" at col 4 (ADJUSTMENT REASON), UPC GTIN col 3 = None
    [None, "175525", "900690", None, "06", None, "7573", "D - Debit",
     "QTY: 12 EA", "UCP - Unit CostPrice:3.34 INV:3.34", None, "40.08"],
    # debit row 2
    [None, "588978", "900701", None, "06", None, "7573", "D - Debit",
     "QTY: 48 EA", "UCP - Unit CostPrice:4.98 INV:4.98", None, "239.04"],
    # notes row (store number)
    ["NOTES ST - StoreNumber: 5089 RV: 500880949", None, None, None, None, None, None, None, None, None, None, None],
]

# Table 1 — sidebar metadata
_T1 = [
    ["2026-02-24\nADJUSTMENT DATE"],
    ["ignored"],
    [
        "VENDOR NUMBER:\n000873237\n580025",
        "DEPARTMENT NUMBER:\n28",
    ],
]

_TABLES_STANDARD = [_T0, _T1]


def test_parse_pdf_returns_dict():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        result = parser.parse_pdf("fake.pdf")
    assert isinstance(result, dict)


def test_parse_pdf_returns_none_when_fewer_than_two_tables():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf([[]])):
        result = parser.parse_pdf("fake.pdf")
    assert result is None


# ── Header fields ──────────────────────────────────────────────────────────────

def test_invoice_num():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["invoice_num"] == "7573"


def test_order_num():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["order_num"] == "1099173067"


def test_adj_num():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["adj_num"] == "9999"


def test_adj_date_from_sidebar():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["adj_date"] == "2026-02-24"


def test_inv_date_and_po_date():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["inv_date"] == "2026-01-28"
    assert r["po_date"] == "2026-01-26"


def test_credit_debit():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_debit"] == "C - Credit"


def test_amount_is_float():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["amount"] == pytest.approx(278.03)


def test_handling():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["handling"] == "A - Off Invoice"


def test_store_from_notes_row():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["store"] == "5089"


def test_vendor_num_two_part():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["vendor_num"] == "000873237 / 580025"


def test_dept():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["dept"] == "28"


def test_file_basename():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("/some/path/invoice.pdf")
    assert r["_file"] == "invoice.pdf"


# ── Rule 1: credit_line (adj_reason=24) ──────────────────────────────────────

def test_credit_line_present():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_line"] is not None


def test_credit_line_adj_reason():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_line"]["adj_reason"] == "24"


def test_credit_line_sellers_inv():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_line"]["sellers_inv"] == "7573"


def test_credit_line_item_total_is_float():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_line"]["item_total"] == pytest.approx(278.03)


def test_credit_line_has_no_sku_or_qty_fields():
    """Rule 1: credit_line dict must NOT contain sku/qty/unit_price."""
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    cl = r["credit_line"]
    assert "sku" not in cl
    assert "qty" not in cl
    assert "unit_price" not in cl


# ── Rule 2: debit items ───────────────────────────────────────────────────────

def test_debit_items_count():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert len(r["debit_items"]) == 2


def test_debit_sku_whitespace_joined():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["debit_items"][0]["sku"] == "175525"
    assert r["debit_items"][1]["sku"] == "588978"


def test_debit_qty_is_int():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["debit_items"][0]["qty"] == 12
    assert r["debit_items"][1]["qty"] == 48


def test_debit_unit():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["debit_items"][0]["unit"] == "EA"


def test_debit_unit_price_is_float():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["debit_items"][0]["unit_price"] == pytest.approx(3.34)
    assert r["debit_items"][1]["unit_price"] == pytest.approx(4.98)


def test_debit_item_total_is_float():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_STANDARD)):
        r = parser.parse_pdf("fake.pdf")
    assert r["debit_items"][0]["item_total"] == pytest.approx(40.08)
    assert r["debit_items"][1]["item_total"] == pytest.approx(239.04)


# ── Rule 3: compact format — no credit row ────────────────────────────────────

_T0_COMPACT = [
    [
        "INVOICE NUMBER / ORDER NUMBER: 8888 / 1111111111\n"
        "ADJUSTMENT NUMBER: 1\n"
        "AMOUNT: 40.08\n"
        "HANDLING: A - Off Invoice\n"
        "CREDIT DEBIT: D - Debit\n"
        "INVOICE DATE / PO DATE: 2026-01-28 / 2026-01-26\n",
        None, None,
    ],
    ["LINE", "SKU", "VENDOR PN", "X", "ADJUSTMENT REASON",
     "DESC", "SELLERS INVOICE #", "CREDIT DEBIT", "QTY", "UNIT PRICE", "DIFF", "ITEM TOTAL"],
    # Only debit row — no 24 row; "06" at col 4 (ADJUSTMENT REASON)
    [None, "175525", "900690", None, "06", None, "8888", "D - Debit",
     "QTY: 12 EA", "UCP - Unit CostPrice:3.34", None, "40.08"],
    ["NOTES ST - StoreNumber: 1001", None, None, None, None, None, None, None, None, None, None, None],
]

_TABLES_COMPACT = [_T0_COMPACT, _T1]


def test_compact_format_credit_line_is_none():
    """Rule 3: no 24 row → credit_line is None."""
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_COMPACT)):
        r = parser.parse_pdf("fake.pdf")
    assert r["credit_line"] is None


def test_compact_format_debit_items_still_parsed():
    with patch("pdf_parser.pdfplumber.open", return_value=_make_pdf(_TABLES_COMPACT)):
        r = parser.parse_pdf("fake.pdf")
    assert len(r["debit_items"]) == 1
    assert r["debit_items"][0]["sku"] == "175525"
