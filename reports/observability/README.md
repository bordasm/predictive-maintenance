# Service observability and SLOs

The inference API exposes Prometheus metrics at `GET /metrics`. The Compose stack
scrapes them every five seconds and provisions a Grafana dashboard without manual
setup.

## Service-level objectives

| Signal | Objective | Alert condition |
|---|---:|---:|
| Availability | 99.5% over 30 days | Target unavailable for 2 minutes |
| Prediction 5xx rate | Below 1% | Above 1% for 10 minutes |
| Prediction p95 latency | Below 500 ms | Above 500 ms for 10 minutes |
| Readiness | Model and store ready | Not ready for 2 minutes |

The alert ratio is displayed as an operational signal but is not treated as a
service failure. A high alert ratio can describe a real change in machine health;
feature and prediction drift remain the responsibility of the model-monitoring
pipeline.

The dashboard uses bounded labels: method, fixed endpoint, HTTP status, model
identity, and alert decision. Machine IDs and observation IDs are intentionally
excluded to prevent unbounded Prometheus series growth.

## Local stack

```powershell
docker compose up --build
```

- API and metrics: `http://127.0.0.1:8000`
- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3000`

Generate a bounded local load-test report while the API is running:

```powershell
uv run python scripts/load_test_api.py --requests 200 --concurrency 8
```

The test covers validation, inference, and durable prediction logging. Results
depend on the workstation and are portfolio evidence, not production capacity
guarantees.
