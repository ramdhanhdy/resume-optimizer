# AI Resume Optimizer

A full-stack AI-powered resume optimization application that uses a deterministic sequential multi-agent system to analyze job requirements and tailor resumes with ethical accuracy while maintaining professional authenticity.

## 🤖 Agent System Architecture

### Sequential Multi-Agent Pipeline

The application implements a **deterministic sequential pattern** where each agent builds upon the previous agent's output:

```
Profile Agent (Optional) → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5 → Renderer
```

**Agent Pipeline:**

- **🔍 Profile Agent** (Optional) - Builds context from LinkedIn/GitHub
- **📋 Agent 1** - Job Analysis: Extracts requirements, role signals, and keywords from job postings
- **🎯 Agent 2** - Resume Optimizer: Generates targeted optimization strategy using evidence-based analysis
- **⚙️ Agent 3** - Optimizer Implementer: Applies strategic changes to the candidate's resume
- **✅ Agent 4** - Validator: Evaluates optimized resume with scoring and red flag analysis
- **✨ Agent 5** - Polish: Applies validator recommendations for final refinement and generates DOCX-ready output

### Real-Time Insight Extraction

The system includes a parallel insight extraction pipeline that provides real-time streaming updates:
- **Event Persistence**: All agent events are stored in SQLite for replay and recovery
- **Reconnection Support**: Clients can reconnect and resume from the last known event
- **Parallel Processing**: Insight extraction runs asynchronously alongside agent execution
- **Chunk Streaming**: Agent outputs are streamed in real-time with configurable throttling

### Agent Responsibilities

- **🔍 Profile Agent** (Optional)
  - Builds evidence-backed profile index from LinkedIn/GitHub
  - Provides contextual enrichment for subsequent agents
  - Location: `backend/src/agents/profile_agent.py`
  - Note: Runs before main pipeline if LinkedIn URL or GitHub username provided

- **📋 Agent 1 — Job Analyzer**
  - Extracts requirements, role signals, and keywords from job postings
  - Identifies key competencies and qualifications needed
  - Location: `backend/src/agents/job_analyzer.py`

- **🎯 Agent 2 — Strategy Generator**
  - Generates targeted optimization strategy using job analysis
  - Creates evidence-based improvement plan
  - Location: `backend/src/agents/resume_optimizer.py`

- **⚙️ Agent 3 — Resume Builder**
  - Applies the optimization strategy to build the enhanced resume
  - Implements strategic changes while preserving authenticity
  - Location: `backend/src/agents/optimizer_implementer.py`

- **✅ Agent 4 — Validator**
  - Evaluates optimized resume against job posting
  - Produces multi-dimensional scoring and red flag analysis
  - Ensures accuracy and ethical compliance
  - Location: `backend/src/agents/validator.py`

- **✨ Agent 5 — Polish**
  - Applies validator recommendations for final refinement
  - Generates DOCX-ready output with page formatting guidance
  - Ensures professional presentation
  - Location: `backend/src/agents/polish.py`

- **📄 Renderer** (Zero-cost utility)
  - Converts final output to downloadable formats
  - Handles final document formatting
  - Location: `backend/src/agents/renderer.py`

- **🔗 GitHub Projects Agent** (Separate Service)
  - Curates relevant GitHub projects for evidence-backed achievements
  - Available as separate API endpoint, not in main pipeline
  - Location: `backend/src/agents/github_projects_agent.py`

### Design Patterns Implemented

- **Sequential Multi-Agent Pattern**: Fixed linear order with context preservation
- **Generator-Critic Pattern**: Validator reviews and critiques without iterative loops
- **Human-in-the-Loop**: User checkpoints for input validation and approvals
- **Custom Logic Pattern**: Optional branches and per-agent model selection

### Orchestration Features

- **Deterministic Execution**: Fixed sequence ensures reproducible results
- **Context Engineering**: Each agent receives structured inputs from prior steps
- **Provider Routing**: Multi-provider facade selects optimal API per agent
- **Streaming Support**: Real-time progress updates via Server-Sent Events
- **Evidence Preservation**: Reduces hallucination through context chaining

## Features

### Core Agent Pipeline
- 🤖 **5-Agent AI Pipeline**: Sequential processing with job analysis, strategy generation, implementation, validation, and polishing
- 🔍 **Profile Enrichment**: Optional LinkedIn/GitHub integration for enhanced context
- 📊 **Multi-dimensional Validation**: Comprehensive scoring with red flag detection and recommendations
- 🛡️ **Ethical Grounding**: Built-in safeguards prevent fabrication with evidence-based optimization

