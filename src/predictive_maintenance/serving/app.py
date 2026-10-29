"""FastAPI application for online champion-model inference."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request

from predictive_maintenance.serving.model_service import ModelService
from predictive_maintenance.serving.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictionBatch,
    PredictionResponse,
)


DEFAULT_MANIFEST = Path("artifacts/experiments/champion.json")


def create_app(manifest_path: str | Path | None = None) -> FastAPI:
    configured_manifest = Path(
        manifest_path
        or os.environ.get("PREDMAINT_CHAMPION_MANIFEST", DEFAULT_MANIFEST)
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.model_service = ModelService.load(configured_manifest)
        yield

    application = FastAPI(
        title="Predictive Maintenance Inference API",
        description="Predict any component failure within the next 24 hours.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    def health(request: Request) -> HealthResponse:
        service: ModelService = request.app.state.model_service
        return HealthResponse(status="ready", model=service.model_name)

    @application.get(
        "/v1/model-info", response_model=ModelInfoResponse, tags=["inference"]
    )
    def model_info(request: Request) -> ModelInfoResponse:
        service: ModelService = request.app.state.model_service
        return ModelInfoResponse(
            model=service.model_name,
            model_version=service.model_version,
            threshold=service.threshold,
            feature_count=len(service.feature_names),
            selection_metric=service.selection_metric,
            selection_value=service.selection_value,
            mlflow_run_id=service.mlflow_run_id,
        )

    @application.post(
        "/v1/predict", response_model=PredictionResponse, tags=["inference"]
    )
    def predict(payload: PredictionBatch, request: Request) -> PredictionResponse:
        service: ModelService = request.app.state.model_service
        return PredictionResponse(
            model=service.model_name,
            model_version=service.model_version,
            threshold=service.threshold,
            predictions=service.predict(payload.observations),
        )

    return application


app = create_app()
