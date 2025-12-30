# Resume Optimizer - System Architecture

## Overview

The Resume Optimizer is a full-stack application that uses AI agents to analyze job postings and optimize resumes for better job matching. The system follows a multi-agent pipeline architecture with real-time streaming updates.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              RESUME OPTIMIZER SYSTEM ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐     HTTP/SSE      ┌────────────────────────────────┐      API       ┌─────────────────────┐
│   FRONTEND           │ ◄──────────────► │       BACKEND                   │ ◄────────────► │  EXTERNAL SERVICES  │
│   (React + Vite)     │                   │       (FastAPI + Python)        │                │                     │
├──────────────────────┤                   ├────────────────────────────────┤                ├─────────────────────┤
│                      │                   │                                │                │                     │
│  ┌────────────────┐  │                   │  ┌──────────────────────────┐  │                │  ┌───────────────┐  │
│  │ InputScreen    │  │                   │  │     server.py            │  │                │  │ OpenRouter    │  │
│  │ - Resume Upload│  │                   │  │     (FastAPI App)        │  │                │  │ API           │  │
│  │ - Job URL/Text │  │                   │  └──────────────────────────┘  │                │  └───────────────┘  │
│  │ - LinkedIn URL │  │                   │            │                   │                │                     │
│  │ - GitHub User  │  │                   │  ┌─────────┴─────────┐         │                │  ┌───────────────┐  │
│  └────────────────┘  │                   │  │                   │         │                │  │ Google        │  │
│                      │                   │  ▼                   ▼         │                │  │ Gemini        │  │
│  ┌────────────────┐  │                   │ REST              SSE          │                │  └───────────────┘  │
│  │ ProcessingScreen│ │                   │ Endpoints         Streaming    │                │                     │
│  │ - Progress     │  │                   │                                │                │  ┌───────────────┐  │
│  │ - Live Insights│  │                   │  ┌──────────────────────────┐  │                │  │ Cerebras      │  │
│  │ - Agent Status │  │                   │  │    AI AGENT PIPELINE     │  │                │  │ Cloud         │  │
│  └────────────────┘  │                   │  ├──────────────────────────┤  │                │  └───────────────┘  │
│                      │                   │  │                          │  │                │                     │
│  ┌────────────────┐  │                   │  │  1. JobAnalyzerAgent     │  │                │  ┌───────────────┐  │
│  │ RevealScreen   │  │                   │  │     ↓                    │  │                │  │ Vertex AI     │  │
│  │ - Final Resume │  │                   │  │  2. ResumeOptimizerAgent │  │                │  └───────────────┘  │
│  │ - Diff View    │  │                   │  │     ↓                    │  │                │                     │
│  │ - Scores       │  │                   │  │  3. OptimizerImplementer │  │                │  ┌───────────────┐  │
│  │ - Export       │  │                   │  │     ↓                    │  │                │  │ Exa           │  │
│  └────────────────┘  │                   │  │  4. ValidatorAgent       │  │                │  │ (Job Scraping)│  │
│                      │                   │  │     ↓                    │  │                │  └───────────────┘  │
│  ┌────────────────┐  │                   │  │  5. PolishAgent          │  │                │                     │
│  │ API Client     │  │                   │  │                          │  │                └─────────────────────┘
│  │ (api.ts)       │  │                   │  │  Optional:               │  │
│  └────────────────┘  │                   │  │  - ProfileAgent          │  │                ┌─────────────────────┐
│                      │                   │  │  - GitHubProjectsAgent   │  │                │    DEPLOYMENT       │
│  ┌────────────────┐  │                   │  └──────────────────────────┘  │                ├─────────────────────┤
│  │ SSE Stream     │  │                   │                                │                │                     │
│  │ Handler        │  │                   │  ┌──────────────────────────┐  │                │  Frontend: Vercel   │
│  └────────────────┘  │                   │  │  LLM PROVIDER CLIENTS    │  │                │                     │
│                      │                   │  ├──────────────────────────┤  │                │  Backend: Cloud Run │
│  ┌────────────────┐  │                   │  │ OpenRouter │ Gemini      │  │                │  (GCP)              │
│  │ TailwindCSS    │  │                   │  │ Cerebras   │ Vertex      │  │                │                     │
│  │ + shadcn/ui    │  │                   │  │ OpenAI     │ LongCat     │  │                └─────────────────────┘
│  └────────────────┘  │                   │  │ Zenmux     │             │  │
│                      │                   │  └──────────────────────────┘  │
└──────────────────────┘                   │                                │
                                           │  ┌────────────┬───────────────┐│
                                           │  │ Streaming  │ Recovery      ││
                                           │  │ Manager    │ Service       ││
                                           │  │ - Events   │ - Checkpoints ││
                                           │  │ - Insights │ - Error Handle││
                                           │  └────────────┴───────────────┘│
                                           │                                │
                                           │  ┌──────────────────────────┐  │
                                           │  │   SQLite Database        │  │
                                           │  │   (ApplicationDatabase)  │  │
                                           │  ├──────────────────────────┤  │
                                           │  │ applications             │  │
                                           │  │ agent_outputs            │  │
                                           │  │ validation_scores        │  │
                                           │  │ profiles                 │  │
                                           │  │ run_metadata             │  │
                                           │  │ recovery_sessions        │  │
                                           │  └──────────────────────────┘  │
                                           └────────────────────────────────┘
