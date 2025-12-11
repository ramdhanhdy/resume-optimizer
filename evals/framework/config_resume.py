"""Resume optimization domain-specific configuration.

This module contains evaluation criteria, stage definitions, and
model configurations specific to the resume optimization pipeline.
"""

import sys
from pathlib import Path
from typing import Dict, List

from .config import StageConfig, ModelConfig, EvalConfig

# Ensure backend is importable so we can read MODEL_REGISTRY
backend_root = Path(__file__).parent.parent.parent / "backend"
backend_src = backend_root / "src"
for p in (backend_root, backend_src):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


# --- Stage Definitions ---

RESUME_STAGES: Dict[str, StageConfig] = {
    "profile": StageConfig(
        stage_id="profile",
        display_name="Profile Agent",
        description="Parses and structures the job seeker's profile",
        criteria=["completeness", "accuracy", "structure"],
        criteria_weights={"completeness": 1.0, "accuracy": 1.5, "structure": 0.8},
    ),
    "job_analyzer": StageConfig(
        stage_id="job_analyzer",
        display_name="Job Posting Agent",
        description="Analyzes the target job description",
        criteria=["requirement_extraction", "priority_identification", "completeness"],
        criteria_weights={
            "requirement_extraction": 1.2,
            "priority_identification": 1.0,
            "completeness": 1.0,
        },
    ),
    "optimizer": StageConfig(
        stage_id="optimizer",
        display_name="Resume Optimizer Agent",
        description="Generates optimized resume tailored to job posting",
        criteria=["relevance", "faithfulness", "clarity", "ats_optimization"],
        criteria_weights={
            "relevance": 1.2,
            "faithfulness": 1.5,  # Critical: no fabrication
            "clarity": 1.0,
            "ats_optimization": 0.8,
        },
    ),
    "qa": StageConfig(
        stage_id="qa",
        display_name="QA Agent",
        description="Checks for fabricated or exaggerated claims",
        criteria=["detection_accuracy", "precision", "actionability"],
        criteria_weights={
            "detection_accuracy": 1.5,
            "precision": 1.2,
            "actionability": 1.0,
        },
    ),
    "polish": StageConfig(
        stage_id="polish",
        display_name="Polish & Export Agent",
        description="Applies stylistic polish and formatting",
        criteria=["formatting", "consistency", "professionalism"],
        criteria_weights={
            "formatting": 1.0,
            "consistency": 1.0,
            "professionalism": 1.0,
        },
    ),
}


# --- Evaluation Criteria Descriptions ---

CRITERIA_DESCRIPTIONS: Dict[str, str] = {
    # Optimizer stage
    "relevance": "How well the resume highlights skills and experience relevant to the job posting",
    "faithfulness": "No invented roles, skills, or credentials beyond the user's profile",
    "clarity": "Readability, logical organization, professional tone",
    "ats_optimization": "Keyword optimization for Applicant Tracking Systems",
    
    # QA stage
    "detection_accuracy": "Correctly flags unsupported or exaggerated statements",
    "precision": "Avoids incorrectly flagging legitimate experience as false",
    "actionability": "Provides clear suggestions for fixing issues",
    
    # Profile stage
    "completeness": "All relevant information extracted from source",
    "accuracy": "Information correctly parsed without errors",
    "structure": "Well-organized output format",
    
    # Job analyzer stage
    "requirement_extraction": "All requirements correctly identified",
    "priority_identification": "Key vs nice-to-have requirements distinguished",
    
    # Polish stage
    "formatting": "Consistent and professional formatting",
    "consistency": "Style consistency throughout document",
    "professionalism": "Appropriate tone and language",
}


# --- Common Tags ---

EVAL_TAGS: Dict[str, List[str]] = {
    "optimizer": [
        "excellent",
        "fabrication",
        "exaggeration",
        "off-target",
        "too-generic",
        "good-structure",
        "poor-formatting",
        "missing-keywords",
        "creative-framing",
    ],
    "qa": [
        "accurate-detection",
        "false-positive",
        "missed-fabrication",
        "helpful-suggestions",
        "vague-feedback",
        "thorough",
    ],
    "profile": [
        "complete",
        "missing-info",
        "parsing-error",
        "well-structured",
    ],
    "job_analyzer": [
        "complete",
        "missed-requirements",
        "good-prioritization",
        "over-extraction",
    ],
    "polish": [
        "professional",
        "formatting-issues",
        "consistent",
        "creative",
    ],
}


# --- Model Configurations ---

_FALLBACK_MODELS: List[ModelConfig] = [
    ModelConfig(
        model_id="openrouter::anthropic/claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        provider="openrouter",
    ),
    ModelConfig(
        model_id="openrouter::openai/gpt-5.1",
        display_name="GPT-5.1",
        provider="openrouter",
    ),
    ModelConfig(
        model_id="gemini::gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        provider="gemini",
    ),
]


def _get_models_from_registry() -> List[ModelConfig]:
    """Get models from backend's MODEL_REGISTRY, fallback if missing/empty."""
    try:
        from src.api.model_registry import MODEL_REGISTRY
    except ImportError:
        return _FALLBACK_MODELS

    models: List[ModelConfig] = []
    for model_id, info in MODEL_REGISTRY.items():
        provider = info.get("provider", "openrouter")
        api_model = info.get("api_model", model_id)

        display_name = api_model.split("/")[-1].replace("-", " ").title()

        models.append(
            ModelConfig(
                model_id=model_id,
                display_name=f"{display_name} ({provider})",
                provider=provider,
            )
        )

    return models or _FALLBACK_MODELS


# Load models from backend registry
CANDIDATE_MODELS: List[ModelConfig] = _get_models_from_registry()


def get_resume_eval_config() -> EvalConfig:
    """Return evaluation configuration for resume optimization."""
    return EvalConfig(
        db_path="./data/resume_evals.db",
        default_evaluator_id="developer",
        randomize_candidate_order=True,
        log_dir="./logs/resume_evals",
    )


def get_stage_config(stage_id: str) -> StageConfig:
    """Get configuration for a specific stage."""
    if stage_id not in RESUME_STAGES:
        raise ValueError(f"Unknown stage: {stage_id}")
    return RESUME_STAGES[stage_id]


def get_criteria_for_stage(stage_id: str) -> List[str]:
    """Get evaluation criteria for a stage."""
    return get_stage_config(stage_id).criteria


def get_tags_for_stage(stage_id: str) -> List[str]:
    """Get available tags for a stage."""
    return EVAL_TAGS.get(stage_id, [])


def get_model_by_id(model_id: str) -> ModelConfig:
    """Get model configuration by ID."""
    for model in CANDIDATE_MODELS:
        if model.model_id == model_id:
            return model
    raise ValueError(f"Unknown model: {model_id}")
