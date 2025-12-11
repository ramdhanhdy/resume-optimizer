"""Evaluation framework for resume optimizer.

Note: We intentionally avoid importing runner/collector/analyzer here to
prevent circular imports (runner -> db -> framework -> runner). Import those
modules explicitly where needed.
"""

import sys
from pathlib import Path

# Ensure evals root is on sys.path for cross-package imports
_evals_root = Path(__file__).parent.parent
if str(_evals_root) not in sys.path:
    sys.path.insert(0, str(_evals_root))

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
