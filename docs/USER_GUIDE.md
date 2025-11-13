# User Guide

This guide explains how to use the Resume Optimizer application to enhance your resume and increase your chances of landing interviews.

## Workflow Overview

The resume optimization process follows a deterministic 6-step pipeline:

### Step 1: Upload Your Resume

**Supported formats**: PDF, DOCX, TXT, HTML

- Click the upload area or drag and drop your resume file
- The system will automatically extract and parse the content
- Original formatting is preserved for reference

### Step 2: Provide Job Details

**Option A: Job URL (Recommended)**
- Paste the job posting URL from LinkedIn, Indeed, or company careers page
- The system will automatically fetch and parse the content using Exa API

**Option B: Manual Entry**
- Copy and paste the job description text directly
- Include requirements, responsibilities, and qualifications

### Step 3: Optional Profile Enhancement

Add context for better optimization:
- **LinkedIn URL**: Builds professional profile index
- **GitHub Username**: Curates relevant projects and contributions

These enhance the evidence-based optimization by providing additional context.

### Step 4: Agent Pipeline Execution

The system processes your application through a sequential pipeline with real-time streaming updates:

**Step 0 - Profile Building (Optional)**
- If LinkedIn/GitHub provided: Creates evidence-backed profile index
- Enriches subsequent agent analysis with verified achievements

**Step 1 - Job Analysis**
- Extracts key requirements, role signals, and keywords
- Identifies must-have qualifications and nice-to-have skills
- Analyzes company culture indicators

**Step 2 - Strategy Generation**
- Creates evidence-based optimization plan
- Maps your experience to job requirements
- Suggests specific improvements without fabrication

**Step 3 - Resume Builder**
- Applies strategic changes to enhance your resume
- Optimizes language while preserving authenticity
- Highlights relevant accomplishments

**Step 4 - Validation**
- Evaluates optimized resume against job posting
- Provides multi-dimensional scoring (1-100 scale)
- Flags potential red flags or unsupported claims
- Generates specific recommendations for improvement

**Step 5 - Polish**
- Applies validator recommendations for final refinement
- Generates DOCX-ready output with professional formatting
- Provides page layout guidance (2-3 pages recommended)

### Step 5: Review Results

Compare before/after versions:
- **Original Resume**: Your uploaded version
- **Optimized Resume**: AI-enhanced version
- **Validation Scores**: Match percentage and improvement metrics
- **Red Flag Analysis**: Potential issues identified
- **Recommendations**: Specific suggestions for refinement

### Step 6: View Cost Tracking

Real-time cost estimates display:
- **Input Tokens**: Cost to send data to LLM
- **Output Tokens**: Cost to generate content
- **Thinking Tokens**: Cost for reasoning (some models)
- **Total Cost**: Per-agent and cumulative breakdowns

### Step 7: Save & Export

Download your optimized resume in multiple formats:
- **DOCX**: Editable Word document with professional formatting
- **PDF**: Print-ready version (via conversion)
- **HTML**: Web-compatible version

### Step 8: Reconnect Anytime (If Needed)

Pipeline state is persisted, enabling:
- **Network Interruption Recovery**: Resume from last event
- **Browser Refresh**: Reconnect without losing progress
- **Multi-Session Access**: Return later to view results
- **Event Replay**: Review previous runs

## Rate Limiting & Free Tier

The application includes built-in rate limiting:

**Free Tier Limits:**
- **5 resume generations per client** (browser)
- Tracking via LocalStorage-maintained client ID
- Persists across browser sessions

**Rate Limit Response:**
- HTTP 429 status code
- `Retry-After` header with wait time
- Contact information for higher limits

**Customizing Limits:**
Set `MAX_FREE_RUNS` environment variable to adjust (default: 5)

## Event Persistence & Replay

All pipeline events are stored in SQLite, enabling powerful features:

**Reconnection Support:**
- Automatically resume from last known event
- SSE client maintains event ID tracking
- No data loss during network issues

**Event Replay:**
- Debug previous runs
- Demonstrate pipeline to others
- Analyze optimization decisions

**State Recovery:**
- Serverless containers recover after restart
- Cloud Run instances preserve event history
- Zero-downtime deployments

**Snapshot Access:**
Retrieve current pipeline state anytime via:
```
GET /api/jobs/{job_id}/snapshot
```

Returns complete state including:
- Agent outputs and progress
- Validation scores
- Generated resume
- Run metadata and costs

## Best Practices

### Before Uploading:
1. **Use clean formatting**: Well-structured resumes parse better
2. **Include all relevant experience**: Don't omit jobs (agent will optimize)
3. **Use consistent dates**: Accurate chronology helps validation

### Job Posting Optimization:
1. **Provide full description**: Include requirements and responsibilities
2. **Company context matters**: Add company name for better tailoring
3. **Specificity helps**: Detailed requirements yield better optimization

### Reviewing Results:
1. **Verify accuracy**: Ensure all statements are true
2. **Check red flags**: Address any unsupported claims
3. **Customize formatting**: Adjust DOCX output to your preference
4. **Tailor further**: Manually adjust based on company culture

### Exporting:
1. **DOCX format**: Best for further editing
2. **PDF format**: Best for online applications
3. **Save application**: Compare multiple versions for different roles

## Support

For additional help:
- Check [troubleshooting guide](./TROUBLESHOOTING.md)
- Review [setup guide](./SETUP.md)
- See [API reference](./API_REFERENCE.md)
- Examine [architecture docs](./architecture/AGENTS_DESIGN_PATTERN.md)
