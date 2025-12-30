"""Streamlit UI for evaluation judging."""

import sys
from pathlib import Path

# Ensure evals root is on sys.path for cross-package imports
_evals_root = Path(__file__).parent.parent
if str(_evals_root) not in sys.path:
    sys.path.insert(0, str(_evals_root))

from .judge_ui import render_judge_ui, render_results_dashboard, render_pending_queue
from .new_eval import render_new_eval_page

__all__ = [
    "render_judge_ui",
    "render_results_dashboard",
    "render_pending_queue",
    "render_new_eval_page",
]
