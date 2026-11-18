"""Export a compact, model-ready sample from the untouched test partition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from predictive_maintenance.serving.schemas import FeatureVector
from predictive_maintenance.sequence.data import build_window_end_indices


def export_demo_data(
    feature_table: Path,
    model_path: Path,
    output_path: Path,
    *,
    positive_count: int,
    negative_count: int,
    seed: int,
    window_size: int = 48,
) -> None:
    frame = pd.read_parquet(feature_table)
    if "split" not in frame or "failure_within_horizon" not in frame:
        raise ValueError("Feature table does not contain split and target columns")
    test = (
        frame.loc[frame["split"] == "test"]
        .sort_values(["machineID", "datetime"])
        .reset_index(drop=True)
    )
    if test.empty:
        raise ValueError("The feature table has no held-out test rows")

    model = joblib.load(model_path)
    feature_names = [str(name) for name in model.feature_names_in_]
    missing = sorted(set(feature_names).difference(test.columns))
    if missing:
        raise ValueError(f"Test data is missing model features: {missing}")

    endpoints = build_window_end_indices(test, window_size=window_size)
    eligible = test.iloc[endpoints].assign(_endpoint=endpoints)
    positive = eligible.loc[eligible["failure_within_horizon"].astype(bool)]
    negative = eligible.loc[~eligible["failure_within_horizon"].astype(bool)]
    selected = pd.concat([
        positive.sample(n=min(positive_count, len(positive)), random_state=seed),
        negative.sample(n=min(negative_count, len(negative)), random_state=seed),
    ]).sort_values(["machineID", "datetime"])

    samples: list[dict[str, object]] = []
    for row in selected.to_dict(orient="records"):
        timestamp = pd.Timestamp(row["datetime"])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        features = FeatureVector.model_validate(
            {name: row[name] for name in feature_names}
        ).model_dump(mode="json")
        endpoint = int(row["_endpoint"])
        window = test.iloc[endpoint - window_size + 1 : endpoint + 1]
        sequence = [
            FeatureVector.model_validate(
                {name: value[name] for name in feature_names}
            ).model_dump(mode="json")
            for value in window.to_dict(orient="records")
        ]
        samples.append(
            {
                "sample_id": (
                    f"test-m{int(row['machineID'])}-"
                    f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
                ),
                "machine_id": int(row["machineID"]),
                "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
                "actual_failure_within_horizon": bool(
                    row["failure_within_horizon"]
                ),
                "failure_component": None,
                "features": features,
                "sequence": sequence,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "name": "Azure PdM held-out machine test observations",
                "split": "test",
                "samples": samples,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--feature-table",
        type=Path,
        default=Path("data/processed/azure_pdm_features.parquet"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/experiments/hist_gradient_boosting.joblib"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("deploy/gcp/generated/demo-samples.json"),
    )
    parser.add_argument("--positives", type=int, default=24)
    parser.add_argument("--negatives", type=int, default=48)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--window-size", type=int, default=48)
    args = parser.parse_args()
    export_demo_data(
        args.feature_table,
        args.model,
        args.output,
        positive_count=args.positives,
        negative_count=args.negatives,
        seed=args.seed,
        window_size=args.window_size,
    )


if __name__ == "__main__":
    main()
