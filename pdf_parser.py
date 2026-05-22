"""
HD Klear 812 — PDF Parser
Parses Home Depot 812 EDI Credit/Debit Adjustment invoice PDFs.

Rules:
  Rule 1 — LI1 is always the credit summary (adj_reason='24'):
            only adj_reason, sellers_inv, line_cd, item_total are exported.
  Rule 2 — Debit line items (adj_reason='06' / '01 - Pricing Error') go in LI2+.
  Rule 3 — Compact-format invoices have no '24' row: credit_line=None, debits start at LI2.
  Rule 4 — Deduplicate by invoice number (handled by caller).
  Rule 5 — Numeric values (QTY, prices, totals) stored as Python numbers, not strings.
"""

import re
import pdfplumber

# Column name constants used by writers
HEADER_COLS = [
    "Invoice #", "Order #", "Adjustment Date",
    "Invoice Date", "PO Date", "Credit/Debit", "Total Amount",
    "Handling", "Store #", "Vendor #", "Dept #",
]

LI1_COLS = [
    "Adj Reason", "Sellers Inv #", "Line C/D", "Item Total",
]

LI_COLS = [
    "SKU", "Vendor PN", "Adj Reason", "Sellers Inv #", "Line C/D",
    "QTY", "Unit", "Unit Price", "Item Total",
]


# ─── helpers ──────────────────────────────────────────────────────────────────

def _rget(pat, txt, g=1, d=''):
    m = re.search(pat, txt)
    return m.group(g).strip() if m else d


def _nstr(s):
    """Join whitespace fragments — fixes pdfplumber splitting numbers like '58897 8' → '588978'."""
    return ''.join(str(s).split()) if s else ''


def _extract_price(raw):
    """
    Extract unit price float from pdfplumber cell.
    Raw: 'UCP - Unit Cost Price: 4. 98 INV: 4.9799'
    pdfplumber may split the number; join all whitespace first,
    then extract the value after 'CostPrice:'.
    """
    joined = ''.join(str(raw).split())
    m = re.search(r'CostPrice:([\d.]+)', joined)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m = re.search(r'([\d.]+)', joined)
    try:
        return float(m.group(1)) if m else None
    except ValueError:
        return None


def _to_float(raw):
    """Convert raw cell to float, joining whitespace + stripping commas."""
    s = ''.join(str(raw or '').split()).replace(',', '')
    try:
        return float(s)
    except ValueError:
        return s


def _clean_cell(raw):
    """Normalize pdfplumber cell text while preserving word boundaries."""
    return str(raw or '').replace('\n', ' ').strip()


def _returned_goods_value(txt, tables):
    """Extract the Returned Goods value from RM invoices."""
    ignored_values = {'UNITS', 'SHIPPED', 'RETURNED'}
    for table in tables:
        for row in table:
            for cell in row:
                cell_txt = str(cell or '')
                if 'RETURNED GOODS' not in cell_txt.upper():
                    continue
                m = re.search(r'RETURNED GOODS:\s*([A-Za-z0-9-]+)', cell_txt, re.I)
                if m and m.group(1).strip().upper() not in ignored_values:
                    return m.group(1).strip()

    # Header text can collapse the RM row into:
    # "RETURNED GOODS: UNITS SHIPPED RETURNED:\nCREDIT DEBIT: D - Debit 10394 0 CT"
    m = re.search(
        r'CREDIT DEBIT:\s*D\s*-\s*Debit\s+([A-Za-z0-9-]+)\s+\d+\s+\w+',
        txt,
        re.I,
    )
    if m:
        return m.group(1).strip()

    m = re.search(r'RETURNED GOODS:\s*([A-Za-z0-9-]+)', txt, re.I)
    return m.group(1).strip() if m else ''


# ─── main parser ──────────────────────────────────────────────────────────────

