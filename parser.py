import re
import pdfplumber

COLUMNS = [
    "Adjustment #", "Adjustment Date", "Invoice #", "Order #",
    "Invoice Date", "PO Date", "Credit/Debit", "SKU", "Vendor PN",
    "UPC/GTIN", "Adjustment Reason", "Sellers Invoice #", "Line C/D",
    "QTY", "Unit", "Unit Price", "Item Total", "Store #", "Vendor #",
    "Dept #", "Total Amount", "Handling",
]


def parse_pdf(pdf_path: str) -> list[dict]:
    """Parse a Home Depot 812 PDF. Returns list of row dicts (one per line item)."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        raw_tables = []
        for page in pdf.pages:
            t = page.extract_table()
            if t:
                raw_tables.extend(t)

    header = _parse_header(full_text)
    line_items = _parse_line_items_from_tables(raw_tables)
    if not line_items:
        line_items = _parse_line_items_from_text(full_text)

    rows = []
    for item in line_items:
        row = {}
        row.update(header)
        row.update(item)
        rows.append(row)

    return rows


def _parse_header(text: str) -> dict:
    def search(pattern, default=""):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    inv_order = re.search(
        r'INVOICE NUMBER / ORDER NUMBER:\s*([\w]+)\s*/\s*([\w]+)', text, re.IGNORECASE
    )
    inv_po = re.search(
        r'INVOICE DATE / PO DATE:\s*([\d-]+)\s*/\s*([\d-]+)', text, re.IGNORECASE
    )
    vendor_m = re.search(r'VENDOR NUMBER:\s*(.+)', text, re.IGNORECASE)

    return {
        "Adjustment #":   search(r'ADJUSTMENT NUMBER:\s*(\S+)'),
        "Adjustment Date": search(r'ADJUSTMENT DATE:\s*([\d-]+)'),
        "Invoice #":      inv_order.group(1).strip() if inv_order else "",
        "Order #":        inv_order.group(2).strip() if inv_order else "",
        "Invoice Date":   inv_po.group(1).strip() if inv_po else "",
        "PO Date":        inv_po.group(2).strip() if inv_po else "",
        "Credit/Debit":   search(r'CREDIT DEBIT:\s*(.+)'),
        "Total Amount":   search(r'AMOUNT:\s*([\d.]+)'),
        "Handling":       search(r'HANDLING:\s*(.+)'),
        "Store #":        search(r'ST - StoreNumber:\s*(\d+)'),
        "Vendor #":       vendor_m.group(1).strip() if vendor_m else "",
        "Dept #":         search(r'DEPARTMENT NUMBER:\s*(\d+)'),
    }


def _parse_line_items_from_tables(table_rows: list) -> list[dict]:
    """Extract line items from pdfplumber table data."""
    return []  # implemented in Task 4


def _parse_line_items_from_text(text: str) -> list[dict]:
    """Fallback: extract line items from raw text."""
    return []  # implemented in Task 4
