# Backend Deployment Guide

This guide covers deploying the Resume Optimizer backend to Google Cloud Run using a hybrid secrets approach.

## Prerequisites

1. **Google Cloud SDK (gcloud)**
   ```bash
   # Install: https://cloud.google.com/sdk/docs/install
   gcloud --version
   ```

2. **GCP Project Setup**
   ```bash
   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   
   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

3. **Local Environment**
   - Create `.env` file with your API keys (see `.env.example`)

## Deployment Architecture

### Hybrid Secrets Approach

**Sensitive Data → Secret Manager:**
- `OPENROUTER_API_KEY`
- `EXA_API_KEY`
- `GEMINI_API_KEY`
- `CEREBRAS_API_KEY`
- `LONGCAT_API_KEY`
- `ZENMUX_API_KEY`

**Configuration → Environment Variables:**
- `DATABASE_PATH`
- `HOST`, `CORS_ORIGINS` (Note: `PORT` is auto-set by Cloud Run)
- Model names (`DEFAULT_MODEL`, `ANALYZER_MODEL`, etc.)
- Temperature settings

## Quick Start

### First-Time Deployment

1. **Setup secrets** (run once):
   ```bash
   chmod +x deploy.sh
   ./deploy.sh --setup-secrets
   ```

2. **Deploy the service**:
   ```bash
   ./deploy.sh
   ```

That's it! The script will output your service URL.

### Update Deployment

**Update code:**
```bash
./deploy.sh
```

**Update secrets** (when API keys change):
```bash
./deploy.sh --setup-secrets
```

**Update environment variables only:**
```bash
gcloud run services update resume-optimizer-backend \
  --set-env-vars="DEFAULT_MODEL=new-model,ANALYZER_TEMPERATURE=0.5" \
  --region us-central1
```

## Manual Deployment (Without Script)

### 1. Create Secrets

```bash
# Create each secret
echo -n "your_api_key_here" | gcloud secrets create openrouter-api-key --data-file=-
echo -n "your_api_key_here" | gcloud secrets create exa-api-key --data-file=-
echo -n "your_api_key_here" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your_api_key_here" | gcloud secrets create cerebras-api-key --data-file=-
echo -n "your_api_key_here" | gcloud secrets create longcat-api-key --data-file=-
echo -n "your_api_key_here" | gcloud secrets create zenmux-api-key --data-file=-
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy resume-optimizer-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets="OPENROUTER_API_KEY=openrouter-api-key:latest,EXA_API_KEY=exa-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,CEREBRAS_API_KEY=cerebras-api-key:latest,LONGCAT_API_KEY=longcat-api-key:latest,ZENMUX_API_KEY=zenmux-api-key:latest" \
  --set-env-vars="DATABASE_PATH=/tmp/applications.db,HOST=0.0.0.0,CORS_ORIGINS=*,DEFAULT_MODEL=qwen/qwen3-max,ANALYZER_MODEL=qwen/qwen3-max,OPTIMIZER_MODEL=qwen/qwen3-max,IMPLEMENTER_MODEL=qwen/qwen3-max,VALIDATOR_MODEL=qwen/qwen3-max,PROFILE_MODEL=qwen/qwen3-max,POLISH_MODEL=zenmux::anthropic/claude-sonnet-4.5,ANALYZER_TEMPERATURE=0.3,OPTIMIZER_TEMPERATURE=0.7,IMPLEMENTER_TEMPERATURE=0.1,VALIDATOR_TEMPERATURE=0.2,PROFILE_TEMPERATURE=0.1,POLISH_TEMPERATURE=0.8" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 20
```

## Testing the Deployment

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe resume-optimizer-backend \
  --region us-central1 \
  --format 'value(status.url)')

# Test the API
curl $SERVICE_URL/

# Expected response:
# {"message":"Resume Optimizer API","version":"1.0.0"}
```

## Monitoring & Debugging

### View Logs
```bash
# Stream logs
gcloud run logs tail resume-optimizer-backend --region us-central1

# View recent logs
gcloud run logs read resume-optimizer-backend --region us-central1 --limit 50
```

### Check Service Status
```bash
gcloud run services describe resume-optimizer-backend --region us-central1
```

### Access Secret Manager
```bash
# List secrets
gcloud secrets list

# View secret metadata (not value)
gcloud secrets describe openrouter-api-key

# Access secret value (requires permissions)
gcloud secrets versions access latest --secret="openrouter-api-key"
```

## Configuration Reference

### Environment Variables

See `.env.cloudrun` for full documentation of environment variables.

### Resource Limits

Default configuration:
- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Timeout**: 300 seconds
- **Max Instances**: 20
- **Min Instances**: 0 (scales to zero)

To adjust:
```bash
gcloud run services update resume-optimizer-backend \
  --memory 1Gi \
  --cpu 2 \
  --max-instances 50 \
  --region us-central1
```

## Important Notes

### ⚠️ SQLite Database Limitation

**Current setup uses SQLite in `/tmp` which is EPHEMERAL:**
- Data is lost when container restarts
- Not suitable for production
- No concurrent write access

**For production, migrate to:**
1. **Cloud SQL** (PostgreSQL/MySQL) - Recommended
2. **Firestore** - Serverless NoSQL
3. **Cloud Storage** with persistence layer

### 🔒 Security

- **API keys** are stored in Secret Manager (encrypted)
- **IAM permissions** control who can access secrets
- **CORS** is set to `*` by default - restrict in production:
  ```bash
  --set-env-vars="CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
  ```

### 💰 Cost Optimization

Cloud Run charges based on:
- Request count
- CPU/memory usage
- Execution time

**Tips:**
- Set `--min-instances 0` to scale to zero when idle
- Adjust `--memory` based on actual usage
- Use `--cpu-throttling` for background workloads

## Troubleshooting

### Deployment Fails

**Check build logs:**
```bash
gcloud builds list --limit 5
gcloud builds log <BUILD_ID>
```

**Common issues:**
- Missing `runtime.txt` → Python version mismatch
- Missing dependencies in `requirements.txt`
- Import errors → Check logs for `ModuleNotFoundError`

### Service Not Starting

**View startup logs:**
```bash
gcloud run logs read resume-optimizer-backend --region us-central1 --limit 100
```

**Common issues:**
- Port configuration → Cloud Run auto-sets PORT=8080, don't override it
- Secret not found → Verify secret names in Secret Manager
- Database path error → Use `/tmp/` not Windows paths

### Secrets Not Working

**Verify secret exists:**
```bash
gcloud secrets list | grep openrouter
```

**Check IAM permissions:**
```bash
# Cloud Run service account needs secretAccessor role
gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Rollback

**Revert to previous revision:**
```bash
# List revisions
gcloud run revisions list --service resume-optimizer-backend --region us-central1

# Rollback
gcloud run services update-traffic resume-optimizer-backend \
  --to-revisions=REVISION_NAME=100 \
  --region us-central1
```

## Next Steps

1. **Update Frontend**: Set `VITE_API_URL` to your Cloud Run URL
2. **Setup CI/CD**: Automate deployments with GitHub Actions
3. **Migrate Database**: Move from SQLite to Cloud SQL
4. **Setup Monitoring**: Configure Cloud Monitoring alerts
5. **Custom Domain**: Map a custom domain to your service

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Monitoring Cloud Run](https://cloud.google.com/run/docs/monitoring)
