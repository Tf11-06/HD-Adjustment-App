import re
import pdfplumber

HEADER_COLS = [
    "Adjustment #", "Adjustment Date", "Invoice #", "Order #",
    "Invoice Date", "PO Date", "Credit/Debit", "Store #", "Vendor #",
    "Dept #", "Total Amount", "Handling",
]

ITEM_COLS = [
    "SKU", "Vendor PN", "UPC/GTIN", "Sellers Inv #", "Line C/D",
    "QTY", "Unit", "Unit Price", "Item Total",
]


def parse_pdf(pdf_path: str) -> dict:
    """Parse a Home Depot 812 PDF.

    Returns:
        {"header": dict, "items": list[dict]}
        header keys match HEADER_COLS; item keys match ITEM_COLS.
    """
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

    return {"header": header, "items": line_items}


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
        "Adjustment #":    search(r'ADJUSTMENT NUMBER:\s*(\S+)'),
        "Adjustment Date": search(r'ADJUSTMENT DATE:\s*([\d-]+)'),
        "Invoice #":       inv_order.group(1).strip() if inv_order else "",
        "Order #":         inv_order.group(2).strip() if inv_order else "",
        "Invoice Date":    inv_po.group(1).strip() if inv_po else "",
        "PO Date":         inv_po.group(2).strip() if inv_po else "",
        "Credit/Debit":    search(r'CREDIT DEBIT:\s*(.+)'),
        "Store #":         search(r'ST - StoreNumber:\s*(\d+)'),
        "Vendor #":        vendor_m.group(1).strip() if vendor_m else "",
        "Dept #":          search(r'DEPARTMENT NUMBER:\s*(\d+)'),
        "Total Amount":    search(r'AMOUNT:\s*([\d.]+)'),
        "Handling":        search(r'HANDLING:\s*(.+)'),
    }


def _parse_line_items_from_tables(table_rows: list) -> list[dict]:
    """Extract line items from pdfplumber table data."""
    if not table_rows:
        return []

    header_idx = None
    for i, row in enumerate(table_rows):
        if row and any(cell and "SKU" in str(cell).upper() for cell in row):
            header_idx = i
            break
    if header_idx is None:
        return []

    header_row = table_rows[header_idx]

    def col(row, *keywords):
        for kw in keywords:
            for i, h in enumerate(header_row):
                if h and kw.upper() in str(h).upper():
                    if i < len(row):
                        return str(row[i]).strip() if row[i] is not None else ""
        return ""

    items = []
    for row in table_rows[header_idx + 1:]:
        if not row:
            continue
        if any(cell and "ALLOWANCE" in str(cell).upper() for cell in row):
            break
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        qty_raw = col(row, "QTY")
        qty, unit = _parse_qty_unit(qty_raw)
        price_raw = col(row, "UNIT PRICE")
        unit_price = _parse_ucp(price_raw)

        item = {
            "SKU":           col(row, "SKU"),
            "Vendor PN":     col(row, "VENDOR PN"),
            "UPC/GTIN":      col(row, "UPC"),
            "Sellers Inv #": col(row, "SELLERS INVOICE"),
            "Line C/D":      col(row, "CREDIT DEBIT"),
            "QTY":           qty,
            "Unit":          unit,
            "Unit Price":    unit_price,
            "Item Total":    col(row, "ITEM TOTAL"),
        }
        items.append(item)

    return items


def _parse_line_items_from_text(text: str) -> list[dict]:
    """Fallback text parser for line items between header row and ALLOWANCE section."""
    header_pattern = re.search(
        r'(LINE\s+SKU\s+VENDOR\s+PN.+?)\n(.+?)(?:ALLOWANCE AND CHARGES|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if not header_pattern:
        return []

    item_block = header_pattern.group(2).strip()
    items = []
    for line in item_block.splitlines():
        line = line.strip()
        if not line:
            continue
        cd_match = re.search(r'(D - Debit|C - Credit)', line)
        total_match = re.search(r'([\d]+\.[\d]{2})\s*$', line)
        qty_match = re.search(r'CREDIT DEBIT QTY:\s*(\d+)\s+(\w+)', line)
        ucp_match = re.search(r'UCP:\s*([\d.]+)', line)
        inv_match = re.search(r'(\d{4})\s+(?:D - Debit|C - Credit)', line)
        tokens = re.findall(r'\b\d{4,7}\b', line)

        item = {
            "SKU":           tokens[0] if tokens else "",
            "Vendor PN":     tokens[1] if len(tokens) > 1 else "",
            "UPC/GTIN":      "",
            "Sellers Inv #": inv_match.group(1) if inv_match else "",
            "Line C/D":      cd_match.group(1) if cd_match else "",
            "QTY":           qty_match.group(1) if qty_match else "",
            "Unit":          qty_match.group(2) if qty_match else "",
            "Unit Price":    ucp_match.group(1) if ucp_match else "",
            "Item Total":    total_match.group(1) if total_match else "",
        }
        items.append(item)

    return items


def _parse_qty_unit(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    m = re.search(r'QTY:\s*(\d+)\s+(\w+)', raw, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r'(\d+)\s*(\w*)', raw)
    if m:
        return m.group(1), m.group(2)
    return "", ""


def _parse_ucp(raw: str) -> str:
    if not raw:
        return ""
    m = re.search(r'UCP:\s*([\d.]+)', raw, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'([\d.]+)', raw)
    return m.group(1) if m else ""
