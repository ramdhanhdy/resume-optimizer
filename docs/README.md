# Resume Optimizer Documentation

This directory is intentionally small. Documentation should help future work, not prove that an agent "did work".

## Canonical docs

- [`SETUP.md`](SETUP.md) — local setup and environment configuration.
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — development workflow, testing, and code conventions.
- [`API_REFERENCE.md`](API_REFERENCE.md) — API endpoints and payloads.
- [`USER_GUIDE.md`](USER_GUIDE.md) — user-facing product flow.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — current known operational/debugging issues.
- [`architecture/AGENTS_DESIGN_PATTERN.md`](architecture/AGENTS_DESIGN_PATTERN.md) — current multi-agent pipeline architecture.
- [`specs/database/minimum_viable_provenance_plan.md`](specs/database/minimum_viable_provenance_plan.md) — durable provenance design decision and implementation plan.
- [`specs/product_positioning_2026-05-05.md`](specs/product_positioning_2026-05-05.md) — product positioning notes.
- [`case-study/resume-optimizer.md`](case-study/resume-optimizer.md) — external-facing portfolio case study.

## Documentation rule

Do **not** add standalone completion reports such as `implementation_complete.md`, `refactor_summary.md`, `progress.md`, or agent-specific files like `*_by_claude.md` / `*_by_codex.md`.

Repository docs should only be created or updated when they serve one of these durable jobs:

1. **Run the system** — setup, deployment, debugging, recovery.
2. **Maintain the system** — architecture, API contracts, code conventions.
3. **Improve product quality** — evaluation methodology, provenance, failure modes.
4. **Record a durable decision** — tradeoff, accepted risk, reason not to reopen.
5. **Explain the project externally** — case study / portfolio narrative.

Temporary implementation summaries belong in PR descriptions, chat handoffs, or commit messages — not as long-lived docs.
