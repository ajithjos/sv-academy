#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
MODE="${1:-deploy}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo manual)}"
DEPLOY_ALLOW_DIRTY="${DEPLOY_ALLOW_DIRTY:-0}"
CLOUD_RUN_DEPLOY_FLAGS=()
REQUIRED_PROJECT_SERVICES=(
  run.googleapis.com
  cloudbuild.googleapis.com
  artifactregistry.googleapis.com
  iam.googleapis.com
)

# shellcheck source=../../dev/devkit/lib/gcloud.sh
source "$REPO_ROOT/dev/devkit/lib/gcloud.sh"

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "[deploy/cloudrun] ERROR: required command not found: $cmd" >&2
    exit 10
  }
}

load_config() {
  dev_gcloud_load_contract "$REPO_ROOT" "deploy/cloudrun"

  : "${CLOUD_RUN_REGION:?CLOUD_RUN_REGION is required}"
  : "${CLOUD_RUN_SERVICE:?CLOUD_RUN_SERVICE is required}"
  : "${ARTIFACT_REPOSITORY:?ARTIFACT_REPOSITORY is required}"
  : "${IMAGE_NAME:?IMAGE_NAME is required}"
  CLOUD_RUN_SERVICE_ACCOUNT_NAME="${CLOUD_RUN_SERVICE_ACCOUNT_NAME:-}"
  CLOUD_RUN_SERVICE_ACCOUNT="${CLOUD_RUN_SERVICE_ACCOUNT:-}"
  if [[ -z "$CLOUD_RUN_SERVICE_ACCOUNT" && -n "$CLOUD_RUN_SERVICE_ACCOUNT_NAME" ]]; then
    CLOUD_RUN_SERVICE_ACCOUNT="${CLOUD_RUN_SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  fi
  CLOUD_RUN_MIN_INSTANCES="${CLOUD_RUN_MIN_INSTANCES:-0}"
  CLOUD_RUN_MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-2}"
  CLOUD_RUN_CPU="${CLOUD_RUN_CPU:-1}"
  CLOUD_RUN_MEMORY="${CLOUD_RUN_MEMORY:-512Mi}"
  CLOUD_RUN_CONCURRENCY="${CLOUD_RUN_CONCURRENCY:-80}"
  CLOUD_RUN_TIMEOUT="${CLOUD_RUN_TIMEOUT:-60s}"
  CLOUD_RUN_INGRESS="${CLOUD_RUN_INGRESS:-all}"
  CLOUD_RUN_EXECUTION_ENVIRONMENT="${CLOUD_RUN_EXECUTION_ENVIRONMENT:-gen2}"
  CLOUD_RUN_CPU_THROTTLING="${CLOUD_RUN_CPU_THROTTLING:-1}"
  CLOUD_RUN_CPU_BOOST="${CLOUD_RUN_CPU_BOOST:-0}"
  IMAGE_URI="${CLOUD_RUN_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
}

build_cloud_run_flags() {
  CLOUD_RUN_DEPLOY_FLAGS=(
    --project "$GCP_PROJECT_ID"
    --image "$IMAGE_URI"
    --region "$CLOUD_RUN_REGION"
    --platform managed
    --allow-unauthenticated
    --port 3000
    --min "$CLOUD_RUN_MIN_INSTANCES"
    --min-instances "$CLOUD_RUN_MIN_INSTANCES"
    --max "$CLOUD_RUN_MAX_INSTANCES"
    --max-instances "$CLOUD_RUN_MAX_INSTANCES"
    --cpu "$CLOUD_RUN_CPU"
    --memory "$CLOUD_RUN_MEMORY"
    --concurrency "$CLOUD_RUN_CONCURRENCY"
    --timeout "$CLOUD_RUN_TIMEOUT"
    --ingress "$CLOUD_RUN_INGRESS"
    --execution-environment "$CLOUD_RUN_EXECUTION_ENVIRONMENT"
  )

  if [[ "$CLOUD_RUN_CPU_THROTTLING" == "1" ]]; then
    CLOUD_RUN_DEPLOY_FLAGS+=(--cpu-throttling)
  else
    CLOUD_RUN_DEPLOY_FLAGS+=(--no-cpu-throttling)
  fi

  if [[ "$CLOUD_RUN_CPU_BOOST" == "1" ]]; then
    CLOUD_RUN_DEPLOY_FLAGS+=(--cpu-boost)
  else
    CLOUD_RUN_DEPLOY_FLAGS+=(--no-cpu-boost)
  fi

  if [[ -n "$CLOUD_RUN_SERVICE_ACCOUNT" ]]; then
    CLOUD_RUN_DEPLOY_FLAGS+=(--service-account "$CLOUD_RUN_SERVICE_ACCOUNT")
  fi
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
  echo "Expected Cloud Run service account: ${CLOUD_RUN_SERVICE_ACCOUNT:-<default>}"
  echo "Image: $IMAGE_URI"
  dev_gcloud_print_active_context "deploy/cloudrun"
}

print_command() {
  printf "  "
  printf "%q " "$@"
  printf "\n"
}

