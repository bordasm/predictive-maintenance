"""Evaluate, promote, and roll back model releases through explicit gates."""

from __future__ import annotations

import argparse
import json
import shutil
import tomllib
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as file:
        return tomllib.load(file)


def _resolve_model_path(manifest_path: Path, configured: str) -> Path:
    configured_path = Path(configured)
    windows_parts = PureWindowsPath(configured).parts
    candidates = (
        configured_path,
        manifest_path.parent.joinpath(*windows_parts),
        manifest_path.parent / configured_path.name,
        manifest_path.parent / PureWindowsPath(configured).name,
    )
    model_path = next((path for path in candidates if path.is_file()), None)
    if model_path is None:
        raise FileNotFoundError(
            "Model artifact not found. Checked: "
            + ", ".join(str(path) for path in candidates)
        )
    return model_path


def _manifest_metrics(
    manifest: dict[str, Any], comparison_path: Path
) -> dict[str, Any]:
    if "metrics" in manifest:
        return manifest["metrics"]
    comparison = _load_json(comparison_path)
    run_id = manifest["mlflow_run_id"]
    if comparison.get("mlflow_run_id") == run_id and "metrics" in comparison:
        return comparison["metrics"]
    for result in comparison["models"].values():
        if result.get("mlflow_run_id") == run_id:
            return {
                "validation": result["validation"],
                "test": result["test"],
            }
    raise ValueError(f"Metrics for MLflow run {run_id} were not found")


def _check(
    name: str,
    candidate_value: float,
    operator: str,
    required_value: float,
) -> dict[str, Any]:
    passed = (
        candidate_value >= required_value
        if operator == ">="
        else candidate_value <= required_value
    )
    return {
        "name": name,
        "candidate_value": candidate_value,
        "operator": operator,
        "required_value": required_value,
        "passed": passed,
    }


def _write_decision_report(
    decision: dict[str, Any], output_directory: str | Path
) -> None:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    (output / "decision.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )
    rows = [
        f"| {item['name']} | {item['candidate_value']:.6f} | "
        f"{item['operator']} {item['required_value']:.6f} | "
        f"{'pass' if item['passed'] else 'fail'} |"
        for item in decision["checks"]
    ]
    markdown = f"""# Model promotion decision

**Decision:** `{decision['decision']}`  
**Candidate:** `{decision['candidate']['model']}` / `{decision['candidate']['mlflow_run_id']}`  
**Incumbent:** `{decision['incumbent']['model']}` / `{decision['incumbent']['mlflow_run_id']}`

| Gate | Candidate | Requirement | Result |
|---|---:|---:|---|
{chr(10).join(rows)}

The gate uses validation performance for relative model selection and held-out
test metrics for absolute operational safeguards. Approval creates no deployment
by itself; promotion remains an explicit command and produces an immutable,
rollback-ready release directory.
"""
    (output / "README.md").write_text(markdown, encoding="utf-8")


def evaluate_candidate(config_path: str | Path) -> dict[str, Any]:
    config = _load_config(config_path)
    candidate_path = Path(config["candidate"]["manifest_path"])
    incumbent_path = Path(config["incumbent"]["manifest_path"])
    candidate = _load_json(candidate_path)
    incumbent = _load_json(incumbent_path)
    _resolve_model_path(candidate_path, candidate["model_path"])
    candidate_metrics = _manifest_metrics(
        candidate, Path(config["candidate"]["comparison_path"])
    )
    incumbent_metrics = _manifest_metrics(
        incumbent, Path(config["incumbent"]["comparison_path"])
    )
    gate = config["gate"]
    validation_ap = float(candidate_metrics["validation"]["average_precision"])
    incumbent_validation_ap = float(
        incumbent_metrics["validation"]["average_precision"]
    )
    test = candidate_metrics["test"]
    checks = [
        _check(
            "minimum validation average precision",
            validation_ap,
            ">=",
            float(gate["minimum_validation_average_precision"]),
        ),
        _check(
            "maximum validation regression from incumbent",
            validation_ap,
            ">=",
            incumbent_validation_ap - float(gate["maximum_validation_regression"]),
        ),
        _check(
            "minimum test average precision",
            float(test["average_precision"]),
            ">=",
            float(gate["minimum_test_average_precision"]),
        ),
        _check(
            "minimum test precision",
            float(test["precision"]),
            ">=",
            float(gate["minimum_test_precision"]),
        ),
        _check(
            "minimum test event recall",
            float(test["failure_events"]["event_recall"]),
            ">=",
            float(gate["minimum_test_event_recall"]),
        ),
        _check(
            "maximum false positives per machine-week",
            float(test["false_positive_rows_per_machine_week"]),
            "<=",
            float(gate["maximum_test_false_positives_per_machine_week"]),
        ),
    ]
    decision = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "decision": "approved" if all(item["passed"] for item in checks) else "rejected",
        "candidate": {
            "model": candidate["model"],
            "mlflow_run_id": candidate["mlflow_run_id"],
            "feature_sha256": candidate.get("feature_sha256"),
        },
        "incumbent": {
            "model": incumbent["model"],
            "mlflow_run_id": incumbent["mlflow_run_id"],
            "feature_sha256": incumbent.get("feature_sha256"),
        },
        "checks": checks,
    }
    _write_decision_report(decision, config["release"]["decision_report_directory"])
    return decision


