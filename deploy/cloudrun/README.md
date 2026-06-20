# Cloud Run

The active deployment path is intentionally simple: build the standalone Next.js container and deploy it to a public Cloud Run service. There is no database, queue, storage bucket, or private runtime dependency in the current app.

```bash
export GCP_PROJECT_ID="your-gcp-project"
export CLOUD_RUN_REGION="us-central1"
export CLOUD_RUN_SERVICE="systemverilog-academy"
export IMAGE_TAG="$(git rev-parse --short HEAD)"

make cloudrun-deploy-plan
make cloudrun-deploy
```

Future backend services should get their own deployment notes instead of being hidden inside this public frontend flow.
