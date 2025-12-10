"""Pytest configuration for evals tests."""

import sys
from pathlib import Path

# Add evals root to path so imports work
evals_root = Path(__file__).parent.parent
sys.path.insert(0, str(evals_root))