print_plan() {
  echo "[deploy/cloudrun] Plan"
  echo "  gcloud config : $GCP_CONFIG_NAME"
  echo "  gcloud account: ${GCP_ACCOUNT:-<not enforced>}"
  echo "  project number: ${GCP_PROJECT_NUMBER:-<not enforced>}"
  echo "  project       : $GCP_PROJECT_ID"
  echo "  region        : $CLOUD_RUN_REGION"
  echo "  service       : $CLOUD_RUN_SERVICE"
  echo "  service acct  : ${CLOUD_RUN_SERVICE_ACCOUNT:-<default>}"
  echo "  repository    : $ARTIFACT_REPOSITORY"
  echo "  image         : $IMAGE_URI"
  echo "  min instances : $CLOUD_RUN_MIN_INSTANCES"
  echo "  max instances : $CLOUD_RUN_MAX_INSTANCES"
  echo "  cpu / memory  : $CLOUD_RUN_CPU / $CLOUD_RUN_MEMORY"
  echo "  concurrency   : $CLOUD_RUN_CONCURRENCY"
  echo "  timeout       : $CLOUD_RUN_TIMEOUT"
  echo "  ingress       : $CLOUD_RUN_INGRESS"
  echo "  cpu throttle  : $CLOUD_RUN_CPU_THROTTLING"
  echo "  cpu boost     : $CLOUD_RUN_CPU_BOOST"
  echo
  echo "Would run:"
  print_command gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" --project "$GCP_PROJECT_ID" --repository-format docker --location "$CLOUD_RUN_REGION" --description "SystemVerilog Academy containers"
  print_command gcloud builds submit --project "$GCP_PROJECT_ID" --tag "$IMAGE_URI" "$REPO_ROOT"
  print_command gcloud run deploy "$CLOUD_RUN_SERVICE" "${CLOUD_RUN_DEPLOY_FLAGS[@]}"
}

print_bootstrap_plan() {
  echo "[deploy/cloudrun] Bootstrap plan"
  echo "  project    : $GCP_PROJECT_ID"
  echo "  region     : $CLOUD_RUN_REGION"
  echo "  repository : $ARTIFACT_REPOSITORY"
  echo "  service acct: ${CLOUD_RUN_SERVICE_ACCOUNT:-<default>}"
  echo
  echo "Would run:"
  print_command gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com --project "$GCP_PROJECT_ID"
  if [[ -n "$CLOUD_RUN_SERVICE_ACCOUNT_NAME" ]]; then
    print_command gcloud iam service-accounts create "$CLOUD_RUN_SERVICE_ACCOUNT_NAME" --project "$GCP_PROJECT_ID" --display-name "SystemVerilog Academy Cloud Run runtime"
  fi
  print_command gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" --project "$GCP_PROJECT_ID" --repository-format docker --location "$CLOUD_RUN_REGION" --description "SystemVerilog Academy containers"
}

confirm_deploy() {
  local phrase="${1:-DEPLOY-SV-ACADEMY}"
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

enable_project_services() {
  gcloud services enable "${REQUIRED_PROJECT_SERVICES[@]}" --project "$GCP_PROJECT_ID"
}

check_project_services_enabled() {
  local service
  local missing=()

  for service in "${REQUIRED_PROJECT_SERVICES[@]}"; do
    if [[ "$(gcloud services list --enabled --project "$GCP_PROJECT_ID" --filter="config.name=$service" --format='value(config.name)' 2>/dev/null | head -n 1)" != "$service" ]]; then
      missing+=("$service")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    echo "[deploy/cloudrun] ERROR: required GCP APIs are not enabled for '$GCP_PROJECT_ID':" >&2
    printf "[deploy/cloudrun]   %s\n" "${missing[@]}" >&2
    echo "[deploy/cloudrun] Run first: make deploy-bootstrap" >&2
    exit 6
  fi
}

ensure_runtime_service_account() {
  if [[ -z "$CLOUD_RUN_SERVICE_ACCOUNT_NAME" ]]; then
    return 0
  fi

  if ! gcloud iam service-accounts describe "$CLOUD_RUN_SERVICE_ACCOUNT" --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$CLOUD_RUN_SERVICE_ACCOUNT_NAME" \
      --project "$GCP_PROJECT_ID" \
      --display-name="SystemVerilog Academy Cloud Run runtime"
  fi
}

ensure_artifact_repo() {
  if ! gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" --project "$GCP_PROJECT_ID" --location="$CLOUD_RUN_REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" \
      --project "$GCP_PROJECT_ID" \
      --repository-format=docker \
      --location="$CLOUD_RUN_REGION" \
      --description="SystemVerilog Academy containers"
  fi
}

deploy() {
  check_project_services_enabled
  ensure_runtime_service_account
  ensure_artifact_repo
  gcloud builds submit --project "$GCP_PROJECT_ID" --tag "$IMAGE_URI" "$REPO_ROOT"
  gcloud run deploy "$CLOUD_RUN_SERVICE" "${CLOUD_RUN_DEPLOY_FLAGS[@]}"
}

load_config
build_cloud_run_flags

case "$MODE" in
  context)
    print_context
    ;;
  gcloud-setup|setup-gcloud)
    dev_gcloud_setup_from_contract "$REPO_ROOT" "deploy/cloudrun"
    ;;
  doctor)
    dev_gcloud_check_context "deploy/cloudrun"
    echo "[deploy/cloudrun] gcloud config, project, and account match the tracked deploy contract."
    ;;
  bootstrap)
    dev_gcloud_check_context "deploy/cloudrun"
    print_bootstrap_plan
    confirm_deploy "BOOTSTRAP-SV-ACADEMY"
    enable_project_services
    ensure_runtime_service_account
    ensure_artifact_repo
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
    echo "Usage: $0 {context|gcloud-setup|doctor|bootstrap|plan|docker-build|deploy}" >&2
    exit 2
    ;;
esac