### Real-Time Streaming & Event System
- 🔄 **Live Streaming**: Real-time progress updates via Server-Sent Events (SSE)
- 💾 **Event Persistence**: All agent events stored in SQLite for replay and recovery
- 🔄 **Reconnection Support**: Clients can reconnect and resume from the last known event
- 💡 **Parallel Insight Extraction**: Real-time chunk-by-chunk streaming with dedicated insight model
- 📈 **Stream History**: Configurable event history for debugging and monitoring

### Advanced LLM Support
- 🧠 **Multi-Provider LLM Support**: OpenRouter, Google Gemini, Cerebras, Zenmux, LongCat, and more
- 🎚️ **Per-Agent Model Configuration**: Individual model and temperature settings for each agent
- ⚙️ **Advanced Parameters**: Support for top_p, top_k, frequency_penalty, presence_penalty, seed, and stop sequences
- 💰 **Cost Tracking**: Real-time cost calculation with input, output, and thinking token breakdowns
- 📝 **Model Registry**: Capability-based model selection with provider-specific optimizations

### Resume Processing
- 📄 **Multi-format Support**: Upload PDF, DOCX, or images with intelligent parsing
- 🔗 **URL Ingestion**: Fetch job postings directly from URLs using Exa API
- 📥 **Export Options**: Download optimized resumes in DOCX, PDF, or HTML format
- 📃 **Flexible Page Constraints**: 2-3 page resumes supported with intelligent content optimization

### Application Management
- 💾 **Application Tracking**: Save and compare multiple applications with version history
- 🎯 **Profile Persistence**: Profile data stored in database for reuse across applications
- 🎨 **Modern UI**: Beautiful React interface with real-time streaming updates and smooth animations
- 👥 **Rate Limiting**: Built-in free tier management (5 runs per client) with abuse prevention

### Production-Ready Features
- ☁️ **Cloud-Native**: Deployed on Cloud Run (backend) and Vercel (frontend)
- 🔐 **Secret Management**: Secure API key handling via Secret Manager
- 🛡️ **Error Recovery**: Distributed systems hardening with state persistence
- 📊 **Monitoring**: Comprehensive logging and event tracking

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **Database**: SQLite with automatic schema migrations (ephemeral in Cloud Run)
- **LLM Orchestration**: Multi-provider model registry with capability-based routing
- **Providers**: OpenRouter, Google Gemini, Cerebras, Zenmux, LongCat, Exa API
- **File Processing**: PDF extraction, DOCX generation, HTML parsing
- **Streaming**: Server-Sent Events with event persistence and replay
- **Cost Tracking**: Real-time pricing calculation with token-based billing

### Frontend
- **React 19** + **TypeScript** + **Vite**
- **Styling**: TailwindCSS v4 + shadcn/ui 2025 component library
- **Design System**: 200+ tokens, CSS variables, runtime theming
- **Animations**: Framer Motion with reduced motion support
- **Forms**: React Hook Form + Zod validation
- **State Management**: LocalStorage + IndexedDB for offline support
- **API Client**: SSE with reconnection and event replay

## Project Structure

```
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
│   │   ├── authentication-and-metering/
│   │   ├── deployment/           # Cloud Run/Vercel deployment specs
│   │   ├── distributed-streaming-hardening/
│   │   ├── experimentation-tracking/
│   │   └── llm-provider-parameters/
│   ├── troubleshooting/          # Troubleshooting guides
│   ├── DOCUMENTATION_INDEX.md   # Documentation navigation
│   └── README.md                # Docs overview
├── exports/                      # Generated resumes storage
├── .gitignore                   # Git ignore rules
├── AGENTS.md                    # Agent development guide
├── CLAUDE.md                    # Claude-specific notes
├── DEPLOYMENT.md                # Deployment guide
├── README.md                    # This file
└── start.sh / start.bat         # Local development scripts
```

## Documentation

📚 **[View Complete Documentation](./docs/DOCUMENTATION_INDEX.md)** - Complete index of all documentation organized by purpose.

