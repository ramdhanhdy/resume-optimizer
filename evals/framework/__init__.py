"""Evaluation framework for resume optimizer.

Note: We intentionally avoid importing runner/collector/analyzer here to
prevent circular imports (runner -> db -> framework -> runner). Import those
modules explicitly where needed.
"""

from .schemas import (  # noqa: F401
    Scenario,
    StageEval,
    CandidateOutput,
    Judgment,
    CandidateConfig,
    EvalCriteria,
    WinRateResult,
    PairwiseResult,
)

__all__ = [
    "Scenario",
    "StageEval",
    "CandidateOutput",
    "Judgment",
    "CandidateConfig",
    "EvalCriteria",
    "WinRateResult",
    "PairwiseResult",
]
