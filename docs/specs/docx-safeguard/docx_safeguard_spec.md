# DOCX Safeguard – gpt-oss-safeguard-20b Integration

**Status:** Experimental (opt-in)  
**Last Updated:** 2025-11-14

---

## 1. Overview

The DOCX safeguard is a **defense-in-depth layer** for the DOCX export path that
uses OpenAI’s **gpt-oss-safeguard-20b** (via OpenRouter) to classify
LLM-generated Python DOCX templates **before** they are executed in the backend
sandbox.

Goal:

- Reduce risk of **remote code execution (RCE)** and **sandbox escape** via
  prompt-injected Python templates from the Polish agent.
- Keep the primary enforcement in our own sandbox (`execute_docx_code`) while
  using gpt-oss-safeguard as a **policy-following safety classifier**.

This spec documents the high-level behavior, configuration, and integration
points. Implementation lives in:

- `backend/src/services/docx_safety_service.py`
- `backend/src/utils/execute_docx_code.py`
- `backend/server.py` (DOCX export endpoint)

---

## 2. Threat Model & Scope

**In scope**

- LLM-generated Python code emitted by the Polish agent and stored as
  `optimized_resume_text` when it is actually Python (not HTML).
- The `/api/export/{application_id}?format=docx` endpoint, which:
  - Detects HTML vs Python.
  - Converts HTML with `html_to_docx`.
  - Executes Python with `execute_docx_code`.

**Out of scope (for this safeguard)**

- HTML-based DOCX export (handled by `html_to_docx`).
- General content moderation of resumes/job postings.
- Authentication / authorization / metering (covered by other specs).

The safeguard assumes that the primary RCE risk is **LLM-generated Python** that
attempts to access the OS, filesystem, environment, or network from within the
DOCX execution environment.

---

## 3. Behavior

### 3.1 High-level flow

1. Frontend calls `GET /api/export/{application_id}?format=docx`.
2. Backend loads `application` and `final_resume` from the database.
3. Backend detects whether `final_resume` is **HTML** or **Python**:
   - HTML → convert with `html_to_docx` (no safeguard call).
   - Python → run DOCX safeguard **before** `execute_docx_code`.
4. If safeguard is **enabled** and the model returns a label:
   - `SAFE` → proceed to `execute_docx_code` (AST sandbox still applies).
   - `UNSAFE` or `REVIEW` → **block execution** and return HTTP 400.
5. If safeguard is **disabled** or the model call fails → log a warning and
   fall back to the sandbox only.

### 3.2 Labels and decisions

The safeguard model returns a JSON object with:

```json
{
  "label": "SAFE" | "UNSAFE" | "REVIEW",
  "reasoning": "<short explanation>",
  "violations": ["<policy reasons>"]
}
```

Decision rule in the export endpoint:

- **SAFE** → allow execution (subject to AST validation and sandbox checks).
- **UNSAFE** → block execution, return `400` with a generic error message.
- **REVIEW** → treated the same as `UNSAFE` (conservative for code execution).

If the safeguard call itself fails (missing key, network error, etc.), the
export path continues without the safeguard and relies purely on
`execute_docx_code`.

---

## 4. Policy & Prompting

The DOCX safeguard uses a **policy-as-system, content-as-user** pattern
consistent with the official gpt-oss-safeguard guide.

### 4.1 Policy structure

The system message (`_DOCX_CODE_POLICY`) is a structured policy with sections:

- **INSTRUCTIONS** – what the model must do; required JSON schema; no raw code
  in reasoning; medium reasoning depth.
- **DEFINITIONS** – DOCX template code, sandbox, OS-level operations, network
  operations.
- **VIOLATES (UNSAFE)** – specific unsafe behaviors:
  - OS / filesystem / environment (e.g. `os`, `subprocess`, `pathlib`, `open`,
    env vars).
  - Network / IPC (HTTP, sockets, DB, queues).
  - Sandbox escape (`eval`, `exec`, `__builtins__` tampering, reflection).
  - Sensitive paths and secrets.
  - Resource abuse (infinite loops, deep recursion, obvious DoS patterns).
- **SAFE** – narrow definition of acceptable behavior (only docx + basic
  computation and formatting).
- **REVIEW** – rarely used; only when SAFE vs UNSAFE is genuinely unclear.
- **EXAMPLES** – labeled examples (SAFE and UNSAFE) near the decision boundary.

### 4.2 Request format

The OpenRouter/OpenAI client is used like this:

- **System message:** DOCX policy
- **User message:** raw Python code snippet
- `response_format={"type": "json_object"}` to enforce JSON output.

The model’s `reasoning` occurs in its internal reasoning channel; only the
final JSON object is returned to the backend.

---

## 5. Configuration

Environment variables (backend):

- `DOCX_SAFEGUARD_ENABLED` (default: `false`)
  - When `true`, DOCX Python templates are pre-checked with the safeguard.
  - When `false`, the system behaves as if the safeguard does not exist.
- `DOCX_SAFEGUARD_MODEL` (default: `openai/gpt-oss-safeguard-20b`)
  - Allows swapping models (e.g., 120B version) without code changes.
- `OPENROUTER_API_KEY`
  - Required when `DOCX_SAFEGUARD_ENABLED=true`.
  - If missing, safeguard calls fail and the export path logs a warning and
    falls back to sandbox-only behavior.

The safeguard is intentionally **opt-in** so local development does not depend
on OpenRouter being configured.

---

## 6. Sandbox Hardening

The safeguard is a **secondary** defense. The primary defense is our Python
sandbox in `execute_docx_code`:

- `ALLOWED_MODULES` **no longer includes** `os`, `os.path`, or `pathlib`.
- `_safe_import` only permits modules explicitly in `ALLOWED_MODULES`.
- `_validate_ast` rejects:
  - Imports of disallowed modules.
  - Use of banned names/attributes (`eval`, `exec`, `__builtins__`, `open`,
    etc.).
- Execution runs with a restricted `SAFE_BUILTINS` and `SAFE_GLOBALS` dict.

Even if the safeguard mislabels code as SAFE, the sandbox must still block
obvious escape attempts.

---

## 7. Limitations & Future Work

Known limitations:

- The safeguard runs synchronously per export and adds latency + cost when
  enabled.
- Reasoning quality and recall are limited by the gpt-oss-safeguard model and
  the policy text; it is not a formal verifier.
- We currently treat `REVIEW` as `UNSAFE`, which may block some benign but
  complex templates.

Possible future improvements:

- Add more **borderline examples** to the policy (complex but safe templates).
- Log the safeguard result (label + violations, not the code) into a
  `safety_events` table for offline review.
- Consider a separate, unprivileged worker process/container for DOCX
  generation, further isolating any remaining risk.
- Expand safeguard usage to other high-risk flows if needed (e.g., free-form
  code or tool invocation in future features).
