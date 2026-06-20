---
applyTo: '**'
---

This is the new SystemVerilog Academy repository. The legacy Django platform remains useful for archaeology, but this repo should not mechanically copy its shape.

## Current Contract

- The active product is a public Next.js landing page.
- There is no authentication, database, student workspace, instructor surface, or course runtime yet.
- Cloud Run is the current deployment target.
- YouTube is the current content delivery surface.

## Engineering Rules

- Keep the public frontend simple and explicit.
- Put editable public copy in `src/content/` rather than burying it inside layout code.
- Add backend, auth, persistence, and course-platform concepts only when there is a real product requirement.
- Prefer small deploy scripts and `make` targets that can be run locally.
- Keep docs current when repository structure, deployment, or product contracts change.

## Validation

Run this before handing off non-trivial changes:

```bash
make check
```

For visual changes, also run the site locally and inspect desktop and mobile widths.
