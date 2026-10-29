# Predictive Maintenance

An end-to-end predictive-maintenance and MLOps portfolio project. The first
milestone predicts whether any machine component will fail during the next
24 hours using the Microsoft Azure Predictive Maintenance sample dataset.

The implementation deliberately separates exploratory notebooks from reusable
code. Older TensorFlow/Keras experiments are kept under `notebooks/legacy`.

## First milestone

The baseline pipeline:

1. loads and validates the five source tables;
2. creates trailing sensor, error-count, and maintenance-recency features;
3. labels failures in the strictly future 24-hour prediction window;
4. assigns complete machines to train, validation, and test partitions;
5. fits preprocessing and a class-balanced logistic regression on training data;
6. selects the decision threshold on validation data only;
7. writes the held-out test metrics, model, and split manifest.

The test set is not used for preprocessing, model fitting, or threshold
selection.

## Data

Download the [Microsoft Azure Predictive Maintenance dataset](https://www.kaggle.com/datasets/arnabbiswas1/microsoft-azure-predictive-maintenance)
and place these files in `data/raw/azure_pdm/`:

```text
PdM_telemetry.csv
PdM_errors.csv
PdM_maint.csv
PdM_failures.csv
PdM_machines.csv
```

Raw and generated data are intentionally excluded from Git.

## Environment

The project uses Python 3.14 and `uv`. On this workstation the environment is
stored in `.predmaint`, so set the project environment before running commands:

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".predmaint"
uv sync
```

The PyTorch dependency is resolved from the CUDA 12.6 package index.

## Run

Execute tests:

```powershell
uv run pytest
```

Run the complete baseline pipeline:

```powershell
uv run python -m predictive_maintenance.pipeline --config configs/baseline.toml
```

Generated outputs:

```text
data/processed/azure_pdm_features.parquet
artifacts/baseline/model.joblib
artifacts/baseline/metadata.json
artifacts/baseline/split_manifest.json
reports/baseline/metrics.json
reports/baseline/README.md
```

The model and large data artifacts are excluded from Git. The compact report is
kept in Git as reproducible portfolio evidence. It records raw-file SHA-256
fingerprints and runtime versions alongside the metrics.

## Baseline result

On the machine-disjoint held-out test partition, the logistic-regression baseline
reached **0.858 PR-AUC**, **0.740 precision**, and **0.870 row-level recall**. It
detected **122 of 126 eligible failure events** and produced about **1.12 false
positive hourly decisions per machine-week**. See the [full baseline report](reports/baseline/README.md)
and its [machine-readable metrics](reports/baseline/metrics.json).

The source dataset is simulated. These numbers demonstrate the implementation and
evaluation workflow; they should not be read as expected performance on real
industrial equipment.
