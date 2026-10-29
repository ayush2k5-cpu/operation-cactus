from backend.gkmkb.settings import load_settings


def test_api_host_defaults_to_local_only(monkeypatch):
    monkeypatch.delenv("API_HOST", raising=False)
    assert load_settings().api_host == "127.0.0.1"


def test_api_host_from_environment(monkeypatch):
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    assert load_settings().api_host == "0.0.0.0"
