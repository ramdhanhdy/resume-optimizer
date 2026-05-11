# Resume Optimizer Deployment Runbook — Railway Backend + Vercel Frontend

**Date:** 2026-05-09  
**Decision owner:** Hermes PM / Kanban deployment workflow  
**Status:** Approved with reviewer corrections  

## Decision

Use **Railway** as the next-week backend host for the FastAPI service, with **Vercel** remaining the frontend host and **Supabase** as auth + Postgres database.

Cloud Run is only the fallback if public browser/Vercel access is already solved within a 24-hour timebox. Do not burn the deployment week on GCP IAM/org-policy issues.

## Why Railway first

- Fastest path for an always-on FastAPI backend.
- Simple env/secrets management.
- Good fit for long-running HTTP/SSE endpoints compared with serverless function shapes.
- Lower operational friction than debugging the old Cloud Run public-access issue.
- More appropriate than Modal for this product because this is a normal web API, not a bursty GPU/job workload.

## Platform ranking

1. **Railway** — recommended next-week target.
2. **Cloud Run** — use only if public browser access from Vercel is already solved quickly.
3. **Render paid** — acceptable fallback if Railway SSE smoke test fails.
4. **Modal** — not recommended for this always-on FastAPI + SSE backend unless the architecture changes.

## Known repo/config findings

- Backend now has Railway config-as-code:
  - `backend/railway.toml`
  - start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
  - healthcheck path: `/api/health`
- Backend still has a Procfile-compatible fallback:
  - `backend/Procfile`: `web: uvicorn server:app --host 0.0.0.0 --port $PORT`
- Backend env example includes Supabase support:
  - `SUPABASE_URL`
  - `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
  - `USE_SUPABASE_DB=true`
- Frontend expects `VITE_API_URL` behavior from `frontend/src/lib/api.ts`:
  - `undefined` means fallback to `http://localhost:8000`
  - empty string means same-origin `/api`
  - explicit URL means cross-origin backend URL
- Reviewer correction: old guidance that `VITE_API_URL='.'` is valid is stale/wrong for current frontend code. Use explicit Railway backend URL unless a Vercel rewrite is actually configured and tested.
- There is no committed `vercel.json` rewrite config found in the repo.
- Existing Cloud Run deploy script exists, but prior notes indicate public access/org-policy friction.

## Supabase setup checklist

In Supabase:

1. Confirm the project is the intended production project.
2. Apply/verify backend migrations in Supabase SQL editor:
   - `backend/migrations/001_supabase_schema.sql`
   - `backend/migrations/002_user_preferences_and_resumes.sql`
   - `backend/migrations/003_application_reviews.sql`
   - any newer provenance migrations if present in current branch
3. Confirm Auth providers needed for demo:
   - Email/password if using email login
   - Google OAuth if using Google login
   - GitHub OAuth only if needed
4. Configure auth redirect URLs after Vercel URL is known:
   - `https://<vercel-domain>/auth/callback`
   - local dev callback if needed: `http://localhost:5173/auth/callback`
