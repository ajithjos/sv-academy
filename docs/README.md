# SystemVerilog Academy

New lightweight repository for `systemverilogacademy.com`.

The immediate goal is a public landing page that points learners to the free YouTube lessons while the larger academy platform is rebuilt deliberately. This repo should grow from clean contracts, not by copying the legacy Django application.
This folder is the lightweight engineering canon for the new repository.

Current state:

- public Next.js landing page
- no authentication
- no database
- Cloud Run as the primary hosting target
- YouTube as the public lesson library

Future docs should be added when the product grows real contracts: content model, backend API, auth model, learner workspace, instructor workflow, deployment changes, and migration notes from the legacy platform.

## Local Development

```bash
make install-dev
make dev
```

Open `http://127.0.0.1:3022`.

## Validation

```bash
make check
```

## Deployment

The current deployment target is Cloud Run with a standalone Next.js container:

```bash
export GCP_PROJECT_ID="your-gcp-project"
export IMAGE_TAG="$(git rev-parse --short HEAD)"
make cloudrun-deploy-plan
make cloudrun-deploy
```

See `deploy/cloudrun/README.md`.

## Repository Shape

- `src/app/`: Next.js public web app
- `src/components/`: reusable UI components
- `src/content/`: editable public copy and site configuration
- `docs/`: engineering notes and future architecture docs
- `deploy/cloudrun/`: active Cloud Run deployment flow
- `public/`: static assets
