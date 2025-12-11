"""CLI scripts for evaluation framework."""

import sys
from pathlib import Path

# Ensure evals root is on sys.path for cross-package imports
_evals_root = Path(__file__).parent.parent
if str(_evals_root) not in sys.path:
    sys.path.insert(0, str(_evals_root))
