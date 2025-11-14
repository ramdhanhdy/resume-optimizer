# Deployment 

This document describes the **current deployment architecture** for Resume Optimizer and
points to the detailed deployment specifications under `docs/specs/deployment/`.

---

## 1. Current Production Architecture

### Backend

- **Platform**: Google Cloud Run
- **Region**: `us-central1`
- **Runtime**: Python 3.11, FastAPI (`backend/server.py`)
- **Storage**: SQLite file in ephemeral container storage (`/tmp`), with a planned
  migration path to PostgreSQL (Cloud SQL or another managed database).

The Cloud Run service is deployed from the `backend/` directory and exposes a FastAPI
application that powers the multi-agent pipeline, streaming endpoints, and export flows.

### Frontend

- **Platform**: Vercel
- **App**: React + Vite frontend under `frontend/`
- **Build**: `npm run build` (Vite)
- **Integration**: Vercel rewrites `/api/*` to the backend service.

The frontend is responsible for the user-facing experience (input, processing, reveal) and
communicates with the backend via JSON + Server-Sent Events.

### Request Flow (High Level)

1. **User Browser** → loads frontend from Vercel.
2. **Frontend** → issues requests to `/api/*`.
3. **Vercel** → rewrites `/api/*` requests to the Cloud Run backend.
4. **Cloud Run** → handles REST + SSE endpoints and returns responses.

This provides a clean separation: Vercel handles static assets and global edge caching,
while Cloud Run hosts the Python API.

---

## 2. Access Model & Authentication

- The Cloud Run service is **not publicly anonymous**. It is intended to be invoked by a
  trusted caller (the Vercel frontend) via **OIDC**.
- Vercel is configured with a **Google Cloud service account** using the OIDC integration
  described in the Vercel docs.
- That service account has the `roles/run.invoker` permission on the Cloud Run service,
  allowing it to call the backend with identity tokens.

At the HTTP level this means:

- Browser → Vercel: normal HTTPS requests.
- Vercel → Cloud Run: authenticated requests using OIDC/identity tokens as the service account.

---

## 3. Configuration & Environment

High-level configuration used in production today:

- **Backend**
  - Deployed as a single Cloud Run service.
  - Uses environment variables for model selection, CORS, and database path.
  - Secrets (API keys) are stored in GCP Secret Manager and exposed at runtime via
    environment variables or `--set-secrets` bindings.

- **Frontend**
  - Uses `VITE_API_URL`/`VITE_API_BASE_URL` to point to the backend via rewrites.
  - Environment variables are configured in the Vercel project settings.

For a full list of recommended environment variables and platform options, see the
deployment specs referenced below.

---

## 4. Detailed Deployment Specifications

All step-by-step commands, alternative hosting options, and cost comparisons live under
`docs/specs/deployment/`:

- `docs/specs/deployment/README.md` – overview of deployment options and recommendations.
- `docs/specs/deployment/quick_deployment_guide.md` – fast path to production
  (e.g. Vercel + Railway).
- `docs/specs/deployment/backend_cloudrun_deployment_guide.md` – Cloud Run backend
  deployment details.
- `docs/specs/deployment/vercel_deployment_specification.md` – Vercel-specific
  considerations.

Consult those documents when you need concrete commands or when changing the deployment
topology.

---

