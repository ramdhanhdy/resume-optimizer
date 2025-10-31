# Deployment Specifications

This directory contains comprehensive deployment documentation for the Resume Optimizer application.

## Documents Overview

### 1. [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)
**Primary deployment guide for Vercel + Railway hybrid approach**

- Why Vercel alone won't work for this app
- Recommended hybrid architecture (Frontend: Vercel, Backend: Railway)
- Step-by-step deployment instructions
- Configuration files and examples
- Cost analysis and comparisons
- Troubleshooting guide

**Read this first** if you want to deploy to production.

---

### 2. [DEPLOYMENT_ALTERNATIVES.md](./DEPLOYMENT_ALTERNATIVES.md)
**Alternative deployment platforms and configurations**

- Railway (full-stack) - RECOMMENDED
- Render (free tier available)
- Fly.io (global edge deployment)
- DigitalOcean App Platform
- Detailed comparison matrix
- Platform-specific configurations

**Read this** if you want to explore other hosting options.

---

### 3. [QUICK_DEPLOY_GUIDE.md](./QUICK_DEPLOY_GUIDE.md)
**Fast-track deployment guide (30 minutes)**

- TL;DR deployment steps
- Prerequisites checklist
- Quick Railway backend setup
- Quick Vercel frontend setup
- Verification steps
- Troubleshooting common issues

**Read this** if you want to deploy quickly without deep details.

---

### 4. [DEPLOYMENT_TECHNICAL_NOTES.md](./DEPLOYMENT_TECHNICAL_NOTES.md)
**Technical deep-dive and architecture decisions**

- Why serverless doesn't work for this app
- Performance analysis
- Security considerations
- Monitoring and observability
- Scaling strategy
- Backup and disaster recovery

**Read this** if you want to understand the technical reasoning.

---

## Quick Decision Tree

```
Do you want to deploy to production?
│
├─ Yes, as fast as possible
│  └─→ Read: QUICK_DEPLOY_GUIDE.md
│
├─ Yes, but I want to understand everything
│  └─→ Read: VERCEL_DEPLOYMENT.md
│
├─ I want to explore different platforms
│  └─→ Read: DEPLOYMENT_ALTERNATIVES.md
│
└─ I want technical details and reasoning
   └─→ Read: DEPLOYMENT_TECHNICAL_NOTES.md
```

---

## Recommended Deployment

**Frontend**: Vercel (Free tier)
**Backend**: Railway ($5/month)
**Total Cost**: $5/month
**Setup Time**: ~30 minutes

### Why This Approach?

✅ **Works with current codebase** (no refactoring needed)
✅ **Lowest cost** ($5/month)
✅ **Best performance** (Vercel CDN + always-on backend)
✅ **No limitations** (full feature support)
✅ **Easy to maintain** (simple deployment process)

### What Doesn't Work?

❌ **Full Vercel deployment** - Serverless limitations:
- 60s max timeout (our LLM streaming takes 3-7 minutes)
- No persistent storage (SQLite needs file system)
- No SSE support (streaming requires persistent connections)
- Would require major refactoring + external services

---

## Prerequisites

Before deploying, ensure you have:

- [ ] GitHub account
- [ ] Vercel account (free)
- [ ] Railway account (free trial, then $5/month)
- [ ] API keys:
  - [ ] OpenRouter API key
  - [ ] Gemini API key
  - [ ] Exa API key
  - [ ] GitHub token (optional)

---

## Deployment Steps Summary

### 1. Deploy Backend (Railway)
```bash
cd backend
railway init
railway volume create data --mount-path /app/data
railway variables set DATABASE_PATH=/app/data/applications.db
railway variables set OPENROUTER_API_KEY=your_key
railway up
```

### 2. Deploy Frontend (Vercel)
```bash
cd frontend
vercel
vercel --prod
```

### 3. Configure CORS
```bash
railway variables set CORS_ORIGINS=https://your-app.vercel.app
```

