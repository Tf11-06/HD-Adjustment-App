import json
import os
import tempfile
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


def test_save_and_load_roundtrip():
    original = {"sheet_id": "sheet999", "credentials_file": "creds.json", "worksheet_name": "Adjustments"}
    config.save_config(original)
    loaded = config.load_config()
    assert loaded == original
