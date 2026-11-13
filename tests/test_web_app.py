from __future__ import annotations

from fastapi.testclient import TestClient

from predictive_maintenance.web.app import create_web_app


def test_dashboard_serves_runtime_configuration(monkeypatch) -> None:
    monkeypatch.setenv("PREDMAINT_API_URL", "https://api.example.test")
    monkeypatch.setenv("PREDMAINT_FIREBASE_API_KEY", "public-firebase-key")
    monkeypatch.setenv("PREDMAINT_FIREBASE_PROJECT_ID", "demo-project")

    with TestClient(create_web_app()) as client:
        index = client.get("/")
        config = client.get("/config.js")
        health = client.get("/health")
        styles = client.get("/static/styles.css")

    assert index.status_code == 200
    assert "RailSense" in index.text
    assert "vectron-predictive-maintenance.png" in styles.text
    assert config.status_code == 200
    assert "https://api.example.test" in config.text
    assert "public-firebase-key" in config.text
    assert config.headers["cache-control"] == "no-store"
    assert health.json() == {"status": "ready"}
