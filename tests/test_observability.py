from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.load_test_api import RequestResult, summarize_results


def test_load_test_summary_calculates_slo_signals() -> None:
    results = [
        RequestResult(200, 10.0),
        RequestResult(200, 20.0),
        RequestResult(500, 30.0, "server error"),
        RequestResult(200, 40.0),
    ]

    summary = summarize_results(results, wall_seconds=2.0)

    assert summary["requests"] == 4
    assert summary["successful_requests"] == 3
    assert summary["error_rate"] == pytest.approx(0.25)
    assert summary["throughput_requests_per_second"] == 2.0
    assert summary["latency_ms"]["p50"] == 25.0
    assert summary["status_counts"] == {"200": 3, "500": 1}


def test_observability_stack_configuration_is_well_formed() -> None:
    root = Path(__file__).parents[1]
    compose = yaml.safe_load((root / "compose.yaml").read_text(encoding="utf-8"))
    prometheus = yaml.safe_load(
        (root / "observability/prometheus/prometheus.yml").read_text(encoding="utf-8")
    )
    alerts = yaml.safe_load(
        (root / "observability/prometheus/alerts.yml").read_text(encoding="utf-8")
    )
    dashboard = json.loads(
        (root / "observability/grafana/dashboards/service-overview.json").read_text(
            encoding="utf-8"
        )
    )

    assert {"inference-api", "prometheus", "grafana"}.issubset(compose["services"])
    assert prometheus["scrape_configs"][0]["metrics_path"] == "/metrics"
    assert len(alerts["groups"][0]["rules"]) == 4
    assert dashboard["uid"] == "predmaint-service"
    assert len(dashboard["panels"]) == 7
