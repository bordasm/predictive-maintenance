"""Run the first end-to-end predictive-maintenance milestone."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tomllib
from pathlib import Path

import joblib
import sklearn

from predictive_maintenance.data.features import build_feature_table
from predictive_maintenance.data.load import load_raw_tables
from predictive_maintenance.data.split import assign_machine_splits
from predictive_maintenance.data.validate import validate_raw_tables
from predictive_maintenance.evaluation.metrics import (
    choose_f1_threshold,
    classification_report,
    failure_event_report,
)
from predictive_maintenance.models.baseline import (
    build_baseline_model,
    feature_columns,
    predict_probabilities,
)


def _load_config(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raw_data_manifest(raw_dir: Path) -> dict[str, dict[str, int | str]]:
    return {
        path.name: {"bytes": path.stat().st_size, "sha256": _file_sha256(path)}
        for path in sorted(raw_dir.glob("*.csv"))
    }


def _markdown_report(report: dict[str, object]) -> str:
    validation = report["validation"]
    test = report["test"]
    events = test["failure_events"]
    event_recall = (
        f"{events['event_recall']:.1%}"
        if events["event_recall"] is not None
        else "not available"
    )
    lead_time = (
        f"{events['median_lead_time_hours']:.1f} hours"
        if events["median_lead_time_hours"] is not None
        else "not available"
    )
    return f"""# Logistic-regression baseline

Objective: predict any component failure within the next 24 hours.

| Metric | Validation | Held-out test |
|---|---:|---:|
| Average precision (PR-AUC) | {validation['average_precision']:.3f} | {test['average_precision']:.3f} |
| Precision | {validation['precision']:.3f} | {test['precision']:.3f} |
| Recall | {validation['recall']:.3f} | {test['recall']:.3f} |
| F1 | {validation['f1']:.3f} | {test['f1']:.3f} |
| False-positive hourly decisions / machine-week | {validation['false_positive_rows_per_machine_week']:.3f} | {test['false_positive_rows_per_machine_week']:.3f} |

The decision threshold ({test['threshold']:.3f}) was selected on validation data.
The test partition contains complete machines that appear in neither training nor
validation. At that threshold, the model detected {events['detected_failure_events']}
of {events['eligible_failure_events']} eligible test failure events
({event_recall} event recall), with a median lead time of {lead_time}.

These results measure performance on a public simulated dataset. They demonstrate
the pipeline and evaluation method; they are not evidence of production performance
on a different machine fleet.
"""


def run_pipeline(config_path: str | Path) -> dict[str, object]:
    config = _load_config(Path(config_path))
    raw_dir = Path(config["data"]["raw_dir"])
    raw_tables = load_raw_tables(raw_dir)
    validate_raw_tables(raw_tables)

    feature_table = build_feature_table(
        raw_tables,
        horizon_hours=config["features"]["horizon_hours"],
        rolling_windows_hours=config["features"]["rolling_windows_hours"],
    )
    feature_table, split_manifest = assign_machine_splits(
        feature_table,
        train_fraction=config["split"]["train_fraction"],
        validation_fraction=config["split"]["validation_fraction"],
        random_seed=config["split"]["random_seed"],
    )

    processed_path = Path(config["data"]["processed_path"])
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    feature_table.to_parquet(processed_path, index=False)

    train = feature_table.loc[feature_table["split"] == "train"]
    validation = feature_table.loc[feature_table["split"] == "validation"]
    test = feature_table.loc[feature_table["split"] == "test"]
    numerical_columns, categorical_columns = feature_columns(train)
    selected_features = numerical_columns + categorical_columns

    model = build_baseline_model(
        numerical_columns,
        categorical_columns,
        max_iterations=config["model"]["max_iterations"],
    )
    model.fit(train[selected_features], train["failure_within_horizon"])
    validation_probabilities = predict_probabilities(model, validation[selected_features])
    threshold = choose_f1_threshold(
        validation["failure_within_horizon"], validation_probabilities
    )
    test_probabilities = predict_probabilities(model, test[selected_features])

    validation_report = classification_report(
        validation, validation_probabilities, threshold=threshold
    )
    test_report = classification_report(test, test_probabilities, threshold=threshold)
    test_report["failure_events"] = failure_event_report(
        test,
        test_probabilities,
        raw_tables.failures,
        threshold=threshold,
        horizon_hours=config["features"]["horizon_hours"],
    )
    report = {
        "objective": (
            f"any component failure within {config['features']['horizon_hours']} hours"
        ),
        "split_strategy": "machine-disjoint random split",
        "random_seed": config["split"]["random_seed"],
        "runtime": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
        },
        "raw_data": _raw_data_manifest(raw_dir),
        "features": selected_features,
        "validation": validation_report,
        "test": test_report,
    }

    artifact_dir = Path(config["output"]["artifact_dir"])
    report_dir = Path(config["output"]["report_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / "model.joblib")
    (artifact_dir / "split_manifest.json").write_text(
        json.dumps(split_manifest, indent=2), encoding="utf-8"
    )
    (artifact_dir / "metadata.json").write_text(
        json.dumps({"threshold": threshold, "features": selected_features}, indent=2),
        encoding="utf-8",
    )
    (report_dir / "metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (report_dir / "README.md").write_text(
        _markdown_report(report), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/baseline.toml"),
        help="Path to the TOML pipeline configuration.",
    )
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.config), indent=2))


if __name__ == "__main__":
    main()
