from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from predictive_maintenance.serving.authentication import (
    AuthenticatedUser,
    build_identity_guard,
)


def test_firebase_guard_accepts_gateway_forwarded_token() -> None:
    def verify(token: str) -> dict[str, str]:
        if token != "valid-token":
            raise ValueError("invalid token")
        return {"uid": "user-123", "email": "operator@example.com"}

    guard = build_identity_guard("demo-project", token_verifier=verify)
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = Depends(guard)) -> dict[str, str | None]:
        return {"uid": user.uid, "email": user.email}

    with TestClient(app) as client:
        missing = client.get("/protected")
        direct = client.get(
            "/protected", headers={"Authorization": "Bearer valid-token"}
        )
        forwarded = client.get(
            "/protected",
            headers={"X-Forwarded-Authorization": "Bearer valid-token"},
        )
        invalid = client.get(
            "/protected", headers={"Authorization": "Bearer invalid"}
        )

    assert missing.status_code == 401
    assert direct.json() == {"uid": "user-123", "email": "operator@example.com"}
    assert forwarded.status_code == 200
    assert invalid.status_code == 401


def test_identity_guard_preserves_local_anonymous_mode() -> None:
    guard = build_identity_guard(None)
    user = guard()
    assert user == AuthenticatedUser(uid="local-anonymous", email=None)
