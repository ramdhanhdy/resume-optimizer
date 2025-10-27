# Agent Design and Patterns

## Overview

A deterministic multi-agent pipeline processes resumes end-to-end. It runs specialized agents in a fixed order, with optional human input and an optional GitHub curation branch. Agents are implemented in `backend/src/agents/*` and exposed via service wrappers in `backend/src/app/services/agents.py`.

## Agents and Responsibilities

- **Profile Agent (Step 0, optional)**
  - Purpose: Build an evidence-backed profile index from LinkedIn/profile text (and optionally GitHub repos) for later context.
  - Code: `src/agents/profile_agent.py`
  - Prompt: `prompts/profile_agent.md`
  - Output: `profile_index` text used to enrich later agents.

- **Agent 1 — Job Analyzer**
  - Purpose: Analyze job posting and extract requirements, role signals, and keywords.
  - Code: `src/agents/job_analyzer.py`
  - Prompt: `prompts/agent1_job_analyzer.md`

- **Agent 2 — Resume Optimizer**
  - Purpose: Generate a targeted optimization plan using Job Analyzer output (and optional profile index).
  - Code: `src/agents/resume_optimizer.py`
  - Prompt: `prompts/agent2_resume_optimizer.md`

- **Agent 3 — Optimizer Implementer**
  - Purpose: Apply the optimization plan to the candidate’s resume.
  - Code: `src/agents/optimizer_implementer.py`
  - Prompt: `prompts/agent3_optimizer_implementer.md`

- **GitHub Projects Agent (optional branch)**
  - Purpose: Curate relevant GitHub projects and produce evidence-backed bullets/HTML.
  - Code: `src/agents/github_projects_agent.py`
  - Prompt: inline within file

- **Agent 4 — Validator**
  - Purpose: Evaluate optimized resume vs job posting; produce scores, red flags, and recommendations.
  - Code: `src/agents/validator.py`
  - Prompt: `prompts/agent3_validator.md`

- **Agent 5 — Polish**
  - Purpose: Apply validator recommendations and produce final HTML or DOCX-ready output.
  - Code: `src/agents/polish.py`
  - Prompts: `prompts/agent5_polish.md` (HTML) or `prompts/agent5_polish_docx.md` (DOCX)

- **Renderer (zero-cost utility)**
  - Purpose: Render HTML/DOCX to PDF/DOCX without additional model calls.
  - Code: `src/agents/renderer.py`

## Orchestration

- **Deterministic sequence (sequential pipeline):** 1 → 2 → (optional GitHub) → 3 → 4 → 5.
- **Service entrypoints:** `src/app/services/agents.py` provides `stream_*` functions for each agent, used by API endpoints and UI flows.
- **Human-in-the-loop:** Execution pauses when required inputs are missing (e.g., resume upload or job text), allowing user review and gating before proceeding.
- **Context engineering:** Each agent composes inputs from prior steps plus optional `profile_index` into structured prompts to preserve evidence and reduce hallucination.
- **Provider routing:** Multi-provider facade (`MultiProviderClient`) selects an API client per model and supports provider-specific options (e.g., `thinking_budget` for LongCat).

## Pattern Mapping (Google Cloud)

- **Multi-agent: Sequential pattern** — Fixed, linear order with outputs feeding the next step.
- **Review and critique (generator–critic, non-iterative)** — Validator reviews generated output; results inform polish without a revision loop.
- **Human-in-the-loop** — User checkpoints for inputs and approvals.
- **Custom logic pattern (lightweight)** — Optional GitHub curation branch and per-agent model selection handled in code.

Not currently used: Parallel, Coordinator/Hierarchical, Loop/Iterative refinement, Swarm, ReAct.

## Key Files

- Agents: `backend/src/agents/*`, `backend/src/agents/base.py`
- Service wrappers: `backend/src/app/services/agents.py`
- Prompts: `backend/prompts/*`

---

**Related:** [Integration Summary](../integrations/INTEGRATION_SUMMARY.md)
