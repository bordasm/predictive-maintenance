"""Versioned HTTP request and response contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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


class PredictionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[FeatureVector] = Field(min_length=1, max_length=1000)


class Prediction(BaseModel):
    failure_probability: float = Field(ge=0, le=1)
    alert: bool


class PredictionResponse(BaseModel):
    model: str
    model_version: str
    threshold: float
    predictions: list[Prediction]


class HealthResponse(BaseModel):
    status: str
    model: str


class ModelInfoResponse(BaseModel):
    model: str
    model_version: str
    threshold: float
    feature_count: int
    selection_metric: str
    selection_value: float
    mlflow_run_id: str
