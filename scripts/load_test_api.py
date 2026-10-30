"""Run a bounded concurrent load test against the prediction endpoint."""

from __future__ import annotations

import argparse
import copy
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from predictive_maintenance.observability.load_test import (
    RequestResult,
    summarize_results,
)


def _send_request(
    url: str,
    template: dict[str, Any],
    index: int,
    timeout: float,
    api_key: str | None,
) -> RequestResult:
    payload = copy.deepcopy(template)
    observation = payload["observations"][0]
    observation["observation_id"] = f"load-{time.time_ns()}-{index}"
    observation["observed_at"] = (
        datetime.now(UTC) + timedelta(microseconds=index)
    ).isoformat()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
            status = response.status
        return RequestResult(status, (time.perf_counter() - started_at) * 1000)
    except urllib.error.HTTPError as error:
        return RequestResult(
            error.code,
            (time.perf_counter() - started_at) * 1000,
            str(error),
        )
    except OSError as error:
        return RequestResult(
            0,
            (time.perf_counter() - started_at) * 1000,
            str(error),
        )


def _write_report(summary: dict[str, Any], output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "load-test.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    latency = summary["latency_ms"]
    markdown = f"""# Inference API load test

| Metric | Result |
|---|---:|
| Requests | {summary['requests']} |
| Successful | {summary['successful_requests']} |
| Error rate | {summary['error_rate']:.2%} |
| Throughput | {summary['throughput_requests_per_second']:.2f} requests/s |
| p50 latency | {latency['p50']:.2f} ms |
| p95 latency | {latency['p95']:.2f} ms |
| p99 latency | {latency['p99']:.2f} ms |
| Maximum latency | {latency['maximum']:.2f} ms |

This bounded local test exercises HTTP validation, model inference, and durable
SQLite prediction logging. It is a reproducible engineering check rather than a
capacity claim for production infrastructure.

The p95 objective is the service gate. A materially higher p99 indicates tail
latency under concurrent local SQLite writes; a multi-instance deployment should
use an external database or asynchronous event sink and repeat the capacity test.
"""
    (output_directory / "LOAD_TEST.md").write_text(markdown, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key")
    parser.add_argument(
        "--payload", type=Path, default=Path("examples/prediction_request.json")
    )
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/observability"))
    args = parser.parse_args()
    if args.requests <= 0 or args.concurrency <= 0:
        parser.error("requests and concurrency must be positive")
    template = json.loads(args.payload.read_text(encoding="utf-8"))
    started_at = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(
            executor.map(
                lambda index: _send_request(
                    f"{args.base_url}/v1/predict",
                    template,
                    index,
                    args.timeout,
                    args.api_key,
                ),
                range(args.requests),
            )
        )
    summary = summarize_results(
        results, wall_seconds=time.perf_counter() - started_at
    )
    _write_report(summary, args.output)
    print(json.dumps(summary, indent=2))
    if summary["error_rate"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
