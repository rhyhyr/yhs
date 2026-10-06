from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from yhs.api.routes import user as user_module


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(user_module, "get_settings", lambda: SimpleNamespace(data_dir=tmp_path))
    app = FastAPI()
    app.include_router(user_module.router)
    return TestClient(app)


def test_profile_roundtrip_is_isolated_per_client(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    body = {"name": "김", "languages": ["ko", "en"]}

    assert c.get("/api/user/profile", headers={"X-Client-Id": "a"}).json() == {}
    assert c.put("/api/user/profile", json=body, headers={"X-Client-Id": "a"}).status_code == 200
    assert c.get("/api/user/profile", headers={"X-Client-Id": "a"}).json() == body
    assert c.get("/api/user/profile", headers={"X-Client-Id": "b"}).json() == {}


def test_rejects_missing_client_id_and_bad_languages(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    assert c.get("/api/user/profile").status_code == 400
    bad = c.put("/api/user/profile", json={"languages": "ko"}, headers={"X-Client-Id": "a"})
    assert bad.status_code == 422
