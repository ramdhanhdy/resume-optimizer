"""Core data models for the evaluation framework.

These dataclasses define the shared vocabulary across runner, collector,
analyzer, and database layers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


class StageId(str, Enum):
    """Pipeline stages that can be evaluated."""
    PROFILE = "profile"
    JOB_ANALYZER = "job_analyzer"
    OPTIMIZER = "optimizer"
    QA = "qa"
    POLISH = "polish"


class ImportanceLevel(str, Enum):
    """Tag importance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CandidateConfig:
    """Configuration for a model candidate in an evaluation run."""
    model_id: str
    prompt_version: str = "default"
    temperature: float = 0.65
    max_tokens: int = 32000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


@dataclass
class Scenario:
    """A single evaluation scenario (profile + job posting pair).
    
    Each scenario represents one real-world usage instance that can be
    used to compare multiple model candidates.
    """
    scenario_id: str
    user_profile: str
    job_posting: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields populated after DB retrieval
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "user_profile": self.user_profile,
            "job_posting": self.job_posting,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CandidateOutput:
    """Output from a single model candidate for a stage evaluation.
    
    The candidate_label (A, B, C, ...) is assigned after shuffling
    to ensure blind evaluation.
    """
    model_id: str
    output_text: str
    latency_ms: int
    token_count: int
    candidate_label: str = ""  # Assigned after shuffle
    
    # Optional fields populated after DB retrieval
    id: Optional[int] = None
    stage_run_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "output_text": self.output_text,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "candidate_label": self.candidate_label,
        }


@dataclass
class StageEval:
    """A stage evaluation run with multiple candidates.
    
    For a given scenario and stage, this captures the context passed
    to all candidates and references their outputs.
    """
    scenario_id: str
    stage_id: str
    context: Dict[str, Any]
    candidates: List[CandidateOutput] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Optional fields populated after DB retrieval
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "stage_id": self.stage_id,
            "context": self.context,
            "candidates": [c.to_dict() for c in self.candidates],
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class EvalCriteria:
    """Evaluation criteria with score."""
    name: str
    score: int  # 1-5 scale
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
        }


@dataclass
class Judgment:
    """Human judgment for a stage evaluation.
    
    Records which candidate was chosen as best, optional full ranking,
    detailed scores per criterion, and qualitative tags/comments.
    """
    stage_run_id: int
    chosen_candidate_id: int
    evaluator_id: str = "default"
    ranking: Optional[List[int]] = None  # Ordered list of candidate IDs
    scores: Optional[Dict[str, int]] = None  # {criterion: score}
    tags: Optional[List[str]] = None
    comments: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Optional fields populated after DB retrieval
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_run_id": self.stage_run_id,
            "chosen_candidate_id": self.chosen_candidate_id,
            "evaluator_id": self.evaluator_id,
            "ranking": self.ranking,
            "scores": self.scores,
            "tags": self.tags,
            "comments": self.comments,
            "created_at": self.created_at.isoformat(),
        }


# --- Analysis Result Types ---

@dataclass
class WinRateResult:
    """Win rate statistics for a model at a stage."""
    model_id: str
    stage_id: str
    wins: int
    appearances: int
    win_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "stage_id": self.stage_id,
            "wins": self.wins,
            "appearances": self.appearances,
            "win_rate": self.win_rate,
        }


@dataclass
class PairwiseResult:
    """Pairwise preference statistics between two models."""
    model_a: str
    model_b: str
    stage_id: str
    a_wins: int
    b_wins: int
    total: int
    p_a_preferred: float  # P(A > B)
    p_value: float
    ci_low: float
    ci_high: float
    significant: bool  # True if CI doesn't include 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_a": self.model_a,
            "model_b": self.model_b,
            "stage_id": self.stage_id,
            "a_wins": self.a_wins,
            "b_wins": self.b_wins,
            "total": self.total,
            "p_a_preferred": self.p_a_preferred,
            "p_value": self.p_value,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "significant": self.significant,
        }


@dataclass
class BradleyTerryResult:
    """Bradley-Terry model ranking result."""
    model_id: str
    stage_id: str
    strength: float  # Latent strength parameter (theta)
    rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "stage_id": self.stage_id,
            "strength": self.strength,
            "rank": self.rank,
        }
