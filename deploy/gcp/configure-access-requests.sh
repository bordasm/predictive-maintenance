#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:?Usage: ./configure-access-requests.sh PROJECT_ID [REGION] [SMTP_USER]}"
REGION="${2:-europe-west1}"
SMTP_USER="${3:-bordas.marton@gmail.com}"
SECRET_ID="predmaint-smtp-password"
SERVICE_ACCOUNT="predmaint-dashboard@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "${PROJECT_ID}" >/dev/null
gcloud services enable firestore.googleapis.com secretmanager.googleapis.com

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create predmaint-dashboard \
    --display-name="Predictive maintenance dashboard"
fi

gcloud secrets describe "${SECRET_ID}" >/dev/null
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user" \
  --quiet >/dev/null
gcloud secrets add-iam-policy-binding "${SECRET_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet >/dev/null

gcloud run services update predmaint-dashboard \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --service-account="${SERVICE_ACCOUNT}" \
  --update-env-vars="PREDMAINT_ACCESS_REQUEST_RECIPIENT=bordas.marton@gmail.com,PREDMAINT_SMTP_USER=${SMTP_USER},PREDMAINT_SMTP_HOST=smtp.gmail.com,PREDMAINT_SMTP_PORT=465" \
  --update-secrets="PREDMAINT_SMTP_PASSWORD=${SECRET_ID}:latest" \
  --quiet

echo "Access-request storage and email notification are configured."
