"""Database layer for application tracking and persistence."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


class ApplicationDatabase:
    """SQLite database for tracking job applications."""

    def __init__(self, db_path: str = "./data/applications.db"):
        """Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                company_name TEXT,
                job_title TEXT,
                job_posting_text TEXT,
                original_resume_text TEXT,
                optimized_resume_text TEXT,
                model_used TEXT,
                total_cost REAL DEFAULT 0.0,
                status TEXT DEFAULT 'in_progress',
                notes TEXT
            )
        """)

        # Agent outputs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                agent_number INTEGER,
                agent_name TEXT,
                input_data TEXT,
                output_data TEXT,
                cost REAL DEFAULT 0.0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
        """)

        # Validation scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                requirements_match REAL,
                ats_optimization REAL,
                cultural_fit REAL,
                presentation_quality REAL,
                competitive_positioning REAL,
                overall_score REAL,
                red_flags TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
        """)

        # Profiles table (persistent profile memory)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sources TEXT,           -- JSON array of sources (e.g., URLs, github:username)
                profile_text TEXT,      -- raw aggregated text
                profile_index TEXT      -- agent-produced index (JSON/text)
            )
            """
        )

        self.conn.commit()

    # --- Profiles API ---
    def save_profile(
        self,
        *,
        sources: list[str],
        profile_text: str,
        profile_index: str,
    ) -> int:
        """Persist a new profile snapshot.

        Returns the profile row ID.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO profiles (sources, profile_text, profile_index)
            VALUES (?, ?, ?)
            """,
            (json.dumps(list(sources) if sources else []), profile_text, profile_index),
        )
        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            msg = "Failed to retrieve lastrowid after profile insert."
            raise RuntimeError(msg)
        return int(last_row)

    def get_latest_profile(self) -> Optional[Dict[str, Any]]:
        """Return the most recent saved profile, if any."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM profiles
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return None
        rec = dict(row)
        try:
            rec["sources"] = json.loads(rec.get("sources") or "[]")
        except Exception:
            rec["sources"] = []
        return rec

    def create_application(
        self,
        company_name: str,
        job_title: str,
        job_posting_text: str,
        original_resume_text: str,
    ) -> int:
        """Create a new application record.

        Args:
            company_name: Name of company
            job_title: Job title/position
            job_posting_text: Full job posting text
            original_resume_text: Original resume text

        Returns:
            Application ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO applications
            (company_name, job_title, job_posting_text, original_resume_text)
            VALUES (?, ?, ?, ?)
        """,
            (company_name, job_title, job_posting_text, original_resume_text),
        )

        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            msg = "Failed to retrieve lastrowid after application insert."
            raise RuntimeError(msg)
        return last_row

    def update_application(self, application_id: int, **kwargs):
        """Update application record with new data.

        Args:
            application_id: Application ID
            **kwargs: Fields to update
        """
        # Build UPDATE query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        if not fields:
            return

        values.append(application_id)
        query = f"""
            UPDATE applications
            SET {", ".join(fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

    def save_agent_output(
        self,
        application_id: int,
        agent_number: int,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Save agent execution output.

        Args:
            application_id: Application ID
            agent_number: Agent number (1, 2, or 3)
            agent_name: Name of agent
            input_data: Input data for agent
            output_data: Output data from agent
            cost: API cost
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO agent_outputs
            (application_id, agent_number, agent_name, input_data, output_data,
             cost, input_tokens, output_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                application_id,
                agent_number,
                agent_name,
                json.dumps(input_data),
                json.dumps(output_data),
                cost,
                input_tokens,
                output_tokens,
            ),
        )

        self.conn.commit()

    def save_validation_scores(
        self,
        application_id: int,
        scores: Dict[str, float],
        red_flags: List[str],
        recommendations: List[str],
    ):
        """Save validation scores and feedback.

        Args:
            application_id: Application ID
            scores: Dictionary of score dimensions
            red_flags: List of red flags
            recommendations: List of recommendations
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO validation_scores
            (application_id, requirements_match, ats_optimization, cultural_fit,
             presentation_quality, competitive_positioning, overall_score,
             red_flags, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                application_id,
                scores.get("requirements_match", 0),
                scores.get("ats_optimization", 0),
                scores.get("cultural_fit", 0),
                scores.get("presentation_quality", 0),
                scores.get("competitive_positioning", 0),
                scores.get("overall_score", 0),
                json.dumps(red_flags),
                json.dumps(recommendations),
            ),
        )

        self.conn.commit()

    def get_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID.

        Args:
            application_id: Application ID

        Returns:
            Application record as dictionary
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_all_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all applications ordered by most recent.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of application records
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, company_name, job_title, created_at, updated_at,
                   status, total_cost
            FROM applications
            ORDER BY updated_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def delete_application(self, application_id: int) -> None:
        """Delete an application and all related records.

        Args:
            application_id: ID of the application to delete
        """
        cursor = self.conn.cursor()
        # Delete dependent rows first
        cursor.execute(
            "DELETE FROM validation_scores WHERE application_id = ?",
            (application_id,),
        )
        cursor.execute(
            "DELETE FROM agent_outputs WHERE application_id = ?",
            (application_id,),
        )
        # Delete the application itself
        cursor.execute(
            "DELETE FROM applications WHERE id = ?",
            (application_id,),
        )
        self.conn.commit()

    def get_agent_outputs(self, application_id: int) -> List[Dict[str, Any]]:
        """Get all agent outputs for an application.

        Args:
            application_id: Application ID

        Returns:
            List of agent output records
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM agent_outputs
            WHERE application_id = ?
            ORDER BY agent_number
        """,
            (application_id,),
        )

        rows = cursor.fetchall()
        outputs = []
        for row in rows:
            output = dict(row)
            output["input_data"] = json.loads(output["input_data"])
            output["output_data"] = json.loads(output["output_data"])
            outputs.append(output)

        return outputs

    def get_validation_scores(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get validation scores for an application.

        Args:
            application_id: Application ID

        Returns:
            Validation scores record
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM validation_scores
            WHERE application_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """,
            (application_id,),
        )

        row = cursor.fetchone()
        if row:
            scores = dict(row)
            scores["red_flags"] = json.loads(scores["red_flags"])
            scores["recommendations"] = json.loads(scores["recommendations"])
            return scores
        return None

    def get_total_spent(self) -> float:
        """Get total amount spent across all applications.

        Returns:
            Total cost in USD
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(total_cost) as total FROM applications")
        result = cursor.fetchone()
        return result["total"] if result["total"] else 0.0

    def close(self):
        """Close database connection."""
        self.conn.close()
