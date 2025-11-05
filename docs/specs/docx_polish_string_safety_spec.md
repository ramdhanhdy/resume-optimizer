# DOCX Polish Agent String-Safety Specification

## 1. Purpose
Ensure the Polish agent (Agent 5) consistently generates valid Python/Docx code by enforcing deterministic string-escaping rules, rich diagnostics, and recovery workflows when syntax errors occur during DOCX export.

## 2. Scope
- Applies to resume export flows that execute model-generated Python against `python-docx`.
- Covers prompt contracts, runtime validation, error surfacing, and operator tooling for remediation.
- Excludes broader export formatting requirements (handled by `docx_generator.py`) and non-DOCX export types.

## 3. Stakeholders
- **Product Engineering** – owns agent prompts and pipeline execution.
- **Runtime Reliability** – monitors export failures and coordinates mitigations.
- **Support/Ops** – replays failed exports for affected users.

## 4. Functional Requirements
1. **Prompt Contract**
   - The Polish agent prompt must include explicit escaping guidance:
     - Prefer single quotes when strings contain double quotes.
     - Prefer double quotes when strings contain single quotes.
     - Require triple-quoted strings or escaped characters when both quote types appear.
     - Reject unterminated strings and emphasize validation prior to emission.
   - Prompt lives in `prompts/agent5_polish_docx.md`; changes require review by Runtime Reliability.

2. **Runtime Validation**
   - `execute_docx_code.py` must parse generated code before execution.
   - On syntax failure, surface file name and exact line (±3 lines of context) with `>>>` indicator.
   - Abort export if parsing fails; do not attempt partial document writes.

3. **Data Integrity**
   - Store the generated code alongside failure metadata to enable later analysis.
   - Preserve original resume payload; no mutation occurs when export fails.

4. **Recovery Workflow**
   - Provide `fix_appXX_polish.py` scripts (or generic equivalent) that:
     1. Fetch application snapshot.
     2. Re-run the Polish agent with updated prompt.
     3. Validate code via runtime validator.
     4. Persist new output on success.
   - Offer read-only inspection utility (`inspect_appXX.py`) to view failing code safely.

## 5. Non-Functional Requirements
- **Reliability**: Syntax errors must be <0.5% of DOCX exports post-change.
- **Observability**: Emit structured logs with `error_category="DOCX_SYNTAX"`.
- **Security/Privacy**: Do not log full resume text; redact user-identifying data when exporting diagnostics.

## 6. Sequence Flow
1. Pipeline triggers Polish agent with optimization + validation context.
2. Agent returns Python code; runtime parser validates syntax.
3. If valid: proceed to document generation.
4. If invalid: emit structured error, skip generation, offer remediation tooling.

## 7. Implementation Guidelines
- Keep validation in `src/utils/execute_docx_code.py`; unit tests must cover:
  - Unterminated strings.
  - Mixed-quote strings.
  - Triple-quoted literals.
- Maintain prompt examples demonstrating correct escaping.
- Future enhancements (versioned prompts, automatic escaping) require RFC before adoption.

## 8. Testing & Validation
- Automated: add pytest coverage for validator edge cases and prompt regression tests.
- Manual: run `python fix_app65_polish.py` after prompt updates, then `curl /api/export/{id}?format=docx`.
- Regression: export a matrix of resumes containing apostrophes, quotes, multi-line bullets.

## 9. Rollout & Operations
- Roll out prompt updates behind feature flag if available; otherwise deploy during low traffic window.
- After deployment, monitor export logs for 48 hours; verify absence of `unterminated string literal`.
- Document runbook steps in on-call handbook referencing this spec.

## 10. Open Questions
- Should the runtime automatically re-escape strings before execution?
- Do we persist failing code samples for analytics, and if so, where?
- Is a generic replay tool preferable to per-application fix scripts?

