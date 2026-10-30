from __future__ import annotations

import json
from pathlib import Path

import pytest

from predictive_maintenance.promotion import (
    evaluate_candidate,
    promote_candidate,
    rollback_release,
)


def _metrics(validation_ap: float = 0.92) -> dict:
    return {
        "validation": {"average_precision": validation_ap},
        "test": {
            "average_precision": 0.93,
            "precision": 0.94,
            "false_positive_rows_per_machine_week": 0.04,
            "failure_events": {"event_recall": 0.98},
        },
    }


def _write_config(tmp_path: Path, candidate_ap: float = 0.92) -> Path:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    candidate_model = artifacts / "candidate.joblib"
    candidate_model.write_bytes(b"candidate-model")
    candidate = {
        "model": "challenger",
        "model_path": str(candidate_model),
        "threshold": 0.6,
        "selection_metric": "average_precision",
        "selection_value": candidate_ap,
        "mlflow_run_id": "candidate1234567890",
        "feature_sha256": "feature-v2",
        "metrics": _metrics(candidate_ap),
    }
    incumbent = {
        "model": "incumbent",
        "model_path": "incumbent.joblib",
        "threshold": 0.5,
        "selection_metric": "average_precision",
        "selection_value": 0.91,
        "mlflow_run_id": "incumbent123456789",
        "feature_sha256": "feature-v1",
        "metrics": _metrics(0.91),
    }
    candidate_path = artifacts / "candidate.json"
    champion_path = artifacts / "champion.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    champion_path.write_text(json.dumps(incumbent), encoding="utf-8")
    config_path = tmp_path / "promotion.toml"
    config_path.write_text(
        f"""
[candidate]
manifest_path = "{candidate_path.as_posix()}"
comparison_path = "{(tmp_path / 'candidate-comparison.json').as_posix()}"

[incumbent]
manifest_path = "{champion_path.as_posix()}"
comparison_path = "{(tmp_path / 'incumbent-comparison.json').as_posix()}"

[gate]
minimum_validation_average_precision = 0.85
maximum_validation_regression = 0.005
minimum_test_average_precision = 0.85
minimum_test_precision = 0.90
minimum_test_event_recall = 0.95
maximum_test_false_positives_per_machine_week = 0.10

[release]
directory = "{(artifacts / 'releases').as_posix()}"
decision_report_directory = "{(tmp_path / 'reports').as_posix()}"
""".strip(),
        encoding="utf-8",
    )
    return config_path


def test_approved_candidate_can_be_promoted_and_rolled_back(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    decision = evaluate_candidate(config_path)
    champion = promote_candidate(config_path, release_id="release-001")
    rolled_back = rollback_release(config_path, "release-001")

    assert decision["decision"] == "approved"
    assert all(item["passed"] for item in decision["checks"])
    assert champion["release_id"] == "release-001"
    assert (tmp_path / "artifacts/releases/release-001/model.joblib").is_file()
    assert rolled_back["release_id"] == "release-001"
    assert "rolled_back_at" in rolled_back
    assert (tmp_path / "reports/decision.json").is_file()
    assert (tmp_path / "reports/README.md").is_file()


def test_rejected_candidate_cannot_be_promoted(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, candidate_ap=0.80)

    decision = evaluate_candidate(config_path)

    assert decision["decision"] == "rejected"
    with pytest.raises(ValueError, match="failed promotion gates"):
        promote_candidate(config_path, release_id="rejected")
