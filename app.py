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

APP_VERSION = "1.1.4"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── palette ───────────────────────────────────────────────────────────────────
_FONT = "Helvetica Neue" if platform.system() == "Darwin" else "Segoe UI"

_THEMES = {
    "light": {
        "bg": "#f5f5f4",
        "shell": "#ffffff",
        "sidebar": "#f8f8f7",
        "surface": "#ffffff",
        "surface2": "#f2f2f1",
        "surface3": "#fff3eb",
        "text": "#171a20",
        "muted": "#717782",
        "border": "#dedede",
        "shadow": "#ececea",
        "accent": "#f96302",
        "accent_dim": "#d94f00",
        "success": "#16a34a",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "sheets": "#22a65a",
        "excel": "#107c41",
    },
    "dark": {
        "bg": "#111315",
        "shell": "#181b1f",
        "sidebar": "#15181c",
        "surface": "#20242a",
        "surface2": "#2a2f36",
        "surface3": "#2c211b",
        "text": "#f3f4f6",
        "muted": "#a1a7b0",
        "border": "#343a43",
        "shadow": "#15181c",
        "accent": "#ff7a1a",
        "accent_dim": "#f96302",
        "success": "#22c55e",
        "error": "#f87171",
        "warning": "#fbbf24",
        "sheets": "#24b864",
        "excel": "#21a366",
    },
}

_theme_name = "light"


def _theme(key: str) -> str:
    return _THEMES[_theme_name][key]


def _apply_theme_globals(name: str) -> None:
    global _theme_name
    global BG, SURFACE, SURFACE2, ACCENT, ACCENT_DIM, SHEETS_CLR, EXCEL_CLR
    global TEXT, TEXT_MUTED, BORDER, SUCCESS, ERROR_CLR, WARNING

    _theme_name = name
    ctk.set_appearance_mode("dark" if name == "dark" else "light")
    BG = _theme("bg")
    SURFACE = _theme("surface")
    SURFACE2 = _theme("surface2")
    ACCENT = _theme("accent")
    ACCENT_DIM = _theme("accent_dim")
    SHEETS_CLR = _theme("sheets")
    EXCEL_CLR = _theme("excel")
    TEXT = _theme("text")
    TEXT_MUTED = _theme("muted")
    BORDER = _theme("border")
    SUCCESS = _theme("success")
    ERROR_CLR = _theme("error")
    WARNING = _theme("warning")


_apply_theme_globals(_theme_name)


