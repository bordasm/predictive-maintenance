"""Versioned HTTP request and response contracts."""

from __future__ import annotations

from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ModelName = Literal["hist_gradient_boosting", "lstm", "transformer"]


class FeatureVector(BaseModel):
    """Features available at one machine observation timestamp."""

    model_config = ConfigDict(extra="forbid")

    volt: float
    rotate: float
    pressure: float
    vibration: float
    volt_mean_3h: float
    volt_std_3h: float = Field(ge=0)
    rotate_mean_3h: float
    rotate_std_3h: float = Field(ge=0)
    pressure_mean_3h: float
    pressure_std_3h: float = Field(ge=0)
    vibration_mean_3h: float
    vibration_std_3h: float = Field(ge=0)
    volt_mean_24h: float
    volt_std_24h: float = Field(ge=0)
    rotate_mean_24h: float
    rotate_std_24h: float = Field(ge=0)
    pressure_mean_24h: float
    pressure_std_24h: float = Field(ge=0)
    vibration_mean_24h: float
    vibration_std_24h: float = Field(ge=0)
    error1_count_24h: float = Field(ge=0)
    error2_count_24h: float = Field(ge=0)
    error3_count_24h: float = Field(ge=0)
    error4_count_24h: float = Field(ge=0)
    error5_count_24h: float = Field(ge=0)
    days_since_comp1_maintenance: float = Field(ge=0)
    days_since_comp2_maintenance: float = Field(ge=0)
    days_since_comp3_maintenance: float = Field(ge=0)
    days_since_comp4_maintenance: float = Field(ge=0)
    age: int = Field(ge=0)
    model: str = Field(min_length=1, max_length=64)


class PredictionObservation(BaseModel):
    """A traceable observation and the features used for inference."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1, max_length=128)
    machine_id: int = Field(ge=1)
    observed_at: datetime
    features: FeatureVector
    sequence: list[FeatureVector] | None = Field(default=None, min_length=2, max_length=168)


class PredictionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: ModelName = "hist_gradient_boosting"
    observations: list[PredictionObservation] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def require_sequence_for_temporal_models(self) -> "PredictionBatch":
        if self.model in {"lstm", "transformer"}:
            missing = [item.observation_id for item in self.observations if item.sequence is None]
            if missing:
                raise ValueError(
                    f"Model '{self.model}' requires a trailing feature sequence "
                    "for every observation"
                )
        return self


class Prediction(BaseModel):
    observation_id: str
    machine_id: int
    observed_at: datetime
    failure_probability: float = Field(ge=0, le=1)
    alert: bool


class PredictionResponse(BaseModel):
    model: str
    model_version: str
    threshold: float
    predictions: list[Prediction]
    guest_observations_remaining: int | None = None


class HealthResponse(BaseModel):
    status: str
    model: str
    prediction_logging: bool


class ModelInfoResponse(BaseModel):
    model: str
    model_version: str
    threshold: float
    feature_count: int
    selection_metric: str
    selection_value: float
    mlflow_run_id: str
    input_type: Literal["feature_row", "sequence_window"] = "feature_row"
    window_size: int = 1
    is_default: bool = False


class ModelListResponse(BaseModel):
    default_model: ModelName
    models: list[ModelInfoResponse]
