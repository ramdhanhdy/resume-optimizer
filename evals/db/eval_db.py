"""SQLite database for evaluation data persistence.

This module provides the data layer for storing scenarios, stage evaluations,
candidate outputs, and human judgments.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from framework.schemas import (
    Scenario,
    StageEval,
    CandidateOutput,
    Judgment,
    WinRateResult,
    PairwiseResult,
)


class EvalDatabase:
    """SQLite database for evaluation data."""

    def __init__(self, db_path: str = "./data/evals.db"):
        """Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Scenarios table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_profile TEXT NOT NULL,
                job_posting TEXT NOT NULL,
                metadata TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_scenarios_id ON eval_scenarios(scenario_id)"
        )

        # Stage evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_stage_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES eval_scenarios(scenario_id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stage_runs_scenario "
            "ON eval_stage_runs(scenario_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stage_runs_stage "
            "ON eval_stage_runs(stage_id)"
        )

        # Candidate outputs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_run_id INTEGER NOT NULL,
                candidate_label TEXT NOT NULL,
                model_id TEXT NOT NULL,
                output_text TEXT NOT NULL,
                latency_ms INTEGER,
                token_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stage_run_id) REFERENCES eval_stage_runs(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_candidates_stage_run "
            "ON eval_candidates(stage_run_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_candidates_model "
            "ON eval_candidates(model_id)"
        )

        # Human judgments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_judgments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_run_id INTEGER NOT NULL,
                evaluator_id TEXT DEFAULT 'default',
                chosen_candidate_id INTEGER NOT NULL,
                ranking TEXT,
                scores TEXT,
                tags TEXT,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stage_run_id) REFERENCES eval_stage_runs(id),
                FOREIGN KEY (chosen_candidate_id) REFERENCES eval_candidates(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_judgments_stage_run "
            "ON eval_judgments(stage_run_id)"
        )

        self.conn.commit()

    # --- Scenario Operations ---

    def create_scenario(self, scenario: Scenario) -> int:
        """Create a new scenario.

        Args:
            scenario: Scenario object to persist

        Returns:
            Database ID of the created scenario
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO eval_scenarios (scenario_id, user_profile, job_posting, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (
                scenario.scenario_id,
                scenario.user_profile,
                scenario.job_posting,
                json.dumps(scenario.metadata) if scenario.metadata else None,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario by ID.

        Args:
            scenario_id: Unique scenario identifier

        Returns:
            Scenario object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM eval_scenarios WHERE scenario_id = ?",
            (scenario_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return Scenario(
            id=row["id"],
            scenario_id=row["scenario_id"],
            user_profile=row["user_profile"],
            job_posting=row["job_posting"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def list_scenarios(self, limit: int = 100) -> List[Scenario]:
        """List all scenarios.

        Args:
            limit: Maximum number of scenarios to return

        Returns:
            List of Scenario objects
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM eval_scenarios
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            Scenario(
                id=row["id"],
                scenario_id=row["scenario_id"],
                user_profile=row["user_profile"],
                job_posting=row["job_posting"],
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

    # --- Stage Run Operations ---

    def create_stage_run(
        self,
        scenario_id: str,
        stage_id: str,
        context: Dict[str, Any],
    ) -> int:
        """Create a new stage evaluation run.

        Args:
            scenario_id: Parent scenario ID
            stage_id: Stage being evaluated
            context: Context passed to all candidates

        Returns:
            Database ID of the created stage run
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO eval_stage_runs (scenario_id, stage_id, context)
            VALUES (?, ?, ?)
            """,
            (scenario_id, stage_id, json.dumps(context)),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_stage_run(self, stage_run_id: int) -> Optional[StageEval]:
        """Get stage run by ID.

        Args:
            stage_run_id: Database ID of the stage run

        Returns:
            StageEval object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM eval_stage_runs WHERE id = ?",
            (stage_run_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        candidates = self.get_candidates_for_stage_run(stage_run_id)

        return StageEval(
            id=row["id"],
            scenario_id=row["scenario_id"],
            stage_id=row["stage_id"],
            context=json.loads(row["context"]) if row["context"] else {},
            candidates=candidates,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def get_stage_runs_for_scenario(
        self, scenario_id: str, stage_id: Optional[str] = None
    ) -> List[StageEval]:
        """Get all stage runs for a scenario.

        Args:
            scenario_id: Parent scenario ID
            stage_id: Optional filter by stage

        Returns:
            List of StageEval objects
        """
        cursor = self.conn.cursor()
        if stage_id:
            cursor.execute(
                """
                SELECT * FROM eval_stage_runs
                WHERE scenario_id = ? AND stage_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id, stage_id),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM eval_stage_runs
                WHERE scenario_id = ?
                ORDER BY created_at DESC
                """,
                (scenario_id,),
            )

        rows = cursor.fetchall()
        return [
            StageEval(
                id=row["id"],
                scenario_id=row["scenario_id"],
                stage_id=row["stage_id"],
                context=json.loads(row["context"]) if row["context"] else {},
                candidates=self.get_candidates_for_stage_run(row["id"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def get_pending_stage_runs(self, limit: int = 50) -> List[StageEval]:
        """Get stage runs that haven't been judged yet.

        Args:
            limit: Maximum number to return

        Returns:
            List of StageEval objects without judgments
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT sr.* FROM eval_stage_runs sr
            LEFT JOIN eval_judgments j ON sr.id = j.stage_run_id
            WHERE j.id IS NULL
            ORDER BY sr.created_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            StageEval(
                id=row["id"],
                scenario_id=row["scenario_id"],
                stage_id=row["stage_id"],
                context=json.loads(row["context"]) if row["context"] else {},
                candidates=self.get_candidates_for_stage_run(row["id"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    # --- Candidate Operations ---

    def save_candidate(
        self,
        stage_run_id: int,
        candidate: CandidateOutput,
    ) -> int:
        """Save a candidate output.

        Args:
            stage_run_id: Parent stage run ID
            candidate: CandidateOutput object to persist

        Returns:
            Database ID of the created candidate
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO eval_candidates
            (stage_run_id, candidate_label, model_id, output_text, latency_ms, token_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                stage_run_id,
                candidate.candidate_label,
                candidate.model_id,
                candidate.output_text,
                candidate.latency_ms,
                candidate.token_count,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_candidates_for_stage_run(
        self, stage_run_id: int
    ) -> List[CandidateOutput]:
        """Get all candidates for a stage run.

        Args:
            stage_run_id: Parent stage run ID

        Returns:
            List of CandidateOutput objects
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM eval_candidates
            WHERE stage_run_id = ?
            ORDER BY candidate_label
            """,
            (stage_run_id,),
        )
        rows = cursor.fetchall()
        return [
            CandidateOutput(
                id=row["id"],
                stage_run_id=row["stage_run_id"],
                candidate_label=row["candidate_label"],
                model_id=row["model_id"],
                output_text=row["output_text"],
                latency_ms=row["latency_ms"],
                token_count=row["token_count"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def get_candidate(self, candidate_id: int) -> Optional[CandidateOutput]:
        """Get candidate by ID.

        Args:
            candidate_id: Database ID of the candidate

        Returns:
            CandidateOutput object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM eval_candidates WHERE id = ?",
            (candidate_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return CandidateOutput(
            id=row["id"],
            stage_run_id=row["stage_run_id"],
            candidate_label=row["candidate_label"],
            model_id=row["model_id"],
            output_text=row["output_text"],
            latency_ms=row["latency_ms"],
            token_count=row["token_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # --- Judgment Operations ---

    def save_judgment(self, judgment: Judgment) -> int:
        """Save a human judgment.

        Args:
            judgment: Judgment object to persist

        Returns:
            Database ID of the created judgment
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO eval_judgments
            (stage_run_id, evaluator_id, chosen_candidate_id, ranking, scores, tags, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                judgment.stage_run_id,
                judgment.evaluator_id,
                judgment.chosen_candidate_id,
                json.dumps(judgment.ranking) if judgment.ranking else None,
                json.dumps(judgment.scores) if judgment.scores else None,
                json.dumps(judgment.tags) if judgment.tags else None,
                judgment.comments,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_judgment_for_stage_run(
        self, stage_run_id: int
    ) -> Optional[Judgment]:
        """Get judgment for a stage run.

        Args:
            stage_run_id: Parent stage run ID

        Returns:
            Judgment object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM eval_judgments
            WHERE stage_run_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (stage_run_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return Judgment(
            id=row["id"],
            stage_run_id=row["stage_run_id"],
            evaluator_id=row["evaluator_id"],
            chosen_candidate_id=row["chosen_candidate_id"],
            ranking=json.loads(row["ranking"]) if row["ranking"] else None,
            scores=json.loads(row["scores"]) if row["scores"] else None,
            tags=json.loads(row["tags"]) if row["tags"] else None,
            comments=row["comments"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # --- Analysis Queries ---

    def get_judgments_for_stage(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all judgments for a stage with model information.

        Args:
            stage_id: Stage to get judgments for

        Returns:
            List of judgment records with winner model info
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                j.*,
                c.model_id as winner_model_id,
                sr.scenario_id
            FROM eval_judgments j
            JOIN eval_stage_runs sr ON j.stage_run_id = sr.id
            JOIN eval_candidates c ON j.chosen_candidate_id = c.id
            WHERE sr.stage_id = ?
            """,
            (stage_id,),
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            # Get all model IDs that participated in this stage run
            cursor.execute(
                "SELECT DISTINCT model_id FROM eval_candidates WHERE stage_run_id = ?",
                (row["stage_run_id"],),
            )
            all_models = [r["model_id"] for r in cursor.fetchall()]

            results.append({
                "id": row["id"],
                "stage_run_id": row["stage_run_id"],
                "scenario_id": row["scenario_id"],
                "winner_model_id": row["winner_model_id"],
                "all_model_ids": all_models,
                "scores": json.loads(row["scores"]) if row["scores"] else None,
                "tags": json.loads(row["tags"]) if row["tags"] else None,
            })

        return results

    def get_head_to_head(
        self, stage_id: str, model_a: str, model_b: str
    ) -> List[Dict[str, Any]]:
        """Get head-to-head comparisons between two models.

        Args:
            stage_id: Stage to analyze
            model_a: First model ID
            model_b: Second model ID

        Returns:
            List of comparison records
        """
        cursor = self.conn.cursor()
        
        # Find stage runs where both models participated
        cursor.execute(
            """
            SELECT sr.id as stage_run_id, j.chosen_candidate_id, c.model_id as winner
            FROM eval_stage_runs sr
            JOIN eval_judgments j ON sr.id = j.stage_run_id
            JOIN eval_candidates c ON j.chosen_candidate_id = c.id
            WHERE sr.stage_id = ?
            AND sr.id IN (
                SELECT stage_run_id FROM eval_candidates WHERE model_id = ?
            )
            AND sr.id IN (
                SELECT stage_run_id FROM eval_candidates WHERE model_id = ?
            )
            """,
            (stage_id, model_a, model_b),
        )
        
        return [dict(row) for row in cursor.fetchall()]

    def get_all_pairwise(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all pairwise comparisons for Bradley-Terry analysis.

        Args:
            stage_id: Stage to analyze

        Returns:
            List of {winner, loser} pairs
        """
        cursor = self.conn.cursor()
        
        # Get all judgments with winner info
        cursor.execute(
            """
            SELECT 
                sr.id as stage_run_id,
                c.model_id as winner
            FROM eval_stage_runs sr
            JOIN eval_judgments j ON sr.id = j.stage_run_id
            JOIN eval_candidates c ON j.chosen_candidate_id = c.id
            WHERE sr.stage_id = ?
            """,
            (stage_id,),
        )
        
        results = []
        for row in cursor.fetchall():
            # Get all other models in this stage run (losers)
            cursor.execute(
                """
                SELECT DISTINCT model_id FROM eval_candidates
                WHERE stage_run_id = ? AND model_id != ?
                """,
                (row["stage_run_id"], row["winner"]),
            )
            losers = [r["model_id"] for r in cursor.fetchall()]
            
            for loser in losers:
                results.append({
                    "winner": row["winner"],
                    "loser": loser,
                })
        
        return results

    def get_model_stats(self, stage_id: str) -> Dict[str, Dict[str, int]]:
        """Get win/appearance counts per model.

        Args:
            stage_id: Stage to analyze

        Returns:
            Dict mapping model_id to {wins, appearances}
        """
        cursor = self.conn.cursor()
        
        # Count appearances
        cursor.execute(
            """
            SELECT c.model_id, COUNT(DISTINCT c.stage_run_id) as appearances
            FROM eval_candidates c
            JOIN eval_stage_runs sr ON c.stage_run_id = sr.id
            WHERE sr.stage_id = ?
            GROUP BY c.model_id
            """,
            (stage_id,),
        )
        stats = {row["model_id"]: {"appearances": row["appearances"], "wins": 0} 
                 for row in cursor.fetchall()}
        
        # Count wins
        cursor.execute(
            """
            SELECT c.model_id, COUNT(*) as wins
            FROM eval_judgments j
            JOIN eval_candidates c ON j.chosen_candidate_id = c.id
            JOIN eval_stage_runs sr ON j.stage_run_id = sr.id
            WHERE sr.stage_id = ?
            GROUP BY c.model_id
            """,
            (stage_id,),
        )
        for row in cursor.fetchall():
            if row["model_id"] in stats:
                stats[row["model_id"]]["wins"] = row["wins"]
        
        return stats

    def delete_stage_run(self, stage_run_id: int) -> bool:
        """Delete a stage run and its candidates/judgments.
        
        Args:
            stage_run_id: ID of the stage run to delete
            
        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM eval_stage_runs WHERE id = ?", (stage_run_id,))
        if not cursor.fetchone():
            return False
        
        # Delete judgments first (foreign key)
        cursor.execute("DELETE FROM eval_judgments WHERE stage_run_id = ?", (stage_run_id,))
        
        # Delete candidates
        cursor.execute("DELETE FROM eval_candidates WHERE stage_run_id = ?", (stage_run_id,))
        
        # Delete stage run
        cursor.execute("DELETE FROM eval_stage_runs WHERE id = ?", (stage_run_id,))
        
        self.conn.commit()
        return True

    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario and all its stage runs.
        
        Args:
            scenario_id: ID of the scenario to delete
            
        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        
        # Get all stage runs for this scenario
        cursor.execute(
            "SELECT id FROM eval_stage_runs WHERE scenario_id = ?",
            (scenario_id,),
        )
        stage_run_ids = [row["id"] for row in cursor.fetchall()]
        
        # Delete each stage run
        for sr_id in stage_run_ids:
            self.delete_stage_run(sr_id)
        
        # Delete scenario
        cursor.execute("DELETE FROM eval_scenarios WHERE scenario_id = ?", (scenario_id,))
        self.conn.commit()
        
        return cursor.rowcount > 0

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
