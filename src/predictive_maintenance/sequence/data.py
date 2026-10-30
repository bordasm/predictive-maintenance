"""Leakage-safe preprocessing and temporal-window indexing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.models.baseline import feature_columns


@dataclass(frozen=True)
class SequencePreprocessor:
    numerical_columns: tuple[str, ...]
    categorical_column: str
    categories: tuple[str, ...]
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, train: pd.DataFrame) -> "SequencePreprocessor":
        numerical, categorical = feature_columns(train)
        if categorical != ["model"]:
            raise ValueError(f"Expected only the model categorical feature, found {categorical}")
        values = train[numerical].to_numpy(dtype=np.float64)
        mean = np.nanmean(values, axis=0)
        scale = np.nanstd(values, axis=0)
        scale[~np.isfinite(scale) | (scale < 1e-12)] = 1.0
        categories = tuple(sorted(str(value) for value in train["model"].dropna().unique()))
        if not categories:
            raise ValueError("Training data contains no machine-model categories")
        return cls(tuple(numerical), "model", categories, mean, scale)

    @property
    def output_features(self) -> tuple[str, ...]:
        encoded = tuple(f"model={category}" for category in self.categories)
        return self.numerical_columns + encoded

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        numerical = frame[list(self.numerical_columns)].to_numpy(dtype=np.float64)
        numerical = (numerical - self.mean) / self.scale
        numerical = np.nan_to_num(numerical, nan=0.0, posinf=0.0, neginf=0.0)
        categorical = np.zeros((len(frame), len(self.categories)), dtype=np.float32)
        values = frame[self.categorical_column].astype(str).to_numpy()
        for index, category in enumerate(self.categories):
            categorical[:, index] = values == category
        return np.ascontiguousarray(
            np.concatenate([numerical.astype(np.float32), categorical], axis=1)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "numerical_columns": list(self.numerical_columns),
            "categorical_column": self.categorical_column,
            "categories": list(self.categories),
            "mean": self.mean.tolist(),
            "scale": self.scale.tolist(),
            "output_features": list(self.output_features),
        }


def build_window_end_indices(
    frame: pd.DataFrame,
    *,
    window_size: int,
    stride: int = 1,
    preserve_positive_labels: bool = False,
) -> np.ndarray:
    """Return endpoints for complete, hourly windows contained in one machine."""
    if window_size < 2:
        raise ValueError("window_size must be at least two")
    if stride < 1:
        raise ValueError("stride must be positive")
    required = {"machineID", "datetime", "failure_within_horizon"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Window frame is missing columns: {sorted(missing)}")

    endpoints: list[np.ndarray] = []
    labels = frame["failure_within_horizon"].to_numpy(dtype=np.int8)
    for _, positions in frame.groupby("machineID", sort=False).indices.items():
        positions = np.asarray(positions, dtype=np.int64)
        times = frame.iloc[positions]["datetime"].to_numpy(dtype="datetime64[ns]")
        breaks = np.flatnonzero(np.diff(times) != np.timedelta64(1, "h")) + 1
        for segment in np.split(positions, breaks):
            if len(segment) < window_size:
                continue
            eligible = segment[window_size - 1 :]
            selected = eligible[::stride]
            if preserve_positive_labels:
                positives = eligible[labels[eligible] == 1]
                selected = np.union1d(selected, positives)
            endpoints.append(selected)
    if not endpoints:
        return np.empty(0, dtype=np.int64)
    return np.concatenate(endpoints).astype(np.int64, copy=False)