def _atomic_write_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    temporary_path.replace(path)


def promote_candidate(
    config_path: str | Path, *, release_id: str | None = None
) -> dict[str, Any]:
    config = _load_config(config_path)
    decision = evaluate_candidate(config_path)
    if decision["decision"] != "approved":
        failed = [item["name"] for item in decision["checks"] if not item["passed"]]
        raise ValueError("Candidate failed promotion gates: " + ", ".join(failed))

    candidate_path = Path(config["candidate"]["manifest_path"])
    candidate = _load_json(candidate_path)
    model_path = _resolve_model_path(candidate_path, candidate["model_path"])
    identifier = release_id or (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + candidate["mlflow_run_id"][:12]
    )
    release_directory = Path(config["release"]["directory"]) / identifier
    if release_directory.exists():
        raise FileExistsError(f"Release already exists: {release_directory}")
    release_directory.mkdir(parents=True)
    release_model_path = release_directory / "model.joblib"
    shutil.copy2(model_path, release_model_path)
    promoted_at = datetime.now(UTC).isoformat()
    release_manifest = {
        **candidate,
        "release_id": identifier,
        "promoted_at": promoted_at,
        "model_path": "model.joblib",
        "promotion_decision": decision,
    }
    _atomic_write_json(release_directory / "manifest.json", release_manifest)

    champion_path = Path(config["incumbent"]["manifest_path"])
    champion_manifest = {
        **release_manifest,
        "model_path": (Path("releases") / identifier / "model.joblib").as_posix(),
    }
    _atomic_write_json(champion_path, champion_manifest)
    return champion_manifest


def rollback_release(config_path: str | Path, release_id: str) -> dict[str, Any]:
    config = _load_config(config_path)
    release_directory = Path(config["release"]["directory"]) / release_id
    release_manifest = _load_json(release_directory / "manifest.json")
    if not (release_directory / "model.joblib").is_file():
        raise FileNotFoundError(f"Release model not found: {release_directory}")
    champion_manifest = {
        **release_manifest,
        "model_path": (Path("releases") / release_id / "model.joblib").as_posix(),
        "rolled_back_at": datetime.now(UTC).isoformat(),
    }
    _atomic_write_json(
        Path(config["incumbent"]["manifest_path"]), champion_manifest
    )
    return champion_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/promotion.toml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("evaluate")
    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--release-id")
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("release_id")
    args = parser.parse_args()
    if args.command == "evaluate":
        result = evaluate_candidate(args.config)
    elif args.command == "promote":
        result = promote_candidate(args.config, release_id=args.release_id)
    else:
        result = rollback_release(args.config, args.release_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