def _resource_path(relative_path: str) -> str:
    """Return a path that works from source and PyInstaller bundles."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ── helpers ───────────────────────────────────────────────────────────────────

def _btn(parent, text, command, bg=None, fg=None, font_size=10, bold=False, pad_x=14, pad_y=6):
    weight = "bold" if bold else "normal"
    return tk.Button(
        parent, text=text, command=command,
        font=(_FONT, font_size, weight),
        bg=bg or SURFACE2, fg=fg or TEXT, activebackground=ACCENT, activeforeground="#fff",
        relief="flat", bd=0, padx=pad_x, pady=pad_y, cursor="hand2",
    )


def _label(parent, text, size=10, bold=False, color=None, anchor="w", **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, font=(_FONT, size, weight),
                    bg=kw.pop("bg", BG), fg=color or TEXT, anchor=anchor, **kw)


# ── modern destination cards ──────────────────────────────────────────────────

class DestinationCards(ctk.CTkFrame):
    """Two large destination cards: Google Sheets | Excel File."""

    def __init__(self, parent, initial="sheets", on_change=None):
        super().__init__(parent, fg_color="transparent")
        self._value = initial
        self._on_change = on_change
        self.grid_columnconfigure((0, 1), weight=1, uniform="dest")
        self._cards = {}
        self._build_card("sheets", 0, "▦", "Google Sheets", SHEETS_CLR)
        self._build_card("excel", 1, "▥", "Excel File", EXCEL_CLR)
        self._refresh()

    def _build_card(self, value, col, icon, title, color):
        card = ctk.CTkFrame(
            self,
            corner_radius=14,
            border_width=1,
            fg_color=_theme("surface"),
            border_color=_theme("border"),
            cursor="hand2",
        )
        card.grid(row=0, column=col, sticky="ew", padx=(0, 12) if col == 0 else (12, 0), ipady=12)
        icon_box = ctk.CTkFrame(card, width=34, height=34, corner_radius=8, fg_color=color)
        icon_box.pack(side="left", padx=(20, 14), pady=14)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=(_FONT, 18, "bold"), text_color="#ffffff").pack(expand=True)
        ctk.CTkLabel(card, text=title, font=(_FONT, 15, "bold"), text_color=_theme("text")).pack(side="left")
        ctk.CTkLabel(card, text="›", font=(_FONT, 24), text_color=_theme("muted")).pack(side="right", padx=20)
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _e, v=value: self._select(v))
        card.bind("<Button-1>", lambda _e, v=value: self._select(v))
        self._cards[value] = card

    def _select(self, value):
        if self._value == value:
            return
        self._value = value
        self._refresh()
        if self._on_change:
            self._on_change(value)

    def _refresh(self):
        for value, card in self._cards.items():
            selected = value == self._value
            card.configure(
                fg_color=_theme("surface3") if selected else _theme("surface"),
                border_color=ACCENT if selected else _theme("border"),
                border_width=2 if selected else 1,
            )

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
        self.geometry("640x560")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._parent = parent
        self._build()

    def _section(self, text):
        ctk.CTkLabel(
            self._body,
            text=text,
            font=(_FONT, 11, "bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=28, pady=(18, 8))

    def _row(self, label, var, browse_cmd=None, placeholder=""):
        ctk.CTkLabel(
            self._body,
            text=label,
            font=(_FONT, 12),
            text_color=TEXT,
        ).pack(anchor="w", padx=28)
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(6, 10))
        e = ctk.CTkEntry(
            row,
            textvariable=var,
            font=(_FONT, 13),
            height=40,
            corner_radius=10,
            fg_color=SURFACE,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text=placeholder,
        )
        if browse_cmd:
            e.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row,
                text="Browse",
                command=browse_cmd,
                height=40,
                width=92,
                corner_radius=10,
                fg_color=SURFACE2,
                hover_color=ACCENT,
                text_color=TEXT,
                font=(_FONT, 12, "bold"),
            ).pack(side="left", padx=(10, 0))
        else:
            e.pack(fill="x")

    def _build(self):
        cfg = config.load_config()

        shell = ctk.CTkFrame(
            self,
            fg_color=_theme("shell"),
            corner_radius=22,
            border_width=1,
            border_color=BORDER,
        )
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        top = ctk.CTkFrame(shell, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(
            top,
            text="Settings",
            font=(_FONT, 24, "bold"),
            text_color=TEXT,
        ).pack(side="left")
        ctk.CTkButton(
            top,
            text="Done",
            command=self.destroy,
            width=78,
            height=34,
            corner_radius=10,
            fg_color=SURFACE2,
            hover_color=BORDER,
            text_color=TEXT,
        ).pack(side="right")

        self._body = ctk.CTkFrame(shell, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

        # Google Sheets
        self._section("GOOGLE SHEETS")
        self._sheet_id  = tk.StringVar(value=cfg.get("sheet_id", ""))
        self._creds     = tk.StringVar(value=cfg.get("credentials_file", "service_account.json"))
        self._worksheet = tk.StringVar(value=cfg.get("worksheet_name", "Adjustments"))
        self._row("Sheet ID", self._sheet_id, placeholder="Paste the Google Sheet ID")
        self._row("Credentials File", self._creds, self._browse_creds)
        self._row("Worksheet Name", self._worksheet)

        # Excel
        self._section("EXCEL FILE")
        self._excel_path = tk.StringVar(value=cfg.get("excel_file_path", ""))
        self._row("Excel File Path", self._excel_path, self._browse_excel)

        # Save
        ctk.CTkButton(
            shell,
            text="Save Settings",
            command=self._save,
            height=44,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color="#ffffff",
            font=(_FONT, 14, "bold"),
        ).pack(fill="x", padx=28, pady=(4, 26))

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
            self._excel_path.set(config.normalize_excel_path(p))

    def _save(self):
        cfg = config.load_config()
        cfg["sheet_id"]        = self._sheet_id.get().strip()
        cfg["credentials_file"]= self._creds.get().strip()
        cfg["worksheet_name"]  = self._worksheet.get().strip()
        cfg["excel_file_path"] = config.normalize_excel_path(self._excel_path.get())
        config.save_config(cfg)
        self._parent.set_status("Settings saved.", SUCCESS)
        self._parent._set_sidebar_summary("Settings saved", SUCCESS)
        self.destroy()


# ── main app ──────────────────────────────────────────────────────────────────

class HDProcessorApp(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("HD Adjustment Processor")
        self._set_window_icon()
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.resizable(True, True)
        self.configure(bg=BG)

        cfg = config.load_config()
        self._dest = cfg.get("active_destination", "sheets")
        self._processing = False
        self._view = "home"
        self._history = []
        self._status_text = "Ready — drop invoices to begin"
        self._status_color = TEXT_MUTED
        self._sidebar_summary_text = "Ready"
        self._sidebar_summary_color = SUCCESS
        self._load_logo_images()
        self._build_ui()

    def _set_window_icon(self):
        try:
            self._app_icon = tk.PhotoImage(file=_resource_path("assets/app_logo.png"))
            self.iconphoto(True, self._app_icon)
        except tk.TclError:
            pass

    def _load_logo_images(self):
        self._logo_sidebar = None
        self._logo_drop = None
        try:
            logo = tk.PhotoImage(file=_resource_path("assets/app_logo.png"))
            self._logo_sidebar = logo.subsample(14, 14)
            self._logo_drop = logo.subsample(18, 18)
        except tk.TclError:
            pass

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        for child in self.winfo_children():
            child.destroy()

        try:
            self.tk.call(self._w, "configure", "-bg", BG)
        except tk.TclError:
            pass

        shell = ctk.CTkFrame(
            self,
            corner_radius=0,
            border_width=0,
            fg_color=_theme("shell"),
            border_color=BORDER,
        )
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, minsize=285)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        self._build_sidebar(shell)
        self._content = ctk.CTkFrame(shell, fg_color=_theme("shell"), corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        if self._view == "history":
            self._show_history()
        else:
            self._show_home()

        self._register_drop_targets()

    def _register_drop_targets(self):
        widgets = [self]
        if hasattr(self, "_drop_frame") and self._drop_frame.winfo_exists():
            widgets.append(self._drop_frame)
            widgets.extend(self._drop_frame.winfo_children())
        for widget in widgets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
            except (tk.TclError, AttributeError):
                pass

    def _build_sidebar(self, parent):
        side = ctk.CTkFrame(
            parent,
            fg_color=_theme("sidebar"),
            corner_radius=0,
            border_width=0,
        )
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_rowconfigure(5, weight=1)

        brand = ctk.CTkFrame(side, fg_color="transparent")
        brand.grid(row=1, column=0, sticky="ew", padx=24, pady=(34, 24))
        if self._logo_sidebar:
            tk.Label(brand, image=self._logo_sidebar, bg=_theme("sidebar"), bd=0).pack(side="left", padx=(0, 16))
        else:
            ctk.CTkFrame(brand, width=64, height=64, corner_radius=14, fg_color=ACCENT).pack(side="left", padx=(0, 16))
        name = ctk.CTkFrame(brand, fg_color="transparent")
        name.pack(side="left", fill="x")
        ctk.CTkLabel(name, text="HD Adjustment", font=(_FONT, 16, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(name, text="Processor", font=(_FONT, 16, "bold"), text_color=TEXT).pack(anchor="w")

        ctk.CTkLabel(
            side,
            text="Klear Concepts\nHome Depot Vendor Tool",
            justify="left",
            font=(_FONT, 13),
            text_color=TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 34))

        self._nav_buttons = {}
        self._nav_buttons["home"] = self._nav_button(side, "⌂", "Home", "home", 3)
        self._nav_buttons["history"] = self._nav_button(side, "◷", "History", "history", 4)
        self._nav_button(side, "⚙", "Settings", "settings", 5)

        bottom = ctk.CTkFrame(
            side,
            fg_color=_theme("surface"),
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        bottom.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 24), ipady=8)
        self._sidebar_status_icon = ctk.CTkLabel(
            bottom,
            text="✓",
            width=24,
            height=24,
            corner_radius=12,
            fg_color=self._sidebar_summary_color,
            text_color="#ffffff",
            font=(_FONT, 13, "bold"),
        )
        self._sidebar_status_icon.grid(row=0, column=0, padx=(18, 8), pady=(12, 4), sticky="w")
        self._sidebar_status_label = ctk.CTkLabel(
            bottom,
            text=self._sidebar_summary_text,
            text_color=TEXT,
            font=(_FONT, 12, "bold"),
        )
        self._sidebar_status_label.grid(row=0, column=1, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            bottom,
            text="Last processed:",
            text_color=TEXT_MUTED,
            font=(_FONT, 11),
        ).grid(row=1, column=0, columnspan=2, padx=18, sticky="w")
        last = self._history[-1]["title"] if self._history else "—"
        self._sidebar_last_label = ctk.CTkLabel(
            bottom,
            text=last,
            text_color=TEXT_MUTED,
            font=(_FONT, 12),
            wraplength=210,
            justify="left",
        )
        self._sidebar_last_label.grid(row=2, column=0, columnspan=2, padx=18, pady=(2, 12), sticky="w")
        ctk.CTkLabel(
            side,
            text=f"Version {APP_VERSION}",
            text_color=TEXT_MUTED,
            font=(_FONT, 11),
        ).grid(row=7, column=0, sticky="w", padx=24, pady=(0, 18))

    def _nav_button(self, parent, icon, text, view, row):
        selected = self._view == view
        command = self._open_settings if view == "settings" else lambda: self._switch_view(view)
        btn = ctk.CTkButton(
            parent,
            text=f"{icon}  {text}",
            command=command,
            height=48,
            corner_radius=10,
            anchor="w",
            fg_color=_theme("surface3") if selected else "transparent",
            hover_color=_theme("surface3"),
            text_color=ACCENT if selected else TEXT,
            font=(_FONT, 14, "bold" if selected else "normal"),
        )
        btn.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
        return btn

    def _build_header(self, title):
        header = ctk.CTkFrame(self._content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=48, pady=(58, 24))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=title, font=(_FONT, 26, "bold"), text_color=TEXT).grid(row=0, column=0, sticky="w")
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        ctk.CTkSwitch(
            right,
            text="Dark Mode",
            command=self._toggle_theme,
            variable=tk.BooleanVar(value=_theme_name == "dark"),
            progress_color=ACCENT,
            button_color="#ffffff",
            text_color=TEXT_MUTED,
            font=(_FONT, 12),
        ).pack(side="left", padx=(0, 16))
        ctk.CTkButton(
            right,
            text="⚙  Settings",
            command=self._open_settings,
            height=42,
            width=136,
            corner_radius=10,
            fg_color=SURFACE,
            hover_color=SURFACE2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=(_FONT, 13, "bold"),
        ).pack(side="left")
        ctk.CTkFrame(header, height=1, fg_color=BORDER).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(28, 0))

    def _show_home(self):
        self._view = "home"
        for child in self._content.winfo_children():
            child.destroy()
        self._build_header("HD Adjustment Processor")

        body = ctk.CTkFrame(self._content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=48, pady=(0, 46))
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(body, text="DESTINATION", font=(_FONT, 11, "bold"), text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self._toggle = DestinationCards(body, initial=self._dest, on_change=self._on_dest_change)
        self._toggle.grid(row=1, column=0, sticky="ew", pady=(12, 28))

        self._drop_frame = ctk.CTkFrame(
            body,
            fg_color=_theme("surface"),
            border_color=ACCENT,
            border_width=2,
            corner_radius=16,
            cursor="hand2",
        )
        self._drop_frame.grid(row=2, column=0, sticky="ew", ipady=58)
        self._drop_frame.bind("<Button-1>", self._on_click_browse)
        self._drop_frame.bind("<Enter>", lambda _e: self._drop_frame.configure(fg_color=_theme("surface3")))
        self._drop_frame.bind("<Leave>", lambda _e: self._drop_frame.configure(fg_color=_theme("surface")))

        if self._logo_drop:
            logo = tk.Label(self._drop_frame, image=self._logo_drop, bg=_theme("surface"), bd=0, cursor="hand2")
            logo.pack(pady=(10, 16))
            logo.bind("<Button-1>", self._on_click_browse)
        else:
            ctk.CTkLabel(self._drop_frame, text="⇧", font=(_FONT, 46), text_color=ACCENT).pack(pady=(10, 16))

        ctk.CTkLabel(
            self._drop_frame,
            text="Drop invoices here · up to 20 PDFs",
            font=(_FONT, 19, "bold"),
            text_color=TEXT,
        ).pack()
        ctk.CTkLabel(
            self._drop_frame,
            text="or click to browse",
            font=(_FONT, 15),
            text_color=TEXT_MUTED,
        ).pack(pady=(8, 0))

        self._progress_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._progress_frame.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        self._progress_label = ctk.CTkLabel(self._progress_frame, text="", font=(_FONT, 12), text_color=TEXT_MUTED)
        self._progress_label.pack(anchor="w")
        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame,
            height=8,
            corner_radius=6,
            progress_color=ACCENT,
            fg_color=SURFACE2,
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", pady=(6, 0))
        self._progress_frame.grid_remove()

        card = ctk.CTkFrame(
            body,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=4, column=0, sticky="ew", pady=(32, 0), ipady=18)
        ctk.CTkLabel(card, text="STATUS", font=(_FONT, 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=28, pady=(16, 12))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(0, 14))
        self._status_icon = ctk.CTkLabel(
            row,
            text="✓",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=self._status_color if self._status_color != TEXT_MUTED else SUCCESS,
            text_color="#ffffff",
            font=(_FONT, 16, "bold"),
        )
        self._status_icon.pack(side="left", padx=(0, 14))
        self._status_label = ctk.CTkLabel(
            row,
            text=self._status_text,
            font=(_FONT, 17),
            text_color=self._status_color,
            wraplength=720,
            justify="left",
        )
        self._status_label.pack(side="left", fill="x", expand=True, anchor="w")

    def _show_history(self):
        self._view = "history"
        for child in self._content.winfo_children():
            child.destroy()
        self._build_header("Processing History")
        body = ctk.CTkScrollableFrame(
            self._content,
            fg_color="transparent",
            scrollbar_button_color=SURFACE2,
            scrollbar_button_hover_color=ACCENT,
        )
        body.grid(row=1, column=0, sticky="nsew", padx=48, pady=(0, 46))
        body.grid_columnconfigure(0, weight=1)
        if not self._history:
            empty = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
            empty.grid(row=0, column=0, sticky="ew", ipady=34)
            ctk.CTkLabel(empty, text="No invoices processed in this session.", font=(_FONT, 16), text_color=TEXT_MUTED).pack()
            return
        for i, item in enumerate(reversed(self._history)):
            card = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
            card.grid(row=i, column=0, sticky="ew", pady=(0, 12), ipady=8)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=item["title"], font=(_FONT, 15, "bold"), text_color=TEXT).grid(row=0, column=0, sticky="w", padx=18, pady=(12, 2))
            ctk.CTkLabel(card, text=item["detail"], font=(_FONT, 12), text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

    # ── callbacks ─────────────────────────────────────────────────────────

    def set_status(self, msg: str, color: str = TEXT_MUTED):
        self._status_text = msg
        self._status_color = color
        if hasattr(self, "_status_label") and self._status_label.winfo_exists():
            self._status_label.configure(text=msg, text_color=color)
        if hasattr(self, "_status_icon") and self._status_icon.winfo_exists():
            icon_color = color if color not in (TEXT_MUTED, TEXT) else SUCCESS
            icon_text = "!" if color in (ERROR_CLR, WARNING) else "✓"
            self._status_icon.configure(text=icon_text, fg_color=icon_color)
        self.update_idletasks()

    def set_last_processed(self, invoice: str, debit_count: int):
        ts = datetime.now().strftime("%I:%M %p").lstrip("0")
        items = f"{debit_count} line item{'s' if debit_count != 1 else ''}"
        title = f"Invoice #{invoice}"
        detail = f"{items} · {ts} · {'Google Sheets' if self._dest == 'sheets' else 'Excel File'}"
        self._history.append({"title": title, "detail": detail})
        if len(self._history) > 50:
            self._history = self._history[-50:]
        if hasattr(self, "_sidebar_last_label") and self._sidebar_last_label.winfo_exists():
            self._sidebar_last_label.configure(text=title)

    def _show_progress(self, label: str, fraction: float):
        if hasattr(self, "_progress_frame") and self._progress_frame.winfo_exists():
            self._progress_frame.grid()
            self._progress_label.configure(text=label)
            self._progress_bar.set(fraction)
        self.update_idletasks()

    def _hide_progress(self):
        if hasattr(self, "_progress_frame") and self._progress_frame.winfo_exists():
            self._progress_frame.grid_remove()
        self.update_idletasks()

    def _set_sidebar_summary(self, text: str, color: str = SUCCESS):
        self._sidebar_summary_text = text
        self._sidebar_summary_color = color
        if hasattr(self, "_sidebar_status_label") and self._sidebar_status_label.winfo_exists():
            self._sidebar_status_label.configure(text=text)
        if hasattr(self, "_sidebar_status_icon") and self._sidebar_status_icon.winfo_exists():
            self._sidebar_status_icon.configure(fg_color=color)

    def _switch_view(self, view: str):
        self._view = view
        self._build_ui()

    def _toggle_theme(self):
        _apply_theme_globals("dark" if _theme_name == "light" else "light")
        self._load_logo_images()
        self._build_ui()

    def _on_dest_change(self, value: str):
        self._dest = value
        cfg = config.load_config()
        cfg["active_destination"] = value
        config.save_config(cfg)
        self._set_sidebar_summary("Destination saved", SUCCESS)

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
        else:
            self.set_status("No PDF files found in the drop. Use PDF invoices only.", WARNING)

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
            cfg["excel_file_path"] = config.normalize_excel_path(cfg["excel_file_path"])
            config.save_config(cfg)
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
            try:
                is_duplicate = bool(inv_num and writer.find_duplicate(inv_num))
            except Exception as e:
                err = str(e)
                self.after(0, lambda e=err: self.set_status(
                    f"Excel check error: {e}", ERROR_CLR))
                self.after(0, lambda: self._hide_progress())
                self.after(0, lambda: setattr(self, '_processing', False))
                return

            if is_duplicate:
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