5. Copy these values for deployment:
   - `SUPABASE_URL`
   - server-side `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
   - frontend publishable key for `VITE_SUPABASE_PUBLISHABLE_KEY`

## Railway backend setup

Create a Railway service from the repo.

Recommended settings:

- **Root directory:** `backend`
- **Config file path:** `/backend/railway.toml`
  - Railway's config file lookup does not automatically follow the root directory setting, so set the config path explicitly if Railway does not detect it.
- **Start command:** already defined in `backend/railway.toml`; if setting it manually in Railway instead, use:

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

- **Healthcheck path:** `/api/health`
- **Python version:** repo has `backend/runtime.txt`; verify Railway uses Python 3.11+.

### Railway backend env vars

Required production env:

```bash
USE_SUPABASE_DB=true
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SECRET_KEY=<server-side-supabase-secret-key>
CORS_ORIGINS=https://<your-vercel-domain>
DEV_MODE=false
MAX_FREE_RUNS=5
```

Railway injects `PORT`; do not set it manually unless debugging a target-port issue.
Do not set `DATABASE_PATH` on Railway. The backend defaults to Supabase and only
creates SQLite files when `USE_SUPABASE_DB=false` is explicitly set for local
development.

LLM/search provider env vars:

```bash
OPENROUTER_API_KEY=<required-if-current-models-use-openrouter>
EXA_API_KEY=<required-for-job/profile enrichment search>
OPENAI_API_KEY=<if any configured model/provider uses OpenAI directly>
GEMINI_API_KEY=<if any configured model/provider uses Gemini>
CEREBRAS_API_KEY=<if used>
LONGCAT_API_KEY=<if used>
ZENMUX_API_KEY=<if used>
```

Reviewer correction — include this if LinkedIn/profile ingestion is part of the production demo:

```bash
SCRAPINGDOG_API_KEY=<required-for-scrapingdog-linkedin/profile-fetch-flow>
```

Model env vars from current backend example:

```bash
DEFAULT_MODEL=gemini::gemini-2.5-pro
ANALYZER_MODEL=gemini::gemini-2.5-pro
OPTIMIZER_MODEL=openrouter::openai/gpt-5.2
IMPLEMENTER_MODEL=openrouter::anthropic/claude-opus-4.5
INSIGHT_MODEL=openrouter::x-ai/grok-4-fast
POLISH_MODEL=openrouter::anthropic/claude-opus-4.5
REFINE_MODEL=openrouter::anthropic/claude-opus-4.5
VALIDATOR_MODEL=openrouter::openai/gpt-5.2
PROFILE_MODEL=openrouter::anthropic/claude-sonnet-4.5
```

Temperature env vars may be copied from `backend/.env.example` unless intentionally changed.

## Vercel frontend setup

Keep Vercel for frontend.

Set Vercel project root/build to the existing frontend app:

- **Root directory:** `frontend`
- **Build command:** `npm run build`
- **Output directory:** Vite default, usually `dist`

### Vercel env vars

Set:

```bash
VITE_API_URL=https://<railway-backend-domain>
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<supabase-publishable-key>
VITE_AUTH_BYPASS=false
VITE_MOCK_STREAM=false
```

Important:

- Do **not** set `VITE_API_URL=.`.
- Use explicit Railway backend URL unless you intentionally add and verify a Vercel rewrite.
- Frontend env vars are baked at build time; redeploy frontend after changing them.

## Production smoke tests

After backend deploys, test backend directly:

```bash
curl https://<railway-backend-domain>/api/health
```

If health endpoint differs, inspect FastAPI docs or root endpoint:

```bash
curl https://<railway-backend-domain>/
```

Then test frontend:

1. Open Vercel production URL.
2. Sign in with Supabase Auth.
3. Upload/paste a resume.
4. Provide a job description or URL.
5. Start pipeline.
6. Confirm `/api/pipeline/start` succeeds.
7. Confirm `/api/jobs/{job_id}/stream` streams events in browser Network tab.
8. Confirm final review/resume appears.
9. Confirm a row appears in Supabase for the run/application/review path.
10. Export/download if that is part of the demo.

## Evidence/screenshots to capture

Capture these for PM confidence:

- Railway deployment success screen.
- Railway env var page with secret values hidden.
- Railway backend logs during a successful pipeline run.
- Vercel deployment success screen.
- Vercel env var page with values hidden.
- Browser Network tab showing:
  - successful `/api/pipeline/start`
  - streaming `/api/jobs/{job_id}/stream`
- Supabase table row created for the application/run/review.
- Final generated resume/review UI.

## Rollback plan

If Railway backend fails:

1. Keep Vercel frontend pointed at the last working backend until Railway passes smoke tests.
2. If Railway fails due to SSE or runtime issues, try Render paid as the next fallback.
3. If Cloud Run public access is already solved, switch `VITE_API_URL` back to the known working Cloud Run URL and redeploy Vercel.
4. If Supabase DB path fails, set `USE_SUPABASE_DB=false` only for local emergency debugging — not as the production target.

## Risk register

- **Vercel env still points to old Cloud Run URL**  
  Mitigation: explicitly set `VITE_API_URL=https://<railway-backend-domain>` and redeploy.

- **CORS blocks Vercel frontend**  
  Mitigation: set Railway backend `CORS_ORIGINS=https://<vercel-domain>`.

- **SSE stream fails cross-origin**  
  Mitigation: smoke-test `/api/jobs/{job_id}/stream` in browser Network tab before declaring deployment done.

- **Supabase auth callback mismatch**  
  Mitigation: add Vercel production callback URL in Supabase Auth settings.

- **LinkedIn/profile ingestion silently missing**  
  Mitigation: add `SCRAPINGDOG_API_KEY` if demo includes LinkedIn/profile evidence.

- **SQLite fallback accidentally used**  
  Mitigation: keep `USE_SUPABASE_DB=true`, do not set `DATABASE_PATH`, and verify
  Supabase rows are created during smoke test.

## Day-by-day plan

### Day 1 — Decide and prepare

- Confirm Railway as backend host.
- Confirm Supabase project and migrations.
- Collect all env vars.
- Confirm Vercel project settings.

### Day 2 — Deploy backend

- Create Railway service from `backend` root.
- Set env vars.
- Deploy.
- Test backend health/root endpoint.
- Check logs.

### Day 3 — Wire frontend

- Update Vercel env vars.
- Redeploy frontend.
- Confirm browser reaches Railway backend.
- Fix CORS if needed.

### Day 4 — Full product smoke test

- Run full authenticated resume optimization flow.
- Verify SSE streaming.
- Verify Supabase rows.
- Verify export/final output.

### Day 5 — Buffer/rollback

- Fix remaining blockers.
- If Railway is blocked, switch to Render paid or Cloud Run fallback if already publicly reachable.
- Capture screenshots/evidence.

## Final PM call

Proceed with **Railway backend + Vercel frontend + Supabase Postgres/Auth**.

Do not use Modal for this launch. Do not spend the week debugging Cloud Run public access unless it is solved within one day.