```

---

## Component Details

### Frontend (React + Vite + TypeScript)

| Component | File | Description |
|-----------|------|-------------|
| **InputScreen** | `InputScreen.tsx` | Handles resume upload, job posting input (URL or text), LinkedIn URL, and GitHub username |
| **ProcessingScreen** | `ProcessingScreen.tsx` | Displays real-time progress, live insights from agents, and step-by-step status |
| **RevealScreen** | `RevealScreen.tsx` | Shows final optimized resume, diff view, validation scores, and export options |
| **API Client** | `services/api.ts` | HTTP client for REST endpoints with client ID tracking |
| **SSE Handler** | Built into ProcessingScreen | Handles Server-Sent Events for real-time streaming |

**Tech Stack:**
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- shadcn/ui for UI components
- Lucide for icons

---

### Backend (FastAPI + Python)

#### Core Server (`server.py`)
- FastAPI application with CORS middleware
- REST endpoints for individual agent operations
- SSE streaming endpoint for full pipeline execution
- Per-agent model configuration via environment variables

#### AI Agent Pipeline

| Agent | File | Purpose |
|-------|------|---------|
| **1. JobAnalyzerAgent** | `job_analyzer.py` | Analyzes job posting to extract requirements, skills, and key criteria |
| **2. ResumeOptimizerAgent** | `resume_optimizer.py` | Creates optimization strategy based on job analysis |
| **3. OptimizerImplementerAgent** | `optimizer_implementer.py` | Applies optimizations to the resume |
| **4. ValidatorAgent** | `validator.py` | Validates optimized resume against job requirements, generates scores |
| **5. PolishAgent** | `polish.py` | Final formatting and polish, outputs DOCX-ready content |

**Optional Agents:**
- **ProfileAgent** (`profile_agent.py`): Builds profile index from LinkedIn/GitHub
- **GitHubProjectsAgent** (`github_projects_agent.py`): Curates relevant GitHub projects

#### LLM Provider Clients (`src/api/`)

| Provider | File | Description |
|----------|------|-------------|
| OpenRouter | `openrouter.py` | Default provider, access to multiple models |
| Gemini | `gemini.py` | Google Gemini API |
| Cerebras | `cerebras.py` | Cerebras Cloud inference |
| Vertex AI | `vertex_ai.py` | Google Cloud Vertex AI |
| OpenAI | `openai_client.py` | OpenAI API |
| LongCat | `longcat.py` | LongCat thinking models |
| Zenmux | `zenmux.py` | Zenmux provider |

**Client Factory** (`client_factory.py`): Routes requests to appropriate provider based on model name.

#### Streaming System (`src/streaming/`)

| Component | File | Purpose |
|-----------|------|---------|
| **StreamManager** | `manager.py` | Manages SSE event emission and subscriptions |
| **Events** | `events.py` | Event types: JobStatus, StepProgress, Insight, Metric, AgentChunk |
| **InsightExtractor** | `insight_extractor.py` | Extracts key insights from agent outputs |
| **RunStore** | `run_store.py` | Persists run metadata for recovery |

#### Recovery System (`src/services/`)

| Component | File | Purpose |
|-----------|------|---------|
| **RecoveryService** | `recovery_service.py` | Session management, checkpoints, retry logic |
| **ErrorInterceptor** | `middleware/error_interceptor.py` | Captures errors for recovery |

#### Database (`src/database/db.py`)

SQLite database with tables:
- `applications`: Job applications with resume data
- `agent_outputs`: Output from each agent step
- `validation_scores`: Resume validation metrics
- `profiles`: Cached profile data (LinkedIn/GitHub)
- `run_metadata`: Pipeline run tracking
- `run_events`: SSE events for replay
- `recovery_sessions`: Error recovery state
- `agent_checkpoints`: Agent output checkpoints

---

### External Services

| Service | Purpose |
|---------|---------|
| **OpenRouter** | Multi-model LLM access (default provider) |
| **Google Gemini** | PDF extraction, alternative LLM |
| **Cerebras** | Fast inference |
| **Vertex AI** | Google Cloud LLM |
| **Exa** | Job posting URL scraping |
| **GitHub API** | Repository data for profile enhancement |

---

### Deployment

| Component | Platform | Details |
|-----------|----------|---------|
| **Frontend** | Vercel | Static site deployment |
| **Backend** | Google Cloud Run | Containerized FastAPI, Python 3.11 |

---

## Data Flow

```
1. User Input
   └─► Frontend (InputScreen)
       └─► POST /api/pipeline/start
           └─► Backend creates job_id
               └─► Returns stream_url

