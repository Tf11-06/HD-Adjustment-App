"""
HD Adjustment Processor — Klear Concepts
Main application entry point.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import platform

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

import config
import pdf_parser as parser
from writers import ExcelWriter, SheetsWriter

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── palette ───────────────────────────────────────────────────────────────────
_FONT = "Helvetica Neue" if platform.system() == "Darwin" else "Segoe UI"

BG          = "#0f1923"
SURFACE     = "#1a2535"
SURFACE2    = "#243044"
ACCENT      = "#f0a500"   # amber gold
ACCENT_DIM  = "#c07d00"
SHEETS_CLR  = "#1d6fa4"   # Google Sheets blue
EXCEL_CLR   = "#1a7a3c"   # Excel green
TEXT        = "#e2e8f0"
TEXT_MUTED  = "#7a8fa6"
BORDER      = "#2e3d52"
SUCCESS     = "#22c55e"
ERROR_CLR   = "#ef4444"
WARNING     = "#f59e0b"


def _resource_path(relative_path: str) -> str:
    """Return a path that works from source and PyInstaller bundles."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ── helpers ───────────────────────────────────────────────────────────────────

def _btn(parent, text, command, bg=SURFACE2, fg=TEXT, font_size=10, bold=False, pad_x=14, pad_y=6):
    weight = "bold" if bold else "normal"
    return tk.Button(
        parent, text=text, command=command,
        font=(_FONT, font_size, weight),
        bg=bg, fg=fg, activebackground=ACCENT, activeforeground="#000",
        relief="flat", bd=0, padx=pad_x, pady=pad_y, cursor="hand2",
    )


def _label(parent, text, size=10, bold=False, color=TEXT, anchor="w", **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, font=(_FONT, size, weight),
                    bg=kw.pop("bg", BG), fg=color, anchor=anchor, **kw)


# ── destination toggle ────────────────────────────────────────────────────────

class DestinationToggle(tk.Frame):
    """Segmented control: Google Sheets | Excel File."""

    def __init__(self, parent, initial="sheets", on_change=None):
        super().__init__(parent, bg=SURFACE, bd=0)
        self._value = initial
        self._on_change = on_change

        self._btn_sheets = tk.Button(
            self, text="☁  Google Sheets",
            font=(_FONT, 10, "bold"),
            relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
            command=lambda: self._select("sheets"),
        )
        self._btn_excel = tk.Button(
            self, text="📊  Excel File",
            font=(_FONT, 10, "bold"),
            relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
            command=lambda: self._select("excel"),
        )

        self._btn_sheets.pack(side="left")
        self._btn_excel.pack(side="left")
        self._refresh()

    def _select(self, value):
        if self._value == value:
            return
        self._value = value
        self._refresh()
        if self._on_change:
            self._on_change(value)

    def _refresh(self):
        if self._value == "sheets":
            self._btn_sheets.configure(bg=SHEETS_CLR, fg="#fff")
            self._btn_excel.configure(bg=SURFACE2, fg=TEXT_MUTED)
        else:
            self._btn_sheets.configure(bg=SURFACE2, fg=TEXT_MUTED)
            self._btn_excel.configure(bg=EXCEL_CLR, fg="#fff")

    def set(self, value):
        self._select(value)

    @property
    def value(self):
        return self._value


# ── duplicate dialog ──────────────────────────────────────────────────────────

class DuplicateDialog:
    """
    Shows a duplicate-invoice modal.
    result: "add" | "skip" | "add_all" | "skip_all"
    """

    def __init__(self, parent, invoice_num: str):
        self._result = "skip"
        self._event = threading.Event()
        parent.after(0, lambda: self._show(parent, invoice_num))

    def _show(self, parent, invoice_num: str):
        win = tk.Toplevel(parent)
        win.title("Duplicate Invoice")
        win.geometry("440x160")
        win.resizable(False, False)
        win.configure(bg=SURFACE)
        win.grab_set()
        win.transient(parent)

        tk.Label(
            win,
            text=f"Invoice #{invoice_num} already exists.",
            font=(_FONT, 12, "bold"), bg=SURFACE, fg=TEXT, justify="center",
        ).pack(pady=(20, 4))
        tk.Label(
            win,
            text="Add this invoice again, or skip it?",
            font=(_FONT, 10), bg=SURFACE, fg=TEXT_MUTED, justify="center",
        ).pack(pady=(0, 14))

        row = tk.Frame(win, bg=SURFACE)
        row.pack()

        def pick(val):
            self._result = val
            win.destroy()
            self._event.set()

        _btn(row, "Skip",     lambda: pick("skip"),    SURFACE2,   TEXT_MUTED).pack(side="left", padx=4)
        _btn(row, "Skip All", lambda: pick("skip_all"), SURFACE2,  TEXT_MUTED).pack(side="left", padx=4)
        _btn(row, "Add Anyway", lambda: pick("add"),   SHEETS_CLR, "#fff", bold=True).pack(side="left", padx=4)
        _btn(row, "Add All",  lambda: pick("add_all"), ACCENT,     "#000", bold=True).pack(side="left", padx=4)

        win.protocol("WM_DELETE_WINDOW", lambda: pick("skip"))

    def wait(self) -> str:
        self._event.wait()
        return self._result


