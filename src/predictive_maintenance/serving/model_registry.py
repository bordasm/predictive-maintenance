"""Load tabular and temporal inference models behind one API contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Protocol

import numpy as np
import pandas as pd

from predictive_maintenance.serving.model_service import ModelService
from predictive_maintenance.serving.schemas import FeatureVector, PredictionObservation


class InferenceModel(Protocol):
    model_name: str
    model_version: str
    threshold: float
    selection_metric: str
    selection_value: float
    mlflow_run_id: str
    feature_names: tuple[str, ...]
    input_type: str
    window_size: int

    def predict(self, observations: list[PredictionObservation]) -> list[tuple[float, bool]]: ...


@dataclass(frozen=True)
class TabularInferenceModel:
    service: ModelService
    input_type: str = "feature_row"
    window_size: int = 1

    def __getattr__(self, name: str) -> Any:
        return getattr(self.service, name)

    def predict(self, observations: list[PredictionObservation]) -> list[tuple[float, bool]]:
        return self.service.predict([item.features for item in observations])


@dataclass(frozen=True)
class SequenceInferenceModel:
    model: Any
    model_name: str
    model_version: str
    threshold: float
    selection_metric: str
    selection_value: float
    mlflow_run_id: str
    feature_names: tuple[str, ...]
    preprocessor: Any
    window_size: int
    input_type: str = "sequence_window"

    @classmethod
    def load(cls, entry: dict[str, Any], registry_path: Path) -> "SequenceInferenceModel":
        from predictive_maintenance.sequence.data import SequencePreprocessor
        from predictive_maintenance.sequence.models import load_sequence_checkpoint

        checkpoint_path = _resolve_path(str(entry["model_path"]), registry_path)
        model, checkpoint = load_sequence_checkpoint(checkpoint_path, device="cpu")
        preprocessing = checkpoint["preprocessor"]
        preprocessor = SequencePreprocessor(
            numerical_columns=tuple(preprocessing["numerical_columns"]),
            categorical_column=str(preprocessing["categorical_column"]),
            categories=tuple(preprocessing["categories"]),
            mean=np.asarray(preprocessing["mean"], dtype=np.float64),
            scale=np.asarray(preprocessing["scale"], dtype=np.float64),
        )
        run_id = str(entry["mlflow_run_id"])
        return cls(
            model=model,
            model_name=str(entry["model"]),
            model_version=run_id[:12],
            threshold=float(entry["threshold"]),
            selection_metric=str(entry["selection_metric"]),
            selection_value=float(entry["selection_value"]),
            mlflow_run_id=run_id,
            feature_names=preprocessor.output_features,
            preprocessor=preprocessor,
            window_size=int(checkpoint["window_size"]),
        )

    def predict(self, observations: list[PredictionObservation]) -> list[tuple[float, bool]]:
        import torch

        transformed: list[np.ndarray] = []
        for observation in observations:
            if observation.sequence is None:
                raise ValueError(f"Model '{self.model_name}' requires a sequence window")
            if len(observation.sequence) != self.window_size:
                raise ValueError(
                    f"Model '{self.model_name}' requires exactly {self.window_size} hourly rows; "
                    f"received {len(observation.sequence)}"
                )
            frame = pd.DataFrame([item.model_dump() for item in observation.sequence])
            transformed.append(self.preprocessor.transform(frame))
        values = torch.from_numpy(np.stack(transformed)).to(dtype=torch.float32)
        with torch.inference_mode():
            probabilities = torch.sigmoid(self.model(values)).cpu().numpy()
        return [
            (float(probability), bool(probability >= self.threshold))
            for probability in probabilities
        ]


@dataclass(frozen=True)
class ModelRegistry:
    models: dict[str, InferenceModel]
    default_model: str

    @classmethod
    def load(cls, registry_path: str | Path) -> "ModelRegistry":
        path = Path(registry_path)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        loaded: dict[str, InferenceModel] = {}
        for name, entry in manifest["models"].items():
            if entry["input_type"] == "feature_row":
                manifest_path = _resolve_path(str(entry["manifest_path"]), path)
                loaded[name] = TabularInferenceModel(ModelService.load(manifest_path))
            else:
                loaded[name] = SequenceInferenceModel.load(entry, path)
        default = str(manifest["default_model"])
        if default not in loaded:
            raise ValueError(f"Default model '{default}' is not present in the registry")
        return cls(models=loaded, default_model=default)

    @classmethod
    def from_tabular_manifest(cls, manifest_path: str | Path) -> "ModelRegistry":
        service = TabularInferenceModel(ModelService.load(manifest_path))
        return cls(models={service.model_name: service}, default_model=service.model_name)

    def get(self, model_name: str) -> InferenceModel:
        try:
            return self.models[model_name]
        except KeyError as error:
            raise ValueError(f"Unsupported model: {model_name}") from error


def _resolve_path(configured_value: str, manifest_file: Path) -> Path:
    configured = Path(configured_value)
    windows_parts = PureWindowsPath(configured_value).parts
    candidates = (
        configured,
        manifest_file.parent.joinpath(*windows_parts),
        manifest_file.parent / configured.name,
        manifest_file.parent / PureWindowsPath(configured_value).name,
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        checked = ", ".join(map(str, candidates))
        raise FileNotFoundError(f"Model artifact not found. Checked: {checked}")
    return path
