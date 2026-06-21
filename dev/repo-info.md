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
make submodules-master-check
make submodules-master
```

Shared developer tooling is pinned as the `dev/devkit` submodule. Root make targets remain the daily interface and call `make -C dev/devkit ...` for shared development behavior.

Deployment commands:

```bash
make gcloud-setup
make deploy-plan
make deploy-bootstrap
make deploy
```

Deployment identity is checked through the tracked GCP contract in `deploy/config/environments/prod.gcp.env`. `make doctor` fails fast when the active gcloud config, account, project id, project number, or authentication is wrong.

The shared deploy contract variable is `DEPLOY_GCP_ENV_FILE`; by default it points at `deploy/config/environments/prod.gcp.env`.

The Cloud Run production contract is intentionally low cost for the public landing page: min instances `0`, max instances `2`, CPU throttling enabled, CPU boost disabled, `1` CPU, and `512Mi` memory. The service uses a dedicated no-extra-roles runtime service account instead of the project default compute service account.
