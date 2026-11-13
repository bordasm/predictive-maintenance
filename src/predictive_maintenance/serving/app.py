"""FastAPI application for online champion-model inference."""

from __future__ import annotations

import os
from uuid import uuid4
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from predictive_maintenance.monitoring.store import (
    DuplicateObservationError,
    PredictionRecord,
)
from predictive_maintenance.observability.metrics import (
    ServiceMetrics,
    normalize_http_path,
)
from predictive_maintenance.serving.model_service import ModelService
from predictive_maintenance.serving.authentication import (
    AuthenticatedUser,
    TokenVerifier,
    build_identity_guard,
)
from predictive_maintenance.serving.demo_data import DemoDataset, load_demo_dataset
from predictive_maintenance.serving.prediction_logging import build_prediction_logger
from predictive_maintenance.serving.security import valid_request_id
from predictive_maintenance.serving.schemas import (
    HealthResponse,
    ModelInfoResponse,
    Prediction,
    PredictionBatch,
    PredictionResponse,
)


DEFAULT_MANIFEST = Path("artifacts/experiments/champion.json")
DEFAULT_PREDICTION_DATABASE = Path("monitoring/predictions.db")
DEFAULT_DEMO_DATA = Path("data/demo/demo-samples.json")
DEFAULT_MAX_REQUEST_BYTES = 1024 * 1024


def create_app(
    manifest_path: str | Path | None = None,
    prediction_database: str | Path | None = None,
    api_key: str | None = None,
    max_request_bytes: int | None = None,
    firebase_project_id: str | None = None,
    token_verifier: TokenVerifier | None = None,
    prediction_backend: str | None = None,
    demo_data_path: str | Path | None = None,
) -> FastAPI:
    configured_manifest = Path(
        manifest_path
        or os.environ.get("PREDMAINT_CHAMPION_MANIFEST", DEFAULT_MANIFEST)
    )
    configured_database = Path(
        prediction_database
        or os.environ.get("PREDMAINT_PREDICTION_DB", DEFAULT_PREDICTION_DATABASE)
    )
    configured_api_key = api_key or os.environ.get("PREDMAINT_API_KEY")
    configured_firebase_project = firebase_project_id or os.environ.get(
        "PREDMAINT_FIREBASE_PROJECT_ID"
    )
    configured_prediction_backend = prediction_backend or os.environ.get(
        "PREDMAINT_PREDICTION_BACKEND", "sqlite"
    )
    configured_firestore_collection = os.environ.get(
        "PREDMAINT_FIRESTORE_COLLECTION", "predictions"
    )
    configured_demo_data = Path(
        demo_data_path or os.environ.get("PREDMAINT_DEMO_DATA", DEFAULT_DEMO_DATA)
    )
    configured_max_request_bytes = max_request_bytes or int(
        os.environ.get("PREDMAINT_MAX_REQUEST_BYTES", DEFAULT_MAX_REQUEST_BYTES)
    )
    if configured_max_request_bytes <= 0:
        raise ValueError("Maximum request size must be positive")
    require_identity = build_identity_guard(
        configured_firebase_project,
        configured_api_key,
        token_verifier,
    )
    metrics = ServiceMetrics()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.model_service = ModelService.load(configured_manifest)
        application.state.prediction_logger = build_prediction_logger(
            configured_prediction_backend,
            database_path=str(configured_database),
            project_id=configured_firebase_project,
            collection=configured_firestore_collection,
        )
        application.state.demo_dataset = (
            load_demo_dataset(configured_demo_data)
            if configured_demo_data.is_file()
            else None
        )
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
        version="1.3.0",
        lifespan=lifespan,
    )
    allowed_origins = [
        origin.strip()
        for origin in os.environ.get("PREDMAINT_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )

    @application.middleware("http")
    async def observe_http(request: Request, call_next):
        record_metrics = request.url.path != "/metrics"
        supplied_request_id = request.headers.get("X-Request-ID")
        request_id = (
            supplied_request_id if valid_request_id(supplied_request_id) else uuid4().hex
        )
        request.state.request_id = request_id
        started_at = perf_counter()
        response_status = 500
        try:
            content_length = request.headers.get("content-length")
            try:
                request_bytes = int(content_length) if content_length else 0
            except ValueError:
                request_bytes = -1
            if request_bytes < 0:
                response = JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid Content-Length header"},
                )
            elif request_bytes > configured_max_request_bytes:
                response = JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": "Request body is too large"},
                )
            else:
                response = await call_next(request)
            response_status = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Cache-Control"] = "no-store"
            return response
        finally:
            if record_metrics:
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
            status="ready",
            model=service.model_name,
            prediction_logging=request.app.state.prediction_logger.enabled,
        )

    @application.get(
        "/v1/model-info",
        response_model=ModelInfoResponse,
        tags=["inference"],
    )
    def model_info(
        request: Request,
        identity: AuthenticatedUser = Depends(require_identity),
    ) -> ModelInfoResponse:
        del identity
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

    @application.get(
        "/v1/demo-samples",
        response_model=DemoDataset,
        tags=["inference"],
    )
    def demo_samples(
        request: Request,
        identity: AuthenticatedUser = Depends(require_identity),
    ) -> DemoDataset:
        del identity
        dataset: DemoDataset | None = request.app.state.demo_dataset
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Held-out demonstration data is not configured",
            )
        return dataset

    @application.post(
        "/v1/predict",
        response_model=PredictionResponse,
        tags=["inference"],
    )
    def predict(
        payload: PredictionBatch,
        request: Request,
        identity: AuthenticatedUser = Depends(require_identity),
    ) -> PredictionResponse:
        service: ModelService = request.app.state.model_service
        logger = request.app.state.prediction_logger
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
            logger.write_batch(
                records,
                model_name=service.model_name,
                model_version=service.model_version,
                mlflow_run_id=service.mlflow_run_id,
                threshold=service.threshold,
                latency_ms=latency_ms,
                user=identity,
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
