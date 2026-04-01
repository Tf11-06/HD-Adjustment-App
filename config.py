import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

_DEFAULTS = {
    "sheet_id": "",
    "credentials_file": "service_account.json",
    "worksheet_name": "Adjustments",
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return _DEFAULTS.copy()
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    for key, val in _DEFAULTS.items():
        data.setdefault(key, val)
    return data


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