**Quick Links:**
- [Setup Guide](./docs/setup/SETUP.md) - Comprehensive installation and configuration
- [Gemini Setup Guide](./docs/setup/GEMINI_SETUP.md) - Google Gemini API configuration
- [Design System Guide](./frontend/DESIGN_SYSTEM.md) - Frontend design system documentation
- [Agent Development Guide](./AGENTS.md) - Complete project overview for AI agents
- [Architecture Design Pattern](./docs/architecture/AGENTS_DESIGN_PATTERN.md) - 5-agent pipeline architecture
- [Integration Summary](./docs/integrations/INTEGRATION_SUMMARY.md) - Full-stack integration overview
- [Streaming Specification](./docs/specs/streaming_specification.md) - Real-time streaming architecture
- [Deployment Guides](./docs/specs/deployment/) - Cloud Run, Vercel, hybrid deployment options
- [Troubleshooting](./docs/troubleshooting/) - Common issues and solutions

## Setup

### Prerequisites

- **Python 3.11+** (with `uv` package manager recommended)
- **Node.js 20+** with npm
- API keys for at least one LLM provider (OpenRouter, Gemini, Cerebras, etc.)

### Backend Setup

1. **Navigate to the backend directory:**
```bash
cd backend
```

2. **Create and activate virtual environment (using uv):**
```bash
uv venv
# Windows (CMD): .\.venv\Scripts\activate
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
```

3. **Install dependencies:**
```bash
uv pip install -r requirements.txt
```

4. **Create environment file:**
```bash
cp .env.example .env  # or copy .env.example .env on Windows
```

5. **Configure your API keys in `.env`:**

**Required (minimum one provider):**
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
# or
GEMINI_API_KEY=your_gemini_key_here
```

**Optional (additional providers):**
```bash
CEREBRAS_API_KEY=your_cerebras_key_here
EXA_API_KEY=your_exa_key_here
ZENMUX_API_KEY=your_zenmux_key_here
LONGCAT_API_KEY=your_longcat_key_here
```

**Advanced Configuration (per-agent models):**
```bash
# Individual models for each agent (defaults shown)
ANALYZER_MODEL=gemini::gemini-2.5-pro
OPTIMIZER_MODEL=openrouter::openai/gpt-5.1
IMPLEMENTER_MODEL=openrouter::anthropic/claude-sonnet-4.5
VALIDATOR_MODEL=gemini::gemini-2.5-pro
POLISH_MODEL=openrouter::anthropic/claude-sonnet-4.5
PROFILE_MODEL=openrouter::anthropic/claude-sonnet-4.5
INSIGHT_MODEL=openrouter::x-ai/grok-4-fast
```

**Per-Agent Temperature Settings:**
```bash
ANALYZER_TEMPERATURE=0.6
OPTIMIZER_TEMPERATURE=1
IMPLEMENTER_TEMPERATURE=0.6
VALIDATOR_TEMPERATURE=0.2
PROFILE_TEMPERATURE=0.6
POLISH_TEMPERATURE=0.7
```

**Rate Limiting:**
```bash
# Maximum free runs per client (default: 5)
MAX_FREE_RUNS=5
```

**Database:**
```bash
# SQLite database path (Cloud Run uses /tmp for ephemeral storage)
DATABASE_PATH=./data/applications.db
```

**CORS Configuration:**
```bash
# Comma-separated list of allowed origins (use * for development)
CORS_ORIGINS=*
```

### Frontend Setup

1. **Navigate to the frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm ci  # or npm install
```

3. **Create environment file:**
```bash
cp .env.example .env.local
# On Windows: copy .env.example .env.local
```

4. **Configure frontend environment variables:**

```bash
# Backend API URL (development)
VITE_API_URL=http://localhost:8000

# Optional: Brand customization
# VITE_BRAND_NAME=Resume Optimizer
# VITE_PRIMARY_COLOR=#0274BD
# VITE_ACCENT_COLOR=#F57251
```

**Note:** In production (Vercel), `VITE_API_URL` should be set to `/api` to use the Vercel rewrite proxy.

## Running the Application

### Quick Start (Both Services)

**Windows:**
```bash
.\start.bat
```

**macOS/Linux:**
```bash
bash ./start.sh
```

### Individual Services

**Backend:**
```bash
cd backend
python server.py
```

