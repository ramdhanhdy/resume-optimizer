"""Pipeline provenance helpers for agent_step, model_invocation, and artifact writes."""

import hashlib
from typing import Any, Dict, List, Optional, Tuple


def parse_model_string(model_str: str) -> Tuple[str, str]:
    """Split 'provider::model_id' or infer provider from well-known prefixes.

    Args:
        model_str: Raw model string from env/config, e.g. 'openrouter::claude-3.5-sonnet'
                   or 'gemini-2.5-flash'.

    Returns:
        (provider, model_name) tuple.  Never raises.
    """
    if not model_str:
        return "unknown", "unknown"
    if "::" in model_str:
        provider, model_name = model_str.split("::", 1)
        return provider, model_name
    if model_str.startswith("gemini"):
        return "gemini", model_str
    if model_str.startswith("claude"):
        return "anthropic", model_str
    return "unknown", model_str


def write_agent_provenance(
    user_db,
    *,
    app_id: int,
    job_id: str,
    agent_number: int,
    agent_name: str,
    model_str: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Optional[int]:
    """Persist agent_step + model_invocation rows for one pipeline agent completion.

    Always non-fatal: logs a warning on error and returns None.
    Skipped silently when user_db does not support provenance writes (e.g. SQLite fallback).

    Args:
        user_db: Database adapter instance (SupabaseDatabase or SQLite fallback).
        app_id: applications.id FK.
        job_id: Pipeline job UUID (run identifier).
        agent_number: Agent position in pipeline (1-5).
        agent_name: Human-readable agent name.
        model_str: Raw model string from env/config (e.g. 'openrouter::claude-3.5-sonnet').
        input_data: Agent input payload dict.
        output_data: Agent output payload dict.
        metadata: Metadata dict returned by run_agent_with_chunk_emission.
                  Expected keys: 'input_tokens', 'output_tokens', 'cost'.

    Returns:
        agent_steps row ID on success, None on failure or when unsupported.
    """
    if not hasattr(user_db, "save_agent_step"):
        return None
    try:
        provider, model_name = parse_model_string(model_str)
        input_tokens = int(metadata.get("input_tokens") or 0)
        output_tokens = int(metadata.get("output_tokens") or 0)
        cost_usd = float(metadata.get("cost") or 0.0)

        step_id = user_db.save_agent_step(
            application_id=app_id,
            agent_number=agent_number,
            agent_name=agent_name,
            job_id=job_id,
            input_data=input_data,
            output_data=output_data,
            model_provider=provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            status="completed",
        )
        user_db.save_model_invocation(
            provider=provider,
            model_name=model_name,
            application_id=app_id,
            agent_step_id=step_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            status="success",
        )
        return step_id
    except Exception as exc:
        print(f"⚠️ Provenance write failed for {agent_name} (non-fatal): {exc}")
        return None


def write_final_review_artifact(
    user_db,
    *,
    app_id: int,
    plain_text: str,
    markdown: str,
    filename: Optional[str] = None,
    summary_points: Optional[List[str]] = None,
    agent_step_id: Optional[int] = None,
) -> Optional[int]:
    """Insert a resume_artifacts row with artifact_type='final_review'.

    Marks any prior 'final_review' artifact for the same application as
    is_current=False before inserting the new row (handled inside
    save_resume_artifact).

    Always non-fatal: logs a warning on error and returns None.
    Skipped silently when user_db does not support save_resume_artifact.

    Args:
        user_db: Database adapter instance.
        app_id: applications.id FK.
        plain_text: Normalized plain-text review content.
        markdown: Markdown representation of the review.
        filename: Suggested download filename.
        summary_points: Optional list of summary bullet points.
        agent_step_id: FK to agent_steps.id for the Polish Agent step.

    Returns:
        resume_artifacts row ID on success, None on failure or when unsupported.
    """
    if not hasattr(user_db, "save_resume_artifact"):
        return None
    try:
        content_hash = hashlib.sha256(
            ((plain_text or "") + "\n" + (markdown or "")).encode()
        ).hexdigest()
        return user_db.save_resume_artifact(
            application_id=app_id,
            artifact_type="final_review",
            content_hash=content_hash,
            plain_text=plain_text or None,
            markdown=markdown or None,
            filename=filename,
            summary_points=list(summary_points or []),
            agent_step_id=agent_step_id,
            is_current=True,
        )
    except Exception as exc:
        print(f"⚠️ Artifact persistence failed for final_review (non-fatal): {exc}")
        return None
