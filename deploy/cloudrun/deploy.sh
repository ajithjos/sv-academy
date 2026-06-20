#!/usr/bin/env bash
set -euo pipefail

MODE="deploy"
if [[ "${1:-}" == "--plan" || "${1:-}" == "plan" ]]; then
  MODE="plan"
fi

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-systemverilog-academy}"
IMAGE_NAME="${IMAGE_NAME:-systemverilog-academy-web}"
IMAGE_TAG="${IMAGE_TAG:-manual}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Set GCP_PROJECT_ID before deploying." >&2
  exit 2
fi

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/svacademy/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE}"
echo "Image: ${IMAGE_URI}"

if [[ "${MODE}" == "plan" ]]; then
  echo
  echo "Would run:"
  echo "  gcloud artifacts repositories create svacademy --repository-format=docker --location=${REGION} --description='SystemVerilog Academy containers'"
  echo "  gcloud builds submit --tag ${IMAGE_URI} ."
  echo "  gcloud run deploy ${SERVICE} --image ${IMAGE_URI} --region ${REGION} --platform managed --allow-unauthenticated --port 3000"
  exit 0
fi

if ! gcloud artifacts repositories describe svacademy --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create svacademy \
    --repository-format=docker \
    --location="${REGION}" \
    --description="SystemVerilog Academy containers"
fi

gcloud builds submit --tag "${IMAGE_URI}" .
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE_URI}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 3000
