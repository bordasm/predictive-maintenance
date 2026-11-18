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
        script = client.get("/static/app.js")

    assert index.status_code == 200
    assert "RailSense - not only for railways (this is a demo)" in index.text
    assert 'data-language="en"' in index.text
    assert 'data-language="hu"' in index.text
    assert index.text.count('class="flag-icon"') == 2
    assert 'id="input-details-modal"' in index.text
    assert 'id="logout-modal"' in index.text
    assert 'id="decision-explanation"' in index.text
    assert "vectron-predictive-maintenance.png" in styles.text
    assert script.status_code == 200
    assert 'const DEFAULT_LANGUAGE = "en"' in script.text
    assert "Gépállapot-irányítópult" in script.text
    assert "A következő 24 órában hiba várható." in script.text
    assert "What does one input row contain?" in script.text
    assert "Valóban ki akar lépni?" in script.text
    assert 'openModal("logout-modal"' in script.text
    assert config.status_code == 200
    assert "https://api.example.test" in config.text
    assert "public-firebase-key" in config.text
    assert config.headers["cache-control"] == "no-store"
    assert health.json() == {"status": "ready"}
