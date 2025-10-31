# Railway-Only Deployment Guide

## Overview

Deploy both frontend and backend to Railway for a **single-platform solution**.

### Pros vs Hybrid (Vercel + Railway)
✅ **Single platform** - easier management, one dashboard
✅ **Simpler setup** - no cross-platform configuration
✅ **One bill** - single payment method
✅ **Internal networking** - frontend and backend on same network
✅ **No CORS complexity** - can use relative URLs

### Cons vs Hybrid
❌ **No Vercel CDN** - slightly slower global asset delivery
❌ **Higher cost** - $10/month vs $5/month (2 services vs 1)
❌ **No preview deployments** - Railway doesn't have Vercel's PR previews

### Cost Comparison

| Approach | Frontend | Backend | Total |
|----------|----------|---------|-------|
| **Railway Only** | $5/mo | $5/mo | **$10/mo** |
| **Vercel + Railway** | Free | $5/mo | **$5/mo** |

**Verdict**: Railway-only costs $5 more but is simpler to manage.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Railway Platform                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Frontend Service│  │ Backend Service │ │
│  │  (React + Vite)  │  │   (FastAPI)     │ │
│  │  Port: 3000      │  │   Port: 8000    │ │
│  │  Public URL      │  │   Public URL    │ │
│  └────────┬─────────┘  └────────┬────────┘ │
│           │                     │          │
│           │  Internal Network   │          │
│           └─────────────────────┘          │
│                                 │          │
│                          ┌──────▼───────┐  │
│                          │   Volume     │  │
│                          │ (SQLite DB)  │  │
│                          │  /app/data   │  │
│                          └──────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Deployment Steps

### Prerequisites

- [ ] Railway account (sign up at railway.app)
- [ ] Railway CLI installed
- [ ] Git repository
- [ ] API keys ready

### Step 1: Install Railway CLI

```bash
# Install
npm i -g @railway/cli

# Login
railway login
```

### Step 2: Initialize Project

```bash
# Create new Railway project
railway init

# This creates a project and links your local directory
```

### Step 3: Deploy Backend

#### 3.1 Prepare Backend

**Create `backend/railway.toml`:**
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn server:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
PORT = "8000"
```

**Update `backend/server.py`:**
```python
import os

# Railway provides PORT environment variable
PORT = int(os.getenv("PORT", 8000))

# CORS - allow frontend service
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
```

#### 3.2 Deploy Backend

```bash
cd backend

# Deploy
railway up

# Create volume for SQLite
railway volume create data --mount-path /app/data --size 1

# Set environment variables
railway variables set DATABASE_PATH=/app/data/applications.db
railway variables set DEFAULT_MODEL=qwen/qwen3-max
railway variables set OPENROUTER_API_KEY=your_key_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set EXA_API_KEY=your_key_here
railway variables set GITHUB_TOKEN=your_token_here

# Get backend URL
railway domain
# Copy this URL (e.g., https://backend-production-xxxx.up.railway.app)
```

### Step 4: Deploy Frontend

#### 4.1 Prepare Frontend

**Create `frontend/railway.toml`:**
```toml
[build]
builder = "NIXPACKS"
buildCommand = "npm install && npm run build"

[deploy]
startCommand = "npm run preview -- --host 0.0.0.0 --port $PORT"

[env]
PORT = "3000"
```

**Update `frontend/package.json`:**
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "serve": "vite preview --host 0.0.0.0 --port $PORT"
  }
}
```

**Update `frontend/vite.config.ts`:**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.PORT || '3000'),
    host: '0.0.0.0',
  },
  preview: {
    port: parseInt(process.env.PORT || '3000'),
    host: '0.0.0.0',
  },
});
```

**Create `frontend/.env.production`:**
```env
# Use your actual backend Railway URL
VITE_API_BASE_URL=https://backend-production-xxxx.up.railway.app
```

**Update `frontend/src/services/api.ts`:**
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

#### 4.2 Deploy Frontend

```bash
cd ../frontend

# Create new service in same project
railway service create frontend

# Deploy
railway up

# Get frontend URL
railway domain
# This is your public URL (e.g., https://frontend-production-xxxx.up.railway.app)
```

### Step 5: Configure CORS

```bash
# Update backend CORS to allow frontend
cd ../backend
railway variables set CORS_ORIGINS=https://frontend-production-xxxx.up.railway.app

# Redeploy backend
railway up --detach
```

### Step 6: Link Services (Optional - Internal Networking)

If you want frontend to use internal Railway networking:

```bash
# Get internal backend URL
railway service

