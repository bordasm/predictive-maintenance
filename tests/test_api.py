from __future__ import annotations

import json
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

    model_path = tmp_path / "champion.joblib"
    manifest_path = tmp_path / "champion.json"
    joblib.dump(model, model_path)
    manifest_path.write_text(
        json.dumps(
            {
                "model": "hist_gradient_boosting",
                "model_path": "artifacts\\experiments\\champion.joblib",
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

    with TestClient(create_app(manifest_path)) as client:
        health = client.get("/health")
        info = client.get("/v1/model-info")
        prediction = client.post(
            "/v1/predict", json={"observations": [payload]}
        )
        invalid_payload = dict(payload)
        invalid_payload["volt_std_3h"] = -1
        invalid = client.post(
            "/v1/predict", json={"observations": [invalid_payload]}
        )

    assert health.status_code == 200
    assert health.json() == {
        "status": "ready",
        "model": "hist_gradient_boosting",
    }
    assert info.status_code == 200
    assert info.json()["feature_count"] == len(features)
    assert prediction.status_code == 200
    assert len(prediction.json()["predictions"]) == 1
    assert 0 <= prediction.json()["predictions"][0]["failure_probability"] <= 1
    assert invalid.status_code == 422
