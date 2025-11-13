# Troubleshooting Guide

This guide covers common issues and solutions for the AI Resume Optimizer application.

## Backend Issues

### Import Errors

**Problem**: Python import errors when starting the backend

**Solutions**:
- Ensure virtual environment is activated
- Run `uv pip install -r requirements.txt` to verify dependencies are installed
- Check that you're running from the `backend/` directory
- Verify Python version is 3.11+ with `python --version`

**Common fix**:
```bash
cd backend
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
uv pip install -r requirements.txt
```

### API Errors

**Problem**: Connection errors or API failures

**Solutions**:
- Verify API keys in `.env` file are correct and active
- Check provider-specific error messages in logs for quota/permission issues
- Ensure model names match supported providers (see `backend/src/api/model_registry.py`)
- Test API connectivity: `curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models`

**Environment variables to check**:
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
GEMINI_API_KEY=your_gemini_key_here
EXA_API_KEY=your_exa_key_here
```

### Database Errors

**Problem**: SQLite database errors or connection issues

**Solutions**:
- Ensure `DATABASE_PATH` directory exists and is writable
- Check file permissions on SQLite database
- In Cloud Run, remember data is ephemeral (use `/tmp` directory)
- For local development: `mkdir -p ./data` in backend directory

**Configuration**:
```bash
DATABASE_PATH=./data/applications.db  # Local development
DATABASE_PATH=/tmp/applications.db    # Cloud Run production
```

### SSE/Streaming Issues

**Problem**: Server-Sent Events not streaming or delayed

**Solutions**:
- SSE buffering in Cloud Run requires proper configuration (see deployment guide)
- Check Cloud Run minimum instance settings to prevent cold starts
- Enable event persistence for reliability
- Verify client is handling reconnection properly

**Cloud Run configuration**:
```bash
gcloud run services update resume-optimizer-backend \
  --min-instances=1 \
  --max-instances=10
```

### Rate Limiting Errors

**Problem**: HTTP 429 errors or "Rate limit exceeded"

**Solutions**:
- Check `MAX_FREE_RUNS` environment variable (default: 5)
- Verify client ID is being sent in `X-Client-ID` header
- Clear browser LocalStorage if client ID issues persist with `localStorage.clear()`
- Check rate limiting status in logs

**Configuration**:
```bash
MAX_FREE_RUNS=5  # Default free tier runs per client
```

## Frontend Issues

### Connection Errors

**Problem**: Frontend cannot connect to backend

**Solutions**:
- Ensure backend is running on the correct port (default: 8000)
- Check `VITE_API_URL` in frontend `.env.local`
- Verify CORS settings in backend `.env`
- Test API endpoint: `curl http://localhost:8000/api/health`

**Common configurations**:
```bash
# Frontend .env.local
VITE_API_URL=http://localhost:8000  # Development

# Backend .env
CORS_ORIGINS=*  # Development (restrict in production)
```

### Build Errors

**Problem**: npm build failures or dependency conflicts

**Solutions**:
- Delete `node_modules` and `package-lock.json`: `rm -rf node_modules package-lock.json`
- Run `npm ci` to reinstall clean dependencies
- Check Node.js version with `node --version` (requires 20+)
- Clear npm cache: `npm cache clean --force`

**Complete rebuild**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm ci
```

### Streaming/SSE Errors

**Problem**: No streaming updates or connection errors

**Solutions**:
- Check browser console for connection errors
- Verify backend `/api/jobs/{id}/stream` endpoint is accessible
- Ensure Cloud Run is configured for streaming (padding enabled)
- Test SSE manually: `curl -N http://localhost:8000/api/jobs/test/stream`

**Cloud Run SSE buffer fix**:
The backend automatically adds padding to force buffer flushes in Cloud Run.

### Styling Issues

**Problem**: Colors not displaying correctly or broken styles

**Solutions**:
- Never use hardcoded hex colors (e.g., `text-[#0274BD]`)
- Always use Tailwind utilities that reference CSS variables (e.g., `text-primary`)
- Check CSS variables are defined in `frontend/src/index.css`
- Verify `applyBrandConfig()` is called in `frontend/src/index.tsx`

**Correct usage**:
```tsx
// ✅ Correct
<div className="text-primary bg-accent/90">

// ❌ Incorrect
<div className="text-[#0274BD] bg-[#F57251]">
```

## Common Solutions

### CORS Errors in Development

**Problem**: CORS errors preventing frontend-backend communication

**Solution**:
```bash
# In backend .env
CORS_ORIGINS=*
```

For production, specify exact origins:
```bash
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.com
```

### Cloud Run SSE Buffering

**Problem**: SSE events delayed or buffered in Cloud Run

**Solution**:
- Events include padding to force buffer flushes
- Configure minimum instances to reduce cold starts
- Use event persistence for reliability
- Enable streaming in Cloud Run settings

**Backend automatically handles this**:
```python
# Each SSE event includes padding in server.py
data = f"{json.dumps(payload)}\n\n"
```

### Model Errors

**Problem**: "Model not found" or capability errors

**Solutions**:
- Check model supports required capabilities (`supports_files`, `supports_images`)
- Some models don't support temperature (e.g., GPT-5.1)
- Verify API keys have sufficient quota
- Check model availability in provider dashboard

**Testing model access**:
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Database Locking

**Problem**: SQLite "database is locked" errors

**Solutions**:
- Use connection pooling with timeout
- Ensure proper connection closing in code
- Consider using WAL mode for better concurrency
- For production, migrate to PostgreSQL

**WAL mode configuration**:
```python
# In db.py
conn.execute("PRAGMA journal_mode=WAL;")
```

### Missing Environment Variables

**Problem**: Application crashes with "KeyError" or "Missing environment variable"

**Solutions**:
- Copy `.env.example` to `.env` before running
- Verify all required variables are set
- Check variable names match exactly (case-sensitive)
- Use `.env.local` for frontend (not `.env`)

**Backend required variables**:
```bash
# Minimum one provider API key
OPENROUTER_API_KEY=your_key_here
# or
GEMINI_API_KEY=your_key_here

# Database
DATABASE_PATH=./data/applications.db

# CORS
CORS_ORIGINS=*
```

**Frontend required variables**:
```bash
VITE_API_URL=http://localhost:8000  # Development
```

### Memory Issues (Cloud Run)

**Problem**: Container running out of memory

**Solutions**:
- Increase memory allocation: `--memory=2Gi`
- Reduce batch sizes for large files
- Stream large responses instead of loading into memory
- Monitor memory usage in Cloud Console

**Cloud Run memory config**:
```bash
gcloud run services update resume-optimizer-backend \
  --memory=2Gi \
  --cpu=2
```
