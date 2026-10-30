"""SQLite persistence for traceable online predictions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from predictive_maintenance.serving.schemas import PredictionObservation


class DuplicateObservationError(ValueError):
    """Raised when an observation ID has already been logged."""


@dataclass(frozen=True)
class PredictionRecord:
    observation: PredictionObservation
    probability: float
    alert: bool


class PredictionStore:
    """Small, process-safe SQLite store opened once per transaction."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_log (
                    observation_id TEXT PRIMARY KEY,
                    machine_id INTEGER NOT NULL,
                    observed_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    mlflow_run_id TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    failure_probability REAL NOT NULL,
                    alert INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    features_json TEXT NOT NULL
                )
                """
            )

    def write_batch(
        self,
        records: list[PredictionRecord],
        *,
        model_name: str,
        model_version: str,
        mlflow_run_id: str,
        threshold: float,
        latency_ms: float,
    ) -> None:
        received_at = datetime.now(UTC).isoformat()
        row_latency = latency_ms / len(records)
        rows = [
            (
                record.observation.observation_id,
                record.observation.machine_id,
                record.observation.observed_at.isoformat(),
                received_at,
                model_name,
                model_version,
                mlflow_run_id,
                threshold,
                record.probability,
                int(record.alert),
                row_latency,
                json.dumps(record.observation.features.model_dump(), sort_keys=True),
            )
            for record in records
        ]
        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.executemany(
                    """
                    INSERT INTO prediction_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateObservationError(
                "At least one observation_id has already been logged"
            ) from error

    def read_predictions(self, *, limit: int | None = None) -> pd.DataFrame:
        query = "SELECT * FROM prediction_log ORDER BY received_at"
        parameters: tuple[int, ...] = ()
        if limit is not None:
            query += " DESC LIMIT ?"
            parameters = (limit,)
        with sqlite3.connect(self.database_path) as connection:
            frame = pd.read_sql_query(query, connection, params=parameters)
        if frame.empty:
            return frame
        features = pd.json_normalize(frame.pop("features_json").map(json.loads))
        return pd.concat([frame.reset_index(drop=True), features], axis=1)
