#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-prepare}"
PROJECT_ID="${2:?Usage: ./cloud-deploy.sh prepare|apply PROJECT_ID [REGION]}"
REGION="${3:-europe-west1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_ROOT="${ROOT}/terraform"
PLAN="${TF_ROOT}/predmaint.tfplan"

gcloud config set project "${PROJECT_ID}" >/dev/null

case "${MODE}" in
  prepare)
    terraform -chdir="${TF_ROOT}" init
    terraform -chdir="${TF_ROOT}" apply \
      -target=google_project_service.required \
      -target=google_artifact_registry_repository.images \
      -target=google_project_iam_member.cloud_build_artifact_writer \
      -var="project_id=${PROJECT_ID}" \
      -var="region=${REGION}" \
      -auto-approve

    REVISION="manual-$(date -u +%Y%m%d%H%M%S)"
    REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/predmaint"
    API_IMAGE="${REGISTRY}/api:${REVISION}"
    WEB_IMAGE="${REGISTRY}/dashboard:${REVISION}"

    gcloud builds submit "${ROOT}/api" --tag "${API_IMAGE}" --project "${PROJECT_ID}"
    gcloud builds submit "${ROOT}/web" --tag "${WEB_IMAGE}" --project "${PROJECT_ID}"
    terraform -chdir="${TF_ROOT}" plan \
      -var="project_id=${PROJECT_ID}" \
      -var="region=${REGION}" \
      -var="api_image=${API_IMAGE}" \
      -var="web_image=${WEB_IMAGE}" \
      -out="${PLAN}"
    terraform -chdir="${TF_ROOT}" show -no-color "${PLAN}" > "${TF_ROOT}/predmaint-plan.txt"
    echo "Prepared ${PLAN}. Review predmaint-plan.txt, then run apply mode."
    ;;
  apply)
    test -f "${PLAN}" || { echo "Missing ${PLAN}; run prepare mode first." >&2; exit 1; }
    terraform -chdir="${TF_ROOT}" apply "${PLAN}"
    terraform -chdir="${TF_ROOT}" output
    ;;
  *)
    echo "Unknown mode: ${MODE}. Use prepare or apply." >&2
    exit 2
    ;;
esac
