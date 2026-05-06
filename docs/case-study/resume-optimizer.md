# Resume Optimizer Case Study

## Evidence-Aware AI Pipeline for Job Seekers

Resume Optimizer is a full-stack AI application that helps individual job seekers tailor resumes for specific roles. The project is intentionally positioned as more than a resume editor: it is an evidence-aware AI pipeline and data product that turns job postings, resume drafts, and profile evidence into validated application materials with a growing provenance trail.

The core product challenge is trust. Generic LLM resume tools can produce polished text, but they often fabricate claims, lose the evidence behind a recommendation, and provide no durable audit trail for what was generated, which model generated it, or why a validation warning was raised. Resume Optimizer addresses that risk by combining a sequential multi-agent pipeline with evidence collection, validation, versioned artifacts, and additive provenance records.

## Problem

Job seekers need tailored resumes because each role emphasizes different requirements, keywords, and proof points. However, resume tailoring is high-risk when delegated to an LLM.

Common failure modes include:

- **Fabricated claims:** A model may invent metrics, responsibilities, employers, or technologies to improve perceived fit.
- **Lost evidence:** The system may use information from a resume, LinkedIn profile, GitHub repository, or user note without preserving where that information came from.
- **Mutable outputs:** Final resumes and reviews can be overwritten by later refinements, making it difficult to reconstruct what was exported.
- **Weak auditability:** A user cannot easily answer which agents ran, which model transformed the input, what artifact was produced, or which validation findings were raised.

For a resume product, these are not just engineering issues. They directly affect user trust and professional authenticity.

## Solution

Resume Optimizer implements a deterministic, sequential multi-agent pipeline that tailors resumes while preserving compatibility with the existing user experience.

The system takes in:

- **Resume evidence:** Uploaded or saved resume text.
- **Additional profile text:** User-provided context that may not appear in the resume.
- **LinkedIn evidence:** Optional profile URL and extracted profile context.
- **GitHub evidence:** Optional GitHub username and repository metadata.
- **Job evidence:** Job posting text or a job URL resolved through the backend.

Those inputs feed a pipeline that analyzes the target role, plans resume changes, implements an optimized resume, validates the result, and produces a polished final review/export-ready artifact.

The key product shift is that the system is designed to preserve enough operational data to answer:

> What evidence was used, which agents ran, what model transformed it, what artifact was produced, and what validation findings were raised?

## System Architecture

### Conversational frontend

The frontend is a React and TypeScript conversational interface. It guides the user through the resume optimization flow, streams pipeline progress in real time, and sends structured inputs to the backend, including resume text, job information, additional profile context, LinkedIn URL, and GitHub username when available.

The frontend behavior was intentionally preserved during the provenance work. The product still presents a simple job-seeker workflow, while the backend records richer execution and evidence metadata behind the scenes.

### Backend pipeline

The backend is a FastAPI service that orchestrates a fixed multi-agent pipeline:

1. **Profile Agent, optional Step 0:** Builds an evidence-aware profile index from resume text, additional user text, LinkedIn context, and GitHub repository data.
2. **Agent 1 — Job Analyzer:** Extracts requirements, role signals, and keywords from the job posting.
3. **Agent 2 — Strategy Generator:** Creates a targeted optimization strategy grounded in the job analysis and candidate evidence.
4. **Agent 3 — Resume Builder:** Applies the strategy to produce an optimized resume draft while preserving authenticity.
5. **Agent 4 — Validator:** Scores the optimized resume, identifies red flags, strengths, and recommendations.
6. **Agent 5 — Polish:** Applies final refinements and prepares the final user-facing review/export content.

The backend also supports streaming progress through Server-Sent Events, event replay/recovery, model provider routing, per-agent model configuration, cost/token metadata, and database-backed application history.

### Data and provenance layer

The project originally centered on compatibility tables such as `applications`, `agent_outputs`, `validation_scores`, `profiles`, and `application_reviews`. Those tables remain important because existing UI/API behavior depends on them.

Recent provenance work added a minimum viable audit layer around the current schema instead of replacing it:

- **`profile_snapshots`:** Versioned profile indexes generated from resume, additional text, LinkedIn, and GitHub evidence.
- **`evidence_items`:** First-class source evidence records for resume uploads, additional profile text, LinkedIn profiles, GitHub repositories, job postings, and manual notes.
- **`agent_steps`:** Immutable per-agent execution records that preserve agent number, agent name, status, inputs, outputs, model metadata, token counts, and cost.
- **`model_invocations`:** Request-level model usage records linked to an application and, when available, an agent step.
- **`resume_artifacts`:** Immutable generated or edited resume/review artifacts with content hashes and current-version markers.
- **`validation_findings`:** Queryable validation results for red flags, recommendations, strengths, and future claim checks.

This design keeps the application usable while making the pipeline more auditable over time.

## Key Technical Decisions

### Preserve existing UI and API behavior

The safest path was not a broad frontend rewrite. The conversational UI had recently been merged, and the existing API response shapes were already wired into the product experience. The implementation therefore keeps compatibility tables and endpoints intact while adding provenance writes in parallel.

`agent_outputs`, `validation_scores`, `applications.optimized_resume_text`, and `application_reviews` continue to support current reads. New provenance tables provide durable history and audit records without forcing a risky immediate read-path migration.

### Add minimum viable provenance instead of a full schema rewrite

The schema review found that `applications` was overloaded and that generated outputs were often mutable or upserted. A full normalized schema rewrite would have been technically cleaner but too disruptive for the current product phase.

