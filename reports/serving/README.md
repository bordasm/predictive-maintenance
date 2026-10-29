# Champion inference service

The FastAPI service loads the `hist_gradient_boosting` champion selected by the
MLflow experiment and exposes a versioned inference contract.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Readiness and loaded-model check |
| `GET /v1/model-info` | Model, threshold, feature count, and MLflow version |
| `POST /v1/predict` | Validated batch prediction for up to 1,000 observations |

Local smoke testing used the actual champion artifact and the checked-in
`examples/prediction_request.json`. All three requests returned HTTP 200. The
service reported:

```text
model: hist_gradient_boosting
model version: 97293e9d3f3a
feature count: 31
decision threshold: 0.6860872735765084
sample failure probability: 0.00429159391192707
sample alert: false
```

The API loads the model once during application lifespan startup. Invalid feature
ranges and unknown request fields produce HTTP 422 responses before inference.
The automated test suite covers successful loading and prediction as well as an
invalid negative rolling standard deviation.

The Docker and Compose definitions are included, but the local Docker daemon was
not available during verification. The native Uvicorn service and its complete
HTTP request path were verified on Python 3.14.10.
