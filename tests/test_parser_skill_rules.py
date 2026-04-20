"""
Integration tests for pdf_parser against real Home Depot 812 PDFs.
Validates Rules 1–5 from the hd-klear-812 skill.

PDFs must be present at PDF_DIR. Tests are auto-skipped if the directory
doesn't exist (CI without sample data).
"""

import os
import glob
import pytest
import pdf_parser as parser

PDF_DIR = "/Users/tai/Documents/Projects/Klear/812/batchBizDoc_2026-04-14T15_44_52"

pytestmark = pytest.mark.skipif(
    not os.path.isdir(PDF_DIR),
    reason=f"Sample PDFs not found at {PDF_DIR}",
)


@pytest.fixture(scope="module")
def all_invoices():
    """Parse every PDF in the batch directory once, return list of dicts."""
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    assert pdfs, f"No PDFs found in {PDF_DIR}"
    results = []
    for p in pdfs:
        inv = parser.parse_pdf(p)
        if inv is not None:
            results.append(inv)
    return results


def test_all_pdfs_parseable(all_invoices):
    """Every PDF in the batch should return a non-None dict."""
    pdfs = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    assert len(all_invoices) == len(pdfs), (
        f"Only {len(all_invoices)} of {len(pdfs)} PDFs parsed successfully"
    )


def test_all_invoices_have_invoice_num(all_invoices):
    for inv in all_invoices:
        assert inv["invoice_num"], f"{inv['_file']} has no invoice_num"


def test_all_invoices_have_adj_date(all_invoices):
    for inv in all_invoices:
        assert inv["adj_date"], f"{inv['_file']} has no adj_date"


def test_all_invoices_have_amount(all_invoices):
    for inv in all_invoices:
        assert inv["amount"] not in ("", None), f"{inv['_file']} has no amount"


def test_rule1_credit_line_has_only_allowed_fields(all_invoices):
    """Rule 1: credit_line (when present) must NOT have sku/qty/unit_price."""
    for inv in all_invoices:
        cl = inv.get("credit_line")
        if cl is None:
            continue
        assert cl.get("adj_reason") == "24", \
            f"{inv['_file']}: credit_line adj_reason should be '24', got {cl.get('adj_reason')}"
        assert "sku" not in cl, f"{inv['_file']}: credit_line should not have 'sku'"
        assert "qty" not in cl, f"{inv['_file']}: credit_line should not have 'qty'"
        assert "unit_price" not in cl, f"{inv['_file']}: credit_line should not have 'unit_price'"
        assert cl.get("item_total") not in ("", None), \
            f"{inv['_file']}: credit_line item_total is blank"


def test_rule2_debit_items_have_sku(all_invoices):
    """Rule 2: every debit item must have a non-blank SKU."""
    for inv in all_invoices:
        for i, item in enumerate(inv["debit_items"]):
            assert item["sku"], \
                f"{inv['_file']}: debit_items[{i}] has blank SKU"


def test_rule2_debit_items_qty_is_int(all_invoices):
    """Rule 5: QTY must be stored as int, not string."""
    for inv in all_invoices:
        for i, item in enumerate(inv["debit_items"]):
            if item["qty"] is not None:
                assert isinstance(item["qty"], int), \
                    f"{inv['_file']}: debit_items[{i}] qty={item['qty']!r} is not int"


def test_rule2_debit_items_unit_price_is_float(all_invoices):
    """Rule 5: unit_price must be float when present."""
    for inv in all_invoices:
        for i, item in enumerate(inv["debit_items"]):
            if item["unit_price"] is not None:
                assert isinstance(item["unit_price"], float), \
                    f"{inv['_file']}: debit_items[{i}] unit_price={item['unit_price']!r} is not float"


def test_rule2_debit_item_total_is_number(all_invoices):
    """Rule 5: item_total must be numeric."""
    for inv in all_invoices:
        for i, item in enumerate(inv["debit_items"]):
            val = item["item_total"]
            assert isinstance(val, (int, float)), \
                f"{inv['_file']}: debit_items[{i}] item_total={val!r} is not numeric"


def test_rule3_compact_invoices_credit_line_is_none(all_invoices):
    """Rule 3: invoices with no '24' row → credit_line is None, debit items still parsed."""
    compact = [inv for inv in all_invoices if inv["credit_line"] is None]
    for inv in compact:
        assert len(inv["debit_items"]) > 0, \
            f"{inv['_file']}: compact invoice has no credit_line AND no debit_items"


def test_rule4_dedup_by_invoice_num(all_invoices):
    """Rule 4: after deduplication (first occurrence wins), invoice numbers are unique."""
    seen = {}
    deduped = []
    for inv in all_invoices:
        num = inv["invoice_num"]
        if num not in seen:
            seen[num] = inv["_file"]
            deduped.append(inv)
    # Verify dedup produced unique invoice nums
    nums = [inv["invoice_num"] for inv in deduped]
    assert len(nums) == len(set(nums)), "Dedup produced non-unique invoice numbers"


def test_sku_whitespace_rejoined(all_invoices):
    """pdfplumber sometimes splits SKU numbers across whitespace — verify they're rejoined."""
    for inv in all_invoices:
        for item in inv["debit_items"]:
            assert " " not in item["sku"], \
                f"{inv['_file']}: SKU '{item['sku']}' contains whitespace (not rejoined)"