The chosen approach was additive:

- Keep `applications` as the user-visible job/application container.
- Keep legacy tables as compatibility summaries.
- Add immutable or append-friendly records for evidence, agent execution, model calls, artifacts, and validation findings.
- Back-fill application links for evidence captured before the application row exists.

This creates a credible audit foundation while reducing migration risk.

### Keep legacy compatibility tables while adding auditable records

The system now writes richer records where supported, but provenance writes are designed to be non-fatal. If a provenance insert fails, the pipeline can still complete and preserve the user-facing workflow.

That is a deliberate reliability tradeoff: provenance improves auditability, but it should not break resume generation for a job seeker.

### Treat GitHub and LinkedIn as first-class profile evidence

For technical job seekers, GitHub repositories can provide concrete evidence of projects, technologies, and implementation experience. LinkedIn can provide additional role and profile context. The pipeline treats these sources as profile evidence rather than incidental notes, and records them as `evidence_items` where possible.

The implementation is careful not to claim perfect claim-to-source citation yet. Today, these sources are captured as structured evidence records and used in profile construction; stronger claim-level linking remains future work.

## Implementation Highlights

### Immutable agent execution with `agent_steps`

The previous `agent_outputs` model behaved like one summary row per application and agent number. That is useful for the UI, but weak for audit history because reruns or retries can overwrite prior state.

`agent_steps` adds append-style execution records. Each completed agent can now record:

- Agent number and name.
- Application and job/run context.
- Input and output payloads.
- Model provider and model name.
- Token usage and estimated cost.
- Execution status.

This makes agent execution history queryable without breaking the old summary table.

### Request-level model records with `model_invocations`

`model_invocations` records provider, model, token counts, estimated cost, status, and links back to the application and agent step where available. This makes model usage easier to reconcile than relying only on summary fields embedded in agent outputs.

### Versioned outputs with `resume_artifacts`

Final reviews and export-ready resume content should not exist only as mutable current-state fields. `resume_artifacts` stores generated artifacts with a content hash and an `is_current` marker. When a new final review artifact is created, previous artifacts of the same type can be marked non-current while remaining available historically.

The current frontend can still load the canonical review through the existing review endpoint, while the database gains artifact lineage.

### Queryable validation with `validation_findings`

The validator already produces red flags, recommendations, strengths, and scores. `validation_findings` makes those findings first-class records rather than only nested arrays in a score row.

Current implementation focuses on persisted red flags, recommendations, and strengths. More granular claim checks and evidence-linked validations are a natural extension, but are not overclaimed as complete today.

### First-class profile evidence

The pipeline captures evidence records for:

- Uploaded resume text.
- Additional profile text.
- LinkedIn profile URL/context.
- GitHub repository metadata.

Because Step 0 profile construction can happen before the application row exists, the backend can create evidence/profile snapshot records first and then back-fill the `application_id` after the application is created.

## Outcome

The result is a stronger technical foundation for an evidence-aware resume pipeline.

The app can now more credibly answer:

- **What evidence was used?** Resume text, additional profile context, LinkedIn input, GitHub repositories, and job posting evidence can be represented as evidence records.
- **Which agents ran?** Agent completions can be represented as immutable `agent_steps` instead of only mutable summaries.
- **What model transformed the data?** `model_invocations` and agent step metadata can record provider, model, tokens, cost, and status.
- **What artifact was produced?** `resume_artifacts` can preserve generated review/resume versions with content hashes.
- **What validation findings were raised?** `validation_findings` can store red flags, recommendations, and strengths as queryable records.

The most important outcome is not simply a better resume editor. It is a job-application pipeline with the beginnings of source/derived/output separation, model execution traceability, and artifact history.

## Technical Honesty and Current Limits

This is minimum viable provenance, not a complete audit system.

Current limits include:

- **Claim-level evidence linking is partial:** Evidence is captured, but individual resume claims are not yet consistently linked to exact evidence rows.
- **Legacy tables still matter:** Current UI/API behavior still depends on compatibility tables such as `applications`, `agent_outputs`, and `application_reviews`.
- **Prompt/version provenance can improve:** The schema supports prompt names and hashes, but complete prompt/version capture is an area for continued hardening.
- **Analytics are foundational:** Model and agent records improve cost/query potential, but full reporting dashboards and reconciliation workflows are future work.

These constraints are intentional for the current phase. The project prioritizes a stable user workflow while adding auditability incrementally.

## Future Work

- **Better claim-to-evidence linking:** Connect generated resume bullets and validation checks to specific evidence items.
- **Provenance viewer UI:** Let users inspect evidence, agent steps, model calls, artifacts, and validation findings from the application history.
- **Export/audit report:** Generate a downloadable report showing evidence sources, model transformations, final artifact hashes, and validation findings.
- **Stronger evaluation harness:** Expand the existing evaluation direction into systematic agent-by-agent and arena-style comparisons for model and prompt variants.
- **Prompt and pipeline versioning:** Store prompt hashes, parameter sets, and pipeline code/config versions more consistently across every agent step.

## Why This Project Matters

Resume Optimizer demonstrates how an LLM application can move beyond a single prompt-and-response workflow. It combines product UX, multi-agent orchestration, evidence-aware profile construction, validation, streaming infrastructure, and an additive provenance schema into a practical tool for job seekers.

The portfolio value is the architecture: a user-friendly resume tailoring app backed by data-product thinking about evidence, transformations, artifacts, and auditability.
