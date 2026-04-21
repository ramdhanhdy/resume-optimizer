"""Database layer for application tracking and persistence."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


_UNSET = object()


class ApplicationDatabase:
    """SQLite database for tracking job applications."""

    def __init__(self, db_path: str = "./data/applications.db", user_id: str = "local"):
        """Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.user_id = user_id
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def for_user(self, user_id: Optional[str]) -> "ApplicationDatabase":
        """Return a lightweight user-scoped view over the same SQLite connection."""
        scoped = ApplicationDatabase.__new__(ApplicationDatabase)
        scoped.db_path = self.db_path
        scoped.conn = self.conn
        scoped.user_id = user_id or "local"
        return scoped

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
                job_url TEXT,
                job_posting_text TEXT,
                original_resume_text TEXT,
                optimized_resume_text TEXT,
                model_used TEXT,
                total_cost REAL DEFAULT 0.0,
                status TEXT DEFAULT 'in_progress',
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_reviews (
                application_id INTEGER PRIMARY KEY,
                plain_text TEXT NOT NULL,
                markdown TEXT NOT NULL,
                filename TEXT NOT NULL,
                summary_points TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_application_reviews_created_at ON application_reviews(created_at DESC)"
        )

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
        # Note: linkedin_url and github_username columns are added via migration 004
        # for existing databases. New databases get them here.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                linkedin_url TEXT,      -- LinkedIn URL for cache lookup
                github_username TEXT,   -- GitHub username for cache lookup
                sources TEXT,           -- JSON array of sources (e.g., URLs, github:username)
                profile_text TEXT,      -- raw aggregated text
                profile_index TEXT      -- agent-produced index (JSON/text)
            )
            """
        )
        
        # Note: Indexes for linkedin_url/github_username are created in migration 004
        # to handle existing databases that don't have these columns yet

        # Run metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS run_metadata (
                job_id TEXT PRIMARY KEY,
                client_id TEXT,
                status TEXT DEFAULT 'pending',
                application_id INTEGER,
                last_event_id INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
            """
        )

        # Run events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                type TEXT NOT NULL,
                payload TEXT,
                ts INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, seq),
                FOREIGN KEY (job_id) REFERENCES run_metadata(job_id)
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_events_job_seq ON run_events(job_id, seq)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_metadata_client ON run_metadata(client_id)")

        # Saved resumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'local',
                label TEXT NOT NULL,
                filename TEXT,
                resume_text TEXT NOT NULL,
                content_hash TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'local' UNIQUE,
                default_linkedin_url TEXT,
                default_github_username TEXT,
                default_resume_id INTEGER REFERENCES saved_resumes(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self._ensure_user_data_schema(cursor)

        self.conn.commit()
        self._run_migrations()

    def _ensure_user_data_schema(self, cursor) -> None:
        """Bring saved resume/preferences tables up to the current user-scoped schema."""
        cursor.execute("PRAGMA table_info(saved_resumes)")
        saved_resume_columns = {row["name"] for row in cursor.fetchall()}
        if "user_id" not in saved_resume_columns:
            cursor.execute("ALTER TABLE saved_resumes ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local'")
        if "content_hash" not in saved_resume_columns:
            cursor.execute("ALTER TABLE saved_resumes ADD COLUMN content_hash TEXT")
        if "is_default" not in saved_resume_columns:
            cursor.execute("ALTER TABLE saved_resumes ADD COLUMN is_default INTEGER DEFAULT 0")

        cursor.execute("PRAGMA table_info(user_preferences)")
        preference_columns = {row["name"] for row in cursor.fetchall()}
        if "user_id" not in preference_columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local'")
        if "default_linkedin_url" not in preference_columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN default_linkedin_url TEXT")
        if "default_github_username" not in preference_columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN default_github_username TEXT")
        if "default_resume_id" not in preference_columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN default_resume_id INTEGER REFERENCES saved_resumes(id) ON DELETE SET NULL")

        # Existing pre-user-scope databases can contain multiple rows that all
        # receive the default local user_id. Keep the newest preference row so
        # ON CONFLICT(user_id) remains valid for future upserts.
        cursor.execute("""
            DELETE FROM user_preferences
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM user_preferences
                GROUP BY user_id
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_resumes_user ON saved_resumes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_resumes_user_default ON saved_resumes(user_id, is_default)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_resumes_user_hash ON saved_resumes(user_id, content_hash) WHERE content_hash IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id)")

    def _run_migrations(self):
        """Run database migrations."""
        cursor = self.conn.cursor()

        # Check if migrations table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration 002: Error recovery tables
        cursor.execute("SELECT COUNT(*) as count FROM migrations WHERE migration_name = '002_add_error_recovery'")
        if cursor.fetchone()['count'] == 0:
            migration_path = Path(__file__).parent / 'migrations' / '002_add_error_recovery.sql'
            if migration_path.exists():
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                cursor.executescript(migration_sql)
                cursor.execute("INSERT INTO migrations (migration_name) VALUES ('002_add_error_recovery')")
                self.conn.commit()

        # Migration 003: Add job_url column
        cursor.execute("SELECT COUNT(*) as count FROM migrations WHERE migration_name = '003_add_job_url'")
        if cursor.fetchone()['count'] == 0:
            # Check if column already exists
            cursor.execute("PRAGMA table_info(applications)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'job_url' not in columns:
                cursor.execute("ALTER TABLE applications ADD COLUMN job_url TEXT")
            cursor.execute("INSERT INTO migrations (migration_name) VALUES ('003_add_job_url')")
            self.conn.commit()

        # Migration 004: Add linkedin_url and github_username to profiles
        cursor.execute("SELECT 1 FROM migrations WHERE migration_name = '004_add_profile_cache_columns'")
        if cursor.fetchone() is None:
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'linkedin_url' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN linkedin_url TEXT")
            if 'github_username' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN github_username TEXT")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_linkedin ON profiles(linkedin_url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_github ON profiles(github_username)")
            cursor.execute("INSERT INTO migrations (migration_name) VALUES ('004_add_profile_cache_columns')")
            self.conn.commit()

        # Migration 005: Add saved_resumes and user_preferences tables
        cursor.execute("SELECT 1 FROM migrations WHERE migration_name = '005_user_preferences_and_resumes'")
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'local',
                    label TEXT NOT NULL,
                    filename TEXT,
                    resume_text TEXT NOT NULL,
                    content_hash TEXT,
                    is_default INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'local' UNIQUE,
                    default_linkedin_url TEXT,
                    default_github_username TEXT,
                    default_resume_id INTEGER REFERENCES saved_resumes(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._ensure_user_data_schema(cursor)
            cursor.execute("INSERT INTO migrations (migration_name) VALUES ('005_user_preferences_and_resumes')")
            self.conn.commit()

        # Migration 006: Add canonical application reviews
        cursor.execute("SELECT 1 FROM migrations WHERE migration_name = '006_add_application_reviews'")
        if cursor.fetchone() is None:
            migration_path = Path(__file__).parent / 'migrations' / '006_add_application_reviews.sql'
            if migration_path.exists():
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                cursor.executescript(migration_sql)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS application_reviews (
                        application_id INTEGER PRIMARY KEY,
                        plain_text TEXT NOT NULL,
                        markdown TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        summary_points TEXT NOT NULL DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_application_reviews_created_at ON application_reviews(created_at DESC)"
                )
            cursor.execute("INSERT INTO migrations (migration_name) VALUES ('006_add_application_reviews')")
            self.conn.commit()

        self._ensure_user_data_schema(cursor)
        self.conn.commit()

    # --- Profiles API ---
    def save_profile(
        self,
        *,
        sources: list[str],
        profile_text: str,
        profile_index: str,
        linkedin_url: Optional[str] = None,
        github_username: Optional[str] = None,
    ) -> int:
        """Persist a new profile snapshot.

        Args:
            sources: List of source identifiers
            profile_text: Raw profile text
            profile_index: Agent-produced index
            linkedin_url: LinkedIn URL for cache lookup
            github_username: GitHub username for cache lookup

        Returns the profile row ID.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO profiles (sources, profile_text, profile_index, linkedin_url, github_username)
            VALUES (?, ?, ?, ?, ?)
            """,
            (json.dumps(list(sources) if sources else []), profile_text, profile_index, linkedin_url, github_username),
        )
        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            msg = "Failed to retrieve lastrowid after profile insert."
            raise RuntimeError(msg)
        return int(last_row)

    def get_cached_profile(
        self,
        *,
        linkedin_url: Optional[str] = None,
        github_username: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached profile by LinkedIn URL or GitHub username.
        
        Returns the most recent profile matching the given identifiers.
        """
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if linkedin_url:
            conditions.append("linkedin_url = ?")
            params.append(linkedin_url)
        if github_username:
            conditions.append("github_username = ?")
            params.append(github_username)
        
        if not conditions:
            return None
        
        # Use OR to match any of the provided identifiers
        where_clause = " OR ".join(conditions)
        cursor.execute(
            f"""
            SELECT * FROM profiles
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            params
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
        job_url: Optional[str] = None,
    ) -> int:
        """Create a new application record.

        Args:
            company_name: Name of company
            job_title: Job title/position
            job_posting_text: Full job posting text
            original_resume_text: Original resume text
            job_url: Optional URL of the job posting

        Returns:
            Application ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO applications
            (company_name, job_title, job_url, job_posting_text, original_resume_text)
            VALUES (?, ?, ?, ?, ?)
        """,
            (company_name, job_title, job_url, job_posting_text, original_resume_text),
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

    def save_application_review(
        self,
        *,
        application_id: int,
        plain_text: str,
        markdown: str,
        filename: str,
        summary_points: List[str],
    ) -> None:
        """Insert or update the canonical review document for an application."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO application_reviews (application_id, plain_text, markdown, filename, summary_points)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(application_id) DO UPDATE SET
                plain_text = excluded.plain_text,
                markdown = excluded.markdown,
                filename = excluded.filename,
                summary_points = excluded.summary_points,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                application_id,
                plain_text,
                markdown,
                filename,
                json.dumps(summary_points or []),
            ),
        )
        self.conn.commit()

    def get_application_review(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get the canonical review document for an application."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                ar.application_id,
                ar.plain_text,
                ar.markdown,
                ar.filename,
                ar.summary_points,
                ar.created_at,
                ar.updated_at,
                a.status
            FROM application_reviews ar
            JOIN applications a ON a.id = ar.application_id
            WHERE ar.application_id = ?
            """,
            (application_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        review = dict(row)
        review["summary_points"] = json.loads(review.get("summary_points") or "[]")
        return review

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
            "DELETE FROM application_reviews WHERE application_id = ?",
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

    # --- Recovery Sessions API ---
    def create_recovery_session(
        self,
        session_id: str,
        form_data: Dict[str, Any],
        file_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Create a new recovery session.

        Args:
            session_id: Unique session ID
            form_data: User form data (job posting, etc.)
            file_metadata: File metadata (filename, size, etc.)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Recovery session ID
        """
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(days=7)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO recovery_sessions
            (session_id, form_data, file_metadata, status, completed_agents,
             ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                json.dumps(form_data),
                json.dumps(file_metadata) if file_metadata else None,
                'pending',
                json.dumps([]),
                ip_address,
                user_agent,
                expires_at,
            ),
        )

        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            raise RuntimeError("Failed to retrieve lastrowid after recovery session insert.")
        return last_row

    def get_recovery_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery session by session ID.

        Args:
            session_id: Session ID

        Returns:
            Recovery session record
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM recovery_sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()

        if row:
            session = dict(row)
            session['form_data'] = json.loads(session['form_data'])
            if session.get('file_metadata'):
                session['file_metadata'] = json.loads(session['file_metadata'])
            if session.get('completed_agents'):
                session['completed_agents'] = json.loads(session['completed_agents'])
            return session
        return None

    def update_recovery_session(
        self,
        session_id: str,
        **kwargs
    ) -> None:
        """Update recovery session.

        Args:
            session_id: Session ID
            **kwargs: Fields to update
        """
        # Convert complex fields to JSON
        for key in ['completed_agents', 'form_data', 'file_metadata']:
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = json.dumps(kwargs[key])

        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        if not fields:
            return

        values.append(session_id)
        query = f"""
            UPDATE recovery_sessions
            SET {", ".join(fields)}
            WHERE session_id = ?
        """

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

    def save_agent_checkpoint(
        self,
        session_id: str,
        agent_index: int,
        agent_name: str,
        agent_output: Dict[str, Any],
        execution_time_ms: Optional[int] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
    ) -> int:
        """Save agent checkpoint.

        Args:
            session_id: Session ID
            agent_index: Agent index (0-4)
            agent_name: Agent name
            agent_output: Agent output data
            execution_time_ms: Execution time in milliseconds
            model_used: Model used
            tokens_used: Tokens used
            cost_usd: Cost in USD

        Returns:
            Checkpoint ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO agent_checkpoints
            (session_id, agent_index, agent_name, agent_output,
             execution_time_ms, model_used, tokens_used, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                agent_index,
                agent_name,
                json.dumps(agent_output),
                execution_time_ms,
                model_used,
                tokens_used,
                cost_usd,
            ),
        )

        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            raise RuntimeError("Failed to retrieve lastrowid after checkpoint insert.")
        return last_row

    def get_agent_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all agent checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint records
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM agent_checkpoints
            WHERE session_id = ?
            ORDER BY agent_index
        """,
            (session_id,)
        )

        rows = cursor.fetchall()
        checkpoints = []
        for row in rows:
            checkpoint = dict(row)
            checkpoint['agent_output'] = json.loads(checkpoint['agent_output'])
            checkpoints.append(checkpoint)

        return checkpoints

    def log_error(
        self,
        error_id: str,
        error_type: str,
        error_category: str,
        error_message: str,
        session_id: Optional[str] = None,
        error_stacktrace: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Log an error.

        Args:
            error_id: Unique error ID
            error_type: Error type
            error_category: Error category (TRANSIENT, RECOVERABLE, PERMANENT)
            error_message: Error message
            session_id: Associated session ID
            error_stacktrace: Full stack trace
            request_path: Request path
            request_method: Request method
            user_agent: User agent
            ip_address: IP address
            additional_context: Additional context data

        Returns:
            Error log ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO error_logs
            (error_id, session_id, error_type, error_category, error_message,
             error_stacktrace, request_path, request_method, user_agent,
             ip_address, additional_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                error_id,
                session_id,
                error_type,
                error_category,
                error_message,
                error_stacktrace,
                request_path,
                request_method,
                user_agent,
                ip_address,
                json.dumps(additional_context) if additional_context else None,
            ),
        )

        self.conn.commit()
        last_row = cursor.lastrowid
        if last_row is None:
            raise RuntimeError("Failed to retrieve lastrowid after error log insert.")
        return last_row

    def cleanup_expired_sessions(self) -> int:
        """Delete expired recovery sessions.

        Returns:
            Number of sessions deleted
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM recovery_sessions
            WHERE expires_at < CURRENT_TIMESTAMP
        """
        )
        self.conn.commit()
        return cursor.rowcount

    # --- Run metadata & streaming state ---
    def create_run_metadata(self, job_id: str, client_id: str, status: str = "pending") -> None:
        """Insert or update run metadata for a job."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO run_metadata (job_id, client_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                client_id = excluded.client_id,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (job_id, client_id, status),
        )
        self.conn.commit()

    def update_run_metadata(
        self,
        job_id: str,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        last_event_id: Optional[int] = None,
    ) -> None:
        """Update run metadata fields."""
        fields = []
        params = []

        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if application_id is not None:
            fields.append("application_id = ?")
            params.append(application_id)
        if last_event_id is not None:
            fields.append("last_event_id = ?")
            params.append(last_event_id)

        if not fields:
            return

        fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE run_metadata SET {', '.join(fields)} WHERE job_id = ?"
        params.append(job_id)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()

    def record_run_event(self, job_id: str, seq: int, event_dict: Dict[str, Any]) -> None:
        """Persist a streaming event for a job."""
        cursor = self.conn.cursor()
        payload = json.dumps(event_dict)
        cursor.execute(
            """
            INSERT INTO run_events (job_id, seq, type, payload, ts)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(job_id, seq) DO UPDATE SET
                type = excluded.type,
                payload = excluded.payload,
                ts = excluded.ts
            """,
            (job_id, seq, event_dict.get("type"), payload, event_dict.get("ts")),
        )
        self.conn.commit()
        self.update_run_metadata(job_id, last_event_id=seq)

    def get_run_events(
        self,
        job_id: str,
        after_seq: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Fetch run events for a job."""
        cursor = self.conn.cursor()
        if after_seq is None:
            cursor.execute(
                """
                SELECT seq, payload
                FROM run_events
                WHERE job_id = ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (job_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT seq, payload
                FROM run_events
                WHERE job_id = ? AND seq > ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (job_id, after_seq, limit),
            )

        rows = cursor.fetchall()
        events = []
        for row in rows:
            payload = json.loads(row["payload"]) if row["payload"] else {}
            payload["event_id"] = row["seq"]
            events.append(payload)
        return events

    def get_last_run_event_seq(self, job_id: str) -> Optional[int]:
        """Return the last recorded event sequence for a job."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT seq FROM run_events
            WHERE job_id = ?
            ORDER BY seq DESC
            LIMIT 1
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return row["seq"]

    def get_run_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch run metadata for a job."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM run_metadata
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)

    def count_runs_for_client(self, client_id: str) -> int:
        """Count the number of runs associated with a client ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM run_metadata
            WHERE client_id = ?
            """,
            (client_id,),
        )
        result = cursor.fetchone()
        return int(result["count"]) if result else 0

    def purge_run_events(self, job_id: str) -> None:
        """Delete persisted events for a job."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM run_events WHERE job_id = ?", (job_id,))
        self.conn.commit()

    # --- Saved Resumes API ---

    def _upsert_preferences_with_cursor(
        self,
        cursor,
        *,
        default_linkedin_url: Any = _UNSET,
        default_github_username: Any = _UNSET,
        default_resume_id: Any = _UNSET,
    ) -> None:
        fields = {"user_id": self.user_id}
        if default_linkedin_url is not _UNSET:
            fields["default_linkedin_url"] = default_linkedin_url
        if default_github_username is not _UNSET:
            fields["default_github_username"] = default_github_username
        if default_resume_id is not _UNSET:
            fields["default_resume_id"] = default_resume_id

        columns = list(fields.keys())
        placeholders = ", ".join(["?"] * len(columns))
        update_columns = [col for col in columns if col != "user_id"]
        if update_columns:
            update_clause = ", ".join([f"{col} = excluded.{col}" for col in update_columns])
            update_clause += ", updated_at = CURRENT_TIMESTAMP"
        else:
            update_clause = "updated_at = CURRENT_TIMESTAMP"

        cursor.execute(
            f"""
            INSERT INTO user_preferences ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(user_id) DO UPDATE SET {update_clause}
            """,
            [fields[col] for col in columns],
        )

    def save_resume(
        self,
        *,
        label: str,
        resume_text: str,
        filename: Optional[str] = None,
        content_hash: Optional[str] = None,
        is_default: bool = False,
    ) -> int:
        """Save a resume for later reuse.

        Returns the saved_resume row ID.
        """
        cursor = self.conn.cursor()

        # If setting as default, clear existing defaults first
        if is_default:
            cursor.execute(
                "UPDATE saved_resumes SET is_default = 0 WHERE user_id = ? AND is_default = 1",
                (self.user_id,),
            )

        cursor.execute(
            """
            INSERT INTO saved_resumes (user_id, label, filename, resume_text, content_hash, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.user_id, label, filename, resume_text, content_hash, 1 if is_default else 0),
        )
        last_row = cursor.lastrowid
        if last_row is None:
            raise RuntimeError("Failed to retrieve lastrowid after saved_resume insert.")
        resume_id = int(last_row)
        if is_default:
            self._upsert_preferences_with_cursor(
                cursor,
                default_resume_id=resume_id,
            )
        self.conn.commit()
        return resume_id

    def list_saved_resumes(self) -> List[Dict[str, Any]]:
        """List all saved resumes for the current user, most recent first."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, label, filename, content_hash, is_default, created_at, updated_at
            FROM saved_resumes
            WHERE user_id = ?
            ORDER BY is_default DESC, created_at DESC
            """,
            (self.user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_saved_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Get a saved resume by ID (includes full text)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM saved_resumes WHERE id = ? AND user_id = ?",
            (resume_id, self.user_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_resume_by_content_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get a saved resume by content hash for the current user."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM saved_resumes WHERE user_id = ? AND content_hash = ?",
            (self.user_id, content_hash),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_default_resume(self) -> Optional[Dict[str, Any]]:
        """Get the user's default saved resume."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM saved_resumes WHERE user_id = ? AND is_default = 1 LIMIT 1",
            (self.user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_saved_resume(self, resume_id: int) -> bool:
        """Delete a saved resume. Returns True if deleted."""
        cursor = self.conn.cursor()
        # Clear preference reference if this was the default
        cursor.execute(
            "UPDATE user_preferences SET default_resume_id = NULL WHERE user_id = ? AND default_resume_id = ?",
            (self.user_id, resume_id),
        )
        cursor.execute(
            "DELETE FROM saved_resumes WHERE id = ? AND user_id = ?",
            (resume_id, self.user_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def set_default_resume(self, resume_id: int) -> bool:
        """Set a resume as the default, clearing any existing default."""
        cursor = self.conn.cursor()
        # Verify resume exists
        cursor.execute(
            "SELECT id FROM saved_resumes WHERE id = ? AND user_id = ?",
            (resume_id, self.user_id),
        )
        if not cursor.fetchone():
            return False
        # Clear existing defaults
        cursor.execute(
            "UPDATE saved_resumes SET is_default = 0 WHERE user_id = ? AND is_default = 1",
            (self.user_id,),
        )
        # Set new default
        cursor.execute(
            "UPDATE saved_resumes SET is_default = 1 WHERE id = ? AND user_id = ?",
            (resume_id, self.user_id),
        )
        # Update preferences
        self._upsert_preferences_with_cursor(cursor, default_resume_id=resume_id)
        self.conn.commit()
        return True

    # --- User Preferences API ---

    def get_preferences(self) -> Optional[Dict[str, Any]]:
        """Get user preferences. Returns None if no preferences set."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM user_preferences WHERE user_id = ? LIMIT 1",
            (self.user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        prefs = dict(row)
        default_resume_id = prefs.get("default_resume_id")
        prefs["default_resume"] = (
            self.get_saved_resume(default_resume_id)
            if default_resume_id is not None
            else None
        )
        return prefs

    def upsert_preferences(
        self,
        *,
        default_linkedin_url: Any = _UNSET,
        default_github_username: Any = _UNSET,
        default_resume_id: Any = _UNSET,
    ) -> Dict[str, Any]:
        """Insert or update user preferences. Returns the upserted row."""
        cursor = self.conn.cursor()
        self._upsert_preferences_with_cursor(
            cursor,
            default_linkedin_url=default_linkedin_url,
            default_github_username=default_github_username,
            default_resume_id=default_resume_id,
        )
        cursor.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        self.conn.commit()
        row = cursor.fetchone()
        return dict(row) if row else {}

    def close(self):
        """Close database connection."""
        self.conn.close()
