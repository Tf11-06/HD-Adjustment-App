import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

import config
import parser
import sheets

# ── Theme ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

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
                 font=("Segoe UI", 14, "bold"), bg=BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block, text="Klear Concepts — Home Depot Vendor Tool",
                 font=("Segoe UI", 10), bg=BG, fg=TEXT_MUTED).pack(anchor="w")

        settings_btn = tk.Button(
            header, text="⚙  Settings", font=("Segoe UI", 10),
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

        tk.Label(self.drop_frame, text="⬇", font=("Segoe UI", 22),
                 bg=DROP_BG, fg=ACCENT).pack()
        tk.Label(self.drop_frame, text="Drop PDF(s) here",
                 font=("Segoe UI", 12, "bold"), bg=DROP_BG, fg=TEXT_MAIN).pack()
        tk.Label(self.drop_frame, text="or click to browse",
                 font=("Segoe UI", 10), bg=DROP_BG, fg=TEXT_MUTED).pack()

        # Status card
        status_card = tk.Frame(self, bg=CARD_BG, bd=1,
                               highlightbackground=BORDER, highlightthickness=1)
        status_card.pack(fill="x", padx=20, pady=(12, 0), ipady=6)
        tk.Label(status_card, text="STATUS", font=("Segoe UI", 8),
                 bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 0))
        self.status_label = tk.Label(
            status_card, text="Ready — drop a PDF to begin",
            font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_MUTED, anchor="w"
        )
        self.status_label.pack(anchor="w", padx=10, pady=(0, 6))

        # Last processed row
        last_row = tk.Frame(self, bg=BG)
        last_row.pack(fill="x", padx=22, pady=(10, 0))
        tk.Label(last_row, text="Last processed: ", font=("Segoe UI", 10),
                 bg=BG, fg=TEXT_MUTED).pack(side="left")
        self.last_label = tk.Label(last_row, text="—",
                                   font=("Segoe UI", 10), bg=BG, fg=TEXT_MAIN)
        self.last_label.pack(side="left")

    def set_status(self, message: str, color: str = TEXT_MUTED):
        self.status_label.configure(text=message, fg=color)
        self.update_idletasks()

    def set_last_processed(self, invoice: str, row_count: int):
        ts = datetime.now().strftime("%#I:%M %p")
        self.last_label.configure(
            text=f"Invoice #{invoice} · {row_count} row{'s' if row_count != 1 else ''} added · {ts}"
        )

    def _on_click_browse(self, event=None):
        paths = filedialog.askopenfilenames(
            title="Select PDF(s)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if paths:
            self._process_files(list(paths))

    def _on_drop(self, event):
        raw = event.data.strip()
        paths = self.tk.splitlist(raw)
        pdf_paths = [p for p in paths if p.lower().endswith(".pdf")]
        if pdf_paths:
            self._process_files(pdf_paths)

    def _open_settings(self):
        SettingsWindow(self)

    def _process_files(self, paths: list[str]):
        total = len(paths)
        processed = 0
        skipped = 0
        total_rows = 0

        cfg = config.load_config()

        if not cfg.get("sheet_id"):
            self.set_status("Sheet ID not configured. Open Settings to add it.", ERROR_CLR)
            return

        try:
            worksheet = sheets.connect_sheet(cfg)
            sheets.ensure_header(worksheet)
        except (FileNotFoundError, ValueError, ConnectionError) as e:
            self.set_status(str(e), ERROR_CLR)
            return

        for i, path in enumerate(paths, 1):
            filename = os.path.basename(path)
            self.set_status(f"Processing {i} of {total}: {filename}...", ACCENT)

            try:
                rows = parser.parse_pdf(path)
            except Exception:
                self.set_status(
                    f"Could not read {filename}. Make sure it's a valid Home Depot adjustment document.",
                    ERROR_CLR
                )
                skipped += 1
                continue

            if not rows:
                self.set_status(f"Warning: No data found in {filename}.", ERROR_CLR)
                skipped += 1
                continue

            invoice_num = rows[0].get("Invoice #", "")

            if invoice_num and sheets.find_duplicate(worksheet, invoice_num):
                answer = messagebox.askyesno(
                    "Duplicate Invoice",
                    f"Invoice #{invoice_num} already exists in the sheet.\n\nAdd anyway?",
                    icon="warning"
                )
                if not answer:
                    skipped += 1
                    continue

            try:
                count = sheets.append_rows(worksheet, rows)
                total_rows += count
                processed += 1
                if invoice_num:
                    self.set_last_processed(invoice_num, count)
            except Exception:
                self.set_status(
                    "Could not connect to Google Sheets. Check your internet connection and credentials.",
                    ERROR_CLR
                )
                return

        if total == 1:
            if processed == 1:
                self.set_status(
                    f"✓ Done — {total_rows} row{'s' if total_rows != 1 else ''} added to sheet.",
                    SUCCESS
                )
            else:
                self.set_status("Skipped (duplicate or error).", TEXT_MUTED)
        else:
            self.set_status(
                f"Batch complete — {processed} of {total} processed, {total_rows} rows added"
                + (f", {skipped} skipped" if skipped else "") + ".",
                SUCCESS if processed > 0 else TEXT_MUTED
            )


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
        tk.Label(self, text="Settings", font=("Segoe UI", 13, "bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 10))

        cfg = config.load_config()

        tk.Label(self, text="Google Sheet ID", font=("Segoe UI", 10),
                 bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=20)
        self.sheet_id_var = tk.StringVar(value=cfg.get("sheet_id", ""))
        tk.Entry(self, textvariable=self.sheet_id_var, font=("Segoe UI", 10),
                 width=44, bd=1, relief="solid").pack(padx=20, pady=(2, 10), anchor="w")

        tk.Label(self, text="Credentials File (service_account.json)",
                 font=("Segoe UI", 10), bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=20)
        creds_row = tk.Frame(self, bg=BG)
        creds_row.pack(anchor="w", padx=20, pady=(2, 0))
        self.creds_var = tk.StringVar(value=cfg.get("credentials_file", "service_account.json"))
        tk.Entry(creds_row, textvariable=self.creds_var, font=("Segoe UI", 10),
                 width=34, bd=1, relief="solid").pack(side="left")
        tk.Button(creds_row, text="Browse…", font=("Segoe UI", 9),
                  bg="#e2e8f2", relief="flat", padx=6, pady=3,
                  command=self._browse_creds).pack(side="left", padx=(6, 0))

        tk.Button(self, text="Save", font=("Segoe UI", 10, "bold"),
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