**Alternative (with hot reload):**
```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Preview production build:**
```bash
cd frontend
npm run build
npm run preview
```

### Accessing the Application

- **Frontend**: http://localhost:5173 (Vite default)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

## Usage

### 🚀 Agent-Powered Optimization Workflow

1. **📤 Upload Resume**: Upload your resume in PDF, DOCX, TXT, or HTML format
2. **🔗 Provide Job Details**: Paste the job posting URL (auto-fetched via Exa API) or enter text manually
3. **🎯 Optional Profile Enhancement**: Add LinkedIn URL and/or GitHub username for contextual evidence
4. **🤖 Agent Pipeline Execution**: The sequential pipeline processes your application with real-time updates:
   - **Step 0 - Profile Building** (Optional): Creates evidence index from LinkedIn/GitHub
   - **Step 1 - Job Analysis**: Extracts requirements, role signals, and keywords
   - **Step 2 - Strategy Generation**: Creates evidence-based optimization plan  
   - **Step 3 - Implementation**: Applies strategic changes to your resume
   - **Step 4 - Validation**: Evaluates accuracy, scores match (1-100), and flags issues
   - **Step 5 - Polish**: Refines output for professional presentation with DOCX-ready formatting

5. **📊 Review Results**: Compare before/after versions with detailed validation scores and red flag analysis
6. **📈 Cost Tracking**: View real-time cost estimates for the optimization process
7. **💾 Save & Export**: Download optimized resume in DOCX, PDF, or HTML format
8. **🔄 Reconnect Anytime**: Pipeline state is persisted, allowing reconnection and resuming from any point

### Rate Limiting & Free Tier

The application includes built-in rate limiting to prevent abuse:
- **Free Tier**: 5 resume generations per client (browser)
- **Client Tracking**: Uses LocalStorage to maintain client ID across sessions
- **Rate Limit Response**: HTTP 429 with `Retry-After` header when limit exceeded
- **Configurable**: Set `MAX_FREE_RUNS` environment variable to adjust limits

### Event Persistence & Replay

All pipeline events are persisted to SQLite, enabling:
- **Reconnection**: Resume from the last known event after network interruption
- **Event Replay**: Replay previous runs for debugging or demonstration
- **State Recovery**: Serverless containers can recover state after restart
- **Snapshot Access**: Get current pipeline state at any time via `/api/jobs/{id}/snapshot`

## API Endpoints

### Main Pipeline
- `POST /api/pipeline/start` - Start full pipeline with streaming
  - **Request**: `{ resume, job_posting_url, job_posting_text, client_id }`
  - **Response**: Job ID for streaming
  - **Headers**: `X-Client-ID` for rate limiting
- `GET /api/jobs/{job_id}/stream` - Server-Sent Events for real-time progress
  - **Features**: Event persistence, reconnection support, replay capability
  - **Parameters**: `?after_event_id={last_event_id}` for resuming
- `GET /api/jobs/{job_id}/snapshot` - Get current pipeline state
  - **Includes**: Agent outputs, validation scores, generated resume, run metadata

### Core Endpoints
- `POST /api/upload-resume` - Upload and parse resume file
  - **Supports**: PDF, DOCX, TXT, HTML
  - **Returns**: Parsed text content
- `POST /api/scan-resume` - Scan resume for detailed structure
  - **Extracts**: Contact info, sections, chronology, achievements
- `POST /api/analyze-job` - Analyze job posting (Agent 1)
  - **Input**: URL (via Exa API) or raw text
  - **Output**: Requirements, role signals, keywords
- `POST /api/optimize-resume` - Generate optimization strategy (Agent 2)
  - **Output**: Evidence-based optimization plan
- `POST /api/implement` - Apply optimizations (Agent 3)
  - **Output**: Optimized resume content
- `POST /api/validate` - Validate resume (Agent 4)
  - **Output**: Multi-dimensional scores, red flags, recommendations
- `POST /api/polish` - Final polish (Agent 5)
  - **Output**: DOCX-ready resume with formatting guidance

### Export & Download
- `GET /api/export/{id}` - Export optimized resume
  - **Formats**: DOCX, PDF (via conversion)
  - **Includes**: Formatted document with styles
- `GET /api/download/{filename}` - Download exported file

### Application Management
- `GET /api/applications` - List all applications
  - **Response**: Array of application metadata
- `GET /api/application/{id}` - Get application details
  - **Includes**: Full pipeline results, scores, generated resume

### GitHub Integration
- `POST /api/curate-github` - Curate relevant GitHub projects
  - **Input**: GitHub username
  - **Output**: Curated project list with descriptions

### Recovery & Health
- `GET /api/health` - Health check endpoint
- `GET /api/recovery/{run_id}/status` - Check recovery status
- `POST /api/recovery/{run_id}/resume` - Resume from checkpoint

### Event Streaming
All SSE events include:
- `event`: Event type (e.g., `job_status`, `agent_step`, `insight`)
- `id`: Monotonically increasing event ID
- `data`: JSON payload
- `retry`: Reconnection timeout

**Event Types:**
- `job_status` - Job state changes
- `agent_step` - Agent execution progress
- `agent_chunk` - Real-time agent output chunks
- `insight` - Extracted insights
- `metrics` - Cost and performance metrics
- `done` - Pipeline completion

## Development

### Code Quality

**Backend (Python):**
```bash
cd backend

