"""Load the champion manifest and perform deterministic batch inference."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

import joblib
import numpy as np
import pandas as pd

from predictive_maintenance.serving.schemas import FeatureVector


@dataclass(frozen=True)
class ModelService:
    model: Any
    model_name: str
    model_version: str
    threshold: float
    selection_metric: str
    selection_value: float
    mlflow_run_id: str
    feature_names: tuple[str, ...]

    @classmethod
    def load(cls, manifest_path: str | Path) -> ModelService:
        manifest_file = Path(manifest_path)
        if not manifest_file.is_file():
            raise FileNotFoundError(f"Champion manifest not found: {manifest_file}")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        configured_value = str(manifest["model_path"])
        configured_path = Path(configured_value)
        windows_parts = PureWindowsPath(configured_value).parts
        candidates = (
            configured_path,
            manifest_file.parent.joinpath(*windows_parts),
            manifest_file.parent / configured_path.name,
            manifest_file.parent / PureWindowsPath(configured_value).name,
        )
        model_path = next((path for path in candidates if path.is_file()), None)
        if model_path is None:
            raise FileNotFoundError(
                "Champion model not found. Checked: "
                + ", ".join(str(path) for path in candidates)
            )

        model = joblib.load(model_path)
        feature_names = tuple(str(name) for name in model.feature_names_in_)
        run_id = str(manifest["mlflow_run_id"])
        return cls(
            model=model,
            model_name=str(manifest["model"]),
            model_version=run_id[:12],
            threshold=float(manifest["threshold"]),
            selection_metric=str(manifest["selection_metric"]),
            selection_value=float(manifest["selection_value"]),
            mlflow_run_id=run_id,
            feature_names=feature_names,
        )

    def predict(self, observations: list[FeatureVector]) -> list[tuple[float, bool]]:
        frame = pd.DataFrame([item.model_dump() for item in observations])
        missing = sorted(set(self.feature_names).difference(frame.columns))
        if missing:
            raise ValueError(f"Missing model features: {missing}")
        probabilities = np.asarray(
            self.model.predict_proba(frame.loc[:, self.feature_names])[:, 1],
            dtype=float,
        )
        return [
            (float(probability), bool(probability >= self.threshold))
            for probability in probabilities
        ]
