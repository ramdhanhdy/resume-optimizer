# Railway-Only Deployment Specification

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

## Step 1: Backend Deployment

### 1.1 Prepare Backend

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
DATABASE_PATH = "/app/data/applications.db"
DEFAULT_MODEL = "qwen/qwen3-max"
```

**Update `backend/server.py`:**
```python
import os

# Railway provides PORT via environment
PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
```

### 1.2 Deploy Backend

```bash
cd backend

# Install Railway CLI
npm i -g @railway/cli
railway login

# Initialize project
railway init

# Create volume for database
railway volume create data --mount-path /app/data

# Set environment variables
railway variables set OPENROUTER_API_KEY=your_key_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set EXA_API_KEY=your_key_here
railway variables set GITHUB_TOKEN=your_token_here
railway variables set CORS_ORIGINS=https://your-frontend.railway.app

# Deploy
railway up
```

### 1.3 Get Backend URL

```bash
# Get the backend URL
railway domain
# Example: https://resume-optimizer-backend.railway.app
```

---

## Step 2: Frontend Deployment

### 2.1 Prepare Frontend

**Create `frontend/railway.toml`:**
```toml
[build]
builder = "NIXPACKS"
buildCommand = "npm install && npm run build"

[deploy]
startCommand = "npm run preview -- --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 30

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
export default defineConfig({
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
VITE_API_BASE_URL=https://your-backend.railway.app
```

### 2.2 Deploy Frontend

```bash
cd frontend

# Create new Railway service
railway service create frontend

# Deploy frontend
railway up

# Get frontend URL
railway domain
# Example: https://resume-optimizer-frontend.railway.app
```

### 2.3 Link Services (Optional)

```bash
# Link frontend to backend in same project
railway link
```

---

## Step 3: Configuration

### 3.1 Update CORS on Backend

```bash
cd backend

# Add frontend URL to CORS origins
railway variables set CORS_ORIGINS=https://your-frontend.railway.app

# Redeploy backend
railway up
```

### 3.2 Update Frontend API URL

```bash
cd frontend

# Update .env.production with actual backend URL
echo "VITE_API_BASE_URL=https://your-backend.railway.app" > .env.production

# Redeploy frontend
railway up
```

---

## Step 4: Testing & Verification

### 4.1 Test Backend

```bash
# Health check
curl https://your-backend.railway.app/

# Test API endpoint
curl https://your-backend.railway.app/api/applications
```

### 4.2 Test Frontend

```bash
# Visit frontend URL
# https://your-frontend.railway.app

# Test file upload and API calls
```

### 4.3 Test Internal Networking

Since both services are on Railway, you can use internal URLs:

**Update frontend `.env.production`:**
```env
# Use internal URL for better performance
VITE_API_BASE_URL=http://backend:8000
```

**Deploy with internal URL:**
```bash
cd frontend
echo "VITE_API_BASE_URL=http://backend:8000" > .env.production
railway up
```

---

## Environment Variables

### Backend Service
```env
PORT=8000
DATABASE_PATH=/app/data/applications.db
DEFAULT_MODEL=qwen/qwen3-max
OPENROUTER_API_KEY=sk-or-xxx
GEMINI_API_KEY=xxx
EXA_API_KEY=xxx
GITHUB_TOKEN=ghp_xxx
CORS_ORIGINS=https://your-frontend.railway.app
```

### Frontend Service
```env
PORT=3000
VITE_API_BASE_URL=https://your-backend.railway.app
# OR for internal networking:
# VITE_API_BASE_URL=http://backend:8000
```

---

## Railway Management

### View Services
```bash
railway services
```

### View Logs
```bash
# Backend logs
railway logs --service backend

# Frontend logs
railway logs --service frontend
```

### Scale Services
```bash
# Scale backend
railway scale backend

# Scale frontend
railway scale frontend
```

### Environment Variables
```bash
# List all variables
railway variables

# Set variable for specific service
railway variables set VAR=value --service backend
```

---

## Custom Domains

### Add Custom Domain
```bash
# For backend
railway domains add api.yourdomain.com --service backend

# For frontend
railway domains add app.yourdomain.com --service frontend
```

### Update CORS for Custom Domain
```bash
railway variables set CORS_ORIGINS=https://app.yourdomain.com --service backend
```

---

## Monitoring & Maintenance

### Built-in Monitoring
- **Metrics**: Available in Railway dashboard
- **Logs**: Access via CLI or dashboard
- **Health Checks**: Automatic based on configuration

### Set Up Alerts
```bash
# Configure alerts in Railway dashboard
# Monitor:
# - Response times
# - Error rates
# - Resource usage
```

### Backup Strategy
```bash
# Backup SQLite database
railway run "cp /app/data/applications.db /app/data/backups/applications-$(date +%Y%m%d).db"

# Automate backups with cron jobs
railway add cron --schedule "0 2 * * *" --command "cp /app/data/applications.db /app/data/backups/applications-$(date +%Y%m%d).db"
```

---

## Troubleshooting

### Service Not Starting
```bash
# Check logs
railway logs --service [service-name]

# Check environment variables
railway variables --service [service-name]

# Check build logs
railway logs --build --service [service-name]
```

### Database Issues
```bash
# Verify volume is mounted
railway run "ls -la /app/data" --service backend

# Check database file
railway run "sqlite3 /app/data/applications.db '.tables'" --service backend
```

### CORS Issues
```bash
# Check current CORS origins
railway variables | grep CORS_ORIGINS

# Update CORS origins
railway variables set CORS_ORIGINS=https://your-frontend.railway.app,https://www.yourdomain.com
```

### Performance Issues
```bash
# Scale up service
railway scale backend --instance-type professional-1x

# Check resource usage
railway status
```

---

## Cost Optimization

### Current Usage
- **2 Services**: $10/month (Starter plan)
- **Storage**: ~$0.10/month for SQLite volume
- **Bandwidth**: Included in starter plans

### Optimization Strategies
1. **Scale down during development**: Pause services when not in use
2. **Use shared resources**: Both services can share the same volume if needed
3. **Monitor usage**: Check Railway dashboard for actual resource consumption

### Scaling Costs
| Plan | Cost | Resources |
|------|------|-----------|
| Starter | $5/mo | 512MB RAM, 1 vCPU |
| Developer | $10/mo | 1GB RAM, 1 vCPU |
| Team | $20/mo | 2GB RAM, 2 vCPU |

---

## Migration from Hybrid

### From Vercel + Railway to Railway Only

1. **Deploy frontend to Railway** (Step 2 above)
2. **Update DNS** to point to Railway frontend
3. **Remove Vercel project**
4. **Update CORS** on backend
5. **Test all functionality**

### Benefits of Migration
- Single platform management
- Internal networking benefits
- Simplified billing and monitoring

---

## Best Practices

### Development Workflow
1. **Use separate environments**: Create staging services
2. **Feature flags**: Use environment variables for feature toggles
3. **Automated testing**: Set up CI/CD with Railway GitHub integration

### Security
1. **Environment variables**: Never commit secrets
2. **CORS restrictions**: Limit to specific domains
3. **HTTPS enforcement**: Railway provides automatic SSL

### Performance
1. **Internal networking**: Use internal URLs when possible
2. **Caching**: Implement appropriate caching strategies
3. **Monitoring**: Set up performance alerts

---

## Rollback Procedures

### Service Rollback
```bash
# View deployment history
railway deployments --service [service-name]

# Rollback to previous deployment
railway rollback [deployment-id] --service [service-name]
```

### Emergency Procedures
1. **Scale down**: `railway scale [service-name] --instance-count 0`
2. **Switch to previous version**: Use rollback command
3. **Database restore**: `railway run "cp /app/data/backups/applications-yyyymmdd.db /app/data/applications.db"`

---

## Conclusion

**Railway-only deployment** provides:
- ✅ Simplified management on single platform
- ✅ Internal networking benefits
- ✅ No CORS complexity
- ✅ Unified monitoring and billing
- ✅ Cost-effective for small teams

**Trade-offs**:
- Higher cost ($10 vs $5 monthly)
- No Vercel CDN benefits
- No preview deployments

**Best for**: Teams that value simplicity and unified management over cost optimization.

---

**Specification Version**: 1.0  
**Last Updated**: 2025-01-31  
**Status**: Production Ready
