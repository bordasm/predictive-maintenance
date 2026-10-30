"""Prometheus metrics with bounded-cardinality labels."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

KNOWN_HTTP_PATHS = frozenset({"/health", "/v1/model-info", "/v1/predict"})


def normalize_http_path(path: str) -> str:
    """Prevent arbitrary request paths from creating unbounded label values."""
    return path if path in KNOWN_HTTP_PATHS else "unmatched"


class ServiceMetrics:
    """Metrics registry owned by one application instance."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "predmaint_http_requests_total",
            "HTTP requests handled by the inference service.",
            ("method", "path", "status"),
            registry=self.registry,
        )
        self.http_duration = Histogram(
            "predmaint_http_request_duration_seconds",
            "End-to-end HTTP request duration.",
            ("method", "path"),
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
            registry=self.registry,
        )
        self.inference_duration = Histogram(
            "predmaint_inference_duration_seconds",
            "Model inference duration, excluding persistence and serialization.",
            buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
            registry=self.registry,
        )
        self.batch_size = Histogram(
            "predmaint_prediction_batch_size",
            "Number of observations in prediction requests.",
            buckets=(1, 2, 5, 10, 25, 50, 100, 250, 500, 1000),
            registry=self.registry,
        )
        self.predictions = Counter(
            "predmaint_predictions_total",
            "Individual model predictions by threshold decision.",
            ("decision",),
            registry=self.registry,
        )
        self.readiness = Gauge(
            "predmaint_service_ready",
            "One when the model and prediction store are ready.",
            registry=self.registry,
        )
        self.model_info = Gauge(
            "predmaint_model_info",
            "Loaded model identity.",
            ("model", "version", "mlflow_run_id"),
            registry=self.registry,
        )

    def set_ready(self, *, model: str, version: str, mlflow_run_id: str) -> None:
        self.model_info.labels(model, version, mlflow_run_id).set(1)
        self.readiness.set(1)

    def observe_predictions(
        self, *, inference_seconds: float, alerts: list[bool]
    ) -> None:
        self.inference_duration.observe(inference_seconds)
        self.batch_size.observe(len(alerts))
        alert_count = sum(alerts)
        self.predictions.labels("alert").inc(alert_count)
        self.predictions.labels("normal").inc(len(alerts) - alert_count)
