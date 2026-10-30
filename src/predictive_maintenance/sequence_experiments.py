"""Train, track, and compare LSTM/Transformer temporal challengers."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import mlflow
import numpy as np
import pandas as pd
import sklearn
import torch

from predictive_maintenance.data.schema import TABLE_SCHEMAS
from predictive_maintenance.evaluation.metrics import (
    choose_f1_threshold,
    classification_report,
    failure_event_report,
)
from predictive_maintenance.models.baseline import predict_probabilities as predict_tabular
from predictive_maintenance.sequence.data import (
    SequencePreprocessor,
    build_window_end_indices,
)
from predictive_maintenance.sequence.models import build_sequence_model
from predictive_maintenance.sequence.training import (
    WindowDataset,
    predict_probabilities,
    set_reproducible_seed,
    train_classifier,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evaluation(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    failures: pd.DataFrame,
    *,
    threshold: float,
    horizon_hours: int,
) -> dict[str, Any]:
    report = classification_report(frame, probabilities, threshold=threshold)
    report["failure_events"] = failure_event_report(
        frame,
        probabilities,
        failures,
        threshold=threshold,
        horizon_hours=horizon_hours,
    )
    return report


def _mlflow_metrics(result: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for partition in ("validation", "test"):
        for name in ("average_precision", "roc_auc", "precision", "recall", "f1"):
            value = result[partition][name]
            if value is not None:
                metrics[f"{partition}_{name}"] = float(value)
    events = result["test"]["failure_events"]
    if events["event_recall"] is not None:
        metrics["test_event_recall"] = float(events["event_recall"])
    return metrics


def _markdown_report(comparison: dict[str, Any]) -> str:
    rows = []
    for name, result in comparison["models"].items():
        validation = result["validation"]
        test = result["test"]
        training = result.get("training")
        duration = f"{training['duration_seconds']:.1f}" if training else "existing"
        rows.append(
            f"| {name} | {validation['average_precision']:.4f} | "
            f"{test['average_precision']:.4f} | {test['precision']:.4f} | "
            f"{test['recall']:.4f} | {test['failure_events']['event_recall']:.1%} | "
            f"{duration} |"
        )
    status = (
        "outperformed"
        if comparison["sequence_champion_outperformed_incumbent"]
        else "did not outperform"
    )
    return f"""# Temporal sequence challenger comparison

All models are evaluated on the same complete `{comparison['window_size']}`-hour
window endpoints from machine-disjoint validation and test fleets. The LSTM and
Transformer receive only the current and preceding observations. Preprocessing
statistics and categories are fitted on training machines only.

| Model | Validation PR-AUC | Test PR-AUC | Test precision | Test recall | Event recall | Training seconds |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

**Sequence champion:** `{comparison['sequence_champion']}`  
**Overall validation champion:** `{comparison['overall_champion']}`

The sequence champion {status} the deployed tabular incumbent on validation
PR-AUC. Held-out test results are reported after selection and do not choose the
model.

