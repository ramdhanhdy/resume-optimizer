#!/bin/bash
# deploy.sh - Railway is the current backend deployment target.
#
# Railway deploys from GitHub using backend/railway.toml. This wrapper exists
# only to prevent accidentally running the legacy Cloud Run deployment script.

set -e

cat <<'EOF'
Resume Optimizer backend deploy target: Railway

Use the Railway dashboard/GitHub integration:
  - Root directory: backend
  - Config file path: /backend/railway.toml
  - Healthcheck path: /api/health

See:
  docs/deployment_railway_runbook_2026-05-09.md

The old Cloud Run script was moved to:
  backend/deploy-cloudrun-fallback.sh

Run that script only if you intentionally choose the documented Cloud Run
fallback path.
EOF