# Update frontend environment
cd ../frontend
railway variables set VITE_API_BASE_URL=http://backend.railway.internal:8000
```

**Note**: Internal networking only works between Railway services in the same project.

---

## Alternative: Monorepo Deployment

Deploy both from root directory with Railway's monorepo support.

### Create `railway.json` at root:

```json
{
  "version": 2,
  "services": [
    {
      "name": "backend",
      "source": {
        "directory": "backend"
      },
      "build": {
        "builder": "NIXPACKS",
        "buildCommand": "pip install -r requirements.txt"
      },
      "deploy": {
        "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
        "healthcheckPath": "/"
      }
    },
    {
      "name": "frontend",
      "source": {
        "directory": "frontend"
      },
      "build": {
        "builder": "NIXPACKS",
        "buildCommand": "npm install && npm run build"
      },
      "deploy": {
        "startCommand": "npm run preview -- --host 0.0.0.0 --port $PORT"
      }
    }
  ]
}
```

### Deploy:

```bash
# From root directory
railway up

# Railway will deploy both services
```

---

## Environment Variables

### Backend Service

```env
# Database
DATABASE_PATH=/app/data/applications.db

# Models
DEFAULT_MODEL=qwen/qwen3-max

# API Keys
OPENROUTER_API_KEY=sk-or-xxx
GEMINI_API_KEY=xxx
EXA_API_KEY=xxx
GITHUB_TOKEN=ghp_xxx

# CORS (use your actual frontend URL)
CORS_ORIGINS=https://frontend-production-xxxx.up.railway.app

# Port (Railway provides this)
PORT=8000
```

### Frontend Service

```env
# Backend URL (use your actual backend URL)
VITE_API_BASE_URL=https://backend-production-xxxx.up.railway.app

# Port (Railway provides this)
PORT=3000
```

---

## Testing Deployment

### 1. Test Backend

```bash
# Health check
curl https://backend-production-xxxx.up.railway.app/

# Should return:
# {"message": "Resume Optimizer API", "version": "1.0.0"}

# Test API endpoint
curl https://backend-production-xxxx.up.railway.app/api/applications
```

### 2. Test Frontend

```bash
# Visit frontend URL
https://frontend-production-xxxx.up.railway.app

# Check browser console for any errors
# Test uploading resume and job posting
```

### 3. Test Full Flow

1. Upload resume
2. Paste job posting
3. Start optimization
4. Verify streaming works
5. Download result

### 4. Verify Database Persistence

```bash
# SSH into backend container
railway run bash

# Check database
ls -la /app/data/
sqlite3 /app/data/applications.db ".tables"

# Exit
exit
```

---

## Monitoring & Logs

### View Logs

```bash
# Backend logs
railway logs --service backend --tail

# Frontend logs
railway logs --service frontend --tail

# All services
railway logs --tail
```

### View Metrics

```bash
# Open Railway dashboard
railway open

# Navigate to:
# - Metrics tab for CPU/Memory usage
# - Deployments tab for history
# - Settings tab for configuration
```

---

## Custom Domains (Optional)

### Add Custom Domain to Frontend

```bash
# In Railway dashboard
1. Go to frontend service
2. Click "Settings"
3. Scroll to "Domains"
4. Click "Add Domain"
5. Enter your domain (e.g., app.yourdomain.com)
6. Add CNAME record to your DNS:
   - Name: app
   - Value: [provided by Railway]
```

### Add Custom Domain to Backend

```bash
# In Railway dashboard
1. Go to backend service
2. Click "Settings"
3. Scroll to "Domains"
4. Click "Add Domain"
5. Enter your domain (e.g., api.yourdomain.com)
6. Add CNAME record to your DNS:
   - Name: api
   - Value: [provided by Railway]
```

### Update Environment Variables

```bash
# Update frontend to use custom backend domain
railway variables set VITE_API_BASE_URL=https://api.yourdomain.com

# Update backend CORS
railway variables set CORS_ORIGINS=https://app.yourdomain.com
```

---

## Scaling

### Vertical Scaling (More Resources)

```bash
# Upgrade plan in Railway dashboard
# Developer: $10/mo per service (1GB RAM, 2 vCPU)
# Team: $20/mo per service (2GB RAM, 4 vCPU)
```

### Horizontal Scaling (More Instances)

```bash
# Scale backend to multiple instances
railway scale --service backend --replicas 3

# Railway automatically load balances
```

---

## Backup Strategy

### Automated Database Backup

**Create `scripts/backup-railway-db.sh`:**
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_$DATE.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Download database from Railway
railway run --service backend cat /app/data/applications.db > $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.db" -mtime +30 -delete

# Optional: Upload to S3
# aws s3 cp $BACKUP_FILE s3://your-bucket/backups/
```

**Make executable:**
```bash
chmod +x scripts/backup-railway-db.sh
```

**Run manually:**
```bash
./scripts/backup-railway-db.sh
```

**Schedule with cron (daily at 2 AM):**
```bash
crontab -e

# Add:
0 2 * * * /path/to/scripts/backup-railway-db.sh
```

### Restore Database

```bash
# Restore from backup
railway run --service backend sh -c 'cat > /app/data/applications.db' < backups/db_20250129_020000.db

# Restart service
railway restart --service backend
```

---

## Cost Optimization

### Current Cost: $10/month

**Breakdown:**
- Backend service: $5/month (Starter)
- Frontend service: $5/month (Starter)
- Volume (1GB): Included
- Bandwidth: Included

