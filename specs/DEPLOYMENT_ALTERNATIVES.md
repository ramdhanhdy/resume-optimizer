# Alternative Deployment Options

## Overview
This document provides deployment specifications for platforms other than Vercel, offering more flexibility for the full-stack Resume Optimizer application.

---

## Option 1: Railway (Full Stack) - RECOMMENDED

### Why Railway?
- ✅ Persistent storage (volumes)
- ✅ No cold starts
- ✅ Simple deployment from Git
- ✅ Built-in CI/CD
- ✅ Affordable ($5/month starter)
- ✅ Excellent DX (developer experience)

### Architecture
```
┌─────────────────────────────────────┐
│         Railway Platform            │
├─────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │ │
│  │  (React/Vite)│  │  (FastAPI)   │ │
│  │  Port: 3000  │  │  Port: 8000  │ │
│  └──────────────┘  └──────────────┘ │
│         │                  │         │
│         │                  │         │
│         │          ┌───────▼──────┐  │
│         │          │   Volume     │  │
│         │          │  (SQLite DB) │  │
│         │          └──────────────┘  │
└─────────────────────────────────────┘
```

### Deployment Steps

#### 1. Prepare Repository Structure
```
resume-optimizer/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   ├── railway.toml
│   └── ...
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
└── railway.json (optional)
```

#### 2. Backend Configuration

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

**Update `backend/server.py` for Railway:**
```python
import os

# Get port from environment (Railway provides this)
PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
```

#### 3. Frontend Configuration

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

#### 4. Deploy to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create new project
railway init

# Deploy backend
cd backend
railway up

# Create volume for database
railway volume create data --mount-path /app/data

# Set environment variables
railway variables set DATABASE_PATH=/app/data/applications.db
railway variables set DEFAULT_MODEL=qwen/qwen3-max
railway variables set OPENROUTER_API_KEY=your_key

# Deploy frontend (separate service)
cd ../frontend
railway service create frontend
railway up

# Link services
railway link
```

#### 5. Environment Variables

**Backend:**
```env
DATABASE_PATH=/app/data/applications.db
DEFAULT_MODEL=qwen/qwen3-max
OPENROUTER_API_KEY=sk-or-xxx
GEMINI_API_KEY=xxx
EXA_API_KEY=xxx
GITHUB_TOKEN=ghp_xxx
CORS_ORIGINS=https://your-frontend.railway.app
```

**Frontend:**
```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

### Cost
- **Starter**: $5/month (512MB RAM, 1GB storage)
- **Developer**: $10/month (1GB RAM, 5GB storage)
- **Team**: $20/month (2GB RAM, 10GB storage)

---

## Option 2: Render

### Why Render?
- ✅ Free tier available
- ✅ Persistent disks
- ✅ Auto-deploy from Git
- ✅ Built-in SSL
- ✅ Easy database management

### Architecture
```
┌─────────────────────────────────────┐
│          Render Platform            │
├─────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐ │
│  │  Static Site │  │  Web Service │ │
│  │  (Frontend)  │  │  (Backend)   │ │
│  └──────────────┘  └──────────────┘ │
│                           │         │
│                    ┌──────▼──────┐  │
│                    │ Disk Storage│  │
│                    │  (SQLite)   │  │
│                    └─────────────┘  │
└─────────────────────────────────────┘
```

### Deployment Steps

#### 1. Backend (Web Service)

**Create `render.yaml`:**
```yaml
services:
  - type: web
    name: resume-optimizer-backend
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    disk:
      name: sqlite-data
      mountPath: /app/data
      sizeGB: 1
    envVars:
      - key: DATABASE_PATH
        value: /app/data/applications.db
      - key: DEFAULT_MODEL
        value: qwen/qwen3-max
      - key: OPENROUTER_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: EXA_API_KEY
        sync: false
```

#### 2. Frontend (Static Site)

**Create `frontend/render.yaml`:**
```yaml
services:
  - type: web
    name: resume-optimizer-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
    routes:
      - type: rewrite
        source: /api/*
        destination: https://resume-optimizer-backend.onrender.com/api/*
```

#### 3. Deploy

1. Connect GitHub repository to Render
2. Create Web Service for backend
3. Create Static Site for frontend
4. Add environment variables
5. Deploy both services

### Cost
- **Free**: $0/month (limited resources, spins down after inactivity)
- **Starter**: $7/month (always on, 512MB RAM)
- **Standard**: $25/month (2GB RAM, better performance)

---

## Option 3: Fly.io

### Why Fly.io?
- ✅ Global edge deployment
- ✅ Persistent volumes
- ✅ Docker-based (full control)
- ✅ Pay-as-you-go pricing
- ✅ Excellent for low-latency