### 4. Test
- Visit your Vercel URL
- Try full optimization flow
- Verify streaming works
- Test export functionality

---

## Cost Breakdown

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| **Vercel** (Frontend) | Hobby | **$0** |
| **Railway** (Backend) | Starter | **$5** |
| **Total** | | **$5/month** |

### What You Get

- ✅ Unlimited frontend requests
- ✅ 100GB bandwidth (Vercel)
- ✅ Always-on backend (no cold starts)
- ✅ 1GB persistent storage (Railway)
- ✅ Automatic SSL/HTTPS
- ✅ Git-based deployments
- ✅ Preview deployments
- ✅ Monitoring & logs

---

## Support & Resources

### Platform Documentation
- **Railway**: https://docs.railway.app
- **Vercel**: https://vercel.com/docs
- **Render**: https://render.com/docs
- **Fly.io**: https://fly.io/docs

### Project Documentation
- **Main README**: ../README.md
- **Backend README**: ../backend/README.md
- **Frontend README**: ../frontend/README.md

### Getting Help
- Open an issue on GitHub
- Check troubleshooting sections in guides
- Platform support channels

---

## Deployment Checklist

### Pre-Deployment
- [ ] Code is tested locally
- [ ] All API keys are ready
- [ ] Git repository is set up
- [ ] Accounts created (Vercel, Railway)

### Backend Deployment
- [ ] Railway project created
- [ ] Volume created for database
- [ ] Environment variables set
- [ ] Backend deployed successfully
- [ ] Health check passes
- [ ] Database persists data

### Frontend Deployment
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Frontend deployed successfully
- [ ] Can access frontend URL
- [ ] API calls work (no CORS errors)

### Post-Deployment
- [ ] Full optimization flow tested
- [ ] Streaming works correctly
- [ ] Export/download works
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Documentation updated

---

## Common Issues

### CORS Errors
**Problem**: Frontend can't connect to backend
**Solution**: Update CORS_ORIGINS on Railway to include Vercel URL

### Database Not Persisting
**Problem**: Data lost after restart
**Solution**: Verify volume is mounted at `/app/data`

### Streaming Timeout
**Problem**: SSE connection drops
**Solution**: Check Railway logs, verify backend is always-on

### Build Failures
**Problem**: Deployment fails
**Solution**: Test build locally first, check logs

---

## Next Steps After Deployment

1. **Monitor Your App**
   - Check Railway metrics
   - Review Vercel analytics
   - Set up error tracking (Sentry)

2. **Configure Backups**
   - Set up automated database backups
   - Store backups externally (S3, etc.)

3. **Custom Domain** (Optional)
   - Add custom domain to Vercel
   - Add custom domain to Railway
   - Update CORS settings

4. **Optimize Performance**
   - Enable caching where appropriate
   - Monitor response times
   - Optimize database queries

5. **Security Hardening**
   - Review API key management
   - Enable rate limiting
   - Set up monitoring alerts

---

## Scaling Considerations

### When to Upgrade

**Railway Developer ($10/month):**
- More than 100 concurrent users
- Need more RAM/CPU
- Want faster processing

**Vercel Pro ($20/month):**
- More than 100GB bandwidth
- Need team features
- Want advanced analytics

### Horizontal Scaling

Railway supports multiple instances:
```bash
railway scale --replicas 3
```

---

## Migration Between Platforms

All platforms support:
- Git-based deployment
- Environment variables
- Docker containers
- Custom domains

**Switching is easy** - just redeploy to new platform with same configuration.

---

## Contributing

Found an issue or have improvements?
1. Open an issue
2. Submit a pull request
3. Update documentation

---

## License

Same as main project - see ../LICENSE

---

## Last Updated

October 29, 2025

---

**Ready to deploy? Start with [QUICK_DEPLOY_GUIDE.md](./QUICK_DEPLOY_GUIDE.md)!**
