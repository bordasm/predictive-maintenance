"""Track and compare baseline and challenger models with MLflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import mlflow
import pandas as pd
import sklearn

from predictive_maintenance.data.schema import TABLE_SCHEMAS
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
from predictive_maintenance.models.challenger import build_challenger_model


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_state() -> dict[str, str | bool | None]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return {"commit": commit, "dirty": bool(status.strip())}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def _evaluate_model(
    model: Any,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    failures: pd.DataFrame,
    features: list[str],
    *,
    horizon_hours: int,
) -> dict[str, Any]:
    model.fit(train[features], train["failure_within_horizon"])
    validation_probabilities = predict_probabilities(model, validation[features])
    threshold = choose_f1_threshold(
        validation["failure_within_horizon"], validation_probabilities
    )
    test_probabilities = predict_probabilities(model, test[features])
    validation_report = classification_report(
        validation, validation_probabilities, threshold=threshold
    )
    test_report = classification_report(test, test_probabilities, threshold=threshold)
    test_report["failure_events"] = failure_event_report(
        test,
        test_probabilities,
        failures,
        threshold=threshold,
        horizon_hours=horizon_hours,
    )
    return {"validation": validation_report, "test": test_report}


def _mlflow_metrics(report: dict[str, Any]) -> dict[str, float]:
    metric_names = (
        "average_precision",
        "roc_auc",
        "precision",
        "recall",
        "f1",
        "false_positive_rows_per_machine_week",
    )
    metrics: dict[str, float] = {}
    for partition in ("validation", "test"):
        for metric_name in metric_names:
            value = report[partition][metric_name]
            if value is not None:
                metrics[f"{partition}_{metric_name}"] = float(value)
    event_metrics = report["test"]["failure_events"]
    for metric_name in ("event_recall", "median_lead_time_hours"):
        value = event_metrics[metric_name]
        if value is not None:
            metrics[f"test_{metric_name}"] = float(value)
    return metrics


def _markdown_report(comparison: dict[str, Any]) -> str:
    rows = []
    for name, result in comparison["models"].items():
        validation = result["validation"]
        test = result["test"]
        events = test["failure_events"]
        rows.append(
            f"| {name} | {validation['average_precision']:.3f} | "
            f"{test['average_precision']:.3f} | {test['precision']:.3f} | "
            f"{test['recall']:.3f} | {events['event_recall']:.1%} | "
            f"{test['false_positive_rows_per_machine_week']:.3f} |"
        )
    return f"""# Model comparison

Both models use the same machine-disjoint train, validation, and test partitions.
The champion is selected by validation PR-AUC; held-out test metrics do not take
part in model selection.

| Model | Validation PR-AUC | Test PR-AUC | Test precision | Test recall | Event recall | FP hourly decisions / machine-week |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

**Champion: `{comparison['champion']}`**

Selection metric: `{comparison['selection_metric']}`. MLflow experiment:
`{comparison['experiment_name']}`. Run IDs are recorded in `comparison.json`.