### Architecture
```
┌─────────────────────────────────────┐
│           Fly.io Platform           │
├─────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │ │
│  │  (Container) │  │  (Container) │ │
│  └──────────────┘  └──────────────┘ │
│                           │         │
│                    ┌──────▼──────┐  │
│                    │   Volume    │  │
│                    │  (SQLite)   │  │
│                    └─────────────┘  │
└─────────────────────────────────────┘
```

### Deployment Steps

#### 1. Backend Configuration

**Create `backend/fly.toml`:**
```toml
app = "resume-optimizer-backend"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  DATABASE_PATH = "/data/applications.db"

[mounts]
  source = "sqlite_data"
  destination = "/data"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
```

**Create `backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Frontend Configuration

**Create `frontend/fly.toml`:**
```toml
app = "resume-optimizer-frontend"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "3000"

[[services]]
  internal_port = 3000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

**Create `frontend/Dockerfile`:**
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Deploy

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy backend
cd backend
fly launch
fly volumes create sqlite_data --size 1
fly deploy

# Deploy frontend
cd ../frontend
fly launch
fly deploy
```

### Cost
- **Free tier**: 3 shared-cpu-1x VMs
- **Paid**: ~$5-10/month for small apps
- **Pay-as-you-go**: Based on actual usage

---

## Option 4: DigitalOcean App Platform

### Why DigitalOcean?
- ✅ Simple pricing
- ✅ Managed databases available
- ✅ Traditional hosting feel
- ✅ Good documentation

### Deployment

**Create `.do/app.yaml`:**
```yaml
name: resume-optimizer
region: nyc

services:
  - name: backend
    github:
      repo: your-username/resume-optimizer
      branch: main
      deploy_on_push: true
    source_dir: /backend
    build_command: pip install -r requirements.txt
    run_command: uvicorn server:app --host 0.0.0.0 --port 8000
    http_port: 8000
    instance_count: 1
    instance_size_slug: basic-xxs
    
  - name: frontend
    github:
      repo: your-username/resume-optimizer
      branch: main
      deploy_on_push: true
    source_dir: /frontend
    build_command: npm install && npm run build
    output_dir: dist
    static_sites:
      - name: frontend
```

### Cost
- **Basic**: $5/month per service
- **Professional**: $12/month per service

---

## Comparison Matrix

| Feature | Railway | Render | Fly.io | DigitalOcean |
|---------|---------|--------|--------|--------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Persistent Storage** | ✅ Volumes | ✅ Disks | ✅ Volumes | ⚠️ External |
| **Cold Starts** | ❌ None | ⚠️ Free tier | ❌ None | ❌ None |
| **Free Tier** | ❌ No | ✅ Yes | ✅ Limited | ❌ Trial only |
| **Starting Price** | $5/mo | $7/mo | ~$5/mo | $5/mo |
| **CI/CD** | ✅ Built-in | ✅ Built-in | ⚠️ Manual | ✅ Built-in |
| **Database Support** | ✅ Volumes | ✅ Disks | ✅ Volumes | ✅ Managed |
| **Global CDN** | ❌ No | ❌ No | ✅ Yes | ⚠️ Paid |
| **Docker Support** | ✅ Yes | ✅ Yes | ✅ Native | ✅ Yes |
| **Best For** | Full-stack | Prototypes | Global apps | Traditional |

---

## Recommendation Summary

### Best Overall: Railway
- **Why**: Best DX, simple pricing, persistent storage, no cold starts
- **Cost**: $5/month
- **Setup Time**: 15 minutes
- **Ideal For**: This project

### Best Free Option: Render
- **Why**: Free tier with persistent disks
- **Cost**: $0 (with limitations)
- **Setup Time**: 20 minutes
- **Ideal For**: Testing/prototypes

### Best for Scale: Fly.io
- **Why**: Global edge, Docker control
- **Cost**: ~$5-10/month
- **Setup Time**: 30 minutes
- **Ideal For**: Production at scale

### Most Traditional: DigitalOcean
- **Why**: Familiar hosting model
- **Cost**: $10/month (both services)
- **Setup Time**: 25 minutes
- **Ideal For**: Teams familiar with DO

---

## Next Steps

1. **Choose platform** based on your priorities
2. **Follow deployment guide** for chosen platform
3. **Set up monitoring** (logs, metrics, alerts)
4. **Configure backups** for SQLite database
5. **Test thoroughly** before going live
6. **Document** your deployment process

---

## Support Resources

- **Railway**: https://docs.railway.app
- **Render**: https://render.com/docs
- **Fly.io**: https://fly.io/docs
- **DigitalOcean**: https://docs.digitalocean.com

---

## Migration Between Platforms

All platforms support:
- Git-based deployment
- Environment variables
- Docker containers
- Custom domains

**Migration is straightforward** - just redeploy to new platform with same configuration.
