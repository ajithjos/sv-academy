# Cloud Run

The active deployment path is intentionally simple: build the standalone Next.js container and deploy it to a public Cloud Run service. There is no database, queue, storage bucket, or private runtime dependency in the current app.

```bash
make context
make doctor
make deploy-plan
make deploy
```

The expected GCP configuration, project, account, region, service, and Artifact Registry repository are tracked in `deploy/config/environments/prod.gcp.env`. If `make doctor` fails, follow the `gcloud` setup commands it prints before deploying.

Future backend services should get their own deployment notes instead of being hidden inside this public frontend flow.
