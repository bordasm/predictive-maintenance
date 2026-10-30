# Automated delivery and retraining

## Container delivery

The CI workflow runs tests first, then builds the serving Dockerfile and checks
that the Python application imports, the configured runtime user is `appuser`,
and the image contains a health check. Pull requests stop after verification.
A successful push to `main` publishes two images to GHCR:

- `ghcr.io/bordasm/predictive-maintenance:sha-<git-commit>` is immutable and
  identifies the exact source revision;
- `ghcr.io/bordasm/predictive-maintenance:latest` is the convenient moving tag.

The model stays outside this serving image. This preserves the existing design
where application delivery and governed model promotion have independent
rollback paths.

## Retraining triggers

`.github/workflows/retrain.yml` supports three triggers:

- Monday at 03:23 UTC;
- a manual Actions run, with an explicit `promote` checkbox;
- the `training-data-updated` repository-dispatch event for an upstream data
  pipeline.

Only one model-lifecycle run executes at a time. A new run waits instead of
cancelling an in-progress training job.

Before training, the workflow restores the newest non-expired
`production-model` artifact, including its release history. The tracked
`configs/incumbent_seed.json` benchmark is used only for the first run or after
all production artifacts have expired. This makes the relative validation gate
compare against the current packaged champion during normal operation.

## Required repository configuration

| Setting | Kind | Purpose |
|---|---|---|
| `PREDMAINT_DATA_URL` | Actions secret | Direct HTTPS URL of the raw Azure PdM ZIP |
| `PREDMAINT_DATA_SHA256` | Actions variable | Expected lowercase SHA-256 digest |
| `PREDMAINT_AUTO_PROMOTE` | Actions variable | Set to `true` to request promotion for scheduled/event runs |
| `model-production` | GitHub Environment | Optional required-reviewer and deployment-policy boundary |

The downloader limits archive size and member count, rejects traversal paths and
symlinks, verifies the digest before extraction, and requires all five source
CSVs exactly once. A missing URL or checksum fails before training.

## Promotion behavior

Every successful training job uploads a 30-day candidate artifact containing
the model, baseline/comparison reports, lifecycle summary, and six-gate decision.
A rejected candidate completes the audit path and cannot enter the promotion
job.

When promotion was requested and every gate passed, the `model-production` job
downloads the exact candidate from the same workflow run and executes the normal
promotion command. That command evaluates the gates again, creates an immutable
release directory, and updates the bundled champion manifest. The resulting
`production-model` bundle is retained as a GitHub Actions artifact for 90 days.

For a long-lived production system, copy that bundle to the organization's model
registry or versioned object store during the environment-specific deployment
step. The GitHub artifact is a reviewable portfolio implementation and a handoff
contract, not permanent model storage.
