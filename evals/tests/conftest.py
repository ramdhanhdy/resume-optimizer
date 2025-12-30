"""Pytest configuration for evals tests."""

import sys
from pathlib import Path

# Add evals root to path for direct imports
evals_root = Path(__file__).parent.parent
if str(evals_root) not in sys.path:
    sys.path.insert(0, str(evals_root))
