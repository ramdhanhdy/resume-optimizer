# Job URL Processing Bug Fix

## Issue Description

**Problem**: When users uploaded a PDF resume and entered a job posting URL, the app would navigate to the processing screen but immediately fail with error:

```
Processing failed: 400: Either job_text or job_url is required
```

**User Flow That Triggered Bug**:
1. User uploads resume PDF → ✅ Extraction succeeds
2. User enters job posting URL (e.g., `https://linkedin.com/jobs/...`) → ✅ Stored in input
3. "Continue" button appears → ✅ User clicks or auto-advances
4. App transitions to ProcessingScreen → ✅ Navigation works
5. **Error appears**: "400: Either job_text or job_url is required" → ❌

## Root Cause

The bug was in the **frontend data flow**, specifically in how the React app passed job input to the backend API.

### Data Flow Analysis

**Before Fix** (Broken):
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

**After Fix** (Working):
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

## Changes Made

### 1. Updated `frontend/src/App.tsx`

**Added `jobUrl` to AppState interface**:
```typescript
export interface AppState {
  applicationId?: number;
  resumeText?: string;
  jobText?: string;
  jobUrl?: string;  // NEW: Support URL input
  // ... other fields
}
```

**Fixed `handleStartProcessing` to store URL**:
```typescript
const handleStartProcessing = useCallback((data: { resumeText: string; jobInput: string; isUrl: boolean }) => {
  setAppState(prev => ({
    ...prev,
    resumeText: data.resumeText,
    jobText: data.isUrl ? undefined : data.jobInput,
    jobUrl: data.isUrl ? data.jobInput : undefined,  // NEW: Store URL
  }));
  setScreen(Screen.Processing);
}, []);
```

**Updated ProcessingScreen props**:
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

### 2. Updated `frontend/src/components/ProcessingScreen.tsx`

**Added `jobUrl` to props interface**:
```typescript
interface ProcessingScreenProps {
  onComplete: (appState: any) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;  // NEW
}
```

**Updated component signature**:
```typescript
const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ 
  onComplete, 
  resumeText, 
  jobText, 
  jobUrl  // NEW
}) => {
```

**Fixed API call to pass both parameters**:
```typescript
const jobAnalysis = await apiClient.analyzeJob({
  job_text: jobText,
  job_url: jobUrl,  // NEW: Pass URL to backend
});
```

**Updated dependency array**:
```typescript
}, [resumeText, jobText, jobUrl]);  // Added jobUrl
```

## Files Modified

1. `frontend/src/App.tsx`
   - AppState interface: Added `jobUrl?: string`
   - handleStartProcessing: Now sets both `jobText` and `jobUrl`
   - ProcessingScreen props: Now passes `jobUrl`

2. `frontend/src/components/ProcessingScreen.tsx`
   - Props interface: Added `jobUrl?: string`
   - Component signature: Accepts `jobUrl`
   - API call: Passes both `job_text` and `job_url`
   - useEffect dependencies: Added `jobUrl`

## Testing

### Build Verification
```bash
cd frontend
npm run build
```
**Result**: ✅ Build succeeded with no TypeScript errors

### Test Scenarios

**Scenario 1: Job URL Input**
1. Upload resume PDF → ✅ Extracts via Gemini 2.5 Flash
2. Enter job URL: `https://linkedin.com/jobs/123` → ✅
3. Click Continue → ✅
4. Processing starts → ✅ No error
5. Backend receives `job_url` → ✅ Fetches via Exa
6. All 5 agents run successfully → ✅

**Scenario 2: Job Text Input**
1. Upload resume PDF → ✅ Extracts via Gemini 2.5 Flash
2. Paste job text (not URL) → ✅
3. Click Continue → ✅
4. Processing starts → ✅ No error
5. Backend receives `job_text` → ✅ Uses directly
6. All 5 agents run successfully → ✅

**Scenario 3: Auto-Advance**
1. Upload resume PDF → ✅ Waits for extraction
2. Enter job URL → ✅
3. Wait 1 second → ✅ Auto-advances
4. Processing starts smoothly → ✅ No error

## Impact

### Before Fix
- ❌ Job URL input was broken
- ❌ Users saw "400: Either job_text or job_url is required"
- ❌ Could only use pasted job text, not URLs

### After Fix
- ✅ Job URL input works correctly
- ✅ Job text input still works (unchanged)
- ✅ Backend receives proper parameters
- ✅ Exa API fetches job postings from URLs
- ✅ Complete pipeline runs end-to-end

## Related Issues

This fix is part of the broader PDF processing implementation. Both features now work together:

1. **PDF Processing** (via Gemini 2.5 Flash):
   - Users can upload PDF resumes
   - Text extraction preserves formatting
   - Works with `POST /api/upload-resume`

2. **Job URL Processing** (this fix):
   - Users can provide job posting URLs
   - Backend fetches content via Exa API
   - Works with `POST /api/analyze-job`

## Deployment

**Frontend Build**: Required
```bash
cd frontend
npm run build
```

**Backend Changes**: None required (backend was already correct)

**Environment Variables**: Ensure `EXA_API_KEY` is set for URL fetching

## Conclusion

The bug was a simple but critical frontend data mapping issue where the `job_url` parameter wasn't being passed through the component hierarchy. The fix ensures that whether users provide a URL or text, the backend receives the correct parameter and can process the job posting appropriately.
