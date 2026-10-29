"""Interpretable logistic-regression baseline."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NON_FEATURE_COLUMNS = {
    "datetime",
    "machineID",
    "failure_within_horizon",
    "split",
}


def feature_columns(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    candidates = [column for column in frame.columns if column not in NON_FEATURE_COLUMNS]
    categorical = [column for column in candidates if column == "model"]
    numerical = [column for column in candidates if column not in categorical]
    return numerical, categorical


def build_baseline_model(
    numerical_columns: list[str],
    categorical_columns: list[str],
    *,
    max_iterations: int = 1000,
) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numerical_columns),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )
    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=max_iterations,
        random_state=42,
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])


def predict_probabilities(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(frame)[:, 1]
