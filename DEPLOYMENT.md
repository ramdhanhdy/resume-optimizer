# Deployment 

This document describes the **current deployment architecture** for Resume Optimizer and
points to the detailed deployment specifications under `docs/specs/deployment/`.

---

## 1. Current Production Architecture

### Database & Auth

- **Platform**: Supabase (hosted PostgreSQL + Auth)
- **Project**: `resume-optimizer` (`ezdjywejiqqxmqenceal`), region `ap-northeast-1`
- **Database**: PostgreSQL 17 with 13 tables, RLS enabled, triggers, and metering RPC
- **Auth**: Supabase Auth (email/password, Google OAuth, GitHub OAuth)
- **Schema**: `backend/migrations/001_supabase_schema.sql` (already applied)

The backend uses the Supabase **service role key** (`SUPABASE_SECRET_KEY`) to bypass RLS
and perform all database operations server-side. The frontend uses the **publishable key**
for authentication only — it never writes to the database directly.

### Backend

- **Runtime**: Python 3.11, FastAPI (`backend/server.py`)
- **Database**: Supabase PostgreSQL via `SupabaseDatabase` adapter (`backend/src/database/supabase_db.py`)
- **Hosting**: TBD (candidates: Railway, Fly.io, Render, or Cloud Run)
- **Toggle**: `USE_SUPABASE_DB=true` env var switches from SQLite to Supabase

The backend exposes a FastAPI application that powers the multi-agent pipeline, streaming
endpoints, and export flows. All endpoints extract user identity from Supabase JWT tokens.

### Frontend

- **Platform**: Vercel
- **App**: React + Vite frontend under `frontend/`
- **Build**: `npm run build` (Vite)
- **Auth**: Supabase JS SDK (`@supabase/supabase-js`) with `AuthProvider` context
- **Integration**: Vercel rewrites `/api/*` to the backend service.

The frontend gates all access behind Supabase Auth. It attaches `Authorization: Bearer`
tokens to API requests. Do not include `access_token` in SSE URLs; attach auth via
an `Authorization: Bearer` header, or mint a short-lived one-time stream token from
the backend and send it in a header or secure cookie when opening the SSE connection.

### Request Flow (High Level)

1. **User Browser** → authenticates via Supabase Auth (email/password or OAuth).
2. **Frontend** → attaches JWT `access_token` and issues requests to `/api/*`.
3. **Vercel** → rewrites `/api/*` requests to the backend service.
4. **Backend** → validates JWT via `supabase.auth.get_user(token)`, resolves `user_id`,
   and routes all DB operations through `SupabaseDatabase(user_id)`.

---

## 2. Access Model & Authentication

- **User authentication**: Supabase Auth (email/password, Google OAuth, GitHub OAuth).
- **Backend auth**: JWT validation via `supabase.auth.get_user(token)` using the service
  role key. Extracts `user_id` (UUID) for all database operations.
- **Fallback**: For backward compatibility, unauthenticated requests fall back to
  `X-Client-Id` header or IP-based identification (returns SQLite database).
- **Metering**: 5 free resume generations per user per month, enforced via
  `check_and_increment_usage` Supabase RPC function. Active subscribers bypass the cap.

---

## 3. Configuration & Environment

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | Supabase secret/service role key (server-side only) |
| `USE_SUPABASE_DB` | Set to `true` to use Supabase instead of SQLite |
| `DEFAULT_MODEL` | Default LLM model for agents |
| `*_MODEL` | Per-agent model overrides (ANALYZER, OPTIMIZER, etc.) |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `EXA_API_KEY` | Exa search API key |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `DEV_MODE` | Set to `true` to bypass rate limiting locally |
| `MAX_FREE_RUNS` | Free generation cap (default: 5) |

### Frontend (`frontend/.env.production`)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (`.` for same-origin via Vercel rewrites) |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key (client-side) |
| `VITE_SUPABASE_ANON_KEY` | Legacy anon key (fallback) |

---

## 4. Detailed Deployment Specifications

All step-by-step commands, alternative hosting options, and cost comparisons live under
`docs/specs/deployment/`:

- `docs/specs/deployment/README.md` – overview of deployment options and recommendations.
- `docs/specs/deployment/quick_deployment_guide.md` – fast path to production
  (e.g. Vercel + Railway).
- `docs/specs/deployment/backend_cloudrun_deployment_guide.md` – Cloud Run backend
  deployment details (legacy).
- `docs/specs/deployment/vercel_deployment_specification.md` – Vercel-specific
  considerations.
- `docs/specs/supabase_auth_and_metering_spec.md` – Supabase auth, database, and
  metering specification.
- `docs/specs/database/supabase_schema_v2.md` – Full PostgreSQL schema documentation.

Consult those documents when you need concrete commands or when changing the deployment
topology.

---

