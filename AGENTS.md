# Project Overview
AI Resume Optimizer is a full‑stack app that tailors resumes to job postings via a deterministic
multi‑agent pipeline. The React/Vite frontend streams progress while a FastAPI backend orchestrates
agents (analysis → optimize → implement → validate → polish), integrates external LLM providers,
and renders outputs. Deployed with Cloud Run (backend) and Vercel (frontend).

## Repository Structure
- **backend/** – FastAPI server, agent pipeline, streaming, persistence, deployment Procfile.
- **frontend/** – React + Vite app, TailwindCSS, design system, Vercel rewrites.
- **docs/** – Architecture, specs, setup guides, troubleshooting, deployment notes.
- **README.md** – Product overview, architecture, live links.
- **DEPLOYMENT.md** – Backend/Frontend deployment to Cloud Run/Vercel.
- **start.sh / start.bat** – Convenience scripts to start backend and frontend locally.
- **.gitignore** – Git excludes for both projects.

## Build & Development Commands
```bash
# Prereqs
# - Python 3.11+
# - Node 20+ and npm
# - (Recommended) uv: https://docs.astral.sh/uv/

# One-liner to run both (Windows)
.\start.bat

# One-liner to run both (macOS/Linux)
bash ./start.sh
```

```bash
# Backend: setup
cd backend
uv venv
# Windows (CMD): .\.venv\Scripts\activate  OR  venv\Scripts\activate
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
uv pip install -r requirements.txt

# Backend: run (dev)
python server.py

# Backend: run (alt, hot reload)
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Backend: production (Procfile)
# web: uvicorn server:app --host 0.0.0.0 --port $PORT
```

```bash
# Frontend: setup
cd frontend
npm ci

# Frontend: run (dev)
npm run dev

# Frontend: build
npm run build

# Frontend: preview production build
npm run preview
```

```bash
# Linting
# Frontend
cd frontend
npm run lint

# Backend (if installed via pyproject dev-deps)
cd backend
ruff check .
black --check .
```

```bash
# Type-check
# Frontend
cd frontend
npx tsc --noEmit
```

```bash
# Tests
# Backend
cd backend
python -m pytest

# Frontend
# > TODO: Add a test runner (Vitest/Playwright) and npm scripts.
```

```bash
# Deploy: Backend (Cloud Run)
cd backend
gcloud run deploy resume-optimizer-backend \
  --source . \
  --region us-central1

# Make backend public (unauthenticated)
gcloud beta run services add-iam-policy-binding resume-optimizer-backend \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker

# Deploy: Frontend (Vercel, from ./frontend)
npm install -g vercel
vercel --prod
```

## Code Style & Conventions
- **Formatting**
  - Backend: `black` (default config).
  - Frontend: ESLint (`npm run lint`). No Prettier config found.
  - > TODO: Add shared Prettier config across `frontend/`.
- **Naming**
  - Python modules and functions: `snake_case`.
  - React components and TypeScript types: `PascalCase`. Variables: `camelCase`.
- **Linting**
  - Backend: `ruff` (no repo config found; default rules).
  - Frontend: ESLint scanning `src` for `ts/tsx`.
- **Commits**
  - > TODO: Adopt Conventional Commits (e.g., `feat:`, `fix:`, `chore:`) and add a commit template.

## Architecture Notes
```mermaid
flowchart LR
  U[User Browser] --> FE[Frontend (React/Vite)]
  FE -- SSE + JSON --> BE[FastAPI Backend]
  subgraph Agents
    A1[Job Analyzer]
    A2[Resume Optimizer]
    A3[Optimizer Implementer]
    A4[Validator]
    A5[Polish]
  end
  BE --> A1 --> A2 --> A3 --> A4 --> A5 --> BE
  BE -- LLM API --> LLM[(OpenRouter / Gemini)]
  BE -- Storage --> DB[(SQLite now → Supabase Postgres)]
  FE <-- Streaming Events --> BE
```

- **Frontend** renders the UI, sends inputs, and subscribes to Server‑Sent Events for live progress.
- **Backend** exposes REST endpoints, orchestrates the sequential agent pipeline, and emits streaming
  events via `src.streaming.*`.
- **LLM Providers** are accessed via a client factory (`src.api.client_factory`) to route to
  OpenRouter, Gemini, etc.
- **Storage**
  - Current: SQLite via `DATABASE_PATH` (ephemeral in Cloud Run when `/tmp`).
  - Planned: Supabase Postgres with Auth + metering (see spec).
- **Deployment**
  - Backend: Cloud Run (Buildpacks + Procfile).
  - Frontend: Vercel with `/api/*` rewrites to Cloud Run.

## Testing Strategy
- **Backend unit/integration**
  - Tools: `pytest`.
  - Run: `cd backend && python -m pytest`.
  - Example tests present: `test_*.py` (e.g., PDF extraction, Gemini).
- **Frontend**
  - > TODO: Add Vitest for unit tests and Playwright/Cypress for E2E; wire into `npm test`.
- **CI**
  - > TODO: Add GitHub Actions for lint, type‑check, tests, and builds.

## Security & Compliance
- **Secrets**
  - Local: `.env` files (`backend/.env`, `frontend/.env`); never commit secrets.
  - Cloud Run: use Secret Manager ("set‑secrets") for API keys (see `DEPLOYMENT.md`).
  - Frontend: configure `VITE_` env vars in Vercel Project Settings.
- **Auth & Data**
  - Supabase Auth + Postgres planned for identity and persistence (replace SQLite).
  - Backend will verify `Authorization: Bearer <access_token>` and enforce usage caps.
- **Dependency hygiene**
  - Backend: pin via `requirements.txt` and audit regularly.
  - Frontend: keep lockfile committed and run `npm audit`.
  - > TODO: Add automated dependency scanning in CI.
- **CORS**
  - Origins via `CORS_ORIGINS` (.env). Ensure production domains are whitelisted.
- **License**
  - Proprietary – All rights reserved (see root `README.md`).

## Agent Guardrails
- **Files agents must not modify**
  - Secrets: `.env`, `vercel.json` rewrites, Cloud Run configs.
  - Lockfiles: `frontend/package-lock.json`, `backend/uv.lock`.
  - Build & deployment manifests: `backend/Procfile`.
- **Protected code paths (require review)**
  - Pipeline orchestration in `backend/server.py`.
  - Shared agent interfaces in `backend/src/agents/*`.
  - Streaming infra in `backend/src/streaming/*`.
- **Operational limits**
  - Product rule: allow 5 free resume generations per user, then require payment.
  - Do not change rate‑limit constants or bypass gating without explicit approval.
- **API usage**
  - Never log raw API keys or PII. Use structured, redacted logs.
  - Respect provider ToS and rate limits.

## Extensibility Hooks
- **Plugin points**
  - Add/replace agents under `backend/src/agents/` and wire in `server.py`.
  - Extend streaming via `backend/src/streaming/` (emit new event types).
  - Add routes in `backend/src/routes/`.
- **Environment variables (backend)**
  - `OPENROUTER_API_KEY`, `EXA_API_KEY`, `GEMINI_API_KEY`, etc.
  - `DATABASE_PATH` (current SQLite), `PORT`, `HOST`, `CORS_ORIGINS`.
  - `DEFAULT_MODEL` (model routing default).
  - > TODO: Add `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, Stripe keys on migration.
- **Environment variables (frontend)**
  - `VITE_API_URL` (defaults to `http://localhost:8000` in dev; Vercel rewrites for prod).
  - Branding options in `frontend/.env.example` (logo, colors, typography).
- **Feature flags**
  - > TODO: Introduce flags for model selection, optional Profile Agent, and streaming verbosity.

## Frontend Design System
The frontend uses a comprehensive design system built on **shadcn/ui (2025)** with Tailwind CSS v4,
React 19, and TypeScript. This provides consistency, accessibility, and white-labeling support.

### Design System Architecture
```
frontend/src/design-system/
├── tokens/           – 200+ design tokens (colors, typography, spacing, etc.)
├── theme/            – Brand configuration, Tailwind preset, CSS variables
├── animations/       – Framer Motion variants + reduced motion support
└── forms/            – Zod schemas, React Hook Form integration, field components
```

### Key Features
- **Design Tokens**: Single source of truth for colors, typography, spacing, shadows, borders, animations.
  - Colors use CSS variables (`hsl(var(--primary) / <alpha-value>)`) for runtime theming
  - Brand colors: `#0274BD` (primary), `#F57251` (accent)
  - Typography: Fluid font sizes with `clamp()` for responsive text
- **shadcn Components**: 10+ installed (Button, Card, Badge, Dialog, Input, Tabs, Tooltip, etc.)
- **Animations**: 20+ Framer Motion variants with `useReducedMotion` hook for accessibility
- **Forms**: React Hook Form + Zod validation with reusable field wrappers
- **Responsive Hooks**: `useMediaQuery`, `useIsMobile`, `useBreakpoint`, etc.
- **Keyboard Navigation**: `useKeyPress`, `useEscapeKey`, `useFocusTrap`, etc.
- **Brand Customization**: White-labeling via `VITE_BRAND_NAME`, `VITE_PRIMARY_COLOR`, etc.

### Color System (Important!)
The design system has been **unified to use CSS variables as the single source of truth**:
- **CSS Variables** (`frontend/src/index.css`): Defines colors in HSL format (e.g., `--primary: 199 97% 42%`)
- **Tailwind Config** (`frontend/tailwind.config.js`): References CSS variables with alpha support
- **Brand Config** (`frontend/src/design-system/theme/brand-config.ts`): Runtime theming system
- **Initialization**: `applyBrandConfig()` called in `frontend/src/index.tsx` on app startup

**Do NOT use hardcoded hex colors** (e.g., `border-[#0274BD]`). Use Tailwind utilities:
- `bg-primary`, `text-primary`, `border-primary` (references CSS variables)
- `bg-primary/90` (90% opacity using alpha value support)

### Accessibility (WCAG 2.1 AA)
- Keyboard navigation for all interactive elements
- Focus management (`useFocusTrap`, focus restoration)
- ARIA attributes (labels, roles, live regions)
- Color contrast: 4.5:1 minimum
- Reduced motion support (`prefers-reduced-motion`)
- Screen reader semantic HTML

### Usage Examples
```typescript
// Import design tokens
import { colors, typography, spacing } from '@/design-system/tokens';

// Use shadcn components
import { Button } from '@/components/ui/button';
<Button variant="default" size="lg">Click Me</Button>

// Animations with reduced motion
import { slideUpVariants, useReducedMotion } from '@/design-system/animations';
const prefersReducedMotion = useReducedMotion();
<motion.div variants={prefersReducedMotion ? undefined : slideUpVariants}>...</motion.div>

// Form validation
import { useFormValidation, jobPostingSchema } from '@/design-system/forms';
const form = useFormValidation(jobPostingSchema);

// Responsive design
import { useIsMobile } from '@/hooks';
const isMobile = useIsMobile();
```

### Agent Guidelines for Frontend Work
- **Always use design tokens**: Import from `@/design-system/tokens` instead of hardcoding values
- **Use shadcn components**: Don't rebuild buttons, cards, etc. Use existing components
- **Respect color system**: Use `bg-primary`, `text-accent`, etc. Never hardcode colors
- **Support accessibility**: Add ARIA attributes, keyboard navigation, reduced motion checks
- **Mobile-first**: Design for mobile, then enhance for larger screens (`sm:`, `md:`, `lg:`)
- **Test responsive**: Verify UI works at `640px`, `768px`, `1024px`, `1280px` breakpoints

### Documentation
- **Design System Guide**: `frontend/DESIGN_SYSTEM.md`
- **Component Docs**: `frontend/src/design-system/docs/README.md`
- **shadcn/ui Docs**: https://ui.shadcn.com/

## Further Reading
- **Root overview** – ./README.md
- **Deployment** – ./DEPLOYMENT.md
- **Backend readme** – ./backend/README.md
- **Docs index** – ./docs/DOCUMENTATION_INDEX.md
- **Agents design** – ./docs/architecture/AGENTS_DESIGN_PATTERN.md
- **Streaming spec** – ./docs/specs/streaming_specification.md
- **UI component spec** – ./docs/specs/ui_component_specification.md
- **Gemini integration** – ./docs/specs/gemini_integration_specification.md
- **Supabase auth + metering (MVP)** – ./docs/specs/supabase_auth_and_metering_spec.md
