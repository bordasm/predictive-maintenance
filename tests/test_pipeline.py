from __future__ import annotations

import json
from pathlib import Path

from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.schema import TABLE_SCHEMAS
from predictive_maintenance.experiments import run_experiments
from predictive_maintenance.pipeline import run_pipeline


def test_pipeline_runs_end_to_end_on_synthetic_data(
    tmp_path: Path, raw_tables: RawTables
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for name, frame in raw_tables.as_dict().items():
        frame.to_csv(raw_dir / TABLE_SCHEMAS[name].filename, index=False)

    processed_path = tmp_path / "processed" / "features.parquet"
    artifact_dir = tmp_path / "artifacts"
    report_dir = tmp_path / "reports"
    config_path = tmp_path / "baseline.toml"
    config_path.write_text(
        f"""
[data]
raw_dir = "{raw_dir.as_posix()}"
processed_path = "{processed_path.as_posix()}"

[features]
horizon_hours = 24
rolling_windows_hours = [3, 24]

[split]
train_fraction = 0.70
validation_fraction = 0.15
random_seed = 42

[model]
max_iterations = 200

[output]
artifact_dir = "{artifact_dir.as_posix()}"
report_dir = "{report_dir.as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    report = run_pipeline(config_path)
    manifest = json.loads((artifact_dir / "split_manifest.json").read_text())

    assert 0.0 <= report["test"]["average_precision"] <= 1.0
    assert processed_path.exists()
    assert (artifact_dir / "model.joblib").exists()
    assert (report_dir / "metrics.json").exists()
    assert (report_dir / "README.md").exists()
    assert set(manifest["train"]).isdisjoint(manifest["validation"])
    assert set(manifest["train"]).isdisjoint(manifest["test"])
    assert set(manifest["validation"]).isdisjoint(manifest["test"])

    experiment_config = tmp_path / "experiments.toml"
    experiment_config.write_text(
        f"""
[data]
raw_dir = "{raw_dir.as_posix()}"
feature_path = "{processed_path.as_posix()}"

[tracking]
database = "{(tmp_path / 'mlflow.db').as_posix()}"
artifact_directory = "{(tmp_path / 'mlruns').as_posix()}"
experiment_name = "synthetic-test"

[evaluation]
horizon_hours = 24
selection_metric = "average_precision"

[baseline]
max_iterations = 200

[challenger]
learning_rate = 0.1
max_iterations = 5
max_leaf_nodes = 7
min_samples_leaf = 5
l2_regularization = 1.0

[output]
artifact_dir = "{(tmp_path / 'experiment-artifacts').as_posix()}"
report_dir = "{(tmp_path / 'comparison').as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    comparison = run_experiments(experiment_config)

    assert set(comparison["models"]) == {
        "logistic_regression",
        "hist_gradient_boosting",
    }
    assert comparison["champion"] in comparison["models"]
    assert (tmp_path / "comparison" / "comparison.json").exists()
    candidate_path = tmp_path / "experiment-artifacts" / "candidate.json"
    assert candidate_path.exists()
    candidate = json.loads(candidate_path.read_text())
    assert Path(candidate["model_path"]).exists()
    assert "metrics" in candidate
