#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy-dashboard-only.sh PROJECT_ID [REGION]}"
REGION="${2:-europe-west1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REVISION="$(git -C "${ROOT}" rev-parse --short=12 HEAD)"
BUILD_ROOT="${ROOT}/.gcp-build/dashboard-only"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/predmaint"
IMAGE="${REGISTRY}/dashboard:${REVISION}"

case "${BUILD_ROOT}" in
  "${ROOT}"/.gcp-build/*) rm -rf -- "${BUILD_ROOT}" ;;
  *) echo "Unexpected build path: ${BUILD_ROOT}" >&2; exit 1 ;;
esac

mkdir -p "${BUILD_ROOT}/src/predictive_maintenance"
cp "${ROOT}/deploy/gcp/Dockerfile.web" "${BUILD_ROOT}/Dockerfile"
cp "${ROOT}/src/predictive_maintenance/__init__.py" \
  "${BUILD_ROOT}/src/predictive_maintenance/__init__.py"
cp -R "${ROOT}/src/predictive_maintenance/web" \
  "${BUILD_ROOT}/src/predictive_maintenance/web"

gcloud config set project "${PROJECT_ID}" >/dev/null
gcloud builds submit "${BUILD_ROOT}" --tag "${IMAGE}" --project "${PROJECT_ID}"
gcloud run services update predmaint-dashboard \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --quiet

echo "Dashboard image: ${IMAGE}"
echo "Dashboard deployed: $(gcloud run services describe predmaint-dashboard --project "${PROJECT_ID}" --region "${REGION}" --format='value(status.url)')"
