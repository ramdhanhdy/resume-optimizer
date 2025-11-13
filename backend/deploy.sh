#!/bin/bash
# deploy.sh - Deploy Resume Optimizer Backend to Google Cloud Run
# 
# This script implements a hybrid secrets approach:
# - Sensitive API keys → Secret Manager (encrypted, auditable)
# - Configuration settings → Environment variables (easily updatable)
#
# Usage:
#   ./deploy.sh [--setup-secrets] [--region REGION] [--project PROJECT]
#
# Options:
#   --setup-secrets    Create/update secrets in Secret Manager (run once or when keys change)
#   --region          GCP region (default: us-central1)
#   --project         GCP project ID (default: from gcloud config)
#   --help            Show this help message

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
SERVICE_NAME="resume-optimizer-backend"
SETUP_SECRETS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --setup-secrets)
      SETUP_SECRETS=true
      shift
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --help)
      head -n 15 "$0" | tail -n 12
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# Validate project ID
if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}❌ Error: No GCP project ID found${NC}"
  echo "Set it with: gcloud config set project YOUR_PROJECT_ID"
  echo "Or use: ./deploy.sh --project YOUR_PROJECT_ID"
  exit 1
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Resume Optimizer Backend - Cloud Run Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "Project:  ${GREEN}$PROJECT_ID${NC}"
echo -e "Region:   ${GREEN}$REGION${NC}"
echo -e "Service:  ${GREEN}$SERVICE_NAME${NC}"
echo ""

# Function to create or update a secret
create_or_update_secret() {
  local secret_name=$1
  local env_var_name=$2
  
  # Get value from environment or .env file
  local secret_value="${!env_var_name}"
  
  if [ -z "$secret_value" ]; then
    if [ -f .env ]; then
      secret_value=$(grep "^${env_var_name}=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    fi
  fi
  
  if [ -z "$secret_value" ]; then
    echo -e "${YELLOW}⚠️  Warning: $env_var_name not found in environment or .env${NC}"
    return 1
  fi
  
  # Check if secret exists
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
    echo -e "${BLUE}📝 Updating secret: $secret_name${NC}"
    echo -n "$secret_value" | gcloud secrets versions add "$secret_name" \
      --data-file=- \
      --project="$PROJECT_ID"
  else
    echo -e "${GREEN}📦 Creating secret: $secret_name${NC}"
    echo -n "$secret_value" | gcloud secrets create "$secret_name" \
      --data-file=- \
      --replication-policy="automatic" \
      --project="$PROJECT_ID"
  fi
}

# Setup secrets if requested
if [ "$SETUP_SECRETS" = true ]; then
  echo -e "${BLUE}🔐 Setting up secrets in Secret Manager...${NC}"
  echo ""
  
  # Check if .env file exists
  if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create a .env file with your API keys"
    echo "See .env.example for reference"
    exit 1
  fi
  
  # Create/update secrets for API keys
  create_or_update_secret "openrouter-api-key" "OPENROUTER_API_KEY"
  create_or_update_secret "exa-api-key" "EXA_API_KEY"
  create_or_update_secret "gemini-api-key" "GEMINI_API_KEY"
  create_or_update_secret "cerebras-api-key" "CEREBRAS_API_KEY"
  create_or_update_secret "longcat-api-key" "LONGCAT_API_KEY"
  create_or_update_secret "zenmux-api-key" "ZENMUX_API_KEY"
  
  echo ""
  echo -e "${BLUE}🔑 Granting Cloud Run service account access to secrets...${NC}"
  
  # Get the Cloud Run service account (use project number)
  PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
  SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
  
  # Grant access to all secrets
  for secret in "openrouter-api-key" "exa-api-key" "gemini-api-key" "cerebras-api-key" "longcat-api-key" "zenmux-api-key"; do
    echo -e "${BLUE}  Granting access to: $secret${NC}"
    gcloud secrets add-iam-policy-binding "$secret" \
      --member="serviceAccount:$SERVICE_ACCOUNT" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID" \
      --condition=None \
      --quiet
  done
  
  echo ""
  echo -e "${GREEN}✅ Secrets setup complete!${NC}"
  echo ""
fi

# Prepare deployment
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
echo ""

# Build secret mapping for gcloud command
SECRET_MAPPING="OPENROUTER_API_KEY=openrouter-api-key:latest"
SECRET_MAPPING+=",EXA_API_KEY=exa-api-key:latest"
SECRET_MAPPING+=",GEMINI_API_KEY=gemini-api-key:latest"
SECRET_MAPPING+=",CEREBRAS_API_KEY=cerebras-api-key:latest"
SECRET_MAPPING+=",LONGCAT_API_KEY=longcat-api-key:latest"
SECRET_MAPPING+=",ZENMUX_API_KEY=zenmux-api-key:latest"

# Non-sensitive environment variables
# Note: PORT is automatically set by Cloud Run (always 8080)
ENV_VARS="DATABASE_PATH=/tmp/applications.db"
ENV_VARS+=",HOST=0.0.0.0"
ENV_VARS+=",CORS_ORIGINS=*"
ENV_VARS+=",DEFAULT_MODEL=gemini::gemini-2.5-pro"
ENV_VARS+=",ANALYZER_MODEL=gemini::gemini-2.5-pro"
ENV_VARS+=",OPTIMIZER_MODEL=openrouter::moonshotai/kimi-k2-thinking"
ENV_VARS+=",IMPLEMENTER_MODEL=openrouter::anthropic/claude-sonnet-4.5"
ENV_VARS+=",VALIDATOR_MODEL=openrouter::gemini::gemini-2.5-pro"
ENV_VARS+=",PROFILE_MODEL=openrouter::anthropic/claude-sonnet-4.5"
ENV_VARS+=",POLISH_MODEL=openrouter::anthropic/claude-sonnet-4.5"
ENV_VARS+=",ANALYZER_TEMPERATURE=0.6"
ENV_VARS+=",OPTIMIZER_TEMPERATURE=1"
ENV_VARS+=",IMPLEMENTER_TEMPERATURE=0.6"
ENV_VARS+=",VALIDATOR_TEMPERATURE=0.2"
ENV_VARS+=",PROFILE_TEMPERATURE=0.6"
ENV_VARS+=",POLISH_TEMPERATURE=0.7"

# Deploy to Cloud Run
# Single-instance mode: Fixes race conditions by ensuring all requests hit same instance
# This preserves in-memory state (_event_history, _subscribers) across SSE connections
# Trade-off: No horizontal scaling (max ~1000 concurrent connections)
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="$SECRET_MAPPING" \
  --set-env-vars="$ENV_VARS" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1 \
  --min-instances 1

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Service URL:${NC} ${GREEN}$SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Test the API: curl $SERVICE_URL/"
echo "  2. Update frontend VITE_API_URL to: $SERVICE_URL"
echo "  3. Monitor logs: gcloud run logs tail $SERVICE_NAME --region $REGION"
echo ""
echo -e "${YELLOW}⚠️  Note: SQLite database in /tmp is ephemeral${NC}"
echo "  Data will be lost when container restarts"
echo "  Consider migrating to Cloud SQL for production"
echo ""
