# PDF Processing with Gemini 2.5 Flash - Implementation Summary

## Overview

Added comprehensive PDF processing functionality using **Gemini 2.5 Flash** for high-quality document understanding. This enables the application to process PDF resumes and job postings with native vision capabilities that preserve formatting, tables, and structure.

## Key Features

### 1. Gemini 2.5 Flash PDF Extraction
- **Native document understanding**: Preserves layout, tables, images, and formatting
- **Two processing modes**:
  - **Inline** (files < 20MB): Direct byte processing using `Part.from_bytes()`
  - **File API** (files > 20MB): Upload via Gemini File API for large documents
- **Structured extraction**: Uses custom prompts to maintain document hierarchy

### 2. Fallback Extraction
- **pypdf library**: Provides basic text extraction when Gemini is unavailable
- **Automatic fallback**: Switches to pypdf if Gemini API key is missing or extraction fails
- **Multi-format support**: Also handles DOCX, TXT, and image files

### 3. Server API Integration
- **POST /api/upload-resume**: Fixed and fully functional
- **Async processing**: Uses asyncio for efficient file handling
- **Response metadata**: Returns extraction method used (gemini-2.5-flash or direct)

### 4. UI Integration
- **File uploads enabled**: Removed disabled flags from Step 1 and Step 2
- **Real-time extraction**: Shows spinner during PDF processing
- **User feedback**: Displays notification when Gemini processing is used
- **Auto-run support**: Works seamlessly with pipeline automation

## Files Created

### Core Modules

#### `backend/src/utils/pdf_extractor.py`
New dedicated module for PDF text extraction:

```python
async def extract_text_from_pdf_gemini(
    file_path: str,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> str:
    """Extract text using Gemini 2.5 Flash document understanding."""

def extract_text_from_pdf_fallback(file_path: str) -> str:
    """Fallback extraction using pypdf library."""
```

**Key functions**:
- `extract_text_from_pdf_gemini()`: Main Gemini extraction with File API support
- `_extract_via_file_api()`: For large PDFs (> 20MB)
- `_extract_inline()`: For smaller PDFs (< 20MB)
- `extract_text_from_pdf_fallback()`: pypdf fallback extraction

#### `backend/test_pdf_extraction.py`
Comprehensive test script:
- Tests PDF extraction module functionality
- Tests file handler integration
- Tests server API endpoint
- Provides clear success/failure feedback

## Files Modified

### 1. `backend/src/utils/file_handler.py`
**Major updates**:
- Modified `save_uploaded_file()`: Now supports both Streamlit and standard file objects
- Added `extract_text_from_file()`: Unified extraction for all file types
- Added `is_pdf()`: Helper to detect PDF files

**Extraction support**:
- PDF: Gemini 2.5 Flash (primary) or pypdf (fallback)
- DOCX: python-docx extraction
- TXT/MD: Direct UTF-8 reading
- Images: Reference notation for multimodal processing

### 2. `backend/server.py`
**POST /api/upload-resume endpoint**:
```python
@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Handle resume file upload with PDF extraction via Gemini."""
    file_path = save_uploaded_file(file.file, file.filename)
    resume_text = await extract_text_from_file(file_path)
    cleanup_temp_file(file_path)
    
    return {
        "success": True,
        "filename": file.filename,
        "text": resume_text,
        "length": len(resume_text),
        "extraction_method": "gemini-2.5-flash" if is_pdf else "direct",
    }
```

### 3. UI Views

#### `backend/src/app/views/step1_job_analysis.py`
- **Enabled file uploads**: Removed `disabled=True`
- **Added text extraction**: Calls `extract_text_from_file()` on upload
- **User feedback**: Shows Gemini processing notification

#### `backend/src/app/views/step2_resume_optimization.py`
- **Enabled file uploads**: Removed `disabled=True`
- **Added text extraction**: Processes PDFs before sending to agents
- **User feedback**: Shows processing status

#### `backend/src/app/pipeline.py`
- **Auto-run support**: Extracts text from uploaded files in pipeline
- **Async handling**: Proper asyncio integration

### 4. `backend/src/utils/__init__.py`
**Added exports**:
```python
from .file_handler import extract_text_from_file, is_pdf
```

## Technical Architecture

### PDF Processing Flow

```
User Upload (PDF)
    ↓
save_uploaded_file() → temp file
    ↓
extract_text_from_file()
    ↓
  ├─ PDF? → Check file size
  │   ├─ < 20MB → extract_text_from_pdf_gemini (inline)
  │   └─ > 20MB → extract_text_from_pdf_gemini (File API)
  ├─ DOCX? → python-docx extraction
  ├─ TXT? → direct read
  └─ Image? → reference notation
    ↓
Extracted Text (string)
    ↓
Pass to LLM Agents (all agents receive text only)
```

### Gemini File Processing

**For files < 20MB (inline)**:
```python
file_bytes = Path(file_path).read_bytes()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=file_bytes,
            mime_type="application/pdf",
        ),
        prompt,
    ],
)
```

**For files > 20MB (File API)**:
```python
uploaded_file = client.files.upload(
    file=file_path,
    config=dict(mime_type="application/pdf"),
)
# Wait for processing
while uploaded_file.state == "PROCESSING":
    time.sleep(2)
    uploaded_file = client.files.get(name=uploaded_file.name)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[uploaded_file, prompt],
)
```

