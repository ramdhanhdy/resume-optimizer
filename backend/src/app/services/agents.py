"""Service wrappers for agents. Return stream generators for views to consume."""

from typing import Any, Dict, Generator, List, Optional

from src.api.client_factory import get_client
from src.api.multiprovider import MultiProviderClient
from src.api.model_registry import get_api_model
from src.agents import (
    GitHubProjectsAgent,
    JobAnalyzerAgent,
    OptimizerImplementerAgent,
    PolishAgent,
    ProfileAgent,
    ResumeOptimizerAgent,
    ValidatorAgent,
)


def _resolve_client(model: str, client):
    # If caller provided the multi-provider facade, use it directly
    if isinstance(client, MultiProviderClient):
        return client
    return get_client(model, default_client=client)


def _is_longcat_thinking(model: str) -> bool:
    """Return True when the selected model is LongCat-Flash-Thinking."""
    if not model:
        return False
    api_model = get_api_model(model)
    return api_model.strip().lower() == "longcat-flash-thinking"


def stream_analyze_job(
    *,
    client,
    model: str,
    job_posting: Optional[str],
    file_path: Optional[str] = None,
    file_type: Optional[str] = None,
    profile_index: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    thinking_budget: Optional[int] = None,
) -> Generator[str, None, Dict[str, Any]]:
    """Stream job analysis output."""
    resolved_client = _resolve_client(model, client)
    agent = JobAnalyzerAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.analyze_job(
        job_posting=job_posting,
        model=model,
        file_path=file_path,
        file_type=file_type,
        profile_index=profile_index,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra,
    )


def stream_optimize_resume(
    *,
    client,
    model: str,
    resume_text: str,
    job_analysis: str,
    profile_index: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    thinking_budget: Optional[int] = None,
):
    resolved_client = _resolve_client(model, client)
    agent = ResumeOptimizerAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.optimize_resume(
        resume_text=resume_text,
        job_analysis=job_analysis,
        profile_index=profile_index,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra,
    )


def stream_curate_github(
    *,
    client,
    model: str,
    github_username: str,
    resume_text: str,
    job_analysis: str,
    github_token: Optional[str] = None,
    repos: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.0,
    max_tokens: int = 4000,
    thinking_budget: Optional[int] = None,
):
    resolved_client = _resolve_client(model, client)
    agent = GitHubProjectsAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.curate_projects(
        github_username=github_username,
        resume_text=resume_text,
        job_analysis=job_analysis,
        model=model,
        github_token=github_token if github_token else None,
        repos=repos,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra,
    )


def stream_implement_optimizations(
    *,
    client,
    model: str,
    resume_text: str,
    optimization_report: str,
    profile_index: Optional[str] = None,
    thinking_budget: Optional[int] = None,
):
    resolved_client = _resolve_client(model, client)
    agent = OptimizerImplementerAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.implement_optimizations(
        resume_text=resume_text,
        optimization_report=optimization_report,
        profile_index=profile_index,
        model=model,
        **extra,
    )


def stream_validate_resume(
    *,
    client,
    model: str,
    optimized_resume: str,
    job_posting: str,
    job_analysis: str,
    profile_index: Optional[str] = None,
    thinking_budget: Optional[int] = None,
):
    resolved_client = _resolve_client(model, client)
    agent = ValidatorAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.validate_resume(
        optimized_resume=optimized_resume,
        job_posting=job_posting,
        job_analysis=job_analysis,
        profile_index=profile_index,
        model=model,
        **extra,
    )


def stream_polish_resume(
    *,
    client,
    model: str,
    optimized_resume: str,
    validation_report: str,
    output_format: str = "html",
    thinking_budget: Optional[int] = None,
):
    resolved_client = _resolve_client(model, client)
    agent = PolishAgent(resolved_client, output_format=output_format)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.polish_resume(
        optimized_resume=optimized_resume,
        validation_report=validation_report,
        model=model,
        **extra,
    )


def stream_index_profile(
    *,
    client,
    model: str,
    profile_text: str,
    profile_repos: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.1,
    max_tokens: int = 3500,
    thinking_budget: Optional[int] = None,
):
    """Stream profile index creation (Step 0)."""
    resolved_client = _resolve_client(model, client)
    agent = ProfileAgent(resolved_client)
    extra = {}
    if _is_longcat_thinking(model) and thinking_budget is not None:
        extra["thinking_budget"] = thinking_budget
    return agent.index_profile(
        model=model,
        profile_text=profile_text,
        profile_repos=profile_repos,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra,
    )
