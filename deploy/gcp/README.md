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

## Access requests and secure password setup

The signed-out page includes a bilingual **Don't have an account yet? / Nincs
még felhasználója?** form. It accepts a required email address of at most 100
characters and a required message of at most 1,000 characters. The dashboard
validates both limits again on the server, stores pending requests in the
Firestore `access_requests` collection, and emails the administrator. A hidden
honeypot plus persistent limits of one request per email address per 24 hours,
five requests per source address per hour, and 50 requests per day reduce
automated abuse.

The form deliberately does not generate a password. Sending a password to the
administrator or requester by email would expose a reusable credential. After
approving a request, create the Firebase user and send a Firebase password-reset
email so that the requester sets a private password through Google's one-time
link. Never copy a temporary password into the approval email.

Notification delivery uses Gmail SMTP over TLS. It requires a Google App
Password; the normal Google account password must not be used. Enable two-step
verification on the sender account, create an App Password, then add only that
value as a new version of a Secret Manager secret named
`predmaint-smtp-password`. Do not put it in source control, Terraform variables,
shell history, or the Cloud Run environment as plain text.

For the current deployment, create the secret in Google Cloud Console under
**Security > Secret Manager**, upload `configure-access-requests.sh` with the
dashboard bundle, and run:

```bash
chmod +x configure-access-requests.sh
./configure-access-requests.sh project-c77f1076-6203-4f0d-abc europe-west1 bordas.marton@gmail.com
```

The script assigns the dashboard its dedicated service account, grants only
Firestore write access and access to that one secret, and creates a new Cloud
Run revision. The normal Terraform deployment models the same configuration;
after the secret exists, enable it with:

```powershell
.\deploy\gcp\deploy.ps1 -ProjectId <PROJECT_ID> -Region europe-west1 -EnableAccessRequestEmail
```

To update only the dashboard from a checked-out repository, without rebuilding
the inference API, run:

```bash
./deploy/gcp/deploy-dashboard-only.sh <PROJECT_ID> europe-west1
```

If SMTP delivery fails, the request remains in Firestore with
`notification_sent = false` for recovery. Delete processed requests when they
are no longer needed, because their email addresses and messages are personal
data.

## Public guest mode

The signed-out dashboard offers a bilingual **Try demo / Demo kipróbálása**
flow. The dashboard backend creates a short-lived Firebase custom token with a
guest claim; no public password is stored or shared. API Gateway and the API
validate the resulting Firebase ID token in the same way as registered users.

Guest sessions are deliberately limited:

- one session expires after 1 hour and is not refreshed;
- one inference request can contain 1–10 held-out observations;
- one session can evaluate at most 30 observations in total;
- one source address can create at most 3 sessions per hour;
- a global safeguard permits at most 100 new guest sessions per day;
- only the packaged, machine-disjoint demonstration test data is exposed.

Registered accounts created by the administrator do not use these guest-mode
limits. Guest session and inference counters are stored transactionally in
Firestore. The dashboard service account can sign Firebase custom tokens only
for this purpose; Terraform grants it `roles/iam.serviceAccountTokenCreator` on
itself rather than at project scope.

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
./predmaint-gcp/cloud-deploy.sh prepare <PROJECT_ID> europe-west1 false
less predmaint-gcp/terraform/predmaint-plan.txt
```

Apply the reviewed plan:

```bash
./predmaint-gcp/cloud-deploy.sh apply <PROJECT_ID> europe-west1 false
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
ID token, lists held-out test samples, and runs inference with the selected model:

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

# Select the tabular model, LSTM, or Transformer.
uv run python scripts/gcp_api_client.py --email user@example.com --model lstm
uv run python scripts/gcp_api_client.py --email user@example.com --model transformer
```

The client keeps the password and Firebase ID token in memory only. It does not
write credentials or tokens to disk. The Firebase Web API key is public project
configuration and is loaded from the dashboard's `/config.js` endpoint.

## Inference input semantics

Selecting a sample in the dashboard always identifies one prediction endpoint.
The selected model determines the input sent for that endpoint. The
`hist_gradient_boosting` model receives the endpoint's single engineered
feature row. The LSTM and Transformer receive an ordered 48-row hourly sequence:
the endpoint plus its preceding 47 observations from the same machine. The API
does not retrieve history from an identifier or timestamp; REST callers must
provide the `sequence` field for either temporal model. The packaged held-out
demo samples already include these leakage-safe windows.

Each displayed row is already a feature-engineered snapshot. In addition to the
current voltage, rotation, pressure, and vibration readings, it contains
historical summaries that were calculated before the held-out demo data was
exported:

- 3-hour rolling means and standard deviations;
- 24-hour rolling means and standard deviations;
- error counts from the preceding 24 hours;
- elapsed days since maintenance for each component;
- machine age and model category.

The tabular model therefore receives historical context in aggregated form.
The temporal models receive 48 consecutive engineered snapshots and can also
learn changes across that sequence. The
`machine_id` and `observed_at` fields provide traceability and prediction
logging; they do not cause the serving application to fetch additional history.
The inference history chart in the dashboard is also presentation state only
and is never fed back into the model.

The default and overall validation champion remains
`hist_gradient_boosting`. The deployed LSTM and Transformer are selectable
challengers, which makes their inference behaviour and results directly
comparable without presenting them as promoted production champions. Use
`GET /v1/models` to discover their versions, thresholds, input types, and window
sizes. `POST /v1/predict` accepts the `model` selector; omitting it preserves the
backward-compatible `hist_gradient_boosting` default.

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
