import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import platform

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
import pdfplumber

import config
import pdf_parser as parser
import pdf_parser
import sheets

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Theme ──────────────────────────────────────────────────────────────────
FONT_FAMILY = "Helvetica" if platform.system() == "Darwin" else "Segoe UI"

BG         = "#f1f4f9"
CARD_BG    = "#ffffff"
ACCENT     = "#3b6fd4"
DROP_BG    = "#eef2fb"
TEXT_MAIN  = "#1a2b4a"
TEXT_MUTED = "#6b7f99"
BORDER     = "#dde4ef"
SUCCESS    = "#22863a"
ERROR_CLR  = "#c0392b"


class HDProcessorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("HD Adjustment Processor")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._modal_result = None
        self._modal_event = threading.Event()
        self._processing = False
        self._build_ui()
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

    def _build_ui(self):
        # Header row: title + settings button
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 0))

        title_block = tk.Frame(header, bg=BG)
        title_block.pack(side="left")
        tk.Label(title_block, text="HD Adjustment Processor",
                 font=(FONT_FAMILY, 14, "bold"), bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block, text="Klear Concepts — Home Depot Vendor Tool",
                 font=(FONT_FAMILY, 10), bg=BG, fg=TEXT_MUTED).pack(anchor="w")

        settings_btn = tk.Button(
            header, text="⚙  Settings", font=(FONT_FAMILY, 10),
            bg="#e2e8f2", fg=TEXT_MUTED, relief="flat", bd=0,
            padx=10, pady=4, cursor="hand2",
            command=self._open_settings
        )
        settings_btn.pack(side="right", anchor="ne")

        # Drop zone
        self.drop_frame = tk.Frame(
            self, bg=DROP_BG, bd=2, relief="flat",
            highlightbackground=ACCENT, highlightthickness=2,
            cursor="hand2"
        )
        self.drop_frame.pack(fill="x", padx=20, pady=(14, 0), ipady=24)
        self.drop_frame.bind("<Button-1>", self._on_click_browse)

        tk.Label(self.drop_frame, text="⬇", font=(FONT_FAMILY, 22),
                 bg=DROP_BG, fg=ACCENT).pack()
        tk.Label(self.drop_frame, text="Drop PDF(s) here",
                 font=(FONT_FAMILY, 12, "bold"), bg=DROP_BG, fg=TEXT_MAIN).pack()
        tk.Label(self.drop_frame, text="or click to browse",
                 font=(FONT_FAMILY, 10), bg=DROP_BG, fg=TEXT_MUTED).pack()

        # Status card
        status_card = tk.Frame(self, bg=CARD_BG, bd=1,
                               highlightbackground=BORDER, highlightthickness=1)
        status_card.pack(fill="x", padx=20, pady=(12, 0), ipady=6)
        tk.Label(status_card, text="STATUS", font=(FONT_FAMILY, 8),
                 bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 0))
        self.status_label = tk.Label(
            status_card, text="Ready — drop a PDF to begin",
            font=(FONT_FAMILY, 11), bg=CARD_BG, fg=TEXT_MUTED, anchor="w"
        )
        self.status_label.pack(anchor="w", padx=10, pady=(0, 6))

        # Last processed row
        last_row = tk.Frame(self, bg=BG)
        last_row.pack(fill="x", padx=22, pady=(10, 0))
        tk.Label(last_row, text="Last processed: ", font=(FONT_FAMILY, 10),
                 bg=BG, fg=TEXT_MUTED).pack(side="left")
        self.last_label = tk.Label(last_row, text="—",
                                   font=(FONT_FAMILY, 10), bg=BG, fg=TEXT_MAIN)
        self.last_label.pack(side="left")

    def set_status(self, message: str, color: str = TEXT_MUTED):
        self.status_label.configure(text=message, fg=color)
        self.update_idletasks()

    def set_last_processed(self, invoice: str, row_count: int):
        ts = datetime.now().strftime("%I:%M %p").lstrip("0")
        self.last_label.configure(
            text=f"Invoice #{invoice} · {row_count} row{'s' if row_count != 1 else ''} added · {ts}"
        )

    def _on_click_browse(self, event=None):
        if self._processing:
            return
        paths = filedialog.askopenfilenames(
            title="Select PDF(s)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if paths:
            self._process_files(list(paths))

    def _on_drop(self, event):
        if self._processing:
            return
        raw = event.data.strip()
        paths = self.tk.splitlist(raw)
        pdf_paths = [p for p in paths if p.lower().endswith(".pdf")]
        if pdf_paths:
            self._process_files(pdf_paths)

    def _open_settings(self):
        SettingsWindow(self)

    def _process_files(self, paths: list[str]):
        self._processing = True
        thread = threading.Thread(target=self._run_batch, args=(paths,), daemon=True)
        thread.start()

    def _ask_add_anyway(self, invoice_num: str) -> bool:
        """Run on the main thread: show duplicate dialog, return True=add, False=skip."""
        self._modal_event.clear()
        self._modal_result = None
        self.after(0, lambda: self._show_duplicate_modal(invoice_num))
        self._modal_event.wait()  # worker thread waits here
        return self._modal_result

    def _show_duplicate_modal(self, invoice_num: str):
        """Called on main thread. Show custom dialog, set result, signal event."""
        win = tk.Toplevel(self)
        win.title("Duplicate Invoice")
        win.geometry("400x130")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.grab_set()
        win.transient(self)

        msg = tk.Label(
            win,
            text=f"Invoice #{invoice_num} already exists in the sheet.\nAdd anyway or skip?",
            font=(FONT_FAMILY, 11), bg=BG, fg=TEXT_MAIN, justify="center", wraplength=360
        )
        msg.pack(pady=(20, 12))

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack()

        def on_add():
            self._modal_result = True
            win.destroy()
            self._modal_event.set()

        def on_skip():
            self._modal_result = False
            win.destroy()
            self._modal_event.set()

        tk.Button(btn_row, text="Add Anyway", font=(FONT_FAMILY, 10), bg=ACCENT, fg="white",
                  relief="flat", padx=14, pady=5, cursor="hand2", command=on_add).pack(side="left", padx=6)
        tk.Button(btn_row, text="Skip", font=(FONT_FAMILY, 10), bg="#e2e8f2", fg=TEXT_MAIN,
                  relief="flat", padx=14, pady=5, cursor="hand2", command=on_skip).pack(side="left", padx=6)

    def _run_batch(self, paths: list[str]):
        total = len(paths)
        processed = 0
        skipped = 0
        total_rows = 0

        cfg = config.load_config()

        if not cfg.get("sheet_id"):
            msg, clr = "Sheet ID not configured. Open Settings to add it.", ERROR_CLR
            self.after(0, lambda msg=msg, clr=clr: self.set_status(msg, clr))
            self.after(0, lambda: setattr(self, '_processing', False))
            return

        try:
            worksheet = sheets.connect_sheet(cfg)
        except (FileNotFoundError, ValueError, ConnectionError) as e:
            err = str(e)
            self.after(0, lambda err=err: self.set_status(err, ERROR_CLR))
            self.after(0, lambda: setattr(self, '_processing', False))
            return

        try:
            all_rows = sheets.get_all_rows(worksheet)
            sheets.ensure_header(worksheet, all_rows=all_rows)
        except Exception:
            self.after(0, lambda: self.set_status(
                "Could not connect to Google Sheets. Check your internet connection and credentials.",
                ERROR_CLR
            ))
            self.after(0, lambda: setattr(self, '_processing', False))
            return

        for i, path in enumerate(paths, 1):
            filename = os.path.basename(path)
            msg = f"Processing {i} of {total}: {filename}..."
            self.after(0, lambda msg=msg: self.set_status(msg, ACCENT))

            try:
                rows = parser.parse_pdf(path)
            except Exception:
                msg = f"Could not read {filename}. Make sure it's a valid Home Depot adjustment document."
                self.after(0, lambda msg=msg: self.set_status(msg, ERROR_CLR))
                skipped += 1
                continue

            warn_no_items = False
            if not rows:
                # Build a single blank-items row from header-only data
                try:
                    with pdfplumber.open(path) as pdf:
                        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    header = pdf_parser._parse_header(full_text)
                except Exception:
                    header = {}
                blank_row = {col: header.get(col, "") for col in pdf_parser.COLUMNS}
                rows = [blank_row]
                warn_no_items = True

            invoice_num = rows[0].get("Invoice #", "")

            if invoice_num and sheets.find_duplicate(worksheet, invoice_num, all_rows=all_rows):
                add_anyway = self._ask_add_anyway(invoice_num)
                if not add_anyway:
                    skipped += 1
                    continue

            try:
                count = sheets.append_rows(worksheet, rows)
                total_rows += count
                processed += 1
                # Refresh the cache so duplicate detection stays current
                try:
                    all_rows = sheets.get_all_rows(worksheet)
                except Exception:
                    all_rows = []  # non-fatal; duplicate detection degrades gracefully
                if invoice_num:
                    inv, cnt = invoice_num, count
                    self.after(0, lambda i=inv, c=cnt: self.set_last_processed(i, c))
                if warn_no_items:
                    warn_msg = f"Warning: No line items detected in {filename}. Row added with blank item columns."
                    self.after(0, lambda m=warn_msg: self.set_status(m, ERROR_CLR))
            except Exception:
                msg = "Could not connect to Google Sheets. Check your internet connection and credentials."
                self.after(0, lambda msg=msg: self.set_status(msg, ERROR_CLR))
                self.after(0, lambda: setattr(self, '_processing', False))
                return

        if not warn_no_items or total > 1:
            if total == 1:
                if processed == 1:
                    msg = f"✓ Done — {total_rows} row{'s' if total_rows != 1 else ''} added to sheet."
                    self.after(0, lambda msg=msg: self.set_status(msg, SUCCESS))
                else:
                    self.after(0, lambda: self.set_status("Skipped (duplicate or error).", TEXT_MUTED))
            else:
                batch_msg = (
                    f"Batch complete — {processed} of {total} processed, {total_rows} rows added"
                    + (f", {skipped} skipped" if skipped else "") + "."
                )
                clr = SUCCESS if processed > 0 else TEXT_MUTED
                self.after(0, lambda m=batch_msg, c=clr: self.set_status(m, c))

        self.after(0, lambda: setattr(self, '_processing', False))


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("380x230")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._parent = parent
        self._build()

    def _build(self):
        tk.Label(self, text="Settings", font=(FONT_FAMILY, 13, "bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 10))

        cfg = config.load_config()

        tk.Label(self, text="Google Sheet ID", font=(FONT_FAMILY, 10),
                 bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=20)
        self.sheet_id_var = tk.StringVar(value=cfg.get("sheet_id", ""))
        tk.Entry(self, textvariable=self.sheet_id_var, font=(FONT_FAMILY, 10),
                 width=44, bd=1, relief="solid").pack(padx=20, pady=(2, 10), anchor="w")

        tk.Label(self, text="Credentials File (service_account.json)",
                 font=(FONT_FAMILY, 10), bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=20)
        creds_row = tk.Frame(self, bg=BG)
        creds_row.pack(anchor="w", padx=20, pady=(2, 0))
        self.creds_var = tk.StringVar(value=cfg.get("credentials_file", "service_account.json"))
        tk.Entry(creds_row, textvariable=self.creds_var, font=(FONT_FAMILY, 10),
                 width=34, bd=1, relief="solid").pack(side="left")
        tk.Button(creds_row, text="Browse…", font=(FONT_FAMILY, 9),
                  bg="#e2e8f2", relief="flat", padx=6, pady=3,
                  command=self._browse_creds).pack(side="left", padx=(6, 0))

        tk.Button(self, text="Save", font=(FONT_FAMILY, 10, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._save).pack(pady=(16, 0))

    def _browse_creds(self):
        path = filedialog.askopenfilename(
            title="Select service_account.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.creds_var.set(path)

    def _save(self):
        cfg = config.load_config()
        cfg["sheet_id"] = self.sheet_id_var.get().strip()
        cfg["credentials_file"] = self.creds_var.get().strip()
        config.save_config(cfg)
        self._parent.set_status("Settings saved.", SUCCESS)
        self.destroy()


if __name__ == "__main__":
    app = HDProcessorApp()
    app.mainloop()
