# Job URL Processing Troubleshooting Guide

## Problem Description

When users upload a PDF resume and enter a job posting URL, the application navigates to the processing screen but immediately fails with a "400: Either job_text or job_url is required" error.

## Symptoms

- Error appears after successful file upload
- Processing screen shows error before any agent execution
- Job URL input appears to be ignored by backend
- Only job text input works correctly

## User Flow That Triggers Bug

1. User uploads resume PDF → ✅ Extraction succeeds
2. User enters job posting URL (e.g., `https://linkedin.com/jobs/...`) → ✅ Stored in input
3. "Continue" button appears → ✅ User clicks or auto-advances
4. App transitions to ProcessingScreen → ✅ Navigation works
5. **Error appears**: "400: Either job_text or job_url is required" → ❌

## Root Cause Analysis

The issue is in the **frontend data flow**, specifically how the React application passes job input to the backend API.

### Data Flow Investigation

**Broken Flow** (Before Fix):
```
InputScreen:
  jobInput = "https://linkedin.com/jobs/123"
  isUrl = true
  ↓
App.tsx handleStartProcessing:
  jobText = undefined (because isUrl=true)
  jobUrl = NOT SET ❌
  ↓
ProcessingScreen:
  apiClient.analyzeJob({ 
    job_text: undefined  ❌
    // job_url missing!
  })
  ↓
Backend API:
  Expects either job_text OR job_url
  Receives: { job_text: undefined }
  Returns: 400 error ❌
```

**Working Flow** (After Fix):
```
InputScreen:
  jobInput = "https://linkedin.com/jobs/123"
  isUrl = true
  ↓
App.tsx handleStartProcessing:
  jobText = undefined (because isUrl=true)
  jobUrl = "https://linkedin.com/jobs/123" ✅
  ↓
ProcessingScreen:
  apiClient.analyzeJob({ 
    job_text: undefined,
    job_url: "https://linkedin.com/jobs/123" ✅
  })
  ↓
Backend API:
  Receives job_url ✅
  Fetches job posting via Exa ✅
  Processing continues ✅
```

## Diagnostic Steps

### 1. Verify Input Detection
```javascript
// In browser console, check InputScreen state
console.log('jobInput:', jobInput);
console.log('isUrl:', jobInput.startsWith('http'));
```

### 2. Check API Request Payload
```javascript
// In Network tab, inspect analyzeJob request
// Should contain: { job_url: "https://..." }
// Broken: { job_text: undefined }
```

### 3. Test Backend Directly
```bash
# Test backend endpoint directly
curl -X POST "http://localhost:8000/api/analyze-job" \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://linkedin.com/jobs/123"}'
```

## Resolution Steps

### Step 1: Update AppState Interface

**File**: `frontend/src/App.tsx`

**Add jobUrl field**:
```typescript
export interface AppState {
  applicationId?: number;
  resumeText?: string;
  jobText?: string;
  jobUrl?: string;  // NEW: Support URL input
  originalResumeText?: string;
  jobAnalysis?: any;
  optimizationStrategy?: any;
  implementedResume?: string;
  validationResults?: any;
  polishedResume?: string;
}
```

### Step 2: Fix Data Flow in handleStartProcessing

**File**: `frontend/src/App.tsx`

**Update function to store URL**:
```typescript
const handleStartProcessing = useCallback((data: { 
  resumeText: string; 
  jobInput: string; 
  isUrl: boolean 
}) => {
  setAppState(prev => ({
    ...prev,
    resumeText: data.resumeText,
    jobText: data.isUrl ? undefined : data.jobInput,
    jobUrl: data.isUrl ? data.jobInput : undefined,  // NEW: Store URL
  }));
  setScreen(Screen.Processing);
}, []);
```

### Step 3: Update ProcessingScreen Props

**File**: `frontend/src/App.tsx`

**Pass jobUrl to component**:
```typescript
{screen === Screen.Processing && (
  <ProcessingScreen 
    key="processing" 
    onComplete={handleProcessingComplete}
    resumeText={appState.resumeText!}
    jobText={appState.jobText}
    jobUrl={appState.jobUrl}  // NEW: Pass URL
  />
)}
```

### Step 4: Update ProcessingScreen Component

**File**: `frontend/src/components/ProcessingScreen.tsx`

