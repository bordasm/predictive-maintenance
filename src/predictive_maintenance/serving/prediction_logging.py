"""Prediction persistence adapters for local SQLite and Cloud Firestore."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from predictive_maintenance.monitoring.store import (
    DuplicateObservationError,
    PredictionRecord,
    PredictionStore,
)
from predictive_maintenance.serving.authentication import AuthenticatedUser


class PredictionLogger(Protocol):
    enabled: bool

    def write_batch(
        self,
        records: Sequence[PredictionRecord],
        *,
        model_name: str,
        model_version: str,
        mlflow_run_id: str,
        threshold: float,
        latency_ms: float,
        user: AuthenticatedUser,
    ) -> None: ...


class SQLitePredictionLogger:
    enabled = True

    def __init__(self, store: PredictionStore) -> None:
        self.store = store

    def write_batch(
        self,
        records: Sequence[PredictionRecord],
        *,
        model_name: str,
        model_version: str,
        mlflow_run_id: str,
        threshold: float,
        latency_ms: float,
        user: AuthenticatedUser,
    ) -> None:
        del user
        self.store.write_batch(
            list(records),
            model_name=model_name,
            model_version=model_version,
            mlflow_run_id=mlflow_run_id,
            threshold=threshold,
            latency_ms=latency_ms,
        )


class FirestorePredictionLogger:
    enabled = True

    def __init__(self, project_id: str, collection: str) -> None:
        from google.cloud import firestore

        self.client = firestore.Client(project=project_id)
        self.collection = self.client.collection(collection)

    def write_batch(
        self,
        records: Sequence[PredictionRecord],
        *,
        model_name: str,
        model_version: str,
        mlflow_run_id: str,
        threshold: float,
        latency_ms: float,
        user: AuthenticatedUser,
    ) -> None:
        from google.api_core.exceptions import AlreadyExists
        from google.cloud import firestore

        batch = self.client.batch()
        for record in records:
            document = self.collection.document(record.observation.observation_id)
            batch.create(
                document,
                {
                    "observation_id": record.observation.observation_id,
                    "machine_id": record.observation.machine_id,
                    "observed_at": record.observation.observed_at,
                    "features": record.observation.features.model_dump(mode="json"),
                    "failure_probability": record.probability,
                    "alert": record.alert,
                    "model_name": model_name,
                    "model_version": model_version,
                    "mlflow_run_id": mlflow_run_id,
                    "threshold": threshold,
                    "latency_ms": latency_ms,
                    "user_uid": user.uid,
                    "user_email": user.email,
                    "created_at": firestore.SERVER_TIMESTAMP,
                },
            )
        try:
            batch.commit()
        except AlreadyExists as error:
            raise DuplicateObservationError(
                "One or more observation IDs have already been logged"
            ) from error


class DisabledPredictionLogger:
    enabled = False

    def write_batch(self, records: Sequence[PredictionRecord], **_: object) -> None:
        del records


def build_prediction_logger(
    backend: str,
    *,
    database_path: str,
    project_id: str | None,
    collection: str,
) -> PredictionLogger:
    normalized = backend.strip().lower()
    if normalized == "firestore":
        if not project_id:
            raise ValueError("Firestore prediction logging requires a project ID")
        return FirestorePredictionLogger(project_id, collection)
    if normalized == "none":
        return DisabledPredictionLogger()
    if normalized != "sqlite":
        raise ValueError(f"Unknown prediction logging backend: {backend}")
    store = PredictionStore(database_path)
    store.initialize()
    return SQLitePredictionLogger(store)