# Format code (requires black and ruff)
black .
ruff check . --fix
```

**Frontend (TypeScript/React):**
```bash
cd frontend

# Lint code (ESLint configured)
npm run lint

# Type check (no compilation needed)
npx tsc --noEmit
```

### Testing

**Backend Unit Tests:**
```bash
cd backend
python -m pytest
```

**Frontend Tests:**
```bash
cd frontend
# TODO: Add Vitest for unit tests and Playwright/Cypress for E2E
# npm test (when test runner is configured)
```

### Frontend Design System

The application uses a comprehensive design system built on **shadcn/ui (2025)** with modern tooling:

**Key Features:**
- **200+ Design Tokens**: Colors, typography, spacing, shadows, borders, animations in `@/design-system/tokens`
- **shadcn Components**: 10+ accessible, customizable components (Button, Card, Badge, Dialog, Input, Tabs, Tooltip)
- **WCAG 2.1 AA Compliance**: Built-in accessibility features including keyboard navigation and reduced motion
- **Responsive Design**: Mobile-first with breakpoint hooks (`useIsMobile`, `useBreakpoint`)
- **Motion System**: 20+ Framer Motion variants with `useReducedMotion` hook
- **Brand Customization**: White-labeling via CSS variables and `applyBrandConfig()`
- **Form Validation**: React Hook Form + Zod integration with reusable field wrappers

**Color System:**
- CSS variables (`--primary: 199 97% 42%`, `--accent: 14 88% 63%`) defined in `src/index.css`
- Tailwind utilities reference CSS variables: `bg-primary`, `text-primary`, `border-primary/90`
- Runtime theming via `VITE_PRIMARY_COLOR`, `VITE_BRAND_NAME` environment variables
- **Never use hardcoded hex colors** - always use Tailwind utilities

**Component Usage:**
```typescript
import { Button } from '@/components/ui/button';
import { useFormValidation } from '@/design-system/forms';
import { slideUpVariants, useReducedMotion } from '@/design-system/animations';
```

**Documentation:**
- Design System Guide: [`frontend/DESIGN_SYSTEM.md`](./frontend/DESIGN_SYSTEM.md)
- Component Docs: [`frontend/src/design-system/docs/README.md`](./frontend/src/design-system/docs/README.md)
- shadcn/ui Docs: https://ui.shadcn.com/

### Continuous Integration

**TODO:** Add GitHub Actions for:
- Backend: black, ruff, pytest
- Frontend: ESLint, TypeScript type checking, test runner
- Build verification for both frontend and backend

## 🛡️ Ethical Guidelines & Validation

### Multi-Layer Safety System

All agents follow strict ethical guidelines with **deterministic validation**:

- **🚫 No Fabrication Rule**: Never create false employers, titles, dates, or metrics
- **📝 Evidence-Based Approach**: All optimizations backed by actual experience
- **⚠️ Conservative Phrasing**: Uses cautious language when uncertain
- **✅ Validation Layer**: Agent 4 performs comprehensive fact-checking and scoring
- **🔍 Red Flag Detection**: Identifies potentially unsupported claims
- **🎯 Final Review**: Agent 5 removes any unsupported claims before output

### Validation Scoring System

Agent 4 provides multi-dimensional analysis:
- **📊 Match Score**: Overall alignment with job requirements
- **⚠️ Risk Assessment**: Red flags for potentially exaggerated claims
- **📈 Improvement Metrics**: Quantified enhancement areas
- **🎯 Recommendation Engine**: Specific suggestions for improvement

**Our Philosophy**: Present your TRUE qualifications optimally, not create fictional credentials.

## Troubleshooting

### Backend Issues

**Import errors:**
- Ensure virtual environment is activated
- Run `python -m pip install -r requirements.txt` to verify dependencies

**API errors:**
- Verify API keys in `.env` file are correct
- Check provider-specific error messages in logs
- Ensure model names match supported providers (see `backend/src/api/model_registry.py`)

**Database errors:**
- Ensure `DATABASE_PATH` directory exists
- Check file permissions on SQLite database
- In Cloud Run, remember data is ephemeral (use `/tmp`)

**SSE/streaming issues:**
- SSE buffering in Cloud Run requires proper configuration (see deployment guide)
- Check Cloud Run minimum instance settings to prevent cold starts
- Enable event persistence for reliability

**Rate limiting errors:**
- Check `MAX_FREE_RUNS` environment variable
- Verify client ID is being sent in `X-Client-ID` header
- Clear browser LocalStorage if client ID issues persist

### Frontend Issues

**Connection errors:**
- Ensure backend is running on the correct port (default: 8000)
- Check `VITE_API_URL` in frontend `.env.local`
- Verify CORS settings in backend `.env`

**Build errors:**
- Delete `node_modules` and `package-lock.json`
- Run `npm ci` to reinstall clean dependencies
- Check Node.js version (requires 20+)

**Streaming/SSE errors:**
- Check browser console for connection errors
- Verify backend `/api/jobs/{id}/stream` endpoint is accessible
- Ensure Cloud Run is configured for streaming (padding enabled)

**Styling issues:**
- Never use hardcoded hex colors (e.g., `text-[#0274BD]`)
- Always use Tailwind utilities that reference CSS variables (e.g., `text-primary`)
- Check CSS variables are defined in `frontend/src/index.css`
- Verify `applyBrandConfig()` is called in `frontend/src/index.tsx`

### Common Solutions

**CORS errors in development:**
```bash
# In backend .env
CORS_ORIGINS=*
```

**Cloud Run SSE buffering:**
- Events include padding to force buffer flushes
- Configure minimum instances to reduce cold starts
- Use event persistence for reliability

**Model errors:**
- Check model supports required capabilities (`supports_files`, `supports_images`)
- Some models don't support temperature (e.g., GPT-5.1)
- Verify API keys have sufficient quota

## 🚀 Deployment

The application is production-ready and deployed using modern cloud platforms:

### Current Deployment

- **Backend**: Google Cloud Run (us-central1)
  - **URL**: https://resume-optimizer-backend-784455190453.us-central1.run.app
  - **Features**: Auto-scaling, SSE streaming support, Secret Manager integration
- **Frontend**: Vercel
  - **URL**: https://resume-optimizer-eosin.vercel.app
  - **Features**: Global CDN, zero-config deployments, API proxy rewrite
- **Database**: SQLite (Cloud Run ephemeral storage at `/tmp`)
  - **Note**: Data persists across requests but is lost on container restart
  - **Future**: Migration to Cloud SQL PostgreSQL planned

### Cloud Run Deployment Highlights

✅ **SSE Streaming**: Configured with event persistence for reliable real-time updates
✅ **Secret Management**: API keys stored in Secret Manager, not environment variables
✅ **Rate Limiting**: Built-in protection with configurable free tier
✅ **Event Replay**: Clients can reconnect and resume from last known event
✅ **Cost Tracking**: Real-time cost calculation with multi-provider support

### Deployment Architecture

```
User Browser → Vercel CDN → Cloud Run Backend
                   ↓
            API Proxy Rewrite (/api/*)
                   ↓
         SQLite Database (/tmp/applications.db)
```

**Key Features:**
- Same-origin requests (no CORS configuration needed)
- Automatic SSL certificate provisioning
- Global CDN for frontend assets
- Serverless scaling for backend

### Production Considerations

**Database Persistence:**
Current SQLite setup is ephemeral. For production persistence:
1. Create Cloud SQL PostgreSQL instance
2. Update `backend/src/database/db.py` connection logic
3. Set environment variables for Cloud SQL

**Monitoring:**
- Cloud Run logs available in Google Cloud Console
- Vercel analytics and monitoring dashboard
- Application logs include cost tracking and performance metrics

**Scaling:**
- Cloud Run auto-scales based on request volume
- Minimum instances recommended for streaming reliability
- Event persistence ensures state survives container restarts

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions and troubleshooting.

## License

Proprietary - All rights reserved

