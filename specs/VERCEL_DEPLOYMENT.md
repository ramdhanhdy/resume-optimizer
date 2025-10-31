# Vercel Deployment Specification

## Overview
This document outlines the deployment strategy for the Resume Optimizer application to Vercel, including architecture considerations, limitations, and implementation steps.

## Architecture

### Current Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI (Python)
- **Database**: SQLite (local file-based)
- **Streaming**: Server-Sent Events (SSE)

### Deployment Model
**Hybrid Deployment** (Recommended):
- **Frontend**: Vercel (static hosting + SSR)
- **Backend**: Alternative platform (Railway, Render, or Fly.io)

**Why not full Vercel?**
Vercel has significant limitations for this application:

1. **Serverless Function Constraints**
   - 10s timeout (Hobby), 60s max (Pro) - insufficient for LLM streaming
   - Cold starts affect user experience
   - No persistent connections for SSE

2. **No Persistent Storage**
   - SQLite requires file system persistence
   - Serverless functions are stateless
   - Would require migration to external database (PostgreSQL, etc.)

3. **No Background Workers**
   - Cannot run long-lived processes
   - No support for job queues
   - Limited cron job capabilities

4. **WebSocket/SSE Limitations**
   - No native support for persistent connections
   - SSE streaming would be unreliable

## Deployment Options

### Option 1: Frontend on Vercel + Backend Elsewhere (RECOMMENDED)

#### Frontend (Vercel)
- Deploy React app as static site
- Configure API proxy to backend
- Use Vercel's CDN for assets
- Environment variables for backend URL

#### Backend (Railway/Render/Fly.io)
- Deploy FastAPI as containerized service
- Persistent storage for SQLite
- Always-on container (no cold starts)
- Support for SSE streaming
- Background job support

**Pros:**
- ✅ Best performance for frontend (Vercel CDN)
- ✅ No backend limitations
- ✅ Keep SQLite without migration
- ✅ SSE streaming works reliably
- ✅ Reasonable cost

**Cons:**
- ❌ Two separate deployments
- ❌ CORS configuration needed
- ❌ Slightly more complex setup

---

### Option 2: Full Vercel Deployment (NOT RECOMMENDED)

#### Requirements
- Migrate SQLite → PostgreSQL/Neon
- Rewrite streaming to work within 60s timeout
- Split long operations into multiple functions
- Use external queue service (Upstash, etc.)

**Pros:**
- ✅ Single platform
- ✅ Simplified deployment

**Cons:**
- ❌ Major code refactoring required
- ❌ Database migration needed
- ❌ Streaming reliability issues
- ❌ Cold start latency
- ❌ Higher complexity
- ❌ Limited by serverless constraints

---

### Option 3: Full Alternative Platform (Railway/Render)

Deploy both frontend and backend to same platform.

**Pros:**
- ✅ Single deployment
- ✅ No limitations
- ✅ Simpler architecture

**Cons:**
- ❌ No Vercel CDN benefits
- ❌ Potentially higher cost

---

## Recommended Implementation: Option 1

### Phase 1: Backend Deployment (Railway)

#### 1.1 Prepare Backend

**Create `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Update `backend/requirements.txt`:**
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-dotenv>=1.0.0
# ... rest of dependencies
```

**Create `backend/Dockerfile` (optional):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create exports directory
RUN mkdir -p exports

# Expose port
EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 Environment Variables (Railway)
```env
DEFAULT_MODEL=qwen/qwen3-max
OPENROUTER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
EXA_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
DATABASE_PATH=/app/data/applications.db
CORS_ORIGINS=https://your-frontend.vercel.app
```

#### 1.3 Deploy to Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add volume for SQLite persistence
railway volume create data --mount-path /app/data

# Deploy
railway up
```

#### 1.4 Configure CORS
Update `backend/server.py`:
```python
import os

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Phase 2: Frontend Deployment (Vercel)

#### 2.1 Prepare Frontend

**Create `vercel.json`:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        }
      ]
    }
  ]
}
```

**Update `frontend/.env.production`:**
```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

**Update API client (`frontend/src/services/api.ts`):**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }
  
  // ... rest of implementation
}
```

#### 2.2 Deploy to Vercel

**Option A: Vercel CLI**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

**Option B: GitHub Integration**
1. Push code to GitHub
2. Connect repository to Vercel
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Add environment variables in Vercel dashboard
5. Deploy

#### 2.3 Environment Variables (Vercel)
```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

