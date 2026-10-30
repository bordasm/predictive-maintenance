# API security and deployment hardening

The inference API supports an optional `X-API-Key` authentication scheme for all
`/v1/*` endpoints. Set `PREDMAINT_API_KEY` to enable it. Health and Prometheus
endpoints remain unauthenticated so orchestrator probes and internal scraping can
operate; production ingress and network policy should keep those operational
endpoints private.

Every regular response includes a bounded `X-Request-ID`, `X-Content-Type-Options:
nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and
`Cache-Control: no-store`. Request bodies larger than 1 MiB are rejected before
JSON parsing. API keys use constant-time comparison and are never used as metric
labels.

The Compose service runs with a read-only root filesystem, all Linux capabilities
dropped, privilege escalation disabled, and a bounded temporary filesystem. The
Kubernetes base adds:

- UID/GID 10001 and `RuntimeDefault` seccomp;
- no mounted service-account token;
- API key from a Kubernetes Secret;
- CPU and memory requests and limits;
- readiness and liveness probes;
- separate read-only model and writable prediction volumes.

The Kubernetes deployment deliberately uses one replica and `Recreate` strategy.
SQLite is suitable for this portfolio deployment but cannot back horizontally
scaled API pods. PostgreSQL or an asynchronous event sink is required before
increasing the replica count.

GitHub CodeQL runs on pushes, pull requests, a weekly schedule, and manual
dispatch. Dependabot checks Python and GitHub Actions dependencies weekly. All
third-party Actions are pinned to immutable commit SHAs.
