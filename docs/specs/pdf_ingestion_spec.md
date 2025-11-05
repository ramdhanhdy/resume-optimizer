# PDF Ingestion & Extraction Specification

## 1. Purpose
Provide deterministic ingestion of PDF resumes and job postings that preserves document structure, leverages Gemini 2.5 Flash for high-fidelity parsing, and guarantees graceful degradation when advanced extraction is unavailable.

## 2. Objectives
- Support PDF upload in all resume/job posting entry points.
- Deliver uniform plain-text output to downstream agents.
- Expose extraction metadata for observability and user feedback.

## 3. Scope
- Covers backend utilities (`pdf_extractor.py`, `file_handler.py`), FastAPI upload endpoint, and UI hooks that trigger extraction.
- Includes fallback extraction and post-processing responsibilities.
- Excludes non-PDF formats beyond ensuring they continue to route through `extract_text_from_file`.

## 4. Stakeholders
- **AI Engineering** – consumes extracted text in agent pipeline.
- **Frontend** – renders upload UX and communicates extraction status.
- **Runtime Operations** – monitors extraction performance and error rates.

## 5. Functional Requirements
1. **Upload Handling**
   - `POST /api/upload-resume` accepts PDF, DOCX, TXT, and image files.
   - Uploaded file is streamed to disk via `save_uploaded_file`.
   - Response includes `text`, `length`, and `extraction_method`.

2. **Primary Extraction (Gemini 2.5 Flash)**
   - Default model `gemini-2.5-flash`.
   - Inline mode for files ≤20 MB using `Part.from_bytes`.
   - File API mode for files >20 MB with managed cleanup.
   - Prompt must preserve structural cues (headings, tables) in output.

3. **Fallback Extraction**
   - Invoke `pypdf` when Gemini API key missing or Gemini call raises.
   - Fallback must return best-effort plain text without raising.

4. **Async Execution**
   - Extraction functions return `await`-able coroutines.
   - Long-running tasks should avoid blocking event loop; use `asyncio.to_thread` for CPU-bound work if necessary.

5. **UI Integration**
   - Step 1 (Job Analysis) and Step 2 (Resume Optimization) screens must allow PDF uploads.
   - UI displays progress indicator while extraction runs and surfaces whether Gemini or fallback processed the file.

6. **Pipeline Automation**
   - Auto-run flows ingest uploaded files by invoking `extract_text_from_file` before agent execution.
   - Pipeline stores extracted text so subsequent steps avoid repeated extraction.

## 6. Non-Functional Requirements
- **Performance**: Inline Gemini extraction ≤15 s for ≤20 MB PDF; fallback extraction ≤1 s for ≤10 MB PDF.
- **Resilience**: Fallback path guarantees text output even without Gemini credentials.
- **Cost**: Track Gemini usage; budget ≤$0.05 per typical session.
- **Security**: Never persist uploaded files beyond extraction; redact API responses from logs.

## 7. Architecture
```
UploadFile -> save_uploaded_file -> extract_text_from_file
      |                                 |
      |                                 +--> Gemini extractor (inline or file API)
      |                                 |
      |                                 +--> pypdf fallback
      |
  cleanup_temp_file
      |
  Response { text, length, extraction_method }
```

## 8. Module Contracts
- `pdf_extractor.py`
  - `async extract_text_from_pdf_gemini(path, api_key, model) -> str`
  - `async _extract_inline(path, client) -> str`
  - `async _extract_via_file_api(path, client) -> str`
  - `def extract_text_from_pdf_fallback(path) -> str`
- `file_handler.py`
  - `async extract_text_from_file(path) -> str`
  - `def is_pdf(path) -> bool`
  - Must call Gemini extractor when `is_pdf` and API key present; fallback otherwise.

## 9. Observability & Error Handling
- Log extraction attempts with `extraction_method` and duration.
- On Gemini failure, log warning with redacted error and switch to fallback.
- Propagate HTTP 500 only when both primary and fallback fail.
- Emit metrics: `pdf_extraction_latency_ms`, `pdf_extraction_fallback_count`.

## 10. Testing Strategy
- Unit tests for:
  - Gemini inline and File API stubs.
  - pypdf fallback.
  - File detection helpers.
- Integration tests covering:
  - `POST /api/upload-resume` with sample PDFs.
  - UI upload flow (manual or Playwright placeholder).
- Regression script `backend/test_pdf_extraction.py` must pass in CI.

## 11. Deployment & Rollout
- Feature ships behind environment variable `GEMINI_API_KEY`; fallback ensures safe rollout.
- Document configuration in `backend/.env.example`.
- After deploy, monitor latency and fallback metrics for 72 hours.

## 12. Future Enhancements
- Progress callbacks for long extractions.
- OCR layer for scanned PDFs.
- Batch uploads and caching of processed documents.
- Automatic prompt tuning based on extraction quality telemetry.

