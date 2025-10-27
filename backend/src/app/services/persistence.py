"""Persistence helpers wrapping ApplicationDatabase with consistent patterns."""

from typing import Any, Dict, Optional
import streamlit as st
import json

from src.api.client_factory import get_client


def extract_job_metadata_with_llm(
    client, model: str, job_posting: str, job_analysis: str = ""
) -> Dict[str, str]:
    """Extract company name and job title using LLM with structured output.

    Args:
        client: OpenRouterClient instance
        model: Model to use for extraction
        job_posting: Original job posting text
        job_analysis: Optional job analysis from Agent 1

    Returns:
        Dictionary with 'company_name' and 'job_title'
    """
    prompt = f"""Extract the company name and job title from the following job posting. Return ONLY a JSON object with this exact structure:

{{
  "company_name": "the company/organization name",
  "job_title": "the job title/position"
}}

If you cannot find the company name or job title, use "Unknown Company" or "Unknown Position" respectively.

Job Posting:
{job_posting}
"""

    if job_analysis:
        prompt += f"\n\nJob Analysis (may contain extracted info):\n{job_analysis}"

    try:
        # Use the provided model (should be metadata extractor model)
        resolved_client = get_client(model, default_client=client)

        response = resolved_client.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a metadata extraction assistant. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=100,
        )

        response_text = response.choices[0].message.content.strip()

        # Clean up potential markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON
        metadata = json.loads(response_text)

        # Validate and clean
        company_name = metadata.get("company_name", "Unknown Company")[:100]
        job_title = metadata.get("job_title", "Unknown Position")[:100]

        return {"company_name": company_name, "job_title": job_title}

    except Exception as e:
        # Fallback to defaults if extraction fails
        print(f"Metadata extraction failed: {e}")
        return {"company_name": "Unknown Company", "job_title": "Unknown Position"}


def create_application_if_needed(
    db,
    *,
    job_posting_text: str,
    company_name: str = "Unknown Company",
    job_title: str = "Unknown Position",
    client=None,
    model: str = "",
    job_analysis: str = "",
) -> int:
    """Create an application if none exists in session_state; return application_id.

    If client and job_posting_text are provided, uses LLM to extract metadata.
    """
    if not st.session_state.get("application_id"):
        # Try to extract metadata with LLM if client provided
        if client and job_posting_text:
            try:
                resolved_client = get_client(model, default_client=client)
                metadata = extract_job_metadata_with_llm(
                    resolved_client, model, job_posting_text, job_analysis
                )
                company_name = metadata.get("company_name", company_name)
                job_title = metadata.get("job_title", job_title)
            except Exception as e:
                print(f"LLM metadata extraction failed, using defaults: {e}")

        app_id = db.create_application(
            company_name=company_name,
            job_title=job_title,
            job_posting_text=job_posting_text,
            original_resume_text="",
        )
        st.session_state.application_id = app_id
    return st.session_state.application_id


def persist_agent_result(
    db,
    *,
    application_id: int,
    agent_number: int,
    agent_name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    update_fields: Optional[Dict[str, Any]] = None,
) -> None:
    """Save agent output and optionally update application fields in a single call."""
    metadata = metadata or {}
    db.save_agent_output(
        application_id=application_id,
        agent_number=agent_number,
        agent_name=agent_name,
        input_data=input_data,
        output_data=output_data,
        cost=metadata.get("cost", 0.0),
        input_tokens=metadata.get("input_tokens", 0),
        output_tokens=metadata.get("output_tokens", 0),
    )
    if update_fields:
        db.update_application(application_id, **update_fields)


def save_validation_scores(
    db,
    *,
    application_id: int,
    scores: Dict[str, float],
    red_flags: list[str],
    recommendations: list[str],
) -> None:
    db.save_validation_scores(
        application_id,
        scores=scores,
        red_flags=red_flags,
        recommendations=recommendations,
    )


def save_profile(
    db,
    *,
    sources: list[str],
    profile_text: str,
    profile_index: str,
) -> int:
    """Persist a profile snapshot for reuse across sessions."""
    return db.save_profile(
        sources=sources,
        profile_text=profile_text,
        profile_index=profile_index,
    )


def load_latest_profile(db) -> Optional[Dict[str, Any]]:
    """Load most recent profile snapshot if available."""
    return db.get_latest_profile()
