from __future__ import annotations

from fastapi.testclient import TestClient

from predictive_maintenance.web.access_requests import (
    AccessRequestRateLimited,
    AccessRequestResult,
)
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
    assert 'id="access-request-modal"' in index.text
    assert 'maxlength="100"' in index.text
    assert 'maxlength="1000"' in index.text
    assert 'id="decision-explanation"' in index.text
    assert 'id="result-model"' in index.text
    assert "vectron-predictive-maintenance.png" in styles.text
    assert script.status_code == 200
    assert 'const DEFAULT_LANGUAGE = "en"' in script.text
    assert "Gépállapot-irányítópult" in script.text
    assert "A következő 24 órában hiba várható." in script.text
    assert "What input does the selected model receive?" in script.text
    assert 'id="model-select"' in index.text
    assert 'apiFetch("/v1/models")' in script.text
    assert 'M${item.sample.machine_id} · ${modelLabel(item.model)}' in script.text
    assert "Valóban ki akar lépni?" in script.text
    assert 'openModal("logout-modal"' in script.text
    assert "Nincs még felhasználója?" in script.text
    assert "no password is sent by email" in script.text
    assert config.status_code == 200
    assert "https://api.example.test" in config.text
    assert "public-firebase-key" in config.text
    assert config.headers["cache-control"] == "no-store"
    assert health.json() == {"status": "ready"}


class RecordingAccessRequestService:
    def __init__(self, *, limited: bool = False) -> None:
        self.limited = limited
        self.calls: list[dict[str, str]] = []

    def submit(self, **kwargs: str) -> AccessRequestResult:
        if self.limited:
            raise AccessRequestRateLimited
        self.calls.append(kwargs)
        return AccessRequestResult("request-123", True)


def test_access_request_is_validated_and_forwarded() -> None:
    app = create_web_app()
    service = RecordingAccessRequestService()
    app.state.access_request_service = service

    with TestClient(app) as client:
        response = client.post(
            "/access-requests",
            headers={"X-Forwarded-For": "203.0.113.8"},
            json={
                "email": " Visitor@Example.com ",
                "message": " I would like to evaluate the demo. ",
                "locale": "en",
                "website": "",
            },
        )
        invalid = client.post(
            "/access-requests",
            json={"email": "not-an-email", "message": "Hello", "locale": "en"},
        )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "notification": "sent"}
    assert service.calls == [
        {
            "email": "visitor@example.com",
            "message": "I would like to evaluate the demo.",
            "locale": "en",
            "client_ip": "203.0.113.8",
        }
    ]
    assert invalid.status_code == 422


def test_access_request_honeypot_and_rate_limit() -> None:
    app = create_web_app()
    service = RecordingAccessRequestService(limited=True)
    app.state.access_request_service = service

    with TestClient(app) as client:
        bot = client.post(
            "/access-requests",
            json={
                "email": "bot@example.com",
                "message": "Bot message",
                "locale": "en",
                "website": "https://spam.example",
            },
        )
        limited = client.post(
            "/access-requests",
            json={"email": "person@example.com", "message": "Hello", "locale": "hu"},
        )

    assert bot.status_code == 202
    assert service.calls == []
    assert limited.status_code == 429
