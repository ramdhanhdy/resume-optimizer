"""Pytest configuration for evals tests."""

import sys
from pathlib import Path

# Add project root (parent of evals/) to path so `from evals.xxx` imports work
evals_root = Path(__file__).parent.parent
project_root = evals_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