The neural checkpoint has a temporal-window serving contract and is deliberately
kept out of the current single-observation promotion workflow. Online deployment
would first require a stateful feature/window service and a versioned sequence
request contract.
"""


def run_sequence_experiments(config_path: str | Path) -> dict[str, Any]:
    with Path(config_path).open("rb") as handle:
        config = tomllib.load(handle)
    feature_path = Path(config["data"]["feature_path"])
    frame = pd.read_parquet(feature_path).sort_values(
        ["machineID", "datetime"]
    )
    partitions = {
        name: frame.loc[frame["split"] == name].reset_index(drop=True)
        for name in ("train", "validation", "test")
    }
    if any(partition.empty for partition in partitions.values()):
        raise ValueError("Train, validation, and test partitions must all be present")
    train_machines = set(partitions["train"]["machineID"])
    validation_machines = set(partitions["validation"]["machineID"])
    test_machines = set(partitions["test"]["machineID"])
    if train_machines & validation_machines or train_machines & test_machines or validation_machines & test_machines:
        raise ValueError("Sequence partitions must be machine-disjoint")

    preprocessor = SequencePreprocessor.fit(partitions["train"])
    matrices = {
        name: preprocessor.transform(partition)
        for name, partition in partitions.items()
    }
    labels = {
        name: partition["failure_within_horizon"].to_numpy(dtype=np.float32)
        for name, partition in partitions.items()
    }
    window_size = int(config["window"]["size"])
    full_endpoints = {
        name: build_window_end_indices(partition, window_size=window_size)
        for name, partition in partitions.items()
    }
    train_endpoints = build_window_end_indices(
        partitions["train"],
        window_size=window_size,
        stride=int(config["training"]["train_negative_stride"]),
        preserve_positive_labels=True,
    )
    stopping_endpoints = build_window_end_indices(
        partitions["validation"],
        window_size=window_size,
        stride=int(config["training"]["early_stopping_validation_stride"]),
        preserve_positive_labels=True,
    )
    datasets = {
        name: WindowDataset(matrices[name], labels[name], full_endpoints[name], window_size)
        for name in ("validation", "test")
    }
    training_dataset = WindowDataset(
        matrices["train"], labels["train"], train_endpoints, window_size
    )
    stopping_dataset = WindowDataset(
        matrices["validation"], labels["validation"], stopping_endpoints, window_size
    )
    endpoint_frames = {
        name: partitions[name].iloc[full_endpoints[name]].reset_index(drop=True)
        for name in ("validation", "test")
    }
    failures = pd.read_csv(
        Path(config["data"]["raw_dir"]) / TABLE_SCHEMAS["failures"].filename,
        parse_dates=["datetime"],
    )

    requested_device = config["training"].get("device", "auto")
    device = torch.device(
        ("cuda" if torch.cuda.is_available() else "cpu")
        if requested_device == "auto"
        else requested_device
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")

    database_path = Path(config["tracking"]["database"])
    tracking_artifacts = Path(config["tracking"]["artifact_directory"]).resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    tracking_artifacts.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{database_path.as_posix()}")
    experiment_name = config["tracking"]["experiment_name"]
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name, artifact_location=tracking_artifacts.as_uri()
        )
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(experiment_id=experiment_id)

    artifact_dir = Path(config["output"]["artifact_dir"])
    report_dir = Path(config["output"]["report_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    input_size = matrices["train"].shape[1]
    model_parameters = {
        "lstm": {
            "hidden_size": int(config["lstm"]["hidden_size"]),
            "num_layers": int(config["lstm"]["num_layers"]),
            "dropout": float(config["lstm"]["dropout"]),
        },
        "transformer": {
            "d_model": int(config["transformer"]["d_model"]),
            "nhead": int(config["transformer"]["nhead"]),
            "num_layers": int(config["transformer"]["num_layers"]),
            "dim_feedforward": int(config["transformer"]["dim_feedforward"]),
            "dropout": float(config["transformer"]["dropout"]),
        },
    }
    seed = int(config["training"]["seed"])
    batch_size = int(config["training"]["batch_size"])
    horizon_hours = int(config["evaluation"]["horizon_hours"])
    results: dict[str, Any] = {}
    for offset, (name, parameters) in enumerate(model_parameters.items()):
        set_reproducible_seed(seed + offset)
        model = build_sequence_model(
            name,
            input_size=input_size,
            window_size=window_size,
            parameters=parameters,
        )
        with mlflow.start_run(run_name=name) as run:
            training = train_classifier(
                model,
                training_dataset,
                stopping_dataset,
                epochs=int(config["training"]["epochs"]),
                batch_size=batch_size,
                learning_rate=float(config["training"]["learning_rate"]),
                weight_decay=float(config["training"]["weight_decay"]),
                patience=int(config["training"]["patience"]),
                device=device,
                seed=seed + offset,
            )
            validation_probabilities = predict_probabilities(
                model, datasets["validation"], batch_size=batch_size, device=device
            )
            threshold = choose_f1_threshold(
                endpoint_frames["validation"]["failure_within_horizon"],
                validation_probabilities,
            )
            test_probabilities = predict_probabilities(
                model, datasets["test"], batch_size=batch_size, device=device
            )
            result = {
                "validation": _evaluation(
                    endpoint_frames["validation"],
                    validation_probabilities,
                    failures,
                    threshold=threshold,
                    horizon_hours=horizon_hours,
                ),
                "test": _evaluation(
                    endpoint_frames["test"],
                    test_probabilities,
                    failures,
                    threshold=threshold,
                    horizon_hours=horizon_hours,
                ),
                "training": training.to_dict(),
                "mlflow_run_id": run.info.run_id,
            }
            checkpoint_path = artifact_dir / "candidates" / run.info.run_id / "model.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "model": name,
                    "state_dict": {
                        key: value.detach().cpu() for key, value in model.state_dict().items()
                    },
                    "window_size": window_size,
                    "input_size": input_size,
                    "preprocessor": preprocessor.to_dict(),
                    "config": parameters,
                },
                checkpoint_path,
            )
            result["model_path"] = str(checkpoint_path)
            mlflow.set_tags(
                {
                    "model_role": "sequence_challenger",
                    "architecture": name,
                    "split_strategy": "machine-disjoint",
                    "window_contract": f"trailing-{window_size}-hours",
                    "feature_sha256": _sha256(feature_path),
                }
            )
            mlflow.log_params(
                {
                    "window_size": window_size,
                    "input_size": input_size,
                    "train_windows": len(training_dataset),
                    "batch_size": batch_size,
                    **{f"architecture_{key}": value for key, value in config[name].items()},
                }
            )
            mlflow.log_metrics(_mlflow_metrics(result))
            mlflow.log_dict(training.to_dict(), "training/history.json")
            mlflow.log_artifact(str(checkpoint_path), artifact_path="model")
            results[name] = result
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    incumbent_model = joblib.load(config["incumbent"]["model_path"])
    incumbent_validation_probabilities = predict_tabular(
        incumbent_model, endpoint_frames["validation"]
    )
    incumbent_threshold = choose_f1_threshold(
        endpoint_frames["validation"]["failure_within_horizon"],
        incumbent_validation_probabilities,
    )
    incumbent_test_probabilities = predict_tabular(
        incumbent_model, endpoint_frames["test"]
    )
    results["hist_gradient_boosting_incumbent"] = {
        "validation": _evaluation(
            endpoint_frames["validation"],
            incumbent_validation_probabilities,
            failures,
            threshold=incumbent_threshold,
            horizon_hours=horizon_hours,
        ),
        "test": _evaluation(
            endpoint_frames["test"],
            incumbent_test_probabilities,
            failures,
            threshold=incumbent_threshold,
            horizon_hours=horizon_hours,
        ),
        "mlflow_run_id": config["incumbent"]["mlflow_run_id"],
        "model_path": config["incumbent"]["model_path"],
    }

    sequence_champion = max(
        ("lstm", "transformer"),
        key=lambda name: results[name]["validation"]["average_precision"],
    )
    overall_champion = max(
        results, key=lambda name: results[name]["validation"]["average_precision"]
    )
    incumbent_name = "hist_gradient_boosting_incumbent"
    comparison = {
        "created_at": datetime.now(UTC).isoformat(),
        "experiment_name": experiment_name,
        "task": "failure_within_24_hours",
        "window_size": window_size,
        "window_semantics": "current observation plus strictly preceding hourly observations",
        "selection_partition": "validation",
        "selection_metric": "average_precision",
        "sequence_champion": sequence_champion,
        "overall_champion": overall_champion,
        "sequence_champion_outperformed_incumbent": (
            results[sequence_champion]["validation"]["average_precision"]
            > results[incumbent_name]["validation"]["average_precision"]
        ),
        "device": str(device),
        "runtime": {
            "python": platform.python_version(),
            "pytorch": torch.__version__,
            "scikit_learn": sklearn.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "feature_path": str(feature_path),
        "feature_sha256": _sha256(feature_path),
        "rows": {name: len(partition) for name, partition in partitions.items()},
        "windows": {
            "train_sampled": len(training_dataset),
            "validation": len(datasets["validation"]),
            "test": len(datasets["test"]),
        },
        "preprocessing": preprocessor.to_dict(),
        "models": results,
    }
    (report_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    (report_dir / "README.md").write_text(
        _markdown_report(comparison), encoding="utf-8"
    )
    champion_result = results[sequence_champion]
    (artifact_dir / "candidate.json").write_text(
        json.dumps(
            {
                "model": sequence_champion,
                "model_path": champion_result["model_path"],
                "mlflow_run_id": champion_result["mlflow_run_id"],
                "window_size": window_size,
                "threshold": champion_result["validation"]["threshold"],
                "selection_metric": "average_precision",
                "selection_value": champion_result["validation"]["average_precision"],
                "serving_contract": "trailing_sequence_window",
                "deployment_eligible": False,
                "deployment_blocker": "current API accepts independent feature rows",
                "feature_sha256": comparison["feature_sha256"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/sequence.toml")
    )
    args = parser.parse_args()
    comparison = run_sequence_experiments(args.config)
    print(
        json.dumps(
            {
                "sequence_champion": comparison["sequence_champion"],
                "overall_champion": comparison["overall_champion"],
                "report": "reports/sequence_comparison/README.md",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
