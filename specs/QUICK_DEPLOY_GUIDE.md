# Quick Deploy Guide - Resume Optimizer

## TL;DR - Fastest Path to Production

**Recommended**: Frontend on Vercel + Backend on Railway
**Time**: ~30 minutes
**Cost**: ~$5/month

---

## Prerequisites

- [ ] GitHub account
- [ ] Vercel account (free)
- [ ] Railway account (free trial, then $5/month)
- [ ] API keys ready:
  - OpenRouter API key
  - Gemini API key
  - Exa API key
  - GitHub token (optional)

---

## Step 1: Deploy Backend to Railway (15 min)

### 1.1 Install Railway CLI
```bash
npm i -g @railway/cli
railway login
```

### 1.2 Prepare Backend
```bash
cd backend

# Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn server:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
EOF
```

### 1.3 Deploy
```bash
# Initialize Railway project
railway init

# Create volume for SQLite
railway volume create data --mount-path /app/data

# Set environment variables
railway variables set DATABASE_PATH=/app/data/applications.db
railway variables set DEFAULT_MODEL=qwen/qwen3-max
railway variables set OPENROUTER_API_KEY=your_key_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set EXA_API_KEY=your_key_here
railway variables set GITHUB_TOKEN=your_token_here
railway variables set CORS_ORIGINS=https://your-app.vercel.app

# Deploy
railway up
```

### 1.4 Get Backend URL
```bash
railway domain
# Copy the URL (e.g., https://your-app.railway.app)
```

### 1.5 Test Backend
```bash
curl https://your-app.railway.app/
# Should return: {"message": "Resume Optimizer API", "version": "1.0.0"}
```

---

## Step 2: Deploy Frontend to Vercel (15 min)

### 2.1 Install Vercel CLI
```bash
npm i -g vercel
vercel login
```

### 2.2 Prepare Frontend
```bash
cd frontend

# Create vercel.json
cat > vercel.json << 'EOF'
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "installCommand": "npm install"
}
EOF

# Create .env.production
cat > .env.production << 'EOF'
VITE_API_BASE_URL=https://your-backend.railway.app
EOF
```

**Important**: Replace `your-backend.railway.app` with your actual Railway URL!

### 2.3 Deploy
```bash
# Deploy to Vercel
vercel

# For production
vercel --prod
```

### 2.4 Get Frontend URL
```bash
# Vercel will output the URL
# e.g., https://resume-optimizer.vercel.app
```

### 2.5 Update CORS on Backend
```bash
cd ../backend
railway variables set CORS_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app
```

---

## Step 3: Verify Deployment (5 min)

### 3.1 Test Frontend
1. Visit your Vercel URL
2. Try uploading a resume
3. Check if API calls work (open browser console)

### 3.2 Test Backend
```bash
# Health check
curl https://your-backend.railway.app/

# Test API endpoint
curl https://your-backend.railway.app/api/applications
```

### 3.3 Test Full Flow
1. Upload resume
2. Paste job posting
3. Start optimization
4. Check streaming works
5. Download result

---

## Troubleshooting

### CORS Errors
```bash
# Update CORS origins on Railway
railway variables set CORS_ORIGINS=https://your-actual-url.vercel.app

# Restart backend
railway up --detach
```

### API Connection Failed
1. Check frontend `.env.production` has correct backend URL
2. Verify backend is running: `railway logs`
3. Check Vercel environment variables in dashboard

### Database Not Persisting
```bash
# Verify volume is mounted
railway run ls -la /app/data

# Check database path
railway variables | grep DATABASE_PATH
```

### Build Failures

**Frontend:**
```bash
# Test build locally
npm run build

# Check Vercel logs in dashboard
```

**Backend:**
```bash
# Test locally
pip install -r requirements.txt
python server.py

# Check Railway logs
railway logs
```

---

## Environment Variables Checklist

### Backend (Railway)
```env
✓ DATABASE_PATH=/app/data/applications.db
✓ DEFAULT_MODEL=qwen/qwen3-max
✓ OPENROUTER_API_KEY=sk-or-xxx
✓ GEMINI_API_KEY=xxx
✓ EXA_API_KEY=xxx
✓ GITHUB_TOKEN=ghp_xxx (optional)
✓ CORS_ORIGINS=https://your-app.vercel.app
```

### Frontend (Vercel)
```env
✓ VITE_API_BASE_URL=https://your-backend.railway.app
```

---

## Post-Deployment

### Monitor Your App
```bash
# Backend logs
railway logs --tail

# Frontend logs
# Check Vercel dashboard
```

### Set Up Custom Domain (Optional)

**Vercel:**
1. Go to project settings
2. Add custom domain
3. Update DNS records

**Railway:**
1. Go to project settings
2. Add custom domain
3. Update DNS records

### Enable Analytics (Optional)

**Vercel:**
- Enable in project settings
- Free on all plans

**Railway:**
- View metrics in dashboard
- Set up alerts

---

## Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Railway (Backend) | Starter | $5/month |
| Vercel (Frontend) | Hobby | Free |
| **Total** | | **$5/month** |

---

## Scaling Up

### When to Upgrade

**Railway Pro ($20/month):**
- More than 100 daily users
- Need more RAM/CPU
- Want priority support

**Vercel Pro ($20/month):**
- Need team features
- Want more bandwidth
- Need advanced analytics

---

## Alternative: All-in-One Railway

If you prefer single platform:

```bash
# Deploy both to Railway
cd backend
railway init
railway up

cd ../frontend
railway service create frontend
railway up

# Link services
railway link
```

**Cost**: $10/month (2 services)
**Pros**: Single platform, simpler management
**Cons**: No Vercel CDN benefits

---

## Rollback Plan

### Railway
```bash
# View deployments
railway deployments

# Rollback to previous
railway rollback <deployment-id>
```

### Vercel
```bash
# View deployments
vercel ls

# Rollback via dashboard
# Or redeploy previous commit
```

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. ✅ Test full application
4. [ ] Set up monitoring
5. [ ] Configure backups
6. [ ] Add custom domain
7. [ ] Enable analytics
8. [ ] Document for team

---

## Support

- **Railway**: https://railway.app/help
- **Vercel**: https://vercel.com/support
- **This Project**: Open an issue on GitHub

---

## Success Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] API calls working (no CORS errors)
- [ ] Database persisting data
- [ ] SSE streaming working
- [ ] File uploads working
- [ ] Export/download working
- [ ] All environment variables set
- [ ] Monitoring configured
- [ ] Backup strategy in place

**Congratulations! Your app is live! 🎉**
