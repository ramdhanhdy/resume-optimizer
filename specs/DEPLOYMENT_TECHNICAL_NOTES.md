# Deployment Technical Notes

## Architecture Decisions

### Why Not Full Vercel Deployment?

#### 1. Serverless Function Limitations

**Timeout Constraints:**
- Hobby: 10 seconds
- Pro: 60 seconds max
- Our LLM streaming can take 2-5 minutes per agent

**Impact on Application:**
```python
# Current implementation
async def run_pipeline_with_streaming(...):
    # Agent 1: Job Analysis (~30-60s)
    # Agent 2: Resume Optimization (~45-90s)
    # Agent 3: Implementation (~60-120s)
    # Agent 4: Validation (~30-60s)
    # Agent 5: Polish (~45-90s)
    # Total: 3-7 minutes ❌ Exceeds Vercel limits
```

**Would Require:**
- Breaking into multiple serverless functions
- Complex state management between functions
- External queue service (Upstash, etc.)
- Significant refactoring

#### 2. Database Persistence

**Current Setup:**
```python
# SQLite with local file system
DATABASE_PATH = "data/applications.db"
db = ApplicationDatabase()
```

**Vercel Limitation:**
- No persistent file system
- Each function invocation is stateless
- Files written are lost after execution

**Would Require:**
- Migration to PostgreSQL/MySQL
- External database service (Neon, PlanetScale, Supabase)
- Schema migration
- Connection pooling management
- Additional cost ($5-20/month)

#### 3. Server-Sent Events (SSE)

**Current Implementation:**
```python
@app.get("/api/jobs/{job_id}/stream")
async def stream_job_events(job_id: str):
    async def event_generator():
        while True:
            event = await stream_manager.get_event(job_id)
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Vercel Limitation:**
- Serverless functions can't maintain persistent connections
- SSE requires long-lived connection
- Would disconnect after timeout

**Would Require:**
- Polling-based approach (inefficient)
- WebSocket alternative (not supported)
- External streaming service
- Degraded UX

#### 4. File Generation & Storage

**Current Implementation:**
```python
# Generate DOCX in memory
docx_bytes = execute_docx_code(final_resume)

# Save to exports directory
export_dir = Path("exports") / f"{company}_{title}"
export_dir.mkdir(parents=True, exist_ok=True)
doc.save(export_dir / "resume.docx")
```

**Vercel Limitation:**
- No persistent storage for generated files
- Would need external storage (S3, Cloudinary)
- Additional complexity and cost

---

## Hybrid Architecture Benefits

### Frontend on Vercel

**Advantages:**
- ✅ Global CDN (fast page loads worldwide)
- ✅ Automatic HTTPS
- ✅ Preview deployments for PRs
- ✅ Zero-config deployment
- ✅ Free tier sufficient
- ✅ Excellent DX

**What Vercel Does Best:**
- Static asset serving
- Frontend builds
- Edge caching
- Git integration

### Backend on Railway/Render

**Advantages:**
- ✅ Always-on containers (no cold starts)
- ✅ Persistent volumes (SQLite works)
- ✅ No timeout limits (LLM streaming works)
- ✅ WebSocket/SSE support
- ✅ Background jobs
- ✅ Simple deployment

**What Railway/Render Does Best:**
- Long-running processes
- Stateful applications
- Database hosting
- Real-time features

---

## Performance Considerations

### Latency Analysis

**Vercel Frontend + Railway Backend:**
```
User Request → Vercel Edge (CDN) → Static Assets [~50ms]
API Call → Railway Backend → Processing [~100-200ms]
Total: ~150-250ms for API calls
```

**All Railway:**
```
User Request → Railway → Static Assets [~100-150ms]
API Call → Same Server → Processing [~50ms]
Total: ~150-200ms for API calls
```

**Verdict**: Negligible difference for API-heavy app like ours.

### Cold Start Impact

**Vercel Serverless:**
- Cold start: 1-3 seconds
- Warm: <100ms
- Frequency: After inactivity

**Railway Container:**
- Always warm: <100ms
- No cold starts
- Consistent performance

---

## Cost Analysis

### Scenario 1: Vercel + Railway (Recommended)

```
Monthly Usage Estimate:
- 1,000 resume optimizations
- 10GB data transfer
- 100GB storage

Costs:
- Vercel (Frontend): $0 (within free tier)
- Railway (Backend): $5 (Starter plan)
- Total: $5/month
```

### Scenario 2: Full Vercel (Hypothetical)

```
Required Services:
- Vercel Pro: $20/month (for 60s timeout)
- Neon PostgreSQL: $19/month (for database)
- Upstash Redis: $10/month (for queues)
- AWS S3: $5/month (for file storage)
- Total: $54/month + development time
```

### Scenario 3: All Railway

```
Costs:
- Railway Backend: $5/month
- Railway Frontend: $5/month
- Total: $10/month
```

**Winner**: Vercel + Railway ($5/month)

---

## Security Considerations

### API Key Management

**Current:**
```python
# Backend environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

