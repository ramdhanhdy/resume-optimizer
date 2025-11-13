# 🚀 Quick Start - Deploy to Cloud Run in 2 Minutes

## Prerequisites
- Google Cloud SDK installed: `gcloud --version`
- GCP project created and configured: `gcloud config get-value project`
- `.env` file with your API keys

## Step 1: Enable Required APIs (First Time Only)

```bash
gcloud services enable run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com
```

## Step 2: Setup Secrets (First Time Only)

```bash
cd backend
chmod +x deploy.sh
./deploy.sh --setup-secrets
```

This creates encrypted secrets in Secret Manager from your `.env` file.

## Step 3: Deploy

```bash
./deploy.sh
```

Done! 🎉

The script will output your service URL. Test it:

```bash
curl https://your-service-url.run.app/
```

## Update Deployment

**When you change code:**
```bash
./deploy.sh
```

**When API keys change:**
```bash
./deploy.sh --setup-secrets
```

## Troubleshooting

**"No module named 'streamlit'" error?**
- Already fixed! Just redeploy: `./deploy.sh`

**"Permission denied: deploy.sh"**
```bash
chmod +x deploy.sh
```

**Service not starting?**
```bash
gcloud run logs tail resume-optimizer-backend --region us-central1
```

## Next Steps

1. **Update Frontend**: Set your Cloud Run URL in frontend `.env`:
   ```
   VITE_API_URL=https://your-service-url.run.app
   ```

2. **Restrict CORS** (production):
   ```bash
   gcloud run services update resume-optimizer-backend \
     --set-env-vars="CORS_ORIGINS=https://yourdomain.com" \
     --region us-central1
   ```

3. **Monitor**: View logs and metrics in [GCP Console](https://console.cloud.google.com/run)

## Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed information.

---

**Need help?** Check the [troubleshooting section](./DEPLOYMENT.md#troubleshooting) in DEPLOYMENT.md
