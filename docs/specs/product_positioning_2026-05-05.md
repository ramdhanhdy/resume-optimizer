# Product Positioning Decision — Resume Optimizer

**Date:** 2026-05-05  
**Status:** Decision memo  
**Scope:** Narrative, product direction, and next documentation/architecture priorities after the conversational UI merge and Supabase migration.

## Decision

Resume Optimizer should be positioned as an **AI pipeline / data product for individual job seekers**.

The product is not merely a resume editor. It is a job-application pipeline that combines job-post ingestion, profile evidence, multi-agent optimization, validation, provenance, metering, and analytics-ready operational data.

## Primary user

**Individual job seekers.**

The system should remain understandable and useful to people applying for jobs, but the implementation should be narrated as a serious AI data product for portfolio/career credibility.

## Positioning statement

> Resume Optimizer is an AI job-application pipeline for individual job seekers. It turns job posts, resume drafts, and profile evidence from sources like LinkedIn and GitHub into validated, tailored application materials — with multi-agent execution, anti-fabrication checks, traceable outputs, usage metering, and analytics-ready event data.

## Strongest proof points

1. **Five-agent resume optimization pipeline**
   - Job analysis
   - Strategy generation
   - Optimized resume implementation
   - Validation/scoring
   - Final polish/export

2. **Validation / anti-fabrication system**
   - Critical differentiator versus generic AI resume tools.
   - Should be framed as trust, evidence, and quality control.

3. **Supabase/Postgres data model + event tracking**
   - Current schema already includes foundations such as applications, agent outputs, validation scores, pipeline runs, run events, recovery state, usage/metering, and analytics tables.
   - This is the core reason the project can be presented as an AI data product.

4. **Job URL ingestion via Exa**
   - Important user-facing workflow: users should not manually paste every job description if a URL can be resolved.

5. **GitHub integration for profile index building**
   - Important evidence source for technical job seekers.
   - Was better represented in the previous UI and has been neglected during the new conversational UI refactor.
   - Should be restored as a first-class part of the profile/evidence pipeline, not treated as a side field.

## Project history / current context

The project was mostly finished months ago and deployed with:

- Backend: Google Cloud
- Frontend: Vercel

The current revamp changed two major product/architecture assumptions:

1. **Infrastructure migration**
   - From Google Cloud backend persistence assumptions toward Supabase because it is cheaper and better aligned with auth/database needs.

2. **Frontend paradigm shift**
   - From the previous UI to a new conversational UI.
   - The new UI has just been merged.

Supabase is already configured, but recent schema review found that the current database model has important design issues for an auditable AI pipeline product.

Canonical schema/provenance follow-up:

- `docs/specs/database/minimum_viable_provenance_plan.md`

Older schema-review and README-revamp notes were removed during documentation pruning so this repo has one durable provenance handoff instead of several overlapping agent drafts.

## PM diagnosis

**Status:** Green/Yellow

- **Green:** Product direction is now clear: AI pipeline/data product for individual job seekers.
- **Yellow:** The current schema and docs do not yet fully support the new story. The product can work as an MVP, but the data model is not yet strong enough for provenance, versioned outputs, profile evidence, and analytics/replay.

The biggest product risk is not the UI anymore. The new UI has just merged.

The biggest risk is now **data model / evidence model mismatch**:

- `applications` mixes source data, derived output, status, metrics, and final state.
- `agent_outputs` behaves like one mutable output per agent per application, not a complete run/attempt history.
- Generated outputs and reviews are often mutable instead of versioned.
- Prompt version, model parameters, retrieved evidence, validation lineage, and cost provenance are inconsistently captured.
- GitHub-derived profile evidence is not restored as a first-class pipeline input in the new conversational flow.

## Recommended next artifact

Create a schema and product architecture plan focused on **minimum viable provenance**, not a full rewrite.

Working title:

`docs/specs/database/minimum_viable_provenance_plan.md`

The plan should answer:

1. What data must be preserved as source truth?
2. What data is derived/model-generated?
3. What artifacts need versions?
4. How should a pipeline run, agent step, prompt/model config, and validation finding be linked?
5. How should LinkedIn/GitHub/profile evidence feed the profile index?
6. What can be added around the current schema without breaking the merged UI?

## Immediate priority order

### P0 — Preserve the new UI merge

Do not destabilize the newly merged conversational UI.

No broad frontend rewrite. No package reinstall. No `node_modules` removal.

### P1 — Restore evidence/profile narrative

Make profile evidence first-class again:

- LinkedIn URL/profile data
- GitHub username/repositories/projects
- Existing resume
- Additional user-provided profile notes

This should feed a versioned `profile_index` / evidence layer.

### P2 — Add minimum viable provenance

Add or revise schema concepts around:

- Pipeline runs / attempts
- Agent steps
- Prompt/model configuration
- Artifact versions
- Validation findings
- Evidence sources

### P3 — Update README/case study narrative

Only after the data model direction is clear, update public-facing docs to tell one consistent story:

> AI job-application pipeline for individual job seekers, backed by auditable multi-agent execution and analytics-ready operational data.

## Phone/Hermes/Laptop split

### Phone-doable

- Decide product story and proof points.
- Review schema critique.
- Draft case study bullets.
- Approve priority order.

### Hermes-doable

- Create decision memos.
- Inspect docs/schema/read paths.
- Draft schema migration plan.
- Draft README/case study copy.
- Create issue list with acceptance criteria.

### Laptop-only / visual QA

- Verify conversational UI flows.
- Confirm GitHub profile integration UX.
- Test end-to-end application run in the browser.
- Verify Supabase-backed auth/session behavior.

## Definition of done for this revamp phase

This phase is done when:

1. New conversational UI remains merged and functional.
2. Supabase schema supports minimum viable provenance.
3. GitHub integration is restored as a first-class profile evidence source.
4. README and portfolio case study communicate the same story.
5. A user can understand the product as a job seeker, while a technical reviewer can recognize the pipeline/data-platform depth.