### Ways to Reduce Cost

#### Option 1: Serve Frontend from Backend ($5/month)

Serve React build from FastAPI:

**Update `backend/server.py`:**
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve frontend static files
app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Serve API routes normally
    if full_path.startswith("api/"):
        return {"error": "Not found"}
    
    # Serve index.html for all other routes (SPA)
    return FileResponse("../frontend/dist/index.html")
```

**Deploy only backend:**
```bash
cd backend
railway up
```

**Cost**: $5/month (single service)

**Cons**: 
- No separate frontend service
- Harder to update frontend independently
- Mixed concerns (API + static files)

#### Option 2: Use Railway's Free Trial

Railway offers $5 free credit monthly:
- Backend: $5/month (covered by free credit)
- Frontend: $5/month (you pay)
- **Total**: $5/month

**Note**: Free credit resets monthly, not cumulative.

---

## Troubleshooting

### Frontend Can't Connect to Backend

**Check:**
1. Backend is running: `railway logs --service backend`
2. Frontend has correct backend URL: `railway variables --service frontend`
3. CORS is configured: `railway variables --service backend | grep CORS`

**Fix:**
```bash
# Update frontend backend URL
railway variables set VITE_API_BASE_URL=https://your-actual-backend.railway.app --service frontend

# Update backend CORS
railway variables set CORS_ORIGINS=https://your-actual-frontend.railway.app --service backend

# Redeploy both
railway up --service backend --detach
railway up --service frontend --detach
```

### Database Not Persisting

**Check:**
```bash
# Verify volume exists
railway volume list

# Check mount path
railway run --service backend ls -la /app/data
```

**Fix:**
```bash
# Create volume if missing
railway volume create data --mount-path /app/data --size 1

# Verify DATABASE_PATH
railway variables set DATABASE_PATH=/app/data/applications.db --service backend
```

### Build Failures

**Frontend:**
```bash
# Test build locally
cd frontend
npm install
npm run build

# Check Railway logs
railway logs --service frontend
```

**Backend:**
```bash
# Test locally
cd backend
pip install -r requirements.txt
python server.py

# Check Railway logs
railway logs --service backend
```

### High Memory Usage

**Monitor:**
```bash
railway metrics --service backend
```

**Fix:**
- Upgrade to Developer plan (1GB RAM)
- Optimize code (add caching, connection pooling)
- Scale horizontally (multiple instances)

---

## Comparison: Railway-Only vs Hybrid

| Aspect | Railway-Only | Vercel + Railway |
|--------|--------------|------------------|
| **Cost** | $10/mo | $5/mo |
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐⭐ Moderate |
| **Management** | Single dashboard | Two dashboards |
| **Global CDN** | ❌ No | ✅ Yes (Vercel) |
| **Preview Deploys** | ❌ No | ✅ Yes (Vercel) |
| **CORS Setup** | ✅ Simpler | ⚠️ Need config |
| **Internal Network** | ✅ Yes | ❌ No |
| **Best For** | Simplicity | Performance + Cost |

---

## When to Choose Railway-Only

✅ **Choose Railway-Only if:**
- You want simplicity over everything
- You prefer single-platform management
- You don't need global CDN
- You're okay with $10/month cost
- You want internal networking between services

❌ **Choose Hybrid (Vercel + Railway) if:**
- You want lowest cost ($5/month)
- You need global CDN for frontend
- You want preview deployments
- You're comfortable with two platforms

---

## Migration from Hybrid to Railway-Only

If you're currently on Vercel + Railway:

```bash
# 1. Deploy frontend to Railway
cd frontend
railway service create frontend
railway up

# 2. Get new frontend URL
railway domain --service frontend

# 3. Update backend CORS
cd ../backend
railway variables set CORS_ORIGINS=https://new-frontend-url.railway.app

# 4. Update frontend backend URL
cd ../frontend
railway variables set VITE_API_BASE_URL=https://backend-url.railway.app

# 5. Test everything works

# 6. Delete Vercel deployment
vercel remove
```

---

## Conclusion

**Railway-Only deployment is perfect for:**
- Developers who value simplicity
- Teams that want single-platform management
- Projects that don't need global CDN
- Applications with moderate traffic

**Cost**: $10/month
**Setup Time**: 20-30 minutes
**Complexity**: Low

**Alternative**: Hybrid (Vercel + Railway) saves $5/month but requires managing two platforms.

---

## Quick Commands Reference

```bash
# Deploy backend
cd backend && railway up

# Deploy frontend
cd frontend && railway up

# View logs
railway logs --tail

# View metrics
railway open

# Backup database
railway run --service backend cat /app/data/applications.db > backup.db

# Restore database
railway run --service backend sh -c 'cat > /app/data/applications.db' < backup.db

# Scale service
railway scale --service backend --replicas 3

# Add domain
railway domain add yourdomain.com --service frontend
```

---

**Ready to deploy? Follow the steps above and you'll be live in 30 minutes!**
