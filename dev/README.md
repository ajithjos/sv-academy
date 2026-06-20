# Developer Layer

This directory holds repo-local developer ergonomics only. Product deployment inputs stay under `deploy/`.

- Source local shell helpers with `source dev/sourceme`.
- Inspect the command surface with `make help` or by reading `dev/help.md`.
- Inspect the current repo mental model with `make context` or by reading `dev/context.md`.
- Use `dev/lib/gcloud.sh` for guarded Cloud Run deployment preflight.
- Use `dev/lib/clean.sh` through `make pc`, `make dev-clean`, or `make dev-clean-all`.
- Use ignored `dev/scratchpad/` for ad hoc developer notes, experiments, and temporary files that are not product runtime state.
