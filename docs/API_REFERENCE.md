# API Reference

Complete reference for all Resume Optimizer API endpoints.

## Base URL

**Development**: `http://localhost:8000`

**Production**: `https://resume-optimizer-backend-784455190453.us-central1.run.app`

All requests use `/api` prefix unless noted otherwise.

## Authentication

### Client ID (Required for Rate Limiting)

Include client ID in request header:
```
X-Client-ID: <client_id>
```

The frontend automatically generates and stores client ID in LocalStorage. For direct API usage, generate a unique UUIDv4.

### API Keys

API keys are configured on the backend via environment variables. No API key required in request headers - client ID is used for rate limiting.

---

## Main Pipeline

### Start Pipeline

**POST** `/api/pipeline/start`

Start the complete resume optimization pipeline with streaming.

**Request Body:**
```json
{
  "resume": "full resume text content",
  "job_posting_url": "https://example.com/job-posting",  // optional
  "job_posting_text": "raw job description text",       // optional
  "linkedin_url": "https://linkedin.com/in/profile",    // optional
  "github_username": "username"                         // optional
}
```

**Response:**
```json
{
  "job_id": "unique-job-identifier",
  "status": "processing",
  "message": "Pipeline started successfully"
}
```

**Features:**
- Asynchronous processing
- Returns immediately with job ID
- Results streamed via SSE
- Configurable rate limiting (default: 5 runs per client)

**Rate Limiting:**
- Returns HTTP 429 if limit exceeded
- Includes `Retry-After` header
- Configured via `MAX_FREE_RUNS` environment variable

---

### Stream Pipeline Events

**GET** `/api/jobs/{job_id}/stream`

Connect to Server-Sent Events for real-time pipeline progress.

**Response:** SSE stream with event types:

**Query Parameters:**
- `after_event_id` (optional): Resume from specific event ID

**Event Types:**

**job_status**: Pipeline state changes
```
event: job_status
id: 1
data: {"status": "processing", "step": "job_analysis", "progress": 16}
```

**agent_step**: Agent execution progress
```
event: agent_step
id: 5
data: {"agent": "job_analyzer", "status": "completed", "output": {...}}
```

**agent_chunk**: Real-time agent output chunks (for insight extraction)
```
event: agent_chunk
id: 12
data: {"agent": "resume_optimizer", "chunk": "optimization strategy..."}
```

**insight**: Extracted insights
```
event: insight
id: 18
data: {"type": "analysis", "content": "Key requirements identified..."}
```

**metrics**: Cost and performance metrics
```
event: metrics
id: 25
data: {
  "agent": "job_analyzer",
  "tokens_in": 1500,
  "tokens_out": 800,
  "cost_usd": 0.003
}
```

**done**: Pipeline completion
```
event: done
id: 42
data: {
  "status": "completed",
  "final_resume": "optimized resume content",
  "validation_score": 87,
  "total_cost": 0.145
}
```

**heartbeat**: Connection keep-alive
```
event: heartbeat
id: 100
data: {"timestamp": 1234567890}
```

**Features:**
- Event IDs increment monotonically
- Automatic reconnection support
- Event persistence for replay
- Configurable history retention

---

### Get Pipeline Snapshot

**GET** `/api/jobs/{job_id}/snapshot`

Get current pipeline state at any time.

**Response:**
```json
{
  "job_id": "unique-job-identifier",
  "status": "completed",
  "created_at": "2025-01-13T10:30:00Z",
  "agent_outputs": {
    "profile": {...},
    "job_analysis": {...},
    "optimization_strategy": {...},
    "optimized_resume": "...",
    "validation": {...},
    "polished_resume": "..."
  },
  "validation_scores": {
    "overall_match": 87,
    "skills_match": 92,
    "experience_match": 85,
    "red_flags": []
  },
  "cost_breakdown": {
    "total_cost": 0.145,
    "by_agent": {
      "job_analyzer": 0.012,
      "resume_optimizer": 0.038,
      "optimizer_implementer": 0.042,
      "validator": 0.028,
      "polish": 0.025
    }
  }
}
```

**Use Cases:**
- Reconnect and resume from last state
- Debug pipeline issues
- Get final results after completion

---

## Core Endpoints

### Upload Resume

**POST** `/api/upload-resume`

Upload and parse a resume file.

**Request:** multipart/form-data
```
file: <binary file content>
```

**Supported Formats:**
- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt)
- HTML (.html, .htm)

**Response:**
```json
{
  "status": "success",
  "filename": "resume.pdf",
  "parsed_text": "full extracted resume text...",
  "format": "pdf",
  "pages": 2
}
```

---

### Scan Resume

**POST** `/api/scan-resume`

Scan resume for detailed structure and metadata.

**Request:**
```json
{
  "resume_text": "full resume content"
}
```

**Response:**
```json
{
  "contact_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "sections": {
    "summary": "...",
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "chronology": {
    "total_years": 8,
    "gaps": [],
    "overlaps": []
  },
  "achievements": [...]
}
```

---

### Analyze Job Posting

**POST** `/api/analyze-job`

Extract structured data from job posting (Agent 1).

**Request:**
```json
{
  "url": "https://example.com/job-posting",     // optional
  "text": "raw job description text"           // optional
}
```

**Response:**
```json
{
  "job_title": "Senior Software Engineer",
  "company": "Tech Corp",
  "requirements": {
    "must_have": [...],
    "nice_to_have": [...]
  },
  "role_signals": {
    "seniority": "senior",
    "tech_stack": [...],
    "industry": "fintech"
  },
  "keywords": [...],
  "salary_range": "$120k-180k"
}
```

