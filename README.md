# Predictive Maintenance

An end-to-end predictive-maintenance and MLOps portfolio project. It predicts
whether any machine component will fail during the next 24 hours using the
Microsoft Azure Predictive Maintenance sample dataset, then tracks and compares
candidate models with MLflow.

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

## Second milestone

The experiment pipeline:

1. loads the versioned feature table produced by the baseline pipeline;
2. trains the logistic-regression baseline and a histogram gradient-boosting
   challenger on exactly the same rows;
3. applies native categorical splits and balanced class weights in the challenger;
4. selects each decision threshold on validation data;
5. logs parameters, validation/test metrics, model files, data fingerprints, and
   run IDs to a local MLflow experiment;
6. selects the champion by validation PR-AUC and writes a comparison report and
   champion manifest.

The held-out test result is reported only after model selection.

## Third milestone

The online inference service:

1. loads the champion manifest and model once during FastAPI lifespan startup;
2. exposes readiness, model metadata, and versioned batch-prediction endpoints;
3. validates all 31 model features with a strict Pydantic contract and rejects
   unknown or invalid fields;
4. returns the failure probability and a threshold-based 24-hour alert;
5. identifies the served model with its MLflow run ID;
6. includes an integration-tested sample request, smoke-test script, Dockerfile,
   and Compose configuration.

The API accepts model-ready features. Computing rolling features from streaming
telemetry remains an upstream responsibility; this keeps online model serving
separate from stateful feature computation. See the
[serving verification report](reports/serving/README.md).

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

Run the tracked baseline/challenger comparison:

```powershell
uv run python -m predictive_maintenance.experiments --config configs/experiments.toml
```

Open the local MLflow UI after at least one experiment run:

```powershell
uv run mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --port 5000
```

Then open `http://127.0.0.1:5000`.

Start the inference API locally:

```powershell
uv run uvicorn predictive_maintenance.serving.app:app --host 127.0.0.1 --port 8000
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.
Run the checked-in request against all public endpoints:

```powershell
uv run python scripts/smoke_api.py
```

The versioned endpoints are:

```text
GET  /health
GET  /v1/model-info
POST /v1/predict
```

Build and run the container after Docker with the Compose plugin is available:

```powershell
docker compose up --build
```

Compose mounts `artifacts/experiments/` read-only at `/models`, so the trained
model stays outside the image and can be replaced independently.

Generated outputs:

```text
data/processed/azure_pdm_features.parquet
artifacts/baseline/model.joblib
artifacts/baseline/metadata.json
artifacts/baseline/split_manifest.json
reports/baseline/metrics.json
reports/baseline/README.md
artifacts/experiments/champion.json
artifacts/experiments/hist_gradient_boosting.joblib
artifacts/experiments/logistic_regression.joblib
reports/model_comparison/comparison.json
reports/model_comparison/README.md
mlflow.db
mlruns/
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

## Model comparison result

The histogram gradient-boosting model was selected as champion because its
validation PR-AUC reached **0.987**, compared with **0.884** for logistic
regression. On held-out test machines it reached **0.9999 PR-AUC**, **0.997
precision**, **1.000 recall**, and detected **126 of 126 eligible failure
events**. See the [comparison report](reports/model_comparison/README.md) and
[machine-readable results](reports/model_comparison/comparison.json).

The near-perfect challenger score reflects the strong, synthetic patterns in this
sample dataset. It is useful for verifying the MLOps workflow, but it is not a
credible production-performance estimate for another machine fleet.
