# Text Safeguard – gpt-oss-safeguard-20b Integration

**Status:** Experimental (opt-in)

---

## 1. Overview

The text safeguard is a **defense-in-depth layer** for user-provided textual inputs
(starting with job postings) that uses **gpt-oss-safeguard-20b** (via OpenRouter)
as a **policy-following classifier**.

Goals:

- Catch obviously unsafe or policy-violating job postings **before** they enter the
  main multi-agent pipeline.
- Provide clear, real-time feedback on job URLs directly on the input screen.
- Keep the final enforcement logic in our own application code while using
  gpt-oss-safeguard as a structured signal.

This spec covers the generic text safety service and its first domain
implementation for job postings.

Implementation lives in:

- `backend/src/services/text_safety_service.py`
- `backend/server.py` (`/api/job-preview`, `/api/analyze-job`, pipeline start)
- `frontend/src/services/api.ts` (`jobPreview`)
- `frontend/src/components/InputScreen.tsx` (job URL preview + UI cues)
- `frontend/src/App.tsx` (propagation to processing screen)

---

## 2. Scope

**In scope**

- Textual job postings provided as:
  - Raw job text (`job_text`), or
  - Job URLs (`job_url`) that are fetched via Exa into text.
- Early-stage safety signal used on the **input screen** via `/api/job-preview`.

**Out of scope (for this safeguard)**

- DOCX Python code execution (covered by `DOCX Safeguard` spec and sandbox).
- General resume content moderation.
- Authentication, metering, and rate limiting (covered by other specs).

---

## 3. Behavior

### 3.1 Text safety service (backend)

`backend/src/services/text_safety_service.py` exposes a generic interface:

- Domains: currently only `"job_posting"` is implemented.
- Model: `openai/gpt-oss-safeguard-20b` via OpenRouter-compatible client.

Key types:

```python
SafetyDecision = Literal["ALLOW", "BLOCK", "REVIEW"]
SafetyDomain = Literal["job_posting"]

@dataclass
class TextSafetyResult:
    decision: SafetyDecision
    reasons: list[str]
    raw_model_label: str  # "SAFE" | "UNSAFE" | "REVIEW"
    policy_name: str      # e.g. "job_posting_policy_v1"
    extra: Optional[Dict[str, Any]]  # may include model reasoning
```

Core functions (simplified):

```python
async def check_text(content: str, *, domain: SafetyDomain) -> Optional[TextSafetyResult]:
    ...

async def check_job_posting(text: str) -> Optional[TextSafetyResult]:
    return await check_text(text, domain="job_posting")
```

Behavior:

- If `TEXT_SAFEGUARD_ENABLED` is `false` or misconfigured, functions return `None`
  and the caller proceeds without a safety label.
- Otherwise, the model is called with a domain-specific policy; its JSON output is
  mapped into `TextSafetyResult`.

### 3.2 Label mapping

The safeguard model is instructed to return:

```json
{"label": "SAFE" | "UNSAFE" | "REVIEW", "reasoning": "...", "violations": ["..."]}
```

The backend maps these to internal decisions:

- `SAFE`   → `decision = "ALLOW"`
- `UNSAFE` → `decision = "BLOCK"`
- *Other* → `decision = "REVIEW"`

`reasons` is derived from `violations` and/or `reasoning` for human-readable
explanations.

---

## 4. Job posting domain & `/api/job-preview`

### 4.1 Job posting policy (system message)

The job posting domain uses a structured policy system prompt with sections:

- **INSTRUCTIONS** – task definition, required JSON schema, no raw HTML/URLs in
  reasoning, medium-depth analysis.
- **DEFINITIONS** – job posting, scam indicators, harmful or discriminatory
  content, extreme or inappropriate asks.
- **VIOLATES (UNSAFE)** – clear criteria for unsafe postings such as:
  - Obvious scams and fraud (advance-fee, crypto “investment” traps, etc.).
  - Highly sensitive personal data collection.
  - Harmful, violent, or abusive content.
  - Explicitly discriminatory hiring criteria.
- **SAFE** – standard, legitimate job postings with normal requirements.
- **REVIEW** – ambiguous content that is neither clearly SAFE nor clearly UNSAFE.
- **EXAMPLES** – SAFE / UNSAFE pairs near the boundary, focusing on realistic
  job descriptions.

