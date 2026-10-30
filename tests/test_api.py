from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import joblib
from fastapi.testclient import TestClient

from predictive_maintenance.data.features import build_feature_table
from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.split import assign_machine_splits
from predictive_maintenance.models.baseline import feature_columns
from predictive_maintenance.models.challenger import build_challenger_model
from predictive_maintenance.serving.app import create_app
from predictive_maintenance.serving.schemas import FeatureVector


def test_inference_api_loads_champion_and_validates_requests(
    tmp_path: Path, raw_tables: RawTables
) -> None:
    frame = build_feature_table(raw_tables)
    frame, _ = assign_machine_splits(frame)
    train = frame.loc[frame["split"] == "train"]
    test = frame.loc[frame["split"] == "test"]
    numerical_columns, categorical_columns = feature_columns(train)
    features = numerical_columns + categorical_columns
    model = build_challenger_model(
        numerical_columns,
        categorical_columns,
        max_iterations=5,
        min_samples_leaf=5,
    )
    model.fit(train[features], train["failure_within_horizon"])

    model_path = tmp_path / "releases" / "release-001" / "model.joblib"
    model_path.parent.mkdir(parents=True)
    manifest_path = tmp_path / "champion.json"
    joblib.dump(model, model_path)
    manifest_path.write_text(
        json.dumps(
            {
                "model": "hist_gradient_boosting",
                "model_path": "releases/release-001/model.joblib",
                "threshold": 0.5,
                "selection_metric": "average_precision",
                "selection_value": 0.9,
                "mlflow_run_id": "1234567890abcdef",
            }
        ),
        encoding="utf-8",
    )
    payload = FeatureVector.model_validate(test.iloc[0][features].to_dict()).model_dump(
        mode="json"
    )

    database_path = tmp_path / "predictions.db"
    request_observation = {
        "observation_id": "machine-6-20260101T000000Z",
        "machine_id": 6,
        "observed_at": "2026-01-01T00:00:00Z",
        "features": payload,
    }
    with TestClient(create_app(manifest_path, database_path)) as client:
        health = client.get("/health")
        info = client.get("/v1/model-info")
        prediction = client.post(
            "/v1/predict", json={"observations": [request_observation]}
        )
        invalid_payload = dict(payload)
        invalid_payload["volt_std_3h"] = -1
        invalid = client.post(
            "/v1/predict",
            json={
                "observations": [
                    {**request_observation, "features": invalid_payload}
                ]
            },
        )
        duplicate = client.post(
            "/v1/predict", json={"observations": [request_observation]}
        )

    assert health.status_code == 200
    assert health.json() == {
        "status": "ready",
        "model": "hist_gradient_boosting",
        "prediction_logging": True,
    }
    assert info.status_code == 200
    assert info.json()["feature_count"] == len(features)
    assert prediction.status_code == 200
    assert len(prediction.json()["predictions"]) == 1
    assert prediction.json()["predictions"][0]["observation_id"] == request_observation["observation_id"]
    assert 0 <= prediction.json()["predictions"][0]["failure_probability"] <= 1
    assert invalid.status_code == 422
    assert duplicate.status_code == 409
    with sqlite3.connect(database_path) as connection:
        stored = connection.execute(
            "SELECT observation_id, model_name, features_json FROM prediction_log"
        ).fetchall()
    assert len(stored) == 1
    assert stored[0][0] == request_observation["observation_id"]
    assert stored[0][1] == "hist_gradient_boosting"
    assert json.loads(stored[0][2])["volt"] == payload["volt"]
