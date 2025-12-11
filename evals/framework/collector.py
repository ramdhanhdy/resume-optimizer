"""Judgment collector for recording human evaluations.

This module provides the interface for recording human judgments
on candidate outputs, including winner selection, rankings, scores, and tags.
"""

import logging
from typing import Dict, List, Optional

from .schemas import Judgment, CandidateOutput, StageEval
from evals.db.eval_db import EvalDatabase

logger = logging.getLogger(__name__)


class JudgmentCollector:
    """Collects and persists human judgments on candidate outputs."""

    def __init__(self, db: EvalDatabase):
        """Initialize the judgment collector.

        Args:
            db: Database for persisting judgments
        """
        self.db = db

    def record_judgment(
        self,
        stage_run_id: int,
        chosen_candidate_id: int,
        evaluator_id: str = "default",
        ranking: Optional[List[int]] = None,
        scores: Optional[Dict[str, int]] = None,
        tags: Optional[List[str]] = None,
        comments: Optional[str] = None,
    ) -> Judgment:
        """Record a human judgment for a stage evaluation.

        Args:
            stage_run_id: ID of the stage run being judged
            chosen_candidate_id: ID of the winning candidate
            evaluator_id: Identifier for the human evaluator
            ranking: Optional full ranking of candidate IDs
            scores: Optional scores per criterion (e.g., {"relevance": 4, "clarity": 5})
            tags: Optional qualitative tags (e.g., ["fabrication", "excellent"])
            comments: Optional free-text comments

        Returns:
            Created Judgment object
        """
        judgment = Judgment(
            stage_run_id=stage_run_id,
            chosen_candidate_id=chosen_candidate_id,
            evaluator_id=evaluator_id,
            ranking=ranking,
            scores=scores,
            tags=tags,
            comments=comments,
        )

        judgment.id = self.db.save_judgment(judgment)

        logger.info(
            f"Recorded judgment for stage_run {stage_run_id}: "
            f"winner={chosen_candidate_id}, evaluator={evaluator_id}"
        )

        return judgment

    def record_judgment_by_label(
        self,
        stage_eval: StageEval,
        chosen_label: str,
        evaluator_id: str = "default",
        ranking_labels: Optional[List[str]] = None,
        scores: Optional[Dict[str, int]] = None,
        tags: Optional[List[str]] = None,
        comments: Optional[str] = None,
    ) -> Judgment:
        """Record judgment using candidate labels (A, B, C, ...).

        This is more convenient for UI integration where labels are displayed.

        Args:
            stage_eval: The StageEval being judged
            chosen_label: Label of the winning candidate (e.g., "A")
            evaluator_id: Identifier for the human evaluator
            ranking_labels: Optional ranking by labels (e.g., ["A", "C", "B"])
            scores: Optional scores per criterion
            tags: Optional qualitative tags
            comments: Optional free-text comments

        Returns:
            Created Judgment object

        Raises:
            ValueError: If chosen_label doesn't match any candidate
        """
        # Find candidate by label
        chosen_candidate = None
        for candidate in stage_eval.candidates:
            if candidate.candidate_label == chosen_label:
                chosen_candidate = candidate
                break

        if not chosen_candidate or not chosen_candidate.id:
            raise ValueError(f"No candidate found with label: {chosen_label}")

        # Convert ranking labels to IDs if provided
        ranking_ids = None
        if ranking_labels:
            label_to_id = {
                c.candidate_label: c.id
                for c in stage_eval.candidates
                if c.id is not None
            }
            ranking_ids = [label_to_id[label] for label in ranking_labels]

        return self.record_judgment(
            stage_run_id=stage_eval.id,
            chosen_candidate_id=chosen_candidate.id,
            evaluator_id=evaluator_id,
            ranking=ranking_ids,
            scores=scores,
            tags=tags,
            comments=comments,
        )

    def get_judgment(self, stage_run_id: int) -> Optional[Judgment]:
        """Get the judgment for a stage run.

        Args:
            stage_run_id: ID of the stage run

        Returns:
            Judgment object or None if not judged
        """
        return self.db.get_judgment_for_stage_run(stage_run_id)

    def has_judgment(self, stage_run_id: int) -> bool:
        """Check if a stage run has been judged.

        Args:
            stage_run_id: ID of the stage run

        Returns:
            True if judgment exists
        """
        return self.get_judgment(stage_run_id) is not None

    def validate_scores(
        self,
        scores: Dict[str, int],
        valid_criteria: List[str],
        min_score: int = 1,
        max_score: int = 5,
    ) -> bool:
        """Validate that scores are within expected ranges.

        Args:
            scores: Scores to validate
            valid_criteria: List of valid criterion names
            min_score: Minimum allowed score
            max_score: Maximum allowed score

        Returns:
            True if all scores are valid
        """
        for criterion, score in scores.items():
            if criterion not in valid_criteria:
                logger.warning(f"Unknown criterion: {criterion}")
                return False
            if not (min_score <= score <= max_score):
                logger.warning(
                    f"Score {score} for {criterion} out of range "
                    f"[{min_score}, {max_score}]"
                )
                return False
        return True


class BatchJudgmentCollector(JudgmentCollector):
    """Extended collector for batch judgment operations."""

    def __init__(self, db: EvalDatabase):
        super().__init__(db)
        self._pending_judgments: List[Judgment] = []

    def queue_judgment(
        self,
        stage_run_id: int,
        chosen_candidate_id: int,
        evaluator_id: str = "default",
        ranking: Optional[List[int]] = None,
        scores: Optional[Dict[str, int]] = None,
        tags: Optional[List[str]] = None,
        comments: Optional[str] = None,
    ) -> None:
        """Queue a judgment for batch saving.

        Args:
            stage_run_id: ID of the stage run being judged
            chosen_candidate_id: ID of the winning candidate
            evaluator_id: Identifier for the human evaluator
            ranking: Optional full ranking of candidate IDs
            scores: Optional scores per criterion
            tags: Optional qualitative tags
            comments: Optional free-text comments
        """
        judgment = Judgment(
            stage_run_id=stage_run_id,
            chosen_candidate_id=chosen_candidate_id,
            evaluator_id=evaluator_id,
            ranking=ranking,
            scores=scores,
            tags=tags,
            comments=comments,
        )
        self._pending_judgments.append(judgment)

    def flush(self) -> List[Judgment]:
        """Save all queued judgments to database.

        Returns:
            List of saved Judgment objects
        """
        saved = []
        for judgment in self._pending_judgments:
            judgment.id = self.db.save_judgment(judgment)
            saved.append(judgment)

        logger.info(f"Flushed {len(saved)} judgments to database")
        self._pending_judgments = []
        return saved

    def pending_count(self) -> int:
        """Get count of pending judgments."""
        return len(self._pending_judgments)