def parse_pdf(filepath: str) -> dict | None:
    """
    Parse one 812 invoice PDF.

    Returns a dict:
      invoice_num, order_num, adj_num, adj_date, inv_date, po_date,
      credit_debit, amount, handling, store, vendor_num, dept,
      credit_line: {adj_reason, sellers_inv, line_cd, item_total} | None,
      debit_items: list of 9-field dicts,
      _file: basename

    Returns None if the PDF cannot be parsed (fewer than 2 tables found).
    """
    with pdfplumber.open(filepath) as pdf:
        tables = pdf.pages[0].extract_tables()

    if len(tables) < 2:
        return None

    t0, t1 = tables[0], tables[1]

    # ── Sidebar metadata (Table 1) ─────────────────────────────────────────
    adj_date = _rget(r'(\d{4}-\d{2}-\d{2})', t1[0][0] or '')

    vendor_raw = t1[2][0] or '' if len(t1) > 2 and len(t1[2]) > 0 else ''
    vm = re.search(r'VENDOR NUMBER:\n?(\w+)\n?(\w+)?', vendor_raw)
    if vm:
        v1, v2 = vm.group(1), vm.group(2) or ''
        vendor_num = f"{v1} / {v2}" if v2 and v2[0].isdigit() else v1
    else:
        vendor_num = ''

    dept_raw = t1[2][1] or '' if len(t1) > 2 and len(t1[2]) > 1 else ''
    dept = _rget(r'DEPARTMENT NUMBER:\n?(\d+)', dept_raw)

    # ── Header text blob (Table 0, row 0) ─────────────────────────────────
    txt = t0[0][0] or ''
    is_rm_invoice = 'RETURNED GOODS:' in txt.upper()
    invoice_num  = _rget(r'INVOICE NUMBER / ORDER NUMBER: (\S+) / \S+', txt)
    order_num    = _rget(r'INVOICE NUMBER / ORDER NUMBER: \S+ / (\S+)', txt)
    adj_num      = _rget(r'ADJUSTMENT NUMBER: (\S+)', txt)
    amount       = _to_float(_rget(r'AMOUNT: ([\d.,]+)', txt).replace(',', ''))
    handling     = _rget(r'HANDLING: (.+?)(?:\s+UNITS|\n)', txt)
    credit_debit = _rget(r'CREDIT DEBIT: (.+?)(?:\s+RETURNED|\n)', txt)
    inv_date     = _rget(r'INVOICE DATE / PO DATE: (\S+) / \S+', txt)
    po_date      = _rget(r'INVOICE DATE / PO DATE: \S+ / (\S+)', txt)

    if is_rm_invoice:
        invoice_num = adj_num
        order_num = ''
        inv_date = ''
        po_date = ''
        handling = _rget(r'HANDLING: (.+?)(?:\s+RETURNED GOODS:|\n)', txt)
        credit_debit = _rget(r'CREDIT DEBIT: (.+?)(?:\s+\d+\s+\d+\s+\w+|\n)', txt)

        # RM PDFs can place the adjustment date on the line after the label.
        if not adj_date:
            adj_date = _rget(r'ADJUSTMENT DATE:\s*(?:\n|\s)+(\d{4}-\d{2}-\d{2})', txt)

    rm_sellers_inv = _returned_goods_value(txt, (t0, t1)) if is_rm_invoice else ''

    # Store number is in a notes row at the bottom of Table 0
    notes_txt = next((r[0] for r in reversed(t0) if r[0] and 'StoreNumber' in str(r[0])), '') or ''
    store = _rget(r'StoreNumber: (\d+)', notes_txt)

    # ── Line items ─────────────────────────────────────────────────────────
    hdr_idx = next(
        (i for i, r in enumerate(t0) if r[1] and 'SKU' in str(r[1]).upper()),
        None
    )

    credit_line = None
    debit_items = []

    if hdr_idx is not None:
        hdr = t0[hdr_idx]

        def find_col(terms):
            for i, c in enumerate(hdr):
                if c and any(t.upper() in str(c).replace('\n', ' ').upper() for t in terms):
                    return i
            return None

        sellers_col = find_col(['SELLER'])
        cd_col      = find_col(['CREDIT DEBIT'])
        qty_col     = find_col(['QTY'])
        price_col   = find_col(['UNIT PRICE', 'RETAIL PRICE'])
        total_col   = len(hdr) - 1
        adj_col     = find_col(['ADJUSTMENT REASON'])
        sku_col     = find_col(['SKU'])
        vpn_col     = find_col(['VENDOR PRODUCT', 'VENDOR PN', 'STYLE'])

        for row in t0[hdr_idx + 1:]:
            if row[0] and ('ALLOWANCE' in str(row[0]).upper() or 'NOTES' in str(row[0]).upper()):
                break

            adj_raw = _clean_cell(row[adj_col]) if adj_col is not None else ''
            if not adj_raw:
                continue

            sellers_inv = _clean_cell(row[sellers_col]) if sellers_col is not None else ''
            if is_rm_invoice and adj_raw.upper() == 'RM':
                sellers_inv = rm_sellers_inv

            line_cd     = _clean_cell(row[cd_col]) if cd_col is not None else ''
            item_total  = _to_float(''.join(str(row[total_col] or '').split()).replace(',', '')) if total_col < len(row) else ''

            if adj_raw == '24':
                # Rule 1 — credit summary row: only 4 fields, rest blank
                credit_line = {
                    'adj_reason': '24',
                    'sellers_inv': sellers_inv,
                    'line_cd': line_cd,
                    'item_total': item_total,
                }
            else:
                # Rule 2 — debit product row
                sku = _nstr(str(row[sku_col] or '') if sku_col is not None else str(row[1] or ''))
                if not sku:
                    continue

                vpn_raw   = row[vpn_col] if vpn_col is not None else (row[2] if len(row) > 2 else '')
                vendor_pn = _nstr(vpn_raw)

                qty_raw = str(row[qty_col] or '').replace('\n', ' ') if qty_col is not None else ''
                qty_m   = re.search(r'QTY:\s*(\d+)', qty_raw)
                qty     = int(qty_m.group(1)) if qty_m else None
                unit    = 'EA' if qty_m else ''

                price_raw  = _clean_cell(row[price_col]) if price_col is not None else ''
                unit_price = _extract_price(price_raw) if price_raw else None
                if is_rm_invoice and item_total == '' and unit_price is not None and qty is not None:
                    item_total = round(qty * unit_price, 2)

                debit_items.append({
                    'sku': sku, 'vendor_pn': vendor_pn, 'adj_reason': adj_raw,
                    'sellers_inv': sellers_inv, 'line_cd': line_cd,
                    'qty': qty, 'unit': unit, 'unit_price': unit_price, 'item_total': item_total,
                })

    import os
    return {
        'invoice_num': invoice_num, 'order_num': order_num, 'adj_num': adj_num,
        'adj_date': adj_date, 'inv_date': inv_date, 'po_date': po_date,
        'credit_debit': credit_debit, 'amount': amount, 'handling': handling,
        'store': store, 'vendor_num': vendor_num, 'dept': dept,
        'credit_line': credit_line, 'debit_items': debit_items,
        '_file': os.path.basename(filepath),
    }
