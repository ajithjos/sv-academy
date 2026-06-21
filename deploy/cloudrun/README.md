# Cloud Run

The active deployment path is intentionally simple: build the standalone Next.js container and deploy it to a public Cloud Run service. There is no database, queue, storage bucket, or private runtime dependency in the current app.

```bash
make context
make gcloud-setup
make doctor
make deploy-bootstrap
make deploy-plan
make deploy
```

The expected GCP configuration, account, project id, project number, region, service, low-cost runtime envelope, and Artifact Registry repository are tracked in `deploy/config/environments/prod.gcp.env`.

All GCP-backed repositories use the same tracked contract location and root variable name: `DEPLOY_GCP_ENV_FILE ?= deploy/config/environments/prod.gcp.env`.

Use `make gcloud-setup` once per machine to create and activate the named local gcloud configuration. If authentication is missing, it will fail with the exact `gcloud auth login ...` command to run.

Use `make deploy-bootstrap` once for a new GCP project to enable Cloud Run, Cloud Build, Artifact Registry, and IAM, then create the Docker repository and dedicated no-extra-roles Cloud Run runtime service account. It requires the same tracked gcloud contract and a separate typed confirmation.

`make deploy` runs the same gcloud contract check as `make doctor`, refuses a dirty worktree by default, prints the resolved plan, requires a typed confirmation, builds the image with Cloud Build, and deploys the public Cloud Run service.

The default Cloud Run envelope is intentionally cost-conscious for a public landing page: min instances `0`, max instances `2`, CPU throttling enabled, CPU boost disabled, `1` CPU, and `512Mi` memory. The service runs as `svacademy-web-runtime` rather than the project default compute service account.

Future backend services should get their own deployment notes instead of being hidden inside this public frontend flow.