# ── settings window ───────────────────────────────────────────────────────────

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._parent = parent
        self._build()

    def _section(self, text):
        f = tk.Frame(self, bg=ACCENT, height=2)
        f.pack(fill="x", padx=20, pady=(14, 0))
        _label(self, text, size=9, color=ACCENT, bg=BG).pack(anchor="w", padx=20, pady=(4, 2))

    def _row(self, label, var, browse_cmd=None, placeholder=""):
        _label(self, label, size=9, color=TEXT_MUTED, bg=BG).pack(anchor="w", padx=20)
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=20, pady=(2, 8))
        e = tk.Entry(
            row, textvariable=var, font=(_FONT, 10),
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        if browse_cmd:
            e.pack(side="left", fill="x", expand=True, ipady=5)
            _btn(row, "Browse…", browse_cmd, SURFACE2, TEXT_MUTED, pad_x=8, pad_y=4).pack(side="left", padx=(6, 0))
        else:
            e.pack(fill="x", ipady=5)

    def _build(self):
        cfg = config.load_config()

        _label(self, "Settings", size=14, bold=True, color=ACCENT, bg=BG).pack(anchor="w", padx=20, pady=(18, 4))

        # Google Sheets
        self._section("GOOGLE SHEETS")
        self._sheet_id  = tk.StringVar(value=cfg.get("sheet_id", ""))
        self._creds     = tk.StringVar(value=cfg.get("credentials_file", "service_account.json"))
        self._worksheet = tk.StringVar(value=cfg.get("worksheet_name", "Adjustments"))
        self._row("Sheet ID", self._sheet_id)
        self._row("Credentials File (service_account.json)", self._creds, self._browse_creds)
        self._row("Worksheet Name", self._worksheet)

        # Excel
        self._section("EXCEL FILE")
        self._excel_path = tk.StringVar(value=cfg.get("excel_file_path", ""))
        self._row("Excel File Path (.xlsx)", self._excel_path, self._browse_excel)

        # Save
        _btn(self, "Save Settings", self._save, ACCENT, "#000", font_size=11, bold=True, pad_x=20, pad_y=8).pack(pady=14)

    def _browse_creds(self):
        p = filedialog.askopenfilename(title="Select service_account.json",
                                       filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if p:
            self._creds.set(p)

    def _browse_excel(self):
        p = filedialog.asksaveasfilename(
            title="Select or create Excel file",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("All", "*.*")],
        )
        if p:
            self._excel_path.set(p)

    def _save(self):
        cfg = config.load_config()
        cfg["sheet_id"]        = self._sheet_id.get().strip()
        cfg["credentials_file"]= self._creds.get().strip()
        cfg["worksheet_name"]  = self._worksheet.get().strip()
        cfg["excel_file_path"] = self._excel_path.get().strip()
        config.save_config(cfg)
        self._parent.set_status("Settings saved.", SUCCESS)
        self.destroy()


# ── main app ──────────────────────────────────────────────────────────────────

class HDProcessorApp(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("HD Adjustment Processor")
        self._set_window_icon()
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(bg=BG)

        cfg = config.load_config()
        self._dest = cfg.get("active_destination", "sheets")
        self._processing = False
        self._build_ui()
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

    def _set_window_icon(self):
        try:
            self._app_icon = tk.PhotoImage(file=_resource_path("assets/app_logo.png"))
            self.iconphoto(True, self._app_icon)
        except tk.TclError:
            pass

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # ── top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg=SURFACE, height=56)
        top.pack(fill="x")
        top.pack_propagate(False)

        left = tk.Frame(top, bg=SURFACE)
        left.pack(side="left", padx=18, pady=10)
        tk.Label(left, text="HD Adjustment Processor",
                 font=(_FONT, 13, "bold"), bg=SURFACE, fg=TEXT).pack(anchor="w")
        tk.Label(left, text="Klear Concepts  ·  Home Depot Vendor Tool",
                 font=(_FONT, 9), bg=SURFACE, fg=TEXT_MUTED).pack(anchor="w")

        _btn(top, "⚙  Settings", self._open_settings,
             bg=SURFACE2, fg=TEXT_MUTED, pad_x=10, pad_y=5).pack(
            side="right", padx=14, pady=14)

        # ── amber accent line ─────────────────────────────────────────────
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # ── destination toggle ────────────────────────────────────────────
        tog_wrap = tk.Frame(self, bg=BG)
        tog_wrap.pack(fill="x", padx=20, pady=(14, 0))
        _label(tog_wrap, "DESTINATION", size=8, color=TEXT_MUTED, bg=BG).pack(anchor="w")
        self._toggle = DestinationToggle(
            tog_wrap, initial=self._dest, on_change=self._on_dest_change
        )
        self._toggle.pack(anchor="w", pady=(4, 0))

        # ── drop zone ─────────────────────────────────────────────────────
        self._drop_frame = tk.Frame(
            self, bg=SURFACE,
            highlightbackground=BORDER, highlightthickness=1,
            cursor="hand2",
        )
        self._drop_frame.pack(fill="x", padx=20, pady=14, ipady=28)
        self._drop_frame.bind("<Button-1>", self._on_click_browse)
        self._drop_frame.bind("<Enter>", lambda e: self._drop_frame.configure(highlightbackground=ACCENT))
        self._drop_frame.bind("<Leave>", lambda e: self._drop_frame.configure(highlightbackground=BORDER))

        self._drop_icon = tk.Label(self._drop_frame, text="⬇",
                                   font=(_FONT, 26), bg=SURFACE, fg=ACCENT)
        self._drop_icon.pack()
        self._drop_icon.bind("<Button-1>", self._on_click_browse)

        tk.Label(self._drop_frame, text="Drop invoices here  ·  up to 20 PDFs",
                 font=(_FONT, 12, "bold"), bg=SURFACE, fg=TEXT).pack()
        tk.Label(self._drop_frame, text="or click to browse",
                 font=(_FONT, 9), bg=SURFACE, fg=TEXT_MUTED).pack(pady=(2, 0))

        # ── progress bar (hidden until batch starts) ──────────────────────
        self._progress_frame = tk.Frame(self, bg=BG)
        self._progress_frame.pack(fill="x", padx=20)

        self._progress_label = _label(self._progress_frame, "", size=9, color=TEXT_MUTED, bg=BG)
        self._progress_label.pack(anchor="w")

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame, height=6,
            progress_color=ACCENT, fg_color=SURFACE,
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", pady=(2, 6))
        self._progress_frame.pack_forget()  # hidden by default

        # ── status card ───────────────────────────────────────────────────
        card = tk.Frame(self, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=20, pady=(4, 0), ipady=6)

        tk.Label(card, text="STATUS", font=(_FONT, 7, "bold"),
                 bg=SURFACE, fg=TEXT_MUTED).pack(anchor="w", padx=12, pady=(6, 0))
        self._status_label = tk.Label(
            card, text="Ready — drop invoices to begin",
            font=(_FONT, 11), bg=SURFACE, fg=TEXT_MUTED, anchor="w", wraplength=460,
        )
        self._status_label.pack(anchor="w", padx=12, pady=(2, 6))

        # ── last processed ────────────────────────────────────────────────
        last_row = tk.Frame(self, bg=BG)
        last_row.pack(fill="x", padx=22, pady=(10, 0))
        _label(last_row, "Last processed: ", size=9, color=TEXT_MUTED, bg=BG).pack(side="left")
        self._last_label = _label(last_row, "—", size=9, color=ACCENT, bg=BG)
        self._last_label.pack(side="left")

    # ── callbacks ─────────────────────────────────────────────────────────

    def set_status(self, msg: str, color: str = TEXT_MUTED):
        self._status_label.configure(text=msg, fg=color)
        self.update_idletasks()

    def set_last_processed(self, invoice: str, debit_count: int):
        ts = datetime.now().strftime("%I:%M %p").lstrip("0")
        items = f"{debit_count} line item{'s' if debit_count != 1 else ''}"
        self._last_label.configure(text=f"Invoice #{invoice}  ·  {items}  ·  {ts}")

    def _show_progress(self, label: str, fraction: float):
        self._progress_frame.pack(fill="x", padx=20)
        self._progress_label.configure(text=label)
        self._progress_bar.set(fraction)
        self.update_idletasks()

    def _hide_progress(self):
        self._progress_frame.pack_forget()
        self.update_idletasks()

    def _on_dest_change(self, value: str):
        self._dest = value
        cfg = config.load_config()
        cfg["active_destination"] = value
        config.save_config(cfg)

    def _on_click_browse(self, event=None):
        if self._processing:
            return
        paths = filedialog.askopenfilenames(
            title="Select PDF invoices (up to 20)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if paths:
            self._process_files(list(paths)[:20])

    def _on_drop(self, event):
        if self._processing:
            return
        paths = [p for p in self.tk.splitlist(event.data.strip()) if p.lower().endswith(".pdf")]
        if paths:
            self._process_files(paths[:20])

    def _open_settings(self):
        SettingsWindow(self)

    def _process_files(self, paths: list[str]):
        self._processing = True
        threading.Thread(target=self._run_batch, args=(paths,), daemon=True).start()

    # ── batch processing ──────────────────────────────────────────────────

    def _ask_duplicate(self, invoice_num: str) -> str:
        """Block the worker thread until the user responds to the duplicate dialog."""
        dialog = DuplicateDialog(self, invoice_num)
        return dialog.wait()  # "add" | "skip" | "add_all" | "skip_all"

    def _run_batch(self, paths: list[str]):
        total = len(paths)
        cfg = config.load_config()
        dest = self._dest

        # ── validate config ────────────────────────────────────────────────
        if dest == "sheets" and not cfg.get("sheet_id"):
            self.after(0, lambda: self.set_status(
                "Sheet ID not configured. Open ⚙ Settings to add it.", ERROR_CLR))
            self.after(0, lambda: setattr(self, '_processing', False))
            return

        if dest == "excel" and not cfg.get("excel_file_path"):
            self.after(0, lambda: self.set_status(
                "Excel file not configured. Open ⚙ Settings to choose a file.", ERROR_CLR))
            self.after(0, lambda: setattr(self, '_processing', False))
            return

        # ── connect writer ─────────────────────────────────────────────────
        if dest == "sheets":
            writer = SheetsWriter(cfg)
            try:
                writer.connect()
            except (FileNotFoundError, ValueError, ConnectionError) as e:
                err = str(e)
                self.after(0, lambda err=err: self.set_status(err, ERROR_CLR))
                self.after(0, lambda: setattr(self, '_processing', False))
                return
        else:
            writer = ExcelWriter(cfg["excel_file_path"])

        # ── process each PDF ───────────────────────────────────────────────
        processed = 0
        skipped = 0
        bulk_choice = None   # "add_all" | "skip_all" | None

        for i, path in enumerate(paths, 1):
            filename = os.path.basename(path)
            frac = (i - 1) / total
            lbl = f"Processing {i} of {total}: {filename}"
            self.after(0, lambda l=lbl, f=frac: self._show_progress(l, f))
            self.after(0, lambda l=lbl: self.set_status(l, TEXT_MUTED))

            # Parse
            try:
                invoice = parser.parse_pdf(path)
            except Exception:
                self.after(0, lambda fn=filename: self.set_status(
                    f"Could not read {fn}. Make sure it's a valid HD adjustment PDF.", ERROR_CLR))
                skipped += 1
                continue

            if invoice is None:
                self.after(0, lambda fn=filename: self.set_status(
                    f"Skipped {fn} — could not extract tables.", WARNING))
                skipped += 1
                continue

            # Duplicate check
            inv_num = invoice.get('invoice_num', '')
            if inv_num and writer.find_duplicate(inv_num):
                if bulk_choice == "add_all":
                    choice = "add"
                elif bulk_choice == "skip_all":
                    skipped += 1
                    continue
                else:
                    choice = self._ask_duplicate(inv_num)
                    if choice == "skip_all":
                        bulk_choice = "skip_all"
                        skipped += 1
                        continue
                    elif choice == "add_all":
                        bulk_choice = "add_all"
                        choice = "add"

                if choice == "skip":
                    skipped += 1
                    continue

            # Write
            try:
                writer.append_invoice(invoice)
                processed += 1
                debit_count = len(invoice.get('debit_items', []))
                if inv_num:
                    self.after(0, lambda n=inv_num, c=debit_count: self.set_last_processed(n, c))
            except Exception as e:
                err = str(e)
                self.after(0, lambda e=err: self.set_status(
                    f"Write error: {e}", ERROR_CLR))
                self.after(0, lambda: self._hide_progress())
                self.after(0, lambda: setattr(self, '_processing', False))
                return

        # ── final status ───────────────────────────────────────────────────
        self.after(0, lambda: self._show_progress("Done", 1.0))

        dest_label = "sheet" if dest == "sheets" else "Excel file"
        if total == 1:
            if processed == 1:
                msg = f"✓ Done — invoice added to {dest_label}."
                self.after(0, lambda m=msg: self.set_status(m, SUCCESS))
            else:
                self.after(0, lambda: self.set_status("Invoice skipped (duplicate or error).", TEXT_MUTED))
        else:
            skip_note = f", {skipped} skipped" if skipped else ""
            msg = f"✓ Batch complete — {processed} of {total} invoices added to {dest_label}{skip_note}."
            clr = SUCCESS if processed > 0 else TEXT_MUTED
            self.after(0, lambda m=msg, c=clr: self.set_status(m, c))

        import time
        time.sleep(1.2)
        self.after(0, self._hide_progress)
        self.after(0, lambda: setattr(self, '_processing', False))


if __name__ == "__main__":
    app = HDProcessorApp()
    app.mainloop()
