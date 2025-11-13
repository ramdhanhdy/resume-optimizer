# Setup Guide

This guide provides step-by-step instructions for setting up the Resume Optimizer application locally.

## Prerequisites

- **Python 3.11+** (with `uv` package manager recommended)
- **Node.js 20+** with npm
- API keys for at least one LLM provider

## Backend Setup

### 1. Navigate to the backend directory

```bash
cd backend
```

### 2. Create and activate virtual environment

Using uv (recommended):
```bash
uv venv
```

Activate the environment:
```bash
# Windows (CMD)
.\.venv\Scripts\activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Create environment file

```bash
cp .env.example .env
# On Windows: copy .env.example .env
```

### 5. Configure API keys

Edit `.env` and add your API keys for at least one provider:

**Required (minimum one provider):**
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
# or
GEMINI_API_KEY=your_gemini_key_here
```

**Optional (additional providers):**
```bash
CEREBRAS_API_KEY=your_cerebras_key_here
EXA_API_KEY=your_exa_api_key
ZENMUX_API_KEY=your_zenmux_key
LONGCAT_API_KEY=your_longcat_key
```

### 6. Advanced configuration (optional)

**Per-agent models** (environment-specific):
```bash
# Individual models for each pipeline step
ANALYZER_MODEL=gemini::gemini-2.5-pro
OPTIMIZER_MODEL=openrouter::openai/gpt-5.1
IMPLEMENTER_MODEL=openrouter::anthropic/claude-sonnet-4.5
VALIDATOR_MODEL=gemini::gemini-2.5-pro
POLISH_MODEL=openrouter::anthropic/claude-sonnet-4.5
PROFILE_MODEL=openrouter::anthropic/claude-sonnet-4.5
INSIGHT_MODEL=openrouter::x-ai/grok-4-fast
```

**Per-agent temperature settings:
```bash
ANALYZER_TEMPERATURE=0.6
OPTIMIZER_TEMPERATURE=1
IMPLEMENTER_TEMPERATURE=0.6
VALIDATOR_TEMPERATURE=0.2
PROFILE_TEMPERATURE=0.6
POLISH_TEMPERATURE=0.7
```

**Rate limiting:
```bash
# Maximum free runs per client (default: 5)
MAX_FREE_RUNS=5
```

**Database:
```bash
# SQLite path (Cloud Run uses /tmp for ephemeral storage)
DATABASE_PATH=./data/applications.db
```

**CORS configuration:
```bash
# Comma-separated list of allowed origins (use * for development)
CORS_ORIGINS=*
```

## Frontend Setup

### 1. Navigate to the frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm ci  # or npm install
```

### 3. Create environment file

```bash
cp .env.example .env.local
# On Windows: copy .env.example .env.local
```

### 4. Configure API URL

Edit `.env.local`:

```bash
# Backend API URL (development)
VITE_API_URL=http://localhost:8000

# Optional: Brand customization
# VITE_BRAND_NAME=Resume Optimizer
# VITE_PRIMARY_COLOR=#0274BD
# VITE_ACCENT_COLOR=#F57251
```

**Note:** In production (Vercel), set to `/api` to use the Vercel rewrite proxy.

## Verification

### Test backend

```bash
cd backend
python server.py
```

Visit http://localhost:8000/docs to access the Swagger UI.

### Test frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

Visit the displayed URL (typically http://localhost:5173).

## Common Setup Issues

### Backend import errors
- Ensure virtual environment is activated
- Verify all dependencies installed: `pip list`

### Frontend build errors
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm ci`
- Check Node.js version: `node --version` (requires 20+)

### API connection errors
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check `VITE_API_URL` in frontend `.env.local`
- Ensure CORS settings in backend `.env`

### Database errors
- Ensure `DATABASE_PATH` directory exists
- Check file permissions on SQLite database
- In Cloud Run, remember data is ephemeral (use `/tmp`)
