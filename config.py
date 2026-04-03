import json
import os
import sys

# When frozen by PyInstaller, store config next to the exe, not in the temp bundle dir.
if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_APP_DIR, "config.json")

_DEFAULTS = {
    "sheet_id": "",
    "credentials_file": "service_account.json",
    "worksheet_name": "Adjustments",
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return _DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: config.json is malformed. Using defaults.")
        return _DEFAULTS.copy()
    if not isinstance(data, dict):
        print(f"Warning: config.json has unexpected format. Using defaults.")
        return _DEFAULTS.copy()
    for key, val in _DEFAULTS.items():
        data.setdefault(key, val)
    return data


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
