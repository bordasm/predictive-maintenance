"""Shared data structures and aggregation for inference load tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RequestResult:
    status: int
    latency_ms: float
    error: str | None = None


def summarize_results(
    results: list[RequestResult], *, wall_seconds: float
) -> dict[str, Any]:
    if not results:
        raise ValueError("At least one request result is required")
    if wall_seconds <= 0:
        raise ValueError("wall_seconds must be positive")
    latencies = np.asarray([item.latency_ms for item in results], dtype=float)
    successes = sum(item.status == 200 for item in results)
    return {
        "requests": len(results),
        "successful_requests": successes,
        "error_rate": float(1 - successes / len(results)),
        "throughput_requests_per_second": float(len(results) / wall_seconds),
        "latency_ms": {
            "minimum": float(latencies.min()),
            "p50": float(np.percentile(latencies, 50)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
            "maximum": float(latencies.max()),
        },
        "status_counts": {
            str(status): sum(item.status == status for item in results)
            for status in sorted({item.status for item in results})
        },
        "errors": [asdict(item) for item in results if item.error],
    }
