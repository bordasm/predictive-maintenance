# Inference API load test

| Metric | Result |
|---|---:|
| Requests | 200 |
| Successful | 200 |
| Error rate | 0.00% |
| Throughput | 31.70 requests/s |
| p50 latency | 147.11 ms |
| p95 latency | 273.23 ms |
| p99 latency | 2735.32 ms |
| Maximum latency | 2799.74 ms |

This bounded local test exercises HTTP validation, model inference, and durable
SQLite prediction logging. It is a reproducible engineering check rather than a
capacity claim for production infrastructure.

The p95 objective is the service gate. A materially higher p99 indicates tail
latency under concurrent local SQLite writes; a multi-instance deployment should
use an external database or asynchronous event sink and repeat the capacity test.
