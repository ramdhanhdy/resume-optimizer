# AI Resume Optimizer

A sophisticated full-stack AI-powered resume optimization application that uses a **deterministic 5-agent pipeline** to analyze job requirements and tailor your resume with ethical accuracy while maintaining professional authenticity.

## 🤖 Agent System Architecture

### Sequential Multi-Agent Pipeline
The application implements a **deterministic sequential pattern** where each agent builds upon the previous agent's output:

```
Profile Agent (Optional) → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5 → Renderer
```

**Actual Execution Flow:**
1. **Profile Agent** (Optional) - Builds context from LinkedIn/GitHub
2. **Agent 1** - Job Analysis 
3. **Agent 2** - Resume Optimization Strategy
4. **Agent 3** - Implementation (applies optimizations)
5. **Agent 4** - Validation (scoring and red flag analysis)
6. **Agent 5** - Polish (final refinement)
7. **Renderer** - Document formatting (zero-cost utility)

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

- **🎯 Agent 2 — Resume Optimizer**
  - Generates targeted optimization strategy using job analysis
  - Creates evidence-based improvement plan
  - Location: `backend/src/agents/resume_optimizer.py`

- **⚙️ Agent 3 — Optimizer Implementer**
  - Applies the optimization plan to the candidate's resume
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

- 🤖 **5-Agent AI Pipeline**: Sequential processing with job analysis, strategy generation, implementation, validation, and polishing
- 🎨 **Modern UI**: Beautiful React interface with real-time streaming updates and smooth animations
- 📄 **Multi-format Support**: Upload PDF, DOCX, or images with intelligent parsing
- 🔍 **URL Ingestion**: Fetch job postings directly from URLs using Exa API
- 📊 **Multi-dimensional Validation**: Comprehensive scoring with red flag detection and recommendations
- 💾 **Application Tracking**: Save and compare multiple applications with version history
- 📥 **Export Options**: Download optimized resumes in DOCX or PDF format
- 🛡️ **Ethical Grounding**: Built-in safeguards prevent fabrication with evidence-based optimization
- 🔄 **Real-time Streaming**: Live progress updates during agent execution
- 🎯 **Profile Enrichment**: Optional LinkedIn/GitHub integration for enhanced context

## Tech Stack

### Backend
- Python 3.11+
- FastAPI (REST API)
- Multi-provider LLM support:
  - OpenRouter (default)
  - Google Gemini API
  - Zenmux
  - Meituan LongCat
- SQLite (database)
- Exa API (job posting retrieval)

### Frontend
- React 19
- TypeScript
- Vite
- Framer Motion (animations)
- TailwindCSS (styling)

## Project Structure

```
resume-optimizer/
├── backend/               # Python FastAPI server
│   ├── src/
│   │   ├── agents/       # 🤖 AI agent implementations
│   │   │   ├── base.py           # Base agent class
│   │   │   ├── profile_agent.py  # Profile enrichment (optional)
│   │   │   ├── job_analyzer.py   # Agent 1: Job analysis
│   │   │   ├── resume_optimizer.py # Agent 2: Strategy generation
│   │   │   ├── optimizer_implementer.py # Agent 3: Implementation
│   │   │   ├── github_projects_agent.py # GitHub curation (optional)
│   │   │   ├── validator.py      # Agent 4: Validation & scoring
│   │   │   ├── polish.py         # Agent 5: Final polish
│   │   │   └── renderer.py       # Document rendering
│   │   ├── api/          # 🔌 API clients (OpenRouter, Exa, Gemini)
│   │   ├── app/
│   │   │   └── services/ # 📋 Service wrappers and orchestration
│   │   │       └── agents.py     # Agent service entrypoints
│   │   ├── database/     # 💾 SQLite database layer
│   │   └── utils/        # 🛠️ File processing utilities
│   ├── prompts/          # 📝 Agent prompt templates
│   ├── server.py         # FastAPI application
│   └── requirements.txt
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # ⚛️ React components with streaming support
│   │   ├── services/     # 🌐 API client with SSE handling
│   │   └── types/        # 📝 TypeScript types
│   └── package.json
├── docs/                 # 📚 Comprehensive documentation
│   ├── architecture/     # 🏗️ System architecture and agent design
│   ├── specs/           # 📋 Technical specifications
│   ├── setup/           # ⚙️ Setup and configuration guides
│   ├── integrations/    # 🔌 Integration documentation
│   ├── troubleshooting/ # 🔧 Bug fixes and solutions
│   └── deployment/      # 🚀 Production deployment guides
└── README.md
```

