import json
import os
import sys

if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_APP_DIR, "config.json")

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
    return data


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
