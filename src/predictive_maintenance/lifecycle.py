"""Orchestrate feature rebuild, retraining, and candidate evaluation."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from predictive_maintenance.experiments import run_experiments
from predictive_maintenance.pipeline import run_pipeline
from predictive_maintenance.promotion import evaluate_candidate


def run_lifecycle(
    config_path: str | Path, *, rebuild_features: bool = False
) -> dict[str, Any]:
    with Path(config_path).open("rb") as file:
        config = tomllib.load(file)
    baseline_result = None
    if rebuild_features:
        baseline_result = run_pipeline(config["pipeline"]["baseline_config"])
    comparison = run_experiments(config["pipeline"]["experiment_config"])
    decision = evaluate_candidate(config["pipeline"]["promotion_config"])
    summary = {
        "completed_at": datetime.now(UTC).isoformat(),
        "features_rebuilt": rebuild_features,
        "baseline_test_average_precision": (
            baseline_result["test"]["average_precision"]
            if baseline_result is not None
            else None
        ),
        "candidate_model": comparison["champion"],
        "candidate_validation_average_precision": comparison["models"][
            comparison["champion"]
        ]["validation"]["average_precision"],
        "promotion_decision": decision["decision"],
        "candidate_mlflow_run_id": decision["candidate"]["mlflow_run_id"],
    }
    summary_path = Path(config["output"]["summary_path"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/lifecycle.toml"))
    parser.add_argument("--rebuild-features", action="store_true")
    args = parser.parse_args()
    result = run_lifecycle(args.config, rebuild_features=args.rebuild_features)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
