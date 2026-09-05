import importlib.util

from fastapi.testclient import TestClient

from narra.app import app


def test_auto_scan_module_exists():
    assert importlib.util.find_spec("narra.autoscan") is not None


def test_settings_exposes_auto_scan_controls():
    with TestClient(app) as client:
        response = client.get("/settings")
    assert response.status_code == 200
    assert "Auto scan" in response.text
    assert "Scan All Now" in response.text
    for minutes in (1, 5, 10, 15, 30, 60):
        assert f'value="{minutes}"' in response.text