2. Pipeline Execution
   └─► Frontend subscribes to SSE stream
       └─► Backend runs agent pipeline:
           ├─► Agent 1: Analyze Job → emit progress/insights
           ├─► Agent 2: Optimize Resume → emit progress/insights
           ├─► Agent 3: Implement Changes → emit progress/insights
           ├─► Agent 4: Validate Resume → emit scores
           └─► Agent 5: Polish Resume → emit completion

3. Results
   └─► Frontend (RevealScreen)
       └─► GET /api/application/{id}
       └─► GET /api/export/{id}?format=docx
```

---

## Environment Variables

### Backend
```env
DEFAULT_MODEL=qwen/qwen3-max
ANALYZER_MODEL=...
OPTIMIZER_MODEL=...
IMPLEMENTER_MODEL=...
VALIDATOR_MODEL=...
POLISH_MODEL=...
PROFILE_MODEL=...

OPENROUTER_API_KEY=...
GEMINI_API_KEY=...
CEREBRAS_API_KEY=...
EXA_API_KEY=...

DATABASE_PATH=./data/applications.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_FREE_RUNS=5
DEV_MODE=false
```

### Frontend
```env
VITE_API_URL=http://localhost:8000
```

---

## Key Features

1. **Multi-Agent Pipeline**: 5 specialized AI agents working in sequence
2. **Real-time Streaming**: SSE-based progress updates and insights
3. **Multi-Provider LLM**: Support for 7+ LLM providers
4. **Error Recovery**: Checkpoint-based recovery with retry support
5. **Profile Enhancement**: LinkedIn and GitHub integration
6. **Export Options**: DOCX, PDF, HTML export formats
7. **Validation Scoring**: ATS optimization, requirements match, cultural fit metrics