## Documentation

📚 **[View Complete Documentation](./docs/)** - Organized guides for setup, integrations, troubleshooting, and development.

**Quick Links:**
- [Setup Guide](./docs/setup/SETUP.md) - Installation and configuration
- [Gemini API Setup](./docs/setup/GEMINI_SETUP.md) - Add Google Gemini support
- [Integration Summary](./docs/integrations/INTEGRATION_SUMMARY.md) - Architecture overview
- [Troubleshooting](./docs/troubleshooting/) - Common issues and fixes
- [Checklists](./docs/checklists/) - Development and testing guides

## Setup

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file from the example:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

6. Add your API keys to `.env`:
```
OPENROUTER_API_KEY=your_actual_api_key
EXA_API_KEY=your_exa_api_key
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```bash
copy .env.example .env.local  # Windows
cp .env.example .env.local    # macOS/Linux
```

4. Configure the backend URL (default is already set to `http://localhost:8000`)

## Running the Application

### Start the Backend

```bash
cd backend
python server.py
```

The API will be available at `http://localhost:8000`

### Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The application will open at `http://localhost:3000`

## Usage

### 🚀 Agent-Powered Optimization Workflow

1. **📤 Upload Resume**: Upload your resume in PDF, DOCX, or image format
2. **🔗 Provide Job Details**: Paste the job posting URL or text (supports Exa API for URL fetching)
3. **🎯 Optional Profile Enhancement**: Add LinkedIn URL and/or GitHub username for contextual evidence
4. **🤖 Agent Pipeline Execution**: The sequential 5-agent system processes your application:
   
   **Step 0 - Profile Building** (Optional): Creates evidence index from LinkedIn/GitHub
   **Step 1 - Job Analysis**: Agent 1 extracts requirements, role signals, and keywords
   **Step 2 - Strategy Generation**: Agent 2 creates evidence-based optimization plan  
   **Step 3 - Implementation**: Agent 3 applies strategic changes to your resume
   **Step 4 - Validation**: Agent 4 evaluates accuracy, scores match, and flags issues
   **Step 5 - Polish**: Agent 5 refines output for professional presentation

5. **📊 Review Results**: Compare before/after versions with detailed explanations and validation scores
6. **💾 Save & Export**: Download optimized resume in DOCX format

## API Endpoints

### Main Pipeline
- `POST /api/pipeline/start` - Start full 5-agent pipeline with streaming
- `GET /api/jobs/{job_id}/stream` - Server-Sent Events for real-time progress
- `GET /api/jobs/{job_id}/snapshot` - Get current pipeline state

### Individual Agent Endpoints
- `POST /api/upload-resume` - Upload resume file
- `POST /api/analyze-job` - Analyze job posting (Agent 1)
- `POST /api/optimize-resume` - Generate strategy (Agent 2)
- `POST /api/implement` - Apply changes (Agent 3)
- `POST /api/validate` - Validate resume (Agent 4)
- `POST /api/polish` - Final polish (Agent 5)

### Additional Services
- `POST /api/curate-github` - Curate GitHub projects (separate service)
- `GET /api/export/{id}` - Export resume
- `GET /api/applications` - List all applications
- `GET /api/application/{id}` - Get application details

## Development

### Backend Development

```bash
cd backend
uvicorn server:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

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

- **Import errors**: Ensure virtual environment is activated
- **API errors**: Verify API keys in `.env` file
- **Port conflicts**: Change PORT in `.env`

### Frontend Issues

- **Connection errors**: Ensure backend is running on correct port
- **CORS errors**: Check CORS_ORIGINS in backend `.env`
- **Build errors**: Delete `node_modules` and reinstall

## License

MIT License - Free to use and modify

## Credits

- Backend prototype: JobHunt Agent
- Frontend prototype: CVit
- Integrated and enhanced for full-stack operation