The public dataset is simulated. This comparison validates the training and
experiment-management workflow rather than expected performance on a real fleet.
"""


def run_experiments(config_path: str | Path) -> dict[str, Any]:
    config = _load_config(Path(config_path))
    feature_path = Path(config["data"]["feature_path"])
    if not feature_path.is_file():
        raise FileNotFoundError(
            f"Processed feature table not found: {feature_path}. Run the baseline pipeline first."
        )

    frame = pd.read_parquet(feature_path)
    expected_splits = {"train", "validation", "test"}
    actual_splits = set(frame["split"].dropna().unique())
    if actual_splits != expected_splits:
        raise ValueError(f"Expected splits {expected_splits}, found {actual_splits}")

    failures_path = (
        Path(config["data"]["raw_dir"]) / TABLE_SCHEMAS["failures"].filename
    )
    failures = pd.read_csv(failures_path, parse_dates=["datetime"])
    train = frame.loc[frame["split"] == "train"]
    validation = frame.loc[frame["split"] == "validation"]
    test = frame.loc[frame["split"] == "test"]
    numerical_columns, categorical_columns = feature_columns(train)
    features = numerical_columns + categorical_columns

    model_specs = {
        "logistic_regression": (
            build_baseline_model(
                numerical_columns,
                categorical_columns,
                max_iterations=config["baseline"]["max_iterations"],
            ),
            config["baseline"],
        ),
        "hist_gradient_boosting": (
            build_challenger_model(
                numerical_columns,
                categorical_columns,
                learning_rate=config["challenger"]["learning_rate"],
                max_iterations=config["challenger"]["max_iterations"],
                max_leaf_nodes=config["challenger"]["max_leaf_nodes"],
                min_samples_leaf=config["challenger"]["min_samples_leaf"],
                l2_regularization=config["challenger"]["l2_regularization"],
            ),
            config["challenger"],
        ),
    }

    database_path = Path(config["tracking"]["database"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    tracking_uri = f"sqlite:///{database_path.as_posix()}"
    tracking_artifact_dir = Path(config["tracking"]["artifact_directory"]).resolve()
    tracking_artifact_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(tracking_uri)
    experiment_name = config["tracking"]["experiment_name"]
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            artifact_location=tracking_artifact_dir.as_uri(),
        )
        mlflow.set_experiment(experiment_id=experiment_id)
    else:
        mlflow.set_experiment(experiment_id=experiment.experiment_id)
    artifact_dir = Path(config["output"]["artifact_dir"])
    report_dir = Path(config["output"]["report_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    feature_fingerprint = _sha256(feature_path)
    git_state = _git_state()
    results: dict[str, Any] = {}
    candidate_models_dir = artifact_dir / "candidates"
    for model_name, (model, parameters) in model_specs.items():
        report = _evaluate_model(
            model,
            train,
            validation,
            test,
            failures,
            features,
            horizon_hours=config["evaluation"]["horizon_hours"],
        )
        with mlflow.start_run(run_name=model_name) as run:
            model_path = candidate_models_dir / run.info.run_id / "model.joblib"
            model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, model_path)
            mlflow.set_tags(
                {
                    "model_role": "baseline" if model_name == "logistic_regression" else "challenger",
                    "split_strategy": "machine-disjoint",
                    "feature_sha256": feature_fingerprint,
                    "git_commit": git_state["commit"] or "unavailable",
                    "git_dirty": str(git_state["dirty"]).lower(),
                }
            )
            mlflow.log_params({f"model_{key}": value for key, value in parameters.items()})
            mlflow.log_params(
                {
                    "horizon_hours": config["evaluation"]["horizon_hours"],
                    "feature_count": len(features),
                    "train_rows": len(train),
                }
            )
            mlflow.log_metrics(_mlflow_metrics(report))
            mlflow.log_artifact(str(model_path), artifact_path="model")
            mlflow.log_dict(report, "evaluation/metrics.json")
            report["mlflow_run_id"] = run.info.run_id
            report["model_path"] = str(model_path)
        results[model_name] = report

    selection_metric = config["evaluation"]["selection_metric"]
    champion = max(
        results,
        key=lambda name: results[name]["validation"][selection_metric],
    )
    comparison = {
        "experiment_name": experiment_name,
        "tracking_backend": "sqlite",
        "tracking_database": str(database_path),
        "feature_path": str(feature_path),
        "feature_sha256": feature_fingerprint,
        "runtime": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "mlflow": mlflow.__version__,
        },
        "git": git_state,
        "selection_partition": "validation",
        "selection_metric": selection_metric,
        "champion": champion,
        "models": results,
    }
    (report_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    (report_dir / "README.md").write_text(
        _markdown_report(comparison), encoding="utf-8"
    )
    candidate_manifest_name = config["output"].get(
        "candidate_manifest", "candidate.json"
    )
    (artifact_dir / candidate_manifest_name).write_text(
        json.dumps(
            {
                "model": champion,
                "model_path": results[champion]["model_path"],
                "threshold": results[champion]["validation"]["threshold"],
                "selection_metric": selection_metric,
                "selection_value": results[champion]["validation"][selection_metric],
                "mlflow_run_id": results[champion]["mlflow_run_id"],
                "feature_sha256": feature_fingerprint,
                "created_at": datetime.now(UTC).isoformat(),
                "metrics": {
                    "validation": results[champion]["validation"],
                    "test": results[champion]["test"],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/experiments.toml"),
        help="Path to the experiment TOML configuration.",
    )
    args = parser.parse_args()
    print(json.dumps(run_experiments(args.config), indent=2))


if __name__ == "__main__":
    main()
