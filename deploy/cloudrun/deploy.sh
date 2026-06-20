#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
CONFIG_FILE="${DEPLOY_ENV_FILE:-$REPO_ROOT/deploy/config/environments/prod.gcp.env}"
LOCAL_CONFIG_FILE="${DEPLOY_LOCAL_ENV_FILE:-$REPO_ROOT/deploy/cloudrun/local/prod.gcp.env}"
MODE="${1:-deploy}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo manual)}"
DEPLOY_ALLOW_DIRTY="${DEPLOY_ALLOW_DIRTY:-0}"

# shellcheck source=../../dev/lib/gcloud.sh
source "$REPO_ROOT/dev/lib/gcloud.sh"

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "[deploy/cloudrun] ERROR: required command not found: $cmd" >&2
    exit 10
  }
}

load_config() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[deploy/cloudrun] ERROR: missing deploy config: $CONFIG_FILE" >&2
    exit 2
  fi

  set -a
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
  if [[ -f "$LOCAL_CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$LOCAL_CONFIG_FILE"
  fi
  set +a

  : "${GCP_CONFIG_NAME:?GCP_CONFIG_NAME is required}"
  : "${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
  : "${CLOUD_RUN_REGION:?CLOUD_RUN_REGION is required}"
  : "${CLOUD_RUN_SERVICE:?CLOUD_RUN_SERVICE is required}"
  : "${ARTIFACT_REPOSITORY:?ARTIFACT_REPOSITORY is required}"
  : "${IMAGE_NAME:?IMAGE_NAME is required}"
  GCP_ACCOUNT="${GCP_ACCOUNT:-}"
  IMAGE_URI="${CLOUD_RUN_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
}

check_dirty_tree() {
  local git_status
  git_status="$(git -C "$REPO_ROOT" status --porcelain)"
  if [[ -n "$git_status" && "$DEPLOY_ALLOW_DIRTY" != "1" ]]; then
    echo "[deploy/cloudrun] ERROR: working tree is dirty. Commit or stash changes before deploying." >&2
    echo "[deploy/cloudrun] For an intentional local validation deploy, rerun with DEPLOY_ALLOW_DIRTY=1." >&2
    exit 5
  fi
}

print_context() {
  echo "Repo: SystemVerilog Academy"
  echo "Runtime: public Next.js standalone container"
  echo "Deploy target: Cloud Run service $CLOUD_RUN_SERVICE in $GCP_PROJECT_ID/$CLOUD_RUN_REGION"
  echo "Expected gcloud config: $GCP_CONFIG_NAME"
  echo "Expected gcloud account: ${GCP_ACCOUNT:-<not enforced>}"
  echo "Image: $IMAGE_URI"
  echo "Active gcloud config: $(gcloud config configurations list --filter=is_active:true --format='value(name)' 2>/dev/null || echo '<gcloud unavailable>')"
  echo "Active gcloud project: $(gcloud config get-value project 2>/dev/null || echo '<gcloud unavailable>')"
  echo "Active gcloud account: $(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -n 1 || echo '<gcloud unavailable>')"
}

print_plan() {
  echo "[deploy/cloudrun] Plan"
  echo "  gcloud config : $GCP_CONFIG_NAME"
  echo "  gcloud account: ${GCP_ACCOUNT:-<not enforced>}"
  echo "  project       : $GCP_PROJECT_ID"
  echo "  region        : $CLOUD_RUN_REGION"
  echo "  service       : $CLOUD_RUN_SERVICE"
  echo "  repository    : $ARTIFACT_REPOSITORY"
  echo "  image         : $IMAGE_URI"
  echo
  echo "Would run:"
  echo "  gcloud artifacts repositories create $ARTIFACT_REPOSITORY --repository-format=docker --location=$CLOUD_RUN_REGION --description='SystemVerilog Academy containers'"
  echo "  gcloud builds submit --tag $IMAGE_URI ."
  echo "  gcloud run deploy $CLOUD_RUN_SERVICE --image $IMAGE_URI --region $CLOUD_RUN_REGION --platform managed --allow-unauthenticated --port 3000"
}

confirm_deploy() {
  local phrase="DEPLOY-SV-ACADEMY"
  local confirmation

  echo
  printf "Type %s to continue: " "$phrase"
  IFS= read -r confirmation
  echo
  if [[ "$confirmation" != "$phrase" ]]; then
    echo "[deploy/cloudrun] Aborted." >&2
    exit 1
  fi
}

ensure_artifact_repo() {
  if ! gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" --location="$CLOUD_RUN_REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" \
      --repository-format=docker \
      --location="$CLOUD_RUN_REGION" \
      --description="SystemVerilog Academy containers"
  fi
}

deploy() {
  ensure_artifact_repo
  gcloud builds submit --tag "$IMAGE_URI" "$REPO_ROOT"
  gcloud run deploy "$CLOUD_RUN_SERVICE" \
    --image "$IMAGE_URI" \
    --region "$CLOUD_RUN_REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 3000
}

load_config

case "$MODE" in
  context)
    print_context
    ;;
  doctor)
    dev_gcloud_check_context "deploy/cloudrun"
    echo "[deploy/cloudrun] gcloud config, project, and account match the tracked deploy contract."
    ;;
  plan|--plan)
    dev_gcloud_check_context "deploy/cloudrun"
    print_plan
    ;;
  docker-build)
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" "$REPO_ROOT"
    ;;
  deploy)
    dev_gcloud_check_context "deploy/cloudrun"
    check_dirty_tree
    print_plan
    confirm_deploy
    deploy
    ;;
  *)
    echo "Usage: $0 {context|doctor|plan|docker-build|deploy}" >&2
    exit 2
    ;;
esac
