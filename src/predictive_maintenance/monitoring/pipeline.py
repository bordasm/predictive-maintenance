"""CLI and reusable pipeline for production model monitoring."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.monitoring.drift import (
    build_reference_profile,
    evaluate_monitoring_window,
)
from predictive_maintenance.monitoring.report import write_monitoring_report
from predictive_maintenance.monitoring.store import PredictionStore
from predictive_maintenance.serving.model_service import ModelService


def load_monitoring_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as file:
        return tomllib.load(file)


def create_reference(config: dict[str, Any]) -> dict[str, Any]:
    service = ModelService.load(config["model"]["manifest_path"])
    frame = pd.read_parquet(config["data"]["feature_path"])
    if "split" in frame:
        frame = frame.loc[frame["split"] == "train"]
    sample_rows = min(int(config["reference"]["sample_rows"]), len(frame))
    sample = frame.sample(
        sample_rows, random_state=int(config["reference"]["random_seed"])
    )
    probabilities = np.asarray(
        service.model.predict_proba(sample.loc[:, service.feature_names])[:, 1],
        dtype=float,
    )
    profile = build_reference_profile(
        sample,
        feature_names=list(service.feature_names),
        probabilities=probabilities,
        threshold=service.threshold,
        quantile_bins=int(config["reference"]["quantile_bins"]),
        metadata={
            "model_name": service.model_name,
            "model_version": service.model_version,
            "mlflow_run_id": service.mlflow_run_id,
            "threshold": service.threshold,
            "source_split": "train",
        },
    )
    profile_path = Path(config["reference"]["profile_path"])
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile


def monitor_frame(
    config: dict[str, Any],
    current: pd.DataFrame,
    *,
    labels: pd.DataFrame | None = None,
    output_directory: str | Path | None = None,
    title: str = "Predictive-maintenance monitoring report",
) -> dict[str, Any]:
    profile_path = Path(config["reference"]["profile_path"])
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    thresholds = config["thresholds"]
    result = evaluate_monitoring_window(
        profile,
        current,
        warning_psi=float(thresholds["warning_psi"]),
        critical_psi=float(thresholds["critical_psi"]),
        warning_categorical_distance=float(
            thresholds["warning_categorical_distance"]
        ),
        critical_categorical_distance=float(
            thresholds["critical_categorical_distance"]
        ),
        labels=labels,
    )
    write_monitoring_report(
        result,
        output_directory or config["output"]["report_dir"],
        title=title,
    )
    return result


def monitor_database(
    config: dict[str, Any],
    *,
    labels_path: str | Path | None = None,
) -> dict[str, Any]:
    store = PredictionStore(config["data"]["prediction_database"])
    store.initialize()
    current = store.read_predictions()
    if current.empty:
        raise ValueError("The prediction database does not contain any observations")
    configured_labels = Path(labels_path or config["data"]["labels_path"])
    labels = pd.read_csv(configured_labels) if configured_labels.is_file() else None
    return monitor_frame(config, current, labels=labels)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/monitoring.toml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-reference")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--labels", type=Path)
    args = parser.parse_args()
    config = load_monitoring_config(args.config)
    if args.command == "build-reference":
        profile = create_reference(config)
        print(f"Reference profile created from {profile['row_count']} rows")
    else:
        result = monitor_database(config, labels_path=args.labels)
        print(f"Monitoring status: {result['overall_status']}")


if __name__ == "__main__":
    main()