---

### Generate Optimization Strategy

**POST** `/api/optimize-resume`

Generate targeted optimization strategy (Agent 2).

**Request:**
```json
{
  "resume": "current resume text",
  "job_analysis": {...}  // from /api/analyze-job
}
```

**Response:**
```json
{
  "strategy": {
    "sections_to_modify": [...],
    "keyword_optimization": [...],
    "experience_mapping": [...],
    "skills_highlighting": [...]
  },
  "rationale": "detailed explanation of optimization approach"
}
```

---

### Build Optimized Resume

**POST** `/api/implement`

Apply optimization strategy to build enhanced resume (Agent 3).

**Request:**
```json
{
  "resume": "original resume",
  "optimization_strategy": {...},
  "job_analysis": {...}
}
```

**Response:**
```json
{
  "optimized_resume": "enhanced resume content",
  "changes_made": [...],
  "sections_modified": [...]
}
```

---

### Validate Resume

**POST** `/api/validate`

Evaluate optimized resume against job requirements (Agent 4).

**Request:**
```json
{
  "optimized_resume": "...",
  "original_resume": "...",
  "job_analysis": {...}
}
```

**Response:**
```json
{
  "scores": {
    "overall_match": 87,
    "skills_match": 92,
    "experience_match": 85,
    "education_match": 90
  },
  "red_flags": [],
  "recommendations": [
    "Consider adding AWS experience",
    "Quantify project impact with metrics"
  ]
}
```

---

### Polish Resume

**POST** `/api/polish`

Apply final polish and generate DOCX-ready output (Agent 5).

**Request:**
```json
{
  "resume": "optimized resume",
  "validation_results": {...}
}
```

**Response:**
```json
{
  "polished_resume": "final refined content",
  "docx_formatted": "DOCX-compatible formatted text",
  "page_recommendations": "2-3 pages recommended based on content",
  "final_score": 92,
  "red_flags_resolved": true
}
```

---

## Export & Download

### Export Resume

**GET** `/api/export/{job_id}`

Export the optimized resume in various formats.

**Query Parameters:**
- `format` (required): `docx`, `pdf`, or `html`

**Response:** File download

**Example:**
```bash
curl -o resume.docx "http://localhost:8000/api/export/12345?format=docx"
```

---

### Download Exported File

**GET** `/api/download/{filename}`

Download previously exported file.

**Response:** File download

---

## Application Management

### List Applications

**GET** `/api/applications`

Get list of all applications.

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset
- `status` (optional): Filter by status

**Response:**
```json
{
  "applications": [
    {
      "id": "uuid",
      "job_title": "Senior Software Engineer",
      "company": "Tech Corp",
      "status": "completed",
      "created_at": "2025-01-13T10:30:00Z",
      "validation_score": 87,
      "cost_usd": 0.145
    }
  ],
  "total": 42
}
```

---

### Get Application Details

**GET** `/api/application/{id}`

Get full details of a specific application.

**Response:**
```json
{
  "application": {
    "id": "uuid",
    "job_title": "Senior Software Engineer",
    "company": "Tech Corp",
    "status": "completed",
    "created_at": "2025-01-13T10:30:00Z",
    "resume_versions": {
      "original": "...",
      "optimized": "...",
      "polished": "..."
    },
    "pipeline_outputs": {...},
    "validation_scores": {...},
    "cost_breakdown": {...}
  }
}
```

---

## GitHub Integration

### Curate GitHub Projects

**POST** `/api/curate-github`

Curate relevant GitHub projects for resume enhancement.

**Request:**
```json
{
  "github_username": "username",
  "job_analysis": {...}  // optional
}
```

**Response:**
```json
{
  "curated_projects": [
    {
      "name": "Machine Learning Project",
      "description": "Built a predictive model achieving 95% accuracy",
      "technologies": ["Python", "TensorFlow"],
      "url": "https://github.com/user/project",
      "relevance_score": 0.92
    }
  ]
}
```

---

## Recovery & Health

### Health Check

**GET** `/api/health`

Simple health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890
}
```

---

### Check Recovery Status

**GET** `/api/recovery/{run_id}/status`

Check if a run can be recovered from checkpoint.

**Response:**
```json
{
  "recoverable": true,
  "last_completed_step": "job_analysis",
  "available_checkpoints": [...]
}
```

---

### Resume from Checkpoint

**POST** `/api/recovery/{run_id}/resume`

Resume pipeline execution from checkpoint.

**Request:**
```json
{
  "checkpoint_id": "checkpoint-uuid"
}
```

**Response:**
```json
{
  "status": "resumed",
  "job_id": "new-job-id"
}
```

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Maximum 5 runs per client.",
    "details": {
      "limit": 5,
      "retry_after": 3600
    }
  }
}
```

### Rate Limiting

**Headers in 429 response:**
```
Retry-After: 3600
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

---

## Rate Limiting Details

**Default Limits:**
- Free tier: 5 runs per client
- Adjustable via `MAX_FREE_RUNS` environment variable

**Client Identification:**
- Uses `X-Client-ID` header
- Frontend auto-generates UUID stored in LocalStorage
- Persists across browser sessions

**Rate Limit Response:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 3600  // seconds
  }
}
```

**Best Practices:**
- Generate unique client ID per user/device
- Implement exponential backoff for retries
- Cache results locally to avoid re-running
- Consider paid tier for higher limits
