"""Create explicit Cloud Build contexts including ignored model/data assets."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path, PureWindowsPath


def copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def prepare(root: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    api = output / "api"
    web = output / "web"
    terraform = output / "terraform"
    api.mkdir(parents=True)
    web.mkdir(parents=True)

    for relative in ("pyproject.toml", "README.md", "requirements-serving.txt"):
        copy_path(root / relative, api / relative)
    copy_path(root / "src", api / "src")
    copy_path(root / "deploy/gcp/Dockerfile.api", api / "Dockerfile")
    copy_path(
        root / "artifacts/experiments/hist_gradient_boosting.joblib",
        api / "model/model.joblib",
    )
    manifest = json.loads(
        (root / "artifacts/experiments/champion.json").read_text(encoding="utf-8")
    )
    manifest["model_path"] = "/models/model.joblib"
    (api / "model").mkdir(exist_ok=True)
    (api / "model/champion.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    comparison = json.loads(
        (root / "reports/sequence_comparison/comparison.json").read_text(encoding="utf-8")
    )
    sequence_models: dict[str, dict[str, object]] = {}
    for name in ("lstm", "transformer"):
        result = comparison["models"][name]
        source = root.joinpath(*PureWindowsPath(str(result["model_path"])).parts)
        destination = api / f"model/{name}.pt"
        copy_path(source, destination)
        sequence_models[name] = {
            "model": name,
            "input_type": "sequence_window",
            "model_path": f"/models/{name}.pt",
            "threshold": result["validation"]["threshold"],
            "selection_metric": comparison["selection_metric"],
            "selection_value": result["validation"][comparison["selection_metric"]],
            "mlflow_run_id": result["mlflow_run_id"],
        }
    registry = {
        "default_model": "hist_gradient_boosting",
        "models": {
            "hist_gradient_boosting": {
                "model": "hist_gradient_boosting",
                "input_type": "feature_row",
                "manifest_path": "/models/champion.json",
            },
            **sequence_models,
        },
    }
    (api / "model/model-registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )
    copy_path(
        root / "deploy/gcp/generated/demo-samples.json",
        api / "data/demo/demo-samples.json",
    )

    copy_path(root / "deploy/gcp/Dockerfile.web", web / "Dockerfile")
    copy_path(
        root / "src/predictive_maintenance/__init__.py",
        web / "src/predictive_maintenance/__init__.py",
    )
    copy_path(root / "src/predictive_maintenance/web", web / "src/predictive_maintenance/web")

    copy_path(root / "deploy/gcp/terraform", terraform)
    copy_path(root / "deploy/gcp/cloud-deploy.sh", output / "cloud-deploy.sh")
    copy_path(
        root / "deploy/gcp/configure-access-requests.sh",
        output / "configure-access-requests.sh",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[2])
    parser.add_argument("--output", type=Path, default=Path(".gcp-build"))
    args = parser.parse_args()
    prepare(args.root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
