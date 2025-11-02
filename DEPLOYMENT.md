# Deployment Guide: Resume Optimizer

## Backend (Cloud Run) ✅ DEPLOYED
- **Service URL**: https://resume-optimizer-backend-784455190453.us-central1.run.app
- **Region**: us-central1
- **Project**: cvit-477003

### Make backend publicly accessible
Run this command to allow unauthenticated access:
```bash
gcloud beta run services add-iam-policy-binding resume-optimizer-backend \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker
```

## Frontend (Vercel)

### 1. Prerequisites
- GitHub account
- Vercel account (sign up at vercel.com with GitHub)
- Domain: xanalabs.com (managed via Google/Squarespace)
- Product subdomain: resume-agents.xanalabs.com

### 2. Deploy to Vercel

#### Option A: Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/new
2. Import your GitHub repository: `ramdhanhdy/resume-optimizer`
3. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Add environment variable:
   - Name: `VITE_API_URL`
   - Value: `/api` (uses the Vercel rewrite)
5. Click **Deploy**

#### Option B: Via Vercel CLI
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
When prompted:
- Set up and deploy: `Y`
- Scope: (select your account)
- Link to existing project: `N`
- Project name: `resume-optimizer`
- Directory: `./`
- Override settings: `N`

### 3. Configure Custom Domain (resume-agents.xanalabs.com)

#### In Vercel:
1. Go to your project → Settings → Domains
2. Add domain: `resume-agents.xanalabs.com`
3. Vercel will show DNS instructions (usually a CNAME record)

#### In your DNS provider (Google Domains or Squarespace):
Add a CNAME record:
- **Type**: CNAME
- **Name**: `resume-agents` (or `resume-agents.xanalabs.com`)
- **Value**: `cname.vercel-dns.com` (Vercel will provide the exact value)
- **TTL**: Auto or 3600

Wait 5-10 minutes for DNS propagation. Vercel will auto-provision SSL.

### 4. How the integration works
- Frontend is served from: `https://resume-agents.xanalabs.com`
- API calls to `/api/*` are proxied to Cloud Run via `vercel.json` rewrite
- No CORS configuration needed (same-origin requests)
- Backend receives requests as if they came directly from Cloud Run URL

### 5. Files created for deployment
- `frontend/vercel.json` - Configures API proxy to Cloud Run
- `frontend/.env.production` - Sets VITE_API_URL to `/api` for production

### 6. Test the deployment
After Vercel deployment completes:
1. Open https://resume-agents.xanalabs.com (or your Vercel preview URL)
2. Try uploading a resume
3. Try analyzing a job posting
4. Check browser DevTools → Network to verify `/api/*` calls work

### 7. Optional: Pretty API domain (api.xanalabs.com)
If you want to expose the API on a custom domain:
```bash
gcloud run domain-mappings create \
  --service resume-optimizer-backend \
  --region us-central1 \
  --domain api.xanalabs.com
```
Then add the DNS records Google provides (CNAME to ghs.googlehosted.com).

Update `vercel.json` to use the new domain:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.xanalabs.com/api/:path*"
    }
  ]
}
```

## Security Improvements (Post-deployment)

### 1. Tighten CORS (if using direct calls instead of proxy)
```bash
gcloud run services update resume-optimizer-backend \
  --region us-central1 \
  --update-env-vars=CORS_ORIGINS=https://resume-agents.xanalabs.com
```

### 2. Move API keys to Secret Manager
```bash
# Create secrets
echo -n "your-openrouter-key" | gcloud secrets create openrouter-api-key --data-file=-
echo -n "your-exa-key" | gcloud secrets create exa-api-key --data-file=-
# ... repeat for other keys

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member=serviceAccount:784455190453-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Redeploy with secrets
gcloud run deploy resume-optimizer-backend \
  --source . \
  --region us-central1 \
  --set-secrets=OPENROUTER_API_KEY=openrouter-api-key:latest,EXA_API_KEY=exa-api-key:latest
```

### 3. Database persistence (Cloud SQL)
Current setup uses SQLite at `/tmp/applications.db` (ephemeral - data lost on restart).

For production persistence, migrate to Cloud SQL PostgreSQL:
1. Create Cloud SQL instance
2. Update `backend/src/database/db.py` to use PostgreSQL
3. Set env vars: `CLOUD_SQL_CONNECTION_NAME`, `DB_USER`, `DB_PASS`, `DB_NAME`

## Troubleshooting

### Frontend can't reach backend
- Check browser console for CORS errors
- Verify `vercel.json` rewrite is correct
- Ensure backend is publicly invokable (run the IAM binding command above)

### Backend returns 403
- Run the IAM binding command to make it public
- Or set up authentication if you want private access

### DNS not resolving
- Wait 10-30 minutes for DNS propagation
- Check DNS with: `nslookup resume-agents.xanalabs.com`
- Verify CNAME points to Vercel's value

### Build fails on Vercel
- Check build logs in Vercel dashboard
- Ensure `frontend` directory is set as root
- Verify all dependencies are in `package.json`

## Summary
1. ✅ Backend deployed to Cloud Run
2. ⏳ Make backend public (run IAM command above)
3. ⏳ Deploy frontend to Vercel
4. ⏳ Add resume-agents.xanalabs.com domain to Vercel
5. ⏳ Add CNAME record in DNS
6. ⏳ Test end-to-end
