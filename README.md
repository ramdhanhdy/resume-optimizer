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
- **⚙️ Agent 3** - Resume Builder: Applies strategic changes to the candidate's resume
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
- 🎚️ **Per-Agent Model Configuration**: Individual model and temperature settings for each agent, configured via environment variables in `backend/.env` (for example `DEFAULT_MODEL`, `ANALYZER_MODEL`, `OPTIMIZER_MODEL`, `IMPLEMENTER_MODEL`, `VALIDATOR_MODEL`, `PROFILE_MODEL`, `INSIGHT_MODEL`, `POLISH_MODEL`).
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
- 👥 **Rate Limiting**: Built-in free tier management (default 5 runs per client) with abuse prevention; see **Rate Limiting & DEV Mode** below for configuration details.

### Demo Deployment Features
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

- **backend/** – FastAPI server, agents, streaming, database, and deployment config.
- **frontend/** – React/Vite app, design system, UI components, and API client.
- **docs/** – Documentation (setup, API reference, specs, architecture, troubleshooting).
- **AGENTS.md** – High-level agent development and architecture guide.
- **DEPLOYMENT.md** – Deployment guide and notes.
- **start.sh / start.bat** – Convenience scripts for running backend and frontend together.

For a detailed tree and file-level description, see **[Project Structure](./docs/PROJECT_STRUCTURE.md)**.

## Documentation

📚 **[View Complete Documentation](./docs/DOCUMENTATION_INDEX.md)** - Complete index of all documentation organized by purpose.

**Quick Links:**
- [Setup Guide](./docs/SETUP.md) - Installation and configuration
- [User Guide](./docs/USER_GUIDE.md) - Step-by-step usage workflow
- [API Reference](./docs/API_REFERENCE.md) - Complete API documentation
- [Development Guide](./docs/DEVELOPMENT.md) - Development workflows and tools
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Design System Guide](./frontend/DESIGN_SYSTEM.md) - Frontend design system documentation
- [Agent Development Guide](./AGENTS.md) - Complete project overview for AI agents

## Quick Start

### Prerequisites

- **Python 3.11+** (with `uv` package manager recommended)
- **Node.js 20+** with npm
- API keys for at least one LLM provider

### Installation

**Backend:**
```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
uv pip install -r requirements.txt
cp .env.example .env
# Configure API keys in .env
```

**Frontend:**
```bash
cd frontend
npm ci
cp .env.example .env.local
```

### Running the Application

**Quick Start (Both Services):**
```bash
# Windows:
.\start.bat

# macOS/Linux:
bash ./start.sh
```

**Individual Services:**
```bash
# Backend:
cd backend
python server.py

# Frontend:
cd frontend
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Rate Limiting & DEV Mode

- For demo deployment, The backend enforces a free tier of **5 full-pipeline runs per client** by default.
- Limits are tracked per `client_id` (from the `x-client-id` header, falling back to IP) and persisted in the SQLite run metadata store.
- An internal `MAX_FREE_RUNS` configuration exists (default `5`) but the product free tier is 5 runs per client; keep this value for public deployments.
- For local development you can set `DEV_MODE=true` in `backend/.env` to temporarily bypass rate limiting:
  - When enabled, the backend logs a warning such as: `⚠️ DEV_MODE enabled - rate limits disabled for client_id=..., run_count=...`.
  - **Never enable `DEV_MODE` in production** — leave it unset or `false` so the free tier remains enforced.

For detailed instructions, see:
- [Setup Guide](./docs/SETUP.md) - Installation and configuration
- [User Guide](./docs/USER_GUIDE.md) - Usage workflow
- [Development Guide](./docs/DEVELOPMENT.md) - Development workflows
- [Troubleshooting Guide](./docs/TROUBLESHOOTING.md) - Common issues

## 🚀 Deployment

This section describes the current deployment setup for the hosted instance of Resume Optimizer:

### Current Deployment

- **Backend**: Google Cloud Run 
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
✅ **Pinned Runtime**: Python version pinned via `backend/runtime.txt` (Python 3.11.x) to avoid incompatibilities with Cloud Run default images.

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

## 🛡️ Safety, Security & Ethics

### Multi-Layer Safety System

All agents follow strict ethical guidelines with **deterministic validation**:

- **🚫 No Fabrication Rule**: Never create false employers, titles, dates, or metrics
- **📝 Evidence-Based Approach**: All optimizations backed by actual experience
- **⚠️ Conservative Phrasing**: Uses cautious language when uncertain
- **✅ Validation Layer**: Agent 4 performs comprehensive fact-checking and scoring
- **🔍 Red Flag Detection**: Identifies potentially unsupported claims
- **🎯 Final Review**: Agent 5 removes any unsupported claims before output

#### Safeguard Layers (High-Risk Flows)

On top of the agent-level ethics, the app includes **defense-in-depth safeguards** for
high-risk operations:

- **DOCX Safeguard (Export Path)**
  - Uses `gpt-oss-safeguard-20b` (via OpenRouter) to classify model-generated Python DOCX
    templates **before** executing them in the sandbox.
  - Unsafe or ambiguous (`REVIEW`) templates are blocked prior to execution; safe ones still
    pass through the hardened AST-based sandbox.
  - See: `docs/specs/docx-safeguard/docx_safeguard_spec.md`.

- **Text Safeguard (Job Postings & Job URLs)**
  - Uses the same safeguard model with a domain-specific policy for job postings.
  - `/api/job-preview` fetches job posting content from a URL via Exa, runs the safeguard, and
    returns a structured decision (`ALLOW`/`BLOCK`/`REVIEW`) plus reasons.
  - The frontend input page calls this endpoint as soon as the user enters a job URL and shows
    inline status (loading, looks good, or flagged) before the pipeline starts; the pipeline then
    reuses the same vetted job text.
  - See: `docs/specs/text_safeguard_spec.md`.

### Validation Scoring System

Agent 4 provides multi-dimensional analysis:
- **📊 Match Score**: Overall alignment with job requirements (1-100)
- **⚠️ Risk Assessment**: Red flags for potentially exaggerated claims
- **📈 Improvement Metrics**: Quantified enhancement areas
- **🎯 Recommendation Engine**: Specific suggestions for improvement

**Principle**: Present your best self without misleading recruiters.

## License

Proprietary - All rights reserved
