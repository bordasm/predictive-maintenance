# Google Cloud deployment

This deployment publishes two scale-to-zero Cloud Run services:

- a private FastAPI champion-model service, reachable through API Gateway;
- a public dashboard shell whose data and inference calls require an Identity
  Platform email/password account.

API Gateway validates Firebase ID tokens before invoking the private API. The
API verifies the forwarded token again, records predictions in Firestore, and
serves only observations from the machine-disjoint test partition. Public user
sign-up and self-deletion are disabled; users are managed in Google Cloud
Console under **Identity Platform > Users**.

## Deploy

Use a billing-enabled Google Cloud project. Run from the repository root in a
PowerShell environment with `gcloud`, Terraform, and `uv` available:

```powershell
.\deploy\gcp\deploy.ps1 -ProjectId <PROJECT_ID> -Region europe-west1
```

The script first shows the final Terraform plan and asks for confirmation. Add
`-AutoApprove` only in a controlled CI environment. The final output contains:

```text
api_url       = https://...gateway.dev
dashboard_url = https://...run.app
```

Create the first account from **Identity Platform > Users > Add user**. There is
no public registration page.

### Google Cloud Shell

When `gcloud` and Terraform are not installed locally, first create the portable
build bundle from the repository root:

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".predmaint"
uv run python scripts/export_demo_data.py
uv run python deploy/gcp/prepare_build_context.py
Compress-Archive -Path .gcp-build\* -DestinationPath predmaint-gcp.zip -Force
```

Upload `predmaint-gcp.zip` to Cloud Shell, then prepare and review the deployment:

```bash
unzip -q predmaint-gcp.zip -d predmaint-gcp
chmod +x predmaint-gcp/cloud-deploy.sh
./predmaint-gcp/cloud-deploy.sh prepare <PROJECT_ID> europe-west1
less predmaint-gcp/terraform/predmaint-plan.txt
```

Apply the reviewed plan:

```bash
./predmaint-gcp/cloud-deploy.sh apply <PROJECT_ID> europe-west1
```

REST clients sign in through Identity Platform, then call the gateway with:

```http
Authorization: Bearer <FIREBASE_ID_TOKEN>
```

The Firebase Web API key identifies the Identity Platform project; it is not an
authorization credential. Terraform passes it only to the dashboard runtime.

## Live deployment

The current portfolio deployment is available at:

- dashboard: <https://predmaint-dashboard-agq2q67cmq-ew.a.run.app/>;
- REST API gateway: <https://predmaint-gateway-222il7n.ew.gateway.dev>;
- public health check: <https://predmaint-gateway-222il7n.ew.gateway.dev/health>.

Protected endpoints require an administrator-created Firebase email/password
account. The checked-in Python client reads the deployment's public Firebase
configuration, prompts for the password without echoing it, obtains a short-lived
ID token, lists held-out test samples, and runs one champion-model inference:

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".predmaint"
uv run python scripts/gcp_api_client.py
```

The email can be supplied as an argument; the password is still prompted:

```powershell
uv run python scripts/gcp_api_client.py --email user@example.com
```

Useful non-default modes:

```powershell
# Authenticate and list the held-out samples without creating a prediction.
uv run python scripts/gcp_api_client.py --email user@example.com --list-only

# Run inference for a particular displayed sample index.
uv run python scripts/gcp_api_client.py --email user@example.com --sample-index 2
```

The client keeps the password and Firebase ID token in memory only. It does not
write credentials or tokens to disk. The Firebase Web API key is public project
configuration and is loaded from the dashboard's `/config.js` endpoint.

## Inference input semantics

Selecting a sample in the dashboard and starting inference sends exactly one
observation to the champion model. The API does not retrieve the machine's raw
preceding rows from the sample identifier, machine identifier, or observation
timestamp. Multiple observations can be submitted through the batch API, but
the current champion scores every row independently.

Each displayed row is already a feature-engineered snapshot. In addition to the
current voltage, rotation, pressure, and vibration readings, it contains
historical summaries that were calculated before the held-out demo data was
exported:

- 3-hour rolling means and standard deviations;
- 24-hour rolling means and standard deviations;
- error counts from the preceding 24 hours;
- elapsed days since maintenance for each component;
- machine age and model category.

The model therefore receives historical context in aggregated form, but it does
not receive the individual measurements that make up those windows. The
`machine_id` and `observed_at` fields provide traceability and prediction
logging; they do not cause the serving application to fetch additional history.
The inference history chart in the dashboard is also presentation state only
and is never fed back into the model.

The deployed champion is the `hist_gradient_boosting` tabular model. The LSTM
and Transformer sequence challengers remain offline experiments and are not
part of this Cloud Run serving path. Serving either sequence model would require
a different inference contract that supplies an ordered time window, or an
online feature pipeline that builds that window before invoking the model.

## Cost control

Both services use request-based billing, zero minimum instances, and at most one
instance. Suspend both URLs without deleting their configuration:

```powershell
.\deploy\gcp\suspend.ps1 -ProjectId <PROJECT_ID>
```

Restore automatic scale-to-zero operation:

```powershell
.\deploy\gcp\resume.ps1 -ProjectId <PROJECT_ID>
```

Remove the managed infrastructure:

```powershell
.\deploy\gcp\destroy.ps1 -ProjectId <PROJECT_ID>
```

Terraform deletes the managed Artifact Registry repository. If additional image
repositories or versions were created outside this configuration, remove those
separately when they are no longer needed.
