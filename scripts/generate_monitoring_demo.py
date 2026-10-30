"""Create reproducible stable and drifted monitoring windows and reports."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from predictive_maintenance.monitoring.pipeline import (
    create_reference,
    load_monitoring_config,
    monitor_frame,
)
from predictive_maintenance.serving.model_service import ModelService


def _serving_window(
    frame: pd.DataFrame, service: ModelService, *, prefix: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    probabilities = np.asarray(
        service.model.predict_proba(frame.loc[:, service.feature_names])[:, 1],
        dtype=float,
    )
    current = frame.loc[:, service.feature_names].reset_index(drop=True).copy()
    current.insert(0, "observation_id", [f"{prefix}-{index:05d}" for index in range(len(frame))])
    current["failure_probability"] = probabilities
    current["alert"] = probabilities >= service.threshold
    labels = pd.DataFrame(
        {
            "observation_id": current["observation_id"],
            "actual_failure_within_horizon": frame[
                "failure_within_horizon"
            ].to_numpy(),
        }
    )
    return current, labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/monitoring.toml"))
    parser.add_argument("--rows", type=int, default=5000)
    args = parser.parse_args()
    config = load_monitoring_config(args.config)
    create_reference(config)
    service = ModelService.load(config["model"]["manifest_path"])
    features = pd.read_parquet(config["data"]["feature_path"])
    training = features.loc[features["split"] == "train"]
    stable_source = training.sample(
        min(args.rows, len(training)),
        random_state=int(config["reference"]["random_seed"]) + 1,
    )

    stable, stable_labels = _serving_window(stable_source, service, prefix="stable")
    stable_result = monitor_frame(
        config,
        stable,
        labels=stable_labels,
        output_directory="reports/monitoring/stable",
        title="Stable-window monitoring demonstration",
    )

    drifted_source = stable_source.copy()
    voltage_columns = [
        name for name in service.feature_names if name == "volt" or name.startswith("volt_mean")
    ]
    for name in voltage_columns:
        drifted_source[name] = drifted_source[name] + 75.0
    drifted, drifted_labels = _serving_window(
        drifted_source, service, prefix="drifted"
    )
    drifted_result = monitor_frame(
        config,
        drifted,
        labels=drifted_labels,
        output_directory="reports/monitoring/drifted",
        title="Injected-voltage-drift monitoring demonstration",
    )
    print(
        f"Stable status: {stable_result['overall_status']}; "
        f"drifted status: {drifted_result['overall_status']}"
    )


if __name__ == "__main__":
    main()
