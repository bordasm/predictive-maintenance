"""Issue short-lived, rate-limited Firebase guest sessions."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4


class GuestSessionRateLimited(Exception):
    """Raised when a source address creates too many guest sessions."""


@dataclass(frozen=True)
class GuestSession:
    custom_token: str
    session_id: str
    expires_in: int = 3600
    max_batch_size: int = 10
    max_observations: int = 30


class GuestSessionService:
    """Create Firebase custom tokens and persist anti-abuse counters."""

    def __init__(self) -> None:
        from google.cloud import firestore

        project_id = os.environ.get("PREDMAINT_FIREBASE_PROJECT_ID") or None
        self._firestore = firestore
        self._client = firestore.Client(project=project_id)
        self._collection = os.environ.get(
            "PREDMAINT_GUEST_SESSION_COLLECTION", "guest_session_limits"
        )

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def issue(self, *, client_ip: str) -> GuestSession:
        from firebase_admin import auth
        import firebase_admin

        now = datetime.now(UTC)
        normalized_ip = client_ip.strip() or "unknown"
        limits = self._client.collection(self._collection)
        ip_ref = limits.document(f"ip-{self._digest(normalized_ip)}")
        global_ref = limits.document(f"global-{now:%Y-%m-%d}")
        transaction = self._client.transaction()

        @self._firestore.transactional
        def reserve(txn) -> None:
            ip_snapshot = ip_ref.get(transaction=txn)
            global_snapshot = global_ref.get(transaction=txn)
            ip_data = ip_snapshot.to_dict() or {}
            window_started = ip_data.get("window_started_at")
            count = int(ip_data.get("count", 0))
            if not window_started or now - window_started >= timedelta(hours=1):
                window_started, count = now, 0
            if count >= 3:
                raise GuestSessionRateLimited

            global_data = global_snapshot.to_dict() or {}
            global_count = int(global_data.get("count", 0))
            if global_count >= 100:
                raise GuestSessionRateLimited

            txn.set(
                ip_ref,
                {
                    "window_started_at": window_started,
                    "count": count + 1,
                    "expires_at": now + timedelta(hours=2),
                },
            )
            txn.set(
                global_ref,
                {
                    "day": f"{now:%Y-%m-%d}",
                    "count": global_count + 1,
                    "expires_at": now + timedelta(days=2),
                },
            )

        reserve(transaction)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(
                options={"projectId": os.environ.get("PREDMAINT_FIREBASE_PROJECT_ID")}
            )

        session_id = uuid4().hex
        token = auth.create_custom_token(
            "predmaint-public-demo",
            {
                "guest": True,
                "guest_session": session_id,
                "guest_limit": 30,
            },
        )
        return GuestSession(
            custom_token=token.decode("utf-8") if isinstance(token, bytes) else str(token),
            session_id=session_id,
        )