## Dependencies

### Newly Required
- **google-genai >= 1.0.0**: Gemini API client (already in requirements)
- **pypdf >= 6.1.0**: Fallback PDF extraction

Both are now installed and functional.

## Usage

### From UI (Streamlit)

**Step 1: Job Analysis**
1. Select "Upload File" input method
2. Upload PDF job posting
3. App automatically extracts text using Gemini
4. Proceed with analysis

**Step 2: Resume Optimization**
1. Select "Upload File" input method
2. Upload PDF resume
3. App extracts text with Gemini 2.5 Flash
4. Continue with optimization

### From API

```python
import httpx

with open("resume.pdf", "rb") as f:
    files = {"file": ("resume.pdf", f, "application/pdf")}
    response = httpx.post(
        "http://localhost:8000/api/upload-resume",
        files=files,
    )

data = response.json()
print(data["text"])  # Extracted resume text
print(data["extraction_method"])  # "gemini-2.5-flash"
```

### Programmatic

```python
import asyncio
from src.utils import extract_text_from_file

async def process_pdf():
    text = await extract_text_from_file("resume.pdf")
    print(text)

asyncio.run(process_pdf())
```

## Configuration

### Required Environment Variables

```bash
# In backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get API Key**: https://aistudio.google.com/apikey

### Fallback Behavior

If `GEMINI_API_KEY` is not set:
- PDF extraction automatically falls back to pypdf
- Basic text extraction without layout preservation
- No API costs incurred

## Testing

### Run Test Script

```bash
cd backend
python test_pdf_extraction.py
```

**Tests include**:
1. PDF extraction module imports
2. File handler integration
3. Server API endpoint (if running)
4. Both Gemini and fallback methods

### Manual Testing

**Test file uploads in UI**:
1. Start Streamlit app: `streamlit run backend/src/app/main.py`
2. Navigate to Step 1 or Step 2
3. Upload a PDF file
4. Verify extraction notification appears
5. Check extracted text quality

**Test API endpoint**:
```bash
# Start server
python backend/server.py

# In another terminal
curl -X POST http://localhost:8000/api/upload-resume \
  -F "file=@sample_resume.pdf"
```

## Benefits

### For Users
- **Upload PDF resumes directly**: No manual copy-paste needed
- **High-quality extraction**: Tables, formatting, and structure preserved
- **Works with job postings**: Process PDF job descriptions
- **Reliable fallback**: Works even without Gemini API key

### For Developers
- **Single extraction point**: PDF processed once at upload
- **Provider agnostic**: All agents receive plain text
- **Async support**: Non-blocking file processing
- **Extensible**: Easy to add support for more file types

## Performance

### Processing Times (estimated)

| File Size | Method | Time |
|-----------|--------|------|
| < 1 MB | Gemini inline | 2-5 seconds |
| 1-20 MB | Gemini inline | 5-15 seconds |
| > 20 MB | Gemini File API | 15-60 seconds |
| Any size | pypdf fallback | < 1 second |

### Cost

**Gemini 2.5 Flash pricing**:
- Input: $0.30 per million tokens
- Output: $2.50 per million tokens

**Estimated cost per PDF**:
- 1-page resume: ~$0.001-0.003
- 5-page resume: ~$0.005-0.015
- 10-page job posting: ~$0.010-0.030

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**: Add key to `backend/.env`:
```bash
GEMINI_API_KEY=your_key_here
```

### Issue: "google.genai module not found"
**Solution**: Install google-genai:
```bash
pip install google-genai
```

### Issue: "pypdf module not found"
**Solution**: Install pypdf:
```bash
pip install pypdf
```

### Issue: PDF extraction fails
**Workaround**: 
1. System automatically falls back to pypdf
2. Or manually paste text instead of uploading

### Issue: Large PDF timeout
**Solution**: 
- Files > 20MB use File API with automatic retry
- Wait up to 60 seconds for processing
- Consider splitting very large PDFs

## Future Enhancements

Potential improvements:
1. **Progress indicators**: Real-time upload/processing progress
2. **Preview extracted text**: Show extraction before processing
3. **Batch processing**: Upload multiple files at once
4. **OCR support**: Handle scanned PDFs with poor text layer
5. **Format detection**: Auto-detect optimal extraction method
6. **Caching**: Cache extractions to avoid reprocessing

## Comparison with Previous State

### Before
- ❌ File uploads disabled in UI
- ❌ POST /api/upload-resume broken (missing function)
- ❌ Files shown as placeholders: `[File: resume.pdf]`
- ❌ No actual PDF text extraction
- ❌ Agents couldn't process file contents

### After
- ✅ File uploads enabled and working
- ✅ POST /api/upload-resume fully functional
- ✅ Native PDF understanding with Gemini 2.5 Flash
- ✅ Automatic text extraction on upload
- ✅ All agents receive extracted text
- ✅ Fallback support with pypdf
- ✅ Multi-format support (PDF, DOCX, TXT, images)

## Conclusion

PDF processing is now fully integrated using Gemini 2.5 Flash's advanced document understanding capabilities. The implementation provides high-quality extraction with automatic fallback, seamless UI integration, and a working API endpoint. All changes maintain backward compatibility while significantly enhancing the application's file handling capabilities.