---

### Phase 3: Testing & Verification

#### 3.1 Backend Health Check
```bash
curl https://your-backend.railway.app/
# Should return: {"message": "Resume Optimizer API", "version": "1.0.0"}
```

#### 3.2 Frontend Access
```bash
# Visit your Vercel URL
https://your-app.vercel.app

# Test API connection
# Open browser console and check network requests
```

#### 3.3 SSE Streaming Test
```bash
# Test streaming endpoint
curl -N https://your-backend.railway.app/api/jobs/test-job-id/stream
```

#### 3.4 Database Persistence
```bash
# SSH into Railway container
railway run bash

# Check database
ls -la /app/data/
sqlite3 /app/data/applications.db ".tables"
```

---

## Cost Estimation

### Railway (Backend)
- **Hobby Plan**: $5/month
  - 512MB RAM, 1 vCPU
  - $0.000231/GB-hour for storage
  - Suitable for development/small scale

- **Pro Plan**: $20/month + usage
  - Better for production
  - More resources
  - Priority support

### Vercel (Frontend)
- **Hobby Plan**: Free
  - 100GB bandwidth
  - Unlimited requests
  - Perfect for frontend

- **Pro Plan**: $20/month
  - More bandwidth
  - Team features
  - Analytics

**Total Monthly Cost**: ~$5-25/month

---

## Alternative Platforms Comparison

| Platform | Backend Support | Database | Pricing | Best For |
|----------|----------------|----------|---------|----------|
| **Railway** | ✅ Excellent | Persistent volumes | $5/mo | Full-stack apps |
| **Render** | ✅ Excellent | Persistent disks | $7/mo | Production apps |
| **Fly.io** | ✅ Excellent | Volumes | Pay-as-go | Global deployment |
| **DigitalOcean** | ✅ Good | Managed DB | $5/mo | Traditional hosting |
| **Vercel** | ⚠️ Limited | External only | Free-$20 | Frontend + simple API |

---

## Migration Checklist

### Backend (Railway)
- [ ] Create Railway account
- [ ] Set up project
- [ ] Configure environment variables
- [ ] Add persistent volume for SQLite
- [ ] Deploy backend
- [ ] Test API endpoints
- [ ] Verify database persistence
- [ ] Test SSE streaming

### Frontend (Vercel)
- [ ] Create Vercel account
- [ ] Connect GitHub repository
- [ ] Configure build settings
- [ ] Set environment variables
- [ ] Deploy frontend
- [ ] Test frontend access
- [ ] Verify API connectivity
- [ ] Test full user flow

### Post-Deployment
- [ ] Update DNS (if custom domain)
- [ ] Configure monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Enable analytics
- [ ] Document deployment process
- [ ] Create rollback plan

---

## Troubleshooting

### CORS Issues
```python
# Backend: Ensure CORS is properly configured
ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-app-*.vercel.app",  # Preview deployments
]
```

### SSE Connection Failures
- Check Railway logs: `railway logs`
- Verify timeout settings
- Test with curl first
- Check browser console for errors

### Database Not Persisting
```bash
# Verify volume is mounted
railway run ls -la /app/data

# Check database path in environment
railway variables
```

### Build Failures
```bash
# Frontend: Check build logs in Vercel dashboard
# Backend: Check Railway build logs

# Test locally first
npm run build  # Frontend
python -m pytest  # Backend
```

---

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **CORS**: Restrict to specific origins
3. **Rate Limiting**: Implement on backend
4. **HTTPS**: Enforced by both platforms
5. **Database**: Regular backups of SQLite file
6. **Secrets**: Use platform secret management

---

## Monitoring & Maintenance

### Railway
- Built-in metrics dashboard
- Log aggregation
- Resource usage monitoring
- Deployment history

### Vercel
- Analytics dashboard
- Performance insights
- Error tracking
- Deployment logs

### Recommended Tools
- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Uptime Robot**: Availability monitoring

---

## Conclusion

**Recommended Approach**: Deploy frontend to Vercel and backend to Railway.

This hybrid approach provides:
- ✅ Best performance (Vercel CDN for frontend)
- ✅ No backend limitations (Railway for FastAPI)
- ✅ Persistent storage (SQLite on Railway volumes)
- ✅ Reliable streaming (always-on containers)
- ✅ Cost-effective (~$5-25/month)
- ✅ Easy maintenance

**Not Recommended**: Full Vercel deployment due to serverless limitations that would require significant refactoring.