**Deployment:**
- Railway: Encrypted environment variables
- Vercel: Encrypted environment variables
- Never in code or Git

### CORS Configuration

**Production Setup:**
```python
ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-app-*.vercel.app",  # Preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Security

**SQLite on Railway:**
- Volume encryption at rest
- Private network access only
- Regular backups via Railway CLI

```bash
# Backup database
railway run cat /app/data/applications.db > backup.db

# Restore
railway run sh -c 'cat > /app/data/applications.db' < backup.db
```

---

## Monitoring & Observability

### Railway Backend

**Built-in Metrics:**
- CPU usage
- Memory usage
- Network traffic
- Request count
- Response times

**Logs:**
```bash
# Real-time logs
railway logs --tail

# Filter by level
railway logs --level error
```

### Vercel Frontend

**Built-in Analytics:**
- Page views
- Unique visitors
- Top pages
- Performance metrics

**Logs:**
- Build logs in dashboard
- Function logs (if using API routes)

### Recommended Additional Tools

**Error Tracking:**
```bash
# Install Sentry
npm install @sentry/react @sentry/node

# Configure
SENTRY_DSN=your_dsn_here
```

**Uptime Monitoring:**
- UptimeRobot (free)
- Pingdom
- Better Uptime

---

## Scaling Strategy

### Current Capacity (Starter Plans)

**Railway Starter ($5/month):**
- 512MB RAM
- 1 vCPU
- Handles: ~50-100 concurrent users
- ~1,000 optimizations/month

**Vercel Hobby (Free):**
- 100GB bandwidth
- Unlimited requests
- Handles: ~10,000 visitors/month

### When to Scale

**Upgrade Railway to Developer ($10/month):**
- More than 100 concurrent users
- RAM usage consistently >80%
- Need faster processing

**Upgrade Vercel to Pro ($20/month):**
- More than 100GB bandwidth
- Need team features
- Want advanced analytics

### Horizontal Scaling

**Railway:**
```bash
# Scale to multiple instances
railway scale --replicas 3
```

**Load Balancing:**
- Railway handles automatically
- No configuration needed

---

## CI/CD Pipeline

### Current Setup

**Railway:**
- Auto-deploy on Git push
- Build on every commit
- Rollback support

**Vercel:**
- Auto-deploy on Git push
- Preview deployments for PRs
- Production on main branch

### Recommended Workflow

```
main branch
  ↓
  ├─→ Vercel (Frontend)
  │   ├─ Build
  │   ├─ Deploy to Preview
  │   └─ Deploy to Production
  │
  └─→ Railway (Backend)
      ├─ Build
      ├─ Run Tests
      └─ Deploy to Production
```

### GitHub Actions (Optional)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: railway up --detach

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## Database Backup Strategy

### Automated Backups

**Script: `backup-db.sh`**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
railway run cat /app/data/applications.db > backups/db_$DATE.db
echo "Backup created: db_$DATE.db"

# Keep only last 7 days
find backups/ -name "db_*.db" -mtime +7 -delete
```

**Cron Job:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup-db.sh
```

### Manual Backup

```bash
# Download database
railway run cat /app/data/applications.db > local_backup.db

# Upload to S3 (optional)
aws s3 cp local_backup.db s3://your-bucket/backups/
```

---

## Disaster Recovery

### Backup Railway Project

```bash
# Export environment variables
railway variables > env_backup.txt

# Export configuration
railway status > config_backup.txt
```

### Restore Procedure

1. Create new Railway project
2. Restore environment variables
3. Create volume
4. Deploy code
5. Restore database

```bash
# Restore database
railway run sh -c 'cat > /app/data/applications.db' < backup.db
```

### Vercel Restore

- Redeploy from Git
- Restore environment variables from dashboard
- No data loss (stateless)

---

## Performance Optimization

### Backend Optimizations

**Database Connection Pooling:**
```python
# Use connection pool for better performance
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_application(app_id: int):
    return db.get_application(app_id)
```

### Frontend Optimizations

**Code Splitting:**
```typescript
// Lazy load heavy components
const RevealScreen = lazy(() => import('./components/RevealScreen'));
const ProcessingScreen = lazy(() => import('./components/ProcessingScreen'));
```

**Asset Optimization:**
```bash
# Vite automatically optimizes
npm run build

# Output:
# - Minified JS/CSS
# - Tree-shaking
# - Code splitting
```

---

## Conclusion

The hybrid deployment (Vercel + Railway) provides:

1. **Best Performance**: CDN for frontend, always-on backend
2. **Lowest Cost**: $5/month total
3. **No Limitations**: Full feature support
4. **Easy Maintenance**: Simple deployment process
5. **Good DX**: Excellent developer experience

**Not Recommended**: Full Vercel deployment due to fundamental architectural incompatibilities that would require extensive refactoring and increased costs.