**Add jobUrl to props**:
```typescript
interface ProcessingScreenProps {
  onComplete: (appState: any) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;  // NEW
}
```

**Update component signature**:
```typescript
const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ 
  onComplete, 
  resumeText, 
  jobText, 
  jobUrl  // NEW
}) => {
```

**Fix API call**:
```typescript
const jobAnalysis = await apiClient.analyzeJob({
  job_text: jobText,
  job_url: jobUrl,  // NEW: Pass URL to backend
});
```

**Update useEffect dependencies**:
```typescript
}, [resumeText, jobText, jobUrl]);  // Added jobUrl
```

## Verification Procedures

### Build Verification
```bash
cd frontend
npm run build
```
**Expected**: ✅ Build succeeds with no TypeScript errors

### Test Scenarios

#### Scenario 1: Job URL Input
1. Upload resume PDF → ✅ Extracts via Gemini 2.5 Flash
2. Enter job URL: `https://linkedin.com/jobs/123` → ✅
3. Click Continue → ✅
4. Processing starts → ✅ No error
5. Backend receives `job_url` → ✅ Fetches via Exa
6. All 5 agents run successfully → ✅

#### Scenario 2: Job Text Input
1. Upload resume PDF → ✅ Extracts via Gemini 2.5 Flash
2. Paste job text (not URL) → ✅
3. Click Continue → ✅
4. Processing starts → ✅ No error
5. Backend receives `job_text` → ✅ Uses directly
6. All 5 agents run successfully → ✅

#### Scenario 3: Auto-Advance
1. Upload resume PDF → ✅ Waits for extraction
2. Enter job URL → ✅
3. Wait 1 second → ✅ Auto-advances
4. Processing starts smoothly → ✅ No error

### Network Request Verification
- Check browser Network tab
- Verify `POST /api/analyze-job` request
- Confirm payload contains correct field
- Status should be 200 OK

## Related Issues

This fix is part of the broader PDF processing implementation:

1. **PDF Processing** (via Gemini 2.5 Flash):
   - Users can upload PDF resumes
   - Text extraction preserves formatting
   - Works with `POST /api/upload-resume`

2. **Job URL Processing** (this fix):
   - Users can provide job posting URLs
   - Backend fetches content via Exa API
   - Works with `POST /api/analyze-job`

## Prevention Measures

### Code Review Checklist
- [ ] All data flow paths tested
- [ ] URL detection logic verified
- [ ] API contracts validated
- [ ] TypeScript interfaces updated

### Testing Protocol
- Test both URL and text input methods
- Verify auto-advance works for both
- Check error handling for invalid URLs
- Test edge cases (empty inputs, malformed URLs)

### Development Guidelines
- Always update interfaces when adding new fields
- Test complete data flow end-to-end
- Verify API contracts match expectations
- Add comprehensive type checking

## Environment Requirements

### Required API Keys
```bash
# backend/.env
EXA_API_KEY=your_exa_api_key_here  # Required for URL fetching
```

### Backend Dependencies
- Exa API client for job posting retrieval
- URL validation and sanitization
- Error handling for network requests

## Escalation Criteria

Escalate to development team if:
- Fix doesn't resolve URL processing
- Text input stops working after changes
- Backend API validation fails
- Multiple users report similar issues

## Files Modified

1. `frontend/src/App.tsx`
   - AppState interface: Added `jobUrl?: string`
   - handleStartProcessing: Sets both `jobText` and `jobUrl`
   - ProcessingScreen props: Passes `jobUrl`

2. `frontend/src/components/ProcessingScreen.tsx`
   - Props interface: Added `jobUrl?: string`
   - Component signature: Accepts `jobUrl`
   - API call: Passes both `job_text` and `job_url`
   - useEffect dependencies: Added `jobUrl`

## Impact Assessment

### Before Fix
- ❌ Job URL input was completely broken
- ❌ Users saw "400: Either job_text or job_url is required"
- ❌ Could only use pasted job text, not URLs

### After Fix
- ✅ Job URL input works correctly
- ✅ Job text input continues to work (unchanged)
- ✅ Backend receives proper parameters
- ✅ Exa API fetches job postings from URLs
- ✅ Complete pipeline runs end-to-end

---

**Last Updated**: 2025-01-31  
**Severity**: High  
**Impact**: Core Functionality
