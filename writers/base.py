"""Abstract Writer interface shared by ExcelWriter and SheetsWriter."""

from abc import ABC, abstractmethod


class Writer(ABC):
    """
    Common interface for appending parsed invoices to a destination
    (Excel file or Google Sheet).

    Invoice dict shape (from pdf_parser.parse_pdf):
      invoice_num, order_num, adj_num, adj_date, inv_date, po_date,
      credit_debit, amount, handling, store, vendor_num, dept,
      credit_line: {adj_reason, sellers_inv, line_cd, item_total} | None,
      debit_items: list of {sku, vendor_pn, adj_reason, sellers_inv,
                            line_cd, qty, unit, unit_price, item_total}
    """

    @abstractmethod
    def is_initialized(self) -> bool:
        """Return True if the destination has been set up with headers."""

    @abstractmethod
    def initialize_headers(self, max_line_items: int = 0) -> None:
        """Write the 2-row header to a blank destination."""

    @abstractmethod
    def find_duplicate(self, invoice_num: str) -> bool:
        """Return True if invoice_num already exists in the destination."""

    @abstractmethod
    def expand_columns_if_needed(self, num_debit_items: int) -> None:
        """Expand header columns if this invoice has more line items than current max."""

    @abstractmethod
    def append_invoice(self, invoice: dict) -> None:
        """Append one invoice as a single row."""

    # ── helpers shared by both writers ────────────────────────────────────

    @staticmethod
    def li1_row(credit_line: dict | None) -> list:
        """Build the 4-cell LI1 credit summary row."""
        if credit_line is None:
            return [''] * 4
        return [
            credit_line.get('adj_reason', ''),
            credit_line.get('sellers_inv', ''),
            credit_line.get('line_cd', ''),
            credit_line.get('item_total', ''),
        ]

    @staticmethod
    def debit_row(item: dict) -> list:
        """Build the 9-cell row for one debit line item."""
        return [
            item.get('sku', ''),
            item.get('vendor_pn', ''),
            item.get('adj_reason', ''),
            item.get('sellers_inv', ''),
            item.get('line_cd', ''),
            item.get('qty', ''),
            item.get('unit', ''),
            item.get('unit_price', ''),
            item.get('item_total', ''),
        ]

    @staticmethod
    def invoice_header_row(invoice: dict) -> list:
        """Build the 12-cell invoice header section of the data row."""
        return [
            invoice.get('invoice_num', ''),
            invoice.get('order_num', ''),
            invoice.get('adj_date', ''),
            invoice.get('inv_date', ''),
            invoice.get('po_date', ''),
            invoice.get('credit_debit', ''),
            invoice.get('amount', ''),
            invoice.get('handling', ''),
            invoice.get('store', ''),
            invoice.get('vendor_num', ''),
            invoice.get('dept', ''),
        ]
