"""FastAPI application for online champion-model inference."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from predictive_maintenance.monitoring.store import (
    DuplicateObservationError,
    PredictionRecord,
    PredictionStore,
)
from predictive_maintenance.observability.metrics import (
    ServiceMetrics,
    normalize_http_path,
)
from predictive_maintenance.serving.model_service import ModelService
from predictive_maintenance.serving.schemas import (
    HealthResponse,
    ModelInfoResponse,
    Prediction,
    PredictionBatch,
    PredictionResponse,
)


DEFAULT_MANIFEST = Path("artifacts/experiments/champion.json")
DEFAULT_PREDICTION_DATABASE = Path("monitoring/predictions.db")


def create_app(
    manifest_path: str | Path | None = None,
    prediction_database: str | Path | None = None,
) -> FastAPI:
    configured_manifest = Path(
        manifest_path
        or os.environ.get("PREDMAINT_CHAMPION_MANIFEST", DEFAULT_MANIFEST)
    )
    configured_database = Path(
        prediction_database
        or os.environ.get("PREDMAINT_PREDICTION_DB", DEFAULT_PREDICTION_DATABASE)
    )
    metrics = ServiceMetrics()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.model_service = ModelService.load(configured_manifest)
        store = PredictionStore(configured_database)
        store.initialize()
        application.state.prediction_store = store
        metrics.set_ready(
            model=application.state.model_service.model_name,
            version=application.state.model_service.model_version,
            mlflow_run_id=application.state.model_service.mlflow_run_id,
        )
        yield
        metrics.readiness.set(0)

    application = FastAPI(
        title="Predictive Maintenance Inference API",
        description="Predict any component failure within the next 24 hours.",
        version="1.2.0",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def observe_http(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        started_at = perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        finally:
            metric_path = normalize_http_path(request.url.path)
            metrics.http_requests.labels(
                request.method, metric_path, str(response_status)
            ).inc()
            metrics.http_duration.labels(
                request.method, metric_path
            ).observe(perf_counter() - started_at)

    @application.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    def health(request: Request) -> HealthResponse:
        service: ModelService = request.app.state.model_service
        return HealthResponse(
            status="ready", model=service.model_name, prediction_logging=True
        )

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
        store: PredictionStore = request.app.state.prediction_store
        started_at = perf_counter()
        scores = service.predict([item.features for item in payload.observations])
        inference_seconds = perf_counter() - started_at
        latency_ms = inference_seconds * 1000
        metrics.observe_predictions(
            inference_seconds=inference_seconds,
            alerts=[score[1] for score in scores],
        )
        records = [
            PredictionRecord(
                observation=observation, probability=score[0], alert=score[1]
            )
            for observation, score in zip(payload.observations, scores, strict=True)
        ]
        try:
            store.write_batch(
                records,
                model_name=service.model_name,
                model_version=service.model_version,
                mlflow_run_id=service.mlflow_run_id,
                threshold=service.threshold,
                latency_ms=latency_ms,
            )
        except DuplicateObservationError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(error)
            ) from error
        return PredictionResponse(
            model=service.model_name,
            model_version=service.model_version,
            threshold=service.threshold,
            predictions=[
                Prediction(
                    observation_id=record.observation.observation_id,
                    machine_id=record.observation.machine_id,
                    observed_at=record.observation.observed_at,
                    failure_probability=record.probability,
                    alert=record.alert,
                )
                for record in records
            ],
        )

    return application


app = create_app()
