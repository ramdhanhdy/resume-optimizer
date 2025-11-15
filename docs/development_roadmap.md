# Development Roadmap

_Last updated: 2025-11-15_

High-level roadmap for upcoming work across core features, integrations, and security. This is a planning document; detailed behavior for any non-trivial feature should live in a dedicated spec under `docs/specs/<feature_name>/`.

## 1. Core Features

### 1.1 Self-Improving Polish Agent

Goal: make the polish agent resilient when generated code fails inside the DOCX sandbox (or other execution environment).

**Concept**
- Agent generates polishing code/snippets to run inside a sandbox.
- Sandbox executes the code and captures any runtime errors, stack traces, or constraint violations.
- Agent receives the error output as additional context and produces an improved version of the code.
- Loop continues for a small, bounded number of iterations until the code runs successfully or we give a clear failure message.

**Key requirements**
- Error channel from sandbox → agent (structured, not plain text logs only).
- Guardrails to avoid infinite repair loops (max attempts, timeouts).
- Clear UX if self-repair fails ( surfaced back to the user as a stable error state, not a crash).
- Logging and metrics for how often self-repair succeeds vs. fails.

**Potential follow-ups**
- Generalize the pattern for other agents that produce executable code (e.g. template transforms).

### 1.2 Final User Feedback Loop

Goal: let users give final feedback after seeing the polished resume, and feed that back into the agents for targeted adjustments.

**Concept**
- After the pipeline completes, show a "Final adjustments" text box to the user.
- User can specify tone tweaks, emphasis changes, or corrections.
- Backend exposes an endpoint that:
  - Accepts the current polished resume + user feedback.
  - Calls a dedicated "feedback adjustment" agent (or reuses the polish agent with a different prompt).
  - Returns an updated polished resume.

**Key requirements**
- Frontend UI element on the final screen (input box + submit button).
- New backend route (e.g. `/api/feedback-adjust`) that plugs into existing agent infrastructure.
- Clear indication of what changed after feedback (diff or bullet summary).

### 1.3 Resume Templates & Layout Options

Goal: offer multiple resume templates so users can choose different layouts/visual styles while keeping the same optimized content.

**Concept**
- Separate content (sections, bullet points, metadata) from layout.
- Maintain a small library of DOCX (and/or HTML) templates.
- Allow user to pick a template at the end of the pipeline and generate the export using that layout.

**Key requirements**
- Template abstraction layer on the backend (template ID → DOCX/HTML skeleton + mapping rules).
- Frontend UI for selecting a template (cards with previews, responsive).
- Ensure templates remain compatible with DOCX export safeguards.

**Future ideas**
- Allow saving a "default" template per user once auth/metering is in place.
- A/B test templates for recruiter engagement (long-term).

## 2. Integrations

### 2.1 Canva MCP Integration (Planned)

Goal: allow users to send an optimized resume into Canva for further visual editing (via Canva MCP), once the MCP is stable enough.

**Status**
- Canva MCP is currently in beta.
- Integration is deferred until the protocol and tooling stabilize.

**Concept**
- Expose a "Open in Canva" option after resume generation.
- Use MCP to:
  - Push structured resume content into a Canva design.
  - Potentially pull updates back (longer-term) if Canva supports a round-trip flow.

**Key requirements (when ready)**
- MCP client in the backend (or a dedicated MCP service) that can talk to Canva.
- Stable mapping from internal resume representation → Canva document elements.
- Clear permission and consent model for sending data to Canva.

**Risks / open questions**
- Beta stability of Canva MCP.
- Rate limits and pricing.
- How much control we have over theming vs. Canva templates.

## 3. Security & Assessment

Security work is tracked in more detailed API/security notes elsewhere. This roadmap focuses on high-level directions to keep frontend, backend, and integrations aligned.

### 3.1 Backend Access & OIDC

- Enforce authenticated access for the production backend (Cloud Run), with Vercel → Cloud Run traffic using OIDC tokens.
- Avoid exposing unauthenticated public endpoints except for simple health checks.
- Ensure CORS configuration only allows relevant frontend origins.

### 3.2 API & Data Handling

- Keep sensitive keys in Secret Manager / Vercel encrypted env vars, never in the repo.
- Continue hardening API request validation and input size limits.
- Maintain structured, non-PII logs for debugging and cost tracking.

### 3.3 Future Hardening

- Periodic API/security assessment and threat modeling.
- Add automated checks (CI) for secret leakage and dependency vulnerabilities.
- When auth/metering is implemented, ensure:
  - Per-user usage caps are enforced.
  - Access tokens are validated server-side and never logged.
