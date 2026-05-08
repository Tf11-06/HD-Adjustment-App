import json
import os
import pytest
import config


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point CONFIG_FILE at a temp path for every test."""
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config.json"))


def test_load_config_returns_defaults_when_file_missing():
    cfg = config.load_config()
    assert cfg["sheet_id"] == ""
    assert cfg["credentials_file"] == "service_account.json"
    assert cfg["worksheet_name"] == "Adjustments"


def test_load_config_reads_existing_file():
    data = {"sheet_id": "abc123", "credentials_file": "creds.json", "worksheet_name": "Sheet1"}
    with open(config.CONFIG_FILE, "w") as f:
        json.dump(data, f)
    cfg = config.load_config()
    assert cfg["sheet_id"] == "abc123"
    assert cfg["credentials_file"] == "creds.json"
    assert cfg["worksheet_name"] == "Sheet1"


def test_load_config_fills_missing_keys():
    with open(config.CONFIG_FILE, "w") as f:
        json.dump({"sheet_id": "abc"}, f)
    cfg = config.load_config()
    assert cfg["credentials_file"] == "service_account.json"
    assert cfg["worksheet_name"] == "Adjustments"


def test_save_config_writes_json():
    config.save_config({"sheet_id": "xyz", "credentials_file": "sa.json", "worksheet_name": "Data"})
    with open(config.CONFIG_FILE) as f:
        saved = json.load(f)
    assert saved["sheet_id"] == "xyz"


def test_save_config_creates_config_directory(tmp_path, monkeypatch):
    nested = tmp_path / "Klear Concepts" / "HD Adjustment Processor" / "config.json"
    monkeypatch.setattr(config, "CONFIG_FILE", str(nested))
    config.save_config({"sheet_id": "xyz"})
    assert nested.exists()


def test_save_and_load_roundtrip():
    original = {
        "sheet_id": "sheet999", "credentials_file": "creds.json",
        "worksheet_name": "Adjustments", "excel_file_path": "",
        "active_destination": "sheets",
    }
    config.save_config(original)
    loaded = config.load_config()
    assert loaded == original


def test_normalize_excel_path_adds_xlsx_when_missing(tmp_path):
    output = tmp_path / "hd test"
    assert config.normalize_excel_path(str(output)) == str(output) + ".xlsx"


def test_normalize_excel_path_replaces_non_xlsx_extension(tmp_path):
    output = tmp_path / "hd test.xls"
    assert config.normalize_excel_path(str(output)) == str(tmp_path / "hd test.xlsx")


def test_save_config_normalizes_excel_path(tmp_path):
    output = tmp_path / "hd test"
    config.save_config({"excel_file_path": str(output)})
    with open(config.CONFIG_FILE) as f:
        saved = json.load(f)
    assert saved["excel_file_path"] == str(output) + ".xlsx"


def test_load_config_normalizes_existing_excel_path(tmp_path):
    output = tmp_path / "hd test"
    with open(config.CONFIG_FILE, "w") as f:
        json.dump({"excel_file_path": str(output)}, f)
    loaded = config.load_config()
    assert loaded["excel_file_path"] == str(output) + ".xlsx"


def test_resolve_credentials_path_keeps_absolute_path(tmp_path):
    creds = tmp_path / "service_account.json"
    assert config.resolve_credentials_path(str(creds)) == str(creds)


def test_resolve_credentials_path_defaults_relative_to_app_dir():
    expected = os.path.join(config._APP_DIR, "service_account.json")
    assert config.resolve_credentials_path("service_account.json") == expected