The raw job text is sent as the **user** message; output is constrained to a
single JSON object via `response_format={"type": "json_object"}`.

### 4.2 `/api/job-preview` endpoint

`POST /api/job-preview` accepts:

```json
{"job_url": "https://..."}
```

Backend flow:

1. Fetch job posting text via Exa (`fetch_job_posting_text`).
2. If `TEXT_SAFEGUARD_ENABLED` is true, call `check_job_posting(job_text)`.
3. On success, return:

   ```json
   {
     "success": true,
     "job_text": "...",       // full text fetched from Exa
     "decision": "ALLOW|BLOCK|REVIEW",
     "reasons": ["..."]
   }
   ```

4. On safeguard failure (network, config, model error), log a warning and
   return `success=true` with `decision="ALLOW"` by default.

The endpoint is **advisory** only: it never blocks the URL on the backend.
Blocking behavior is implemented in the caller (currently the frontend).

---

## 5. Frontend UX – Job URL preview

### 5.1 Input screen behavior

On the input screen (`InputScreen.tsx`):

1. The user types into the job input field.
2. If the value normalizes to a job URL, the frontend:
   - Calls `apiClient.jobPreview(job_url)`.
   - Shows a live status line under the input:
     - `loading` → "Fetching job posting from link..." (muted).
     - `ok` → "Job link looks good." (green).
     - `blocked` → first safeguard reason (destructive/red).
     - `error` → "Could not fetch job posting. You can paste the text instead." (amber).
3. The fetched `job_text` is stored in local component state as
   `jobPreviewText`.

On form submit:

- If the job input is a URL and `jobPreviewText` exists, the app passes:

  ```ts
  onStart({
    resumeText,
    jobInput: normalizedJobInput,
    isUrl: true,
    jobTextFromPreview: jobPreviewText,
    ...
  })
  ```

- Otherwise, if the job input is plain text, it is sent directly as `jobText`.

### 5.2 Pipeline integration

`App.tsx` persists both the URL and (if available) the preview text:

- `jobUrl` – the original URL (for traceability and future features).
- `jobText` – either:
  - `jobTextFromPreview` when the input was a URL and preview succeeded, or
  - the raw job text when the input was not a URL.

The backend streaming pipeline then **prefers `job_text` over `job_url`**:

1. If `job_text` is present in the pipeline request, it is used directly.
2. Else, if `job_url` is present, the backend fetches the job text once via Exa.
3. If neither is present, the pipeline fails early with a user-visible error.

This ensures that, when a preview exists, the pipeline uses the exact text that
was previously inspected by the safeguard and surfaced to the user.

---

## 6. Configuration

Environment variables (backend):

- `TEXT_SAFEGUARD_ENABLED` (default: `false`)
  - When `true`, text safeguard calls are enabled where implemented
    (currently `/api/job-preview`).
  - When `false`, `check_text` / `check_job_posting` return `None` and callers
    treat the safeguard as unavailable.
- `TEXT_SAFEGUARD_MODEL` (default: `openai/gpt-oss-safeguard-20b`)
  - Allows swapping to newer safeguard variants without code changes.
- `OPENROUTER_API_KEY`
  - Required when `TEXT_SAFEGUARD_ENABLED=true`.
  - If missing or invalid, safeguard calls fail open and are logged.

The feature is **opt-in** so local development does not depend on OpenRouter.

---

## 7. Limitations & Future Work

Current limitations:

- Safeguard is **advisory-only** today:
  - `/api/job-preview` exposes the decision but does not enforce it server-side.
  - The frontend currently surfaces warnings; it does not hard-block form
    submission on `BLOCK`/`REVIEW` decisions.
- Model quality and coverage depend on gpt-oss-safeguard and the policy text; it
  is not a formal verifier.
- Only the `job_posting` domain is implemented, even though the service is
  domain-agnostic.

Potential future enhancements:

- Enforce stricter behavior in the UI, e.g. disabling pipeline start on `BLOCK`.
- Add additional domains, e.g. `github_readme` or `public_page` for other
  ingestion flows.
- Persist anonymized safety events (label + reasons, not raw text) for offline
  analysis.
- Share policy fragments with DOCX safeguard where appropriate (e.g. shared
  definitions of unsafe behaviors).
