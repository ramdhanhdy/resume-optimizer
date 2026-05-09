# Resume Optimizer — Evidence-Aware AI Pipeline

## Subtitle
A portfolio case study in turning resume tailoring from a one-off LLM rewrite into a provenance-enabled data product for job seekers.

## Executive Summary
Resume Optimizer is a full-stack AI/data product that helps job seekers tailor resumes for specific roles while preserving the evidence and execution trail behind the output. The product flow is simple — resume + job target + optional LinkedIn/GitHub context — but the backend is built as a sequential multi-agent pipeline with additive provenance records for source evidence, agent steps, model calls, generated artifacts, and validation findings. The recent provenance milestone does not make the system fully auditable yet; it creates a credible foundation for answering what evidence was used, which agents ran, what model transformed the data, what artifact was produced, and what issues the validator raised.

## Problem
Generic LLM resume tools can produce polished text quickly, but they create a trust problem for job seekers:

- They can invent metrics, responsibilities, technologies, or seniority.
- They often lose the source behind a recommendation.
- They treat generated resumes as mutable output instead of durable artifacts.
- They rarely expose which model, prompt path, or validation step shaped the final resume.

For a resume product, this is not just a UX issue. Unsupported claims can hurt the user professionally. The product needed to stay fast and usable while becoming more evidence-aware behind the scenes.

## Architecture
The application uses a React/TypeScript conversational frontend and a FastAPI backend. The user-facing flow asks for a resume, target job, and optional profile evidence such as LinkedIn or GitHub. Those inputs are sent into a fixed, sequential pipeline:

1. Optional Profile Agent builds an evidence-aware profile index from resume text, additional notes, LinkedIn, and GitHub context.
2. Job Analyzer extracts requirements, role signals, and keywords.
3. Strategy Generator decides what to emphasize for the target role.
4. Resume Builder applies the strategy while preserving authenticity.
5. Validator checks the result for strengths, recommendations, and red flags.
6. Polish prepares the final review/export-ready content.

Evidence:
- `README.md:21-35` documents the sequential agent pipeline.
- `frontend/src/conversation/script.ts:108-125` foregrounds LinkedIn/GitHub as optional profile evidence in the conversation.
- `backend/server.py` orchestrates the pipeline and writes both legacy compatibility records and new provenance records.

## Provenance and Data-Product Angle
The key technical decision was not to rewrite the entire schema. The project already had working UI/API behavior backed by compatibility tables such as `applications`, `agent_outputs`, `validation_scores`, `profiles`, and `application_reviews`. A destructive migration would have risked the product experience.

Instead, the milestone added a minimum viable provenance layer around the current system:

- `profile_snapshots` for versioned profile indexes.
- `evidence_items` for resume, additional profile text, LinkedIn, GitHub, job posting, and manual evidence records.
- `agent_steps` for append-style per-agent execution history.
- `model_invocations` for provider/model/token/cost records.
- `resume_artifacts` for generated resume or review artifacts with content hashes and current-version markers.
- `validation_findings` for queryable red flags, recommendations, strengths, and future claim checks.

This gives the project a source → transformation → artifact shape: evidence comes in, agents transform it, artifacts are produced, and validation findings can be inspected later. It is still pragmatic rather than compliance-grade. Provenance writes are intentionally non-fatal, so a failed provenance insert should not block a user from getting a resume draft.

Evidence:
- Commit `4d03aaf` added the minimum viable provenance implementation plan.
- Commit `d9df253` implemented the additive provenance schema with agent step tracking.
- Commit `636de9d` linked final review artifacts to application reviews and resolved profile evidence from Settings.
- Commit `27d0f2e` persisted validation findings for red flags, recommendations, and strengths.
- `docs/specs/database/minimum_viable_provenance_plan.md:23-33` records the PM decision to avoid a full rewrite and preserve the current frontend/API flow.
- `backend/migrations/004_minimum_viable_provenance.sql:8-180` creates the core provenance tables.

## Implementation Highlights

### Additive schema design
The migration is explicitly additive: it creates new provenance tables and compatibility columns without dropping the legacy path. This lets the product keep using existing reads while writing richer records in parallel.

Evidence:
- `backend/migrations/004_minimum_viable_provenance.sql:1-3` describes the migration as non-destructive.
- `backend/migrations/004_minimum_viable_provenance.sql:196-246` adds compatibility columns and indexes to existing tables.

### Agent and model traceability
Each supported agent completion can be written to `agent_steps`, then linked to a request-level `model_invocations` row. The records include agent number/name, input and output payloads, provider/model, token counts, estimated cost, and status.

Evidence:
- `backend/src/app/services/provenance.py:29-96` implements non-fatal `agent_steps` + `model_invocations` writes.
- `backend/tests/test_provenance_writer.py:149-217` verifies step creation, field persistence, and model-invocation linking.

### Versioned artifacts
Final review content can be stored as a `resume_artifacts` row with a content hash and `is_current` marker. Older artifacts of the same type can be marked non-current instead of disappearing.

Evidence:
- `backend/src/app/services/provenance.py:99-149` writes final review artifacts with SHA-256 content hashes.
- `backend/tests/test_provenance_helpers.py:237-260` verifies artifact creation and current-version behavior.

### Queryable validation findings
The validator’s red flags, recommendations, and strengths can be persisted as first-class rows. This makes the validation layer easier to inspect than nested summary blobs alone.

Evidence:
- `backend/src/app/services/provenance.py:163-218` writes validation findings item by item and keeps failures non-fatal.
- Commit `27d0f2e` captures this milestone in git history.

### First-class profile evidence
The conversational UI and backend support LinkedIn/GitHub profile evidence alongside resume text and job-posting input. That matters because technical job seekers often prove relevant experience through public repos and profile context, not only through a static resume.

Evidence:
- `frontend/src/conversation/script.ts:108-125` asks for LinkedIn/GitHub evidence before processing.
- `docs/specs/database/minimum_viable_provenance_plan.md:138-166` identifies GitHub/LinkedIn as profile evidence and calls out why the UI needed to foreground them.

## Current Limits
This is minimum viable provenance, not a complete audit system.

Known limits:

- Claim-level evidence linking is still partial. The system captures evidence records, but generated resume bullets are not yet consistently linked to exact evidence rows.
- Legacy tables still matter for current UI/API behavior.
- Provenance writes are non-fatal by design, so the product should be described as provenance-enabled, not guaranteed exhaustive.
- There is no finished user-facing provenance viewer, audit export, or dashboard yet.
- Prompt/version provenance is improving, but not complete across every step.
- No production-scale adoption, hiring outcomes, or accuracy-improvement metrics are claimed here.

## Future Work

- Link individual resume bullets and validation checks to specific evidence items.
- Add a provenance viewer so users can inspect evidence, agent steps, model calls, artifacts, and findings from application history.
- Generate a downloadable evidence/audit report for a tailored resume.
- Store prompt hashes, parameters, and pipeline version metadata more consistently across all agents.
- Expand evaluation harnesses for agent-by-agent and model/prompt comparisons.
- Move more read paths from compatibility summaries to provenance-backed records once verified.

## Why It Matters
Resume Optimizer demonstrates the product and engineering work required to make applied AI useful in a high-trust workflow. The project is not just a resume formatter. It combines a conversational job-search UX, sequential agent orchestration, external evidence inputs, validation, artifact history, and a growing provenance model into a practical system for faster, more accountable resume tailoring.
