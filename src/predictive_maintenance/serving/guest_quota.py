"""Transactional inference quotas for public guest sessions."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta


class GuestQuotaExceeded(Exception):
    """Raised when a guest exceeds a batch or session quota."""


class GuestQuotaService:
    max_batch_size = 10
    max_observations = 30

    def __init__(self, project_id: str | None = None) -> None:
        from google.cloud import firestore

        self._firestore = firestore
        self._client = firestore.Client(project=project_id)
        self._collection = os.environ.get(
            "PREDMAINT_GUEST_QUOTA_COLLECTION", "guest_inference_quotas"
        )

    def consume(self, *, session_id: str, observation_count: int) -> int:
        if not session_id or observation_count < 1:
            raise GuestQuotaExceeded
        if observation_count > self.max_batch_size:
            raise GuestQuotaExceeded

        now = datetime.now(UTC)
        document = self._client.collection(self._collection).document(session_id)
        transaction = self._client.transaction()

        @self._firestore.transactional
        def update(txn) -> int:
            snapshot = document.get(transaction=txn)
            data = snapshot.to_dict() or {}
            used = int(data.get("observations", 0))
            if used + observation_count > self.max_observations:
                raise GuestQuotaExceeded
            new_total = used + observation_count
            txn.set(
                document,
                {
                    "observations": new_total,
                    "updated_at": now,
                    "expires_at": now + timedelta(hours=2),
                },
            )
            return self.max_observations - new_total

        return update(transaction)
