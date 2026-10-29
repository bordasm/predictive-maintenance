"""Histogram gradient-boosting challenger model."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder


def build_challenger_model(
    numerical_columns: list[str],
    categorical_columns: list[str],
    *,
    learning_rate: float = 0.08,
    max_iterations: int = 150,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 50,
    l2_regularization: float = 1.0,
) -> Pipeline:
    """Build a class-balanced tree model with native categorical splits."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", numerical_columns),
            (
                "categorical",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
                categorical_columns,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    categorical_indices = list(
        range(len(numerical_columns), len(numerical_columns) + len(categorical_columns))
    )
    classifier = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_iter=max_iterations,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        categorical_features=categorical_indices,
        class_weight="balanced",
        early_stopping=False,
        random_state=42,
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])
