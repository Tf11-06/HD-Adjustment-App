import json
import os
import platform
import sys

if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _config_dir() -> str:
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Klear Concepts", "HD Adjustment Processor")
    if system == "Darwin":
        return os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "Klear Concepts",
            "HD Adjustment Processor",
        )
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "Klear Concepts", "HD Adjustment Processor")


CONFIG_FILE = os.path.join(_config_dir(), "config.json")

_DEFAULTS = {
    "sheet_id": "",
    "credentials_file": "service_account.json",
    "worksheet_name": "Adjustments",
    "excel_file_path": "",
    "active_destination": "sheets",  # "sheets" | "excel"
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return _DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _DEFAULTS.copy()
    if not isinstance(data, dict):
        return _DEFAULTS.copy()
    for key, val in _DEFAULTS.items():
        data.setdefault(key, val)
    data["excel_file_path"] = normalize_excel_path(data.get("excel_file_path", ""))
    return data


def save_config(data: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    data = data.copy()
    data["excel_file_path"] = normalize_excel_path(data.get("excel_file_path", ""))
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def resolve_credentials_path(path: str) -> str:
    """
    Resolve the configured credentials file path.

    Browse selections are stored as absolute paths. The default
    service_account.json remains relative to the app/source directory for
    development and backwards-compatible manual setups.
    """
    path = os.path.expanduser(path or _DEFAULTS["credentials_file"])
    if os.path.isabs(path):
        return path
    return os.path.join(_APP_DIR, path)


def normalize_excel_path(path: str) -> str:
    """Return an Excel output path with a .xlsx extension."""
    path = os.path.expanduser((path or "").strip())
    if not path:
        return ""
    root, ext = os.path.splitext(path)
    if ext.lower() == ".xlsx":
        return path
    if ext:
        return root + ".xlsx"
    return path + ".xlsx"
