# Project Structure

This document describes the layout of the Resume Optimizer repository in more detail than the brief
summary in the root `README.md`.

Use this as a reference when navigating the codebase or wiring new features into the correct layer
(backend agents, streaming, frontend UI, docs, etc.).

## Top-Level Layout

```text
resume-optimizer/
├── backend/                       # Python FastAPI server
│   ├── src/
│   │   ├── agents/               # 🤖 AI agent implementations
│   │   │   ├── base.py                   # Base agent class
│   │   │   ├── profile_agent.py          # Profile enrichment (optional)
│   │   │   ├── job_analyzer.py           # Agent 1: Job analysis
│   │   │   ├── resume_optimizer.py       # Agent 2: Strategy generation
│   │   │   ├── optimizer_implementer.py  # Agent 3: Implementation
│   │   │   ├── validator.py              # Agent 4: Validation & scoring
│   │   │   ├── github_projects_agent.py  # GitHub curation (separate)
│   │   │   ├── polish.py                 # Agent 5: Final polish
│   │   │   └── renderer.py               # Document rendering
│   │   ├── api/                  # 🔌 Multi-provider LLM clients
│   │   │   ├── cerebras.py
│   │   │   ├── client_factory.py
│   │   │   ├── gemini.py
│   │   │   ├── longcat.py
│   │   │   ├── model_registry.py         # Model capability registry
│   │   │   ├── multiprovider.py
│   │   │   ├── openrouter.py
│   │   │   ├── pricing.py                # Cost tracking system
│   │   │   ├── types.py
│   │   │   └── zenmux.py
│   │   ├── app/
│   │   │   ├── services/         # 📋 Service layer
│   │   │   │   ├── agents.py
│   │   │   │   ├── export.py
│   │   │   │   ├── persistence.py
│   │   │   │   └── validation_parser.py
│   │   │   ├── streaming.py              # Stream manager
│   │   │   └── __init__.py
│   │   ├── database/             # 💾 SQLite database layer
│   │   │   ├── db.py
│   │   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── middleware/           # 🔒 Error handling
│   │   │   ├── error_interceptor.py
│   │   │   └── __init__.py
│   │   ├── routes/               # 🛣️ API routes
│   │   │   ├── recovery.py
│   │   │   └── __init__.py
│   │   ├── services/             # 🔧 Core services
│   │   │   └── recovery_service.py
│   │   ├── streaming/            # 🌊 SSE streaming infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── events.py                 # Event types
│   │   │   ├── manager.py                # Stream manager with history
│   │   │   ├── run_store.py              # Run persistence
│   │   │   ├── insight_extractor.py      # Insight extraction
│   │   │   └── insight_listener.py       # Parallel processing
│   │   ├── templates/            # 📝 HTML templates
│   │   │   ├── resume_basic.html
│   │   │   ├── resume_structured.html
│   │   │   └── resume_styled.html
│   │   └── utils/                # 🛠️ Utilities
│   │       ├── docx_generator.py
│   │       ├── error_classification.py
│   │       ├── file_handler.py
│   │       ├── pdf_extractor.py
│   │       ├── pricing_calculator.py
│   │       ├── prompt_loader.py          # Prompt loader system
│   │       └── __init__.py
│   ├── prompts/                  # 📝 Agent prompt files
│   │   ├── insights/             # Real-time insight prompts
│   │   │   ├── content_analyzer.md
│   │   │   ├── content_implementer.md
│   │   │   ├── content_optimizer.md
│   │   │   ├── quality_polish.md
│   │   │   └── quality_validator.md
│   │   ├── agent1_job_analyzer.md
│   │   ├── agent2_resume_optimizer.md
│   │   ├── agent3_optimizer_implementer.md
│   │   ├── agent5_polish.md
│   │   └── profile_agent.md
│   ├── .env.cloudrun            # Cloud Run environment template
│   ├── .env.example             # Local environment template
│   ├── deploy.sh                # Deployment script
│   ├── Procfile                 # Cloud Run web process
│   ├── pyproject.toml           # Python dependencies (uv)
│   ├── requirements.txt         # Legacy pip dependencies
│   ├── runtime.txt              # Python version for Cloud Run
│   └── server.py                # FastAPI application entry
├── frontend/                     # React + Vite application
│   ├── src/
│   │   ├── components/           # ⚛️ React components
│   │   │   ├── shared/           # Shared UI components
│   │   │   ├── tabs/             # Tabbed interface components
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   ├── DownloadHero.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ExportModal.tsx
│   │   │   ├── InputScreen.tsx
│   │   │   ├── ProcessingScreen.tsx
│   │   │   └── RevealScreen.tsx
│   │   ├── design-system/        # 🎨 Design tokens and theme
│   │   │   ├── animations/       # Framer Motion variants
│   │   │   ├── docs/             # Design system documentation
│   │   │   ├── forms/            # Form validation (React Hook Form + Zod)
│   │   │   ├── theme/            # Brand config and presets
│   │   │   └── tokens/           # 200+ design tokens
│   │   ├── hooks/                # 🪝 Custom React hooks
│   │   ├── lib/                  # 🛠️ Utilities
│   │   ├── services/             # 🌐 API and storage
│   │   │   ├── api.ts            # SSE client with reconnection
│   │   │   └── storage/
│   │   │       ├── IndexedDBAdapter.ts
│   │   │       ├── LocalStorageAdapter.ts
│   │   │       └── StateManager.ts
│   │   ├── types/                # 📝 TypeScript types
│   │   ├── utils/                # 🔧 Utilities
│   │   │   └── clientId.ts       # Client ID generation
│   │   ├── App.tsx               # Root component
│   │   ├── constants.ts          # Application constants
│   │   ├── index.css             # Global styles (CSS variables)
│   │   ├── index.tsx             # Entry point
│   │   ├── types.ts              # Global types
│   │   └── vite-env.d.ts         # Vite environment types
│   ├── .env.example             # Frontend environment template
│   ├── .env.production          # Production environment
│   ├── components.json          # shadcn/ui configuration
│   ├── DESIGN_SYSTEM.md         # Design system guide
│   ├── IMPLEMENTATION_PROGRESS.md
│   ├── REFACTORING_COMPLETE.md
│   ├── REFACTORING_SUMMARY.md
│   ├── package.json             # Node dependencies
│   ├── tailwind.config.js       # Tailwind configuration
│   ├── tsconfig.json            # TypeScript configuration
│   ├── vercel.json              # Vercel deployment config
│   └── vite.config.ts           # Vite configuration
├── docs/                         # 📚 Documentation
│   ├── architecture/             # Architecture documents
│   ├── integrations/             # Integration guides
│   ├── setup/                    # Setup and configuration
│   ├── specs/                    # Technical specifications
│   ├── troubleshooting/          # Troubleshooting guides
│   ├── API_REFERENCE.md         # Complete API documentation
│   ├── DEVELOPMENT.md           # Development workflows
│   ├── DOCUMENTATION_INDEX.md   # Documentation navigation
│   ├── TROUBLESHOOTING.md       # Common issues and solutions
│   ├── USER_GUIDE.md            # Usage workflow guide
│   └── README.md                # Docs overview
├── exports/                      # Generated resumes storage
├── .gitignore                   # Git ignore rules
├── AGENTS.md                    # Agent development guide
├── CLAUDE.md                    # Claude-specific notes
├── DEPLOYMENT.md                # Deployment guide
├── README.md                    # Root project README
└── start.sh / start.bat         # Local development scripts
```

## Backend Highlights

- **Agents** live under `backend/src/agents/` and implement the multi-agent pipeline.
- **Streaming** (SSE) is handled by `backend/src/streaming/` and `backend/src/app/streaming.py`.
- **LLM providers** and model routing are under `backend/src/api/`.
- **Persistence** is implemented in `backend/src/database/` with SQLite today
  and is designed to be swapped for Postgres later.

## Frontend Highlights

- The main React entry point is `frontend/src/App.tsx`.
- Primary screens: `InputScreen.tsx`, `ProcessingScreen.tsx`, `RevealScreen.tsx`.
- The design system and theming live under `frontend/src/design-system/`.
- API interactions go through `frontend/src/services/api.ts`.

## Documentation & Ops

- High-level docs live under `docs/` (setup, API reference, specs, architecture).
- Deployment details are in `DEPLOYMENT.md` and `docs/specs/deployment/`.
- Agent-development guidance is in `AGENTS.md`.
