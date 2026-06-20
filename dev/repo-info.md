# SystemVerilog Academy Repo Info

Runtime: Next.js public website deployed to Cloud Run.

Daily startup:

```bash
make setup
source dev/sourceme
make dev-up
```

Useful commands:

```bash
make context
make doctor
make clean
make clean-python
make clean-all
make clean-deps
make check
make build
```

Deployment commands:

```bash
make deploy-plan
make deploy
```

Deployment identity is checked through the tracked GCP contract in `deploy/config/environments/prod.gcp.env`. `make doctor` fails fast when the active gcloud config, account, project, or authentication is wrong.
