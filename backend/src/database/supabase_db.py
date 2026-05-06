"""Supabase PostgreSQL database adapter for application tracking.

This adapter implements the same interface as ApplicationDatabase (SQLite)
but uses Supabase PostgreSQL as the backend. It requires a user_id for
all operations to support multi-tenant isolation.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from supabase import create_client, Client


_UNSET = object()


class SupabaseDatabase:
    """Supabase PostgreSQL database for tracking job applications."""

    def __init__(self, user_id: str):
        """Initialize Supabase connection.

        Args:
            user_id: The authenticated user's ID (from Supabase Auth)
        """
        self.user_id = user_id
        
        supabase_url = os.getenv("SUPABASE_URL")
        
        # Prefer new secret key format (sb_secret_...), fall back to legacy service_role key
        supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url:
            raise ValueError("SUPABASE_URL must be set")
        if not supabase_key:
            raise ValueError(
                "SUPABASE_SECRET_KEY (preferred) or SUPABASE_SERVICE_ROLE_KEY (legacy) must be set. "
                "Get your secret key from Supabase Dashboard > Settings > API > Secret keys"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)

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
        # profile_index column is jsonb — ensure we store valid JSON
        # If it's already a dict/list, use as-is; if it's a string, try parsing
        # or wrap it as a JSON string value
        pi_value = profile_index
        if isinstance(profile_index, str):
            try:
                pi_value = json.loads(profile_index)
            except (json.JSONDecodeError, TypeError):
                # Raw text from agent — store as a JSON string
                pi_value = profile_index
        
        data = {
            "user_id": self.user_id,
            "sources": sources if sources else [],
            "profile_text": profile_text,
            "profile_index": pi_value,
        }
        if linkedin_url:
            data["linkedin_url"] = linkedin_url
        if github_username:
            data["github_username"] = github_username
            
        result = self.client.table("profiles").insert(data).execute()
        
        if not result.data:
            raise RuntimeError("Failed to insert profile")
        return result.data[0]["id"]

    def get_cached_profile(
        self,
        *,
        linkedin_url: Optional[str] = None,
        github_username: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached profile by LinkedIn URL or GitHub username.
        
        Returns the most recent profile matching the given identifiers for this user.
        """
        if not linkedin_url and not github_username:
            return None
        
        # Build query - check LinkedIn URL first, then GitHub
        query = self.client.table("profiles").select("*").eq("user_id", self.user_id)
        
        if linkedin_url:
            result = query.eq("linkedin_url", linkedin_url).order(
                "created_at", desc=True
            ).limit(1).execute()
            if result.data:
                rec = result.data[0]
                if isinstance(rec.get("sources"), str):
                    rec["sources"] = json.loads(rec["sources"])
                return rec
        
        if github_username:
            result = self.client.table("profiles").select("*").eq(
                "user_id", self.user_id
            ).eq("github_username", github_username).order(
                "created_at", desc=True
            ).limit(1).execute()
            if result.data:
                rec = result.data[0]
                if isinstance(rec.get("sources"), str):
                    rec["sources"] = json.loads(rec["sources"])
                return rec
        
        return None

    def get_latest_profile(self) -> Optional[Dict[str, Any]]:
        """Return the most recent saved profile for this user, if any."""
        result = self.client.table("profiles").select("*").eq(
            "user_id", self.user_id
        ).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            return None
        
        rec = result.data[0]
        # sources is already a list in PostgreSQL JSONB
        if isinstance(rec.get("sources"), str):
            rec["sources"] = json.loads(rec["sources"])
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
        result = self.client.table("applications").insert({
            "user_id": self.user_id,
            "company_name": company_name,
            "job_title": job_title,
            "job_url": job_url,
            "job_posting_text": job_posting_text,
            "original_resume_text": original_resume_text,
            "status": "processing",
        }).execute()
        
        if not result.data:
            raise RuntimeError("Failed to insert application")
        return result.data[0]["id"]

    def update_application(self, application_id: int, **kwargs):
        """Update application record with new data.

        Args:
            application_id: Application ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return
        
        # Map SQLite field names to Supabase field names
        field_mapping = {
            "total_cost": "total_cost_usd",
        }
        
        update_data = {}
        for key, value in kwargs.items():
            mapped_key = field_mapping.get(key, key)
            update_data[mapped_key] = value
        
        # Handle completed_at timestamp
        if kwargs.get("status") == "completed" and "completed_at" not in update_data:
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        self.client.table("applications").update(update_data).eq(
            "id", application_id
        ).eq("user_id", self.user_id).execute()

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
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        agent_step_id: Optional[int] = None,
    ):
        """Save agent execution output.

        Args:
            application_id: Application ID
            agent_number: Agent number (1-5)
            agent_name: Name of agent
            input_data: Input data for agent
            output_data: Output data from agent
            cost: API cost in USD
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_provider: Model provider (e.g., "gemini", "openrouter")
            model_name: Model name (e.g., "gemini-2.5-flash")
            execution_time_ms: Execution time in milliseconds
            agent_step_id: FK to agent_steps.id for provenance linkage (nullable).
        """
        # Use upsert to handle re-runs of the same agent
        self.client.table("agent_outputs").upsert({
            "application_id": application_id,
            "user_id": self.user_id,
            "agent_number": agent_number,
            "agent_name": agent_name,
            "input_data": input_data,
            "output_data": output_data,
            "cost_usd": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_provider": model_provider,
            "model_name": model_name,
            "execution_time_ms": execution_time_ms,
            "agent_step_id": agent_step_id,
        }, on_conflict="application_id,agent_number").execute()
        
        # Update application totals
        self._update_application_totals(application_id)

    def _update_application_totals(self, application_id: int):
        """Update denormalized totals on application from agent_outputs."""
        result = self.client.table("agent_outputs").select(
            "cost_usd, input_tokens, output_tokens"
        ).eq("application_id", application_id).execute()
        
        if result.data:
            total_cost = sum(r.get("cost_usd", 0) or 0 for r in result.data)
            total_input = sum(r.get("input_tokens", 0) or 0 for r in result.data)
            total_output = sum(r.get("output_tokens", 0) or 0 for r in result.data)
            
            self.client.table("applications").update({
                "total_cost_usd": total_cost,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
            }).eq("id", application_id).execute()

    def save_validation_scores(
        self,
        application_id: int,
        scores: Dict[str, float],
        red_flags: List[str],
        recommendations: List[str],
        model_name: Optional[str] = None,
    ):
        """Save validation scores and feedback.

        Args:
            application_id: Application ID
            scores: Dictionary of score dimensions
            red_flags: List of red flags
            recommendations: List of recommendations
            model_name: Model used for validation
        """
        overall_score = scores.get("overall_score", 0)
        
        self.client.table("validation_scores").insert({
            "application_id": application_id,
            "user_id": self.user_id,
            "requirements_match": scores.get("requirements_match", 0),
            "ats_optimization": scores.get("ats_optimization", 0),
            "cultural_fit": scores.get("cultural_fit", 0),
            "presentation_quality": scores.get("presentation_quality", 0),
            "competitive_positioning": scores.get("competitive_positioning", 0),
            "overall_score": overall_score,
            "red_flags": red_flags,
            "recommendations": recommendations,
            "model_name": model_name,
        }).execute()
        
        # Update denormalized overall_score on application
        self.client.table("applications").update({
            "overall_score": overall_score,
        }).eq("id", application_id).execute()

    def get_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID.

        Args:
            application_id: Application ID

        Returns:
            Application record as dictionary
        """
        result = self.client.table("applications").select("*").eq(
            "id", application_id
        ).eq("user_id", self.user_id).is_("deleted_at", "null").execute()
        
        if result.data:
            return self._map_application_to_sqlite_format(result.data[0])
        return None

    def save_application_review(
        self,
        *,
        application_id: int,
        plain_text: str,
        markdown: str,
        filename: str,
        summary_points: List[str],
        current_artifact_id: Optional[int] = None,
    ) -> None:
        """Insert or update the canonical review document for an application."""
        application_check = self.client.table("applications").select("id").eq(
            "id", application_id
        ).eq("user_id", self.user_id).is_("deleted_at", "null").limit(1).execute()
        if not application_check.data:
            raise ValueError("Application not found or not owned by the current user.")

        upsert_data: Dict[str, Any] = {
            "application_id": application_id,
            "user_id": self.user_id,
            "plain_text": plain_text,
            "markdown": markdown,
            "filename": filename,
            "summary_points": summary_points or [],
        }
        if current_artifact_id is not None:
            upsert_data["current_artifact_id"] = current_artifact_id
        self.client.table("application_reviews").upsert(
            upsert_data,
            on_conflict="application_id",
        ).execute()

    def get_application_review(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get the canonical review document for an application."""
        result = self.client.table("application_reviews").select("*").eq(
            "application_id", application_id
        ).eq("user_id", self.user_id).limit(1).execute()

        if not result.data:
            return None

        review = result.data[0]
        app = self.client.table("applications").select("status").eq(
            "id", application_id
        ).eq("user_id", self.user_id).is_("deleted_at", "null").limit(1).execute()
        if not app.data:
            return None

        review["status"] = app.data[0]["status"]
        summary_points = review.get("summary_points")
        if isinstance(summary_points, str):
            try:
                summary_points = json.loads(summary_points)
            except (TypeError, json.JSONDecodeError):
                summary_points = []
        if summary_points is None:
            summary_points = []
        elif not isinstance(summary_points, list):
            summary_points = list(summary_points) if isinstance(summary_points, (tuple, set)) else []
        review["summary_points"] = summary_points
        return review

    def get_latest_completed_application_with_review(self) -> Optional[Dict[str, Any]]:
        """Return the latest completed application review for this user, if any."""
        applications = self.client.table("applications").select(
            "id"
        ).eq("user_id", self.user_id).eq("status", "completed").is_(
            "deleted_at", "null"
        ).order("updated_at", desc=True).limit(25).execute()

        for application in applications.data or []:
            review = self.get_application_review(application["id"])
            if review:
                return review
        return None

    def _map_application_to_sqlite_format(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Map Supabase application fields to SQLite format for compatibility."""
        return {
            "id": app["id"],
            "created_at": app["created_at"],
            "updated_at": app["updated_at"],
            "company_name": app.get("company_name"),
            "job_title": app.get("job_title"),
            "job_url": app.get("job_url"),
            "job_posting_text": app.get("job_posting_text"),
            "original_resume_text": app.get("original_resume_text"),
            "optimized_resume_text": app.get("optimized_resume_text"),
            "model_used": app.get("model_used"),
            "total_cost": app.get("total_cost_usd", 0),
            "status": app.get("status"),
            "notes": None,  # Not in Supabase schema
        }

    def get_all_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all applications for this user ordered by most recent.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of application records
        """
        result = self.client.table("applications").select(
            "id, company_name, job_title, created_at, updated_at, status, total_cost_usd, overall_score"
        ).eq("user_id", self.user_id).is_(
            "deleted_at", "null"
        ).order("updated_at", desc=True).limit(limit).execute()
        
        return [
            {
                "id": r["id"],
                "company_name": r.get("company_name"),
                "job_title": r.get("job_title"),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "status": r.get("status"),
                "total_cost": r.get("total_cost_usd", 0),
                "overall_score": r.get("overall_score"),
            }
            for r in result.data
        ]

    def delete_application(self, application_id: int) -> None:
        """Soft delete an application.

        Args:
            application_id: ID of the application to delete
        """
        # Soft delete - just set deleted_at
        self.client.table("applications").update({
            "deleted_at": datetime.utcnow().isoformat(),
        }).eq("id", application_id).eq("user_id", self.user_id).execute()

    def get_agent_outputs(self, application_id: int) -> List[Dict[str, Any]]:
        """Get all agent outputs for an application.

        Args:
            application_id: Application ID

        Returns:
            List of agent output records
        """
        result = self.client.table("agent_outputs").select("*").eq(
            "application_id", application_id
        ).eq("user_id", self.user_id).order("agent_number").execute()
        
        outputs = []
        for row in result.data:
            output = {
                "id": row["id"],
                "application_id": row["application_id"],
                "agent_number": row["agent_number"],
                "agent_name": row["agent_name"],
                "input_data": row.get("input_data", {}),
                "output_data": row.get("output_data", {}),
                "cost": row.get("cost_usd", 0),
                "input_tokens": row.get("input_tokens", 0),
                "output_tokens": row.get("output_tokens", 0),
                "created_at": row["created_at"],
            }
            outputs.append(output)
        
        return outputs

    def get_validation_scores(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get validation scores for an application.

        Args:
            application_id: Application ID

        Returns:
            Validation scores record
        """
        result = self.client.table("validation_scores").select("*").eq(
            "application_id", application_id
        ).eq("user_id", self.user_id).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            return None
        
        row = result.data[0]
        return {
            "id": row["id"],
            "application_id": row["application_id"],
            "requirements_match": row.get("requirements_match"),
            "ats_optimization": row.get("ats_optimization"),
            "cultural_fit": row.get("cultural_fit"),
            "presentation_quality": row.get("presentation_quality"),
            "competitive_positioning": row.get("competitive_positioning"),
            "overall_score": row.get("overall_score"),
            "red_flags": row.get("red_flags", []),
            "recommendations": row.get("recommendations", []),
            "created_at": row["created_at"],
        }

    def get_total_spent(self) -> float:
        """Get total amount spent across all applications for this user.

        Returns:
            Total cost in USD
        """
        result = self.client.table("applications").select(
            "total_cost_usd"
        ).eq("user_id", self.user_id).is_("deleted_at", "null").execute()
        
        if not result.data:
            return 0.0
        
        return sum(r.get("total_cost_usd", 0) or 0 for r in result.data)

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
        expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        result = self.client.table("recovery_sessions").insert({
            "user_id": self.user_id,
            "session_id": session_id,
            "form_data": form_data,
            "file_metadata": file_metadata,
            "status": "pending",
            "completed_agents": [],
            "ip_address": ip_address,
            "user_agent": user_agent,
            "expires_at": expires_at,
        }).execute()
        
        if not result.data:
            raise RuntimeError("Failed to insert recovery session")
        return result.data[0]["id"]

    def get_recovery_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery session by session ID.

        Args:
            session_id: Session ID

        Returns:
            Recovery session record
        """
        result = self.client.table("recovery_sessions").select("*").eq(
            "session_id", session_id
        ).eq("user_id", self.user_id).execute()
        
        if not result.data:
            return None
        
        return result.data[0]

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
        if not kwargs:
            return
        
        self.client.table("recovery_sessions").update(kwargs).eq(
            "session_id", session_id
        ).eq("user_id", self.user_id).execute()

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
        result = self.client.table("agent_checkpoints").upsert({
            "user_id": self.user_id,
            "session_id": session_id,
            "agent_index": agent_index,
            "agent_name": agent_name,
            "agent_output": agent_output,
            "execution_time_ms": execution_time_ms,
            "model_used": model_used,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
        }, on_conflict="session_id,agent_index").execute()
        
        if not result.data:
            raise RuntimeError("Failed to insert checkpoint")
        return result.data[0]["id"]

    def get_agent_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all agent checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint records
        """
        result = self.client.table("agent_checkpoints").select("*").eq(
            "session_id", session_id
        ).eq("user_id", self.user_id).order("agent_index").execute()
        
        return result.data

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
        result = self.client.table("error_logs").insert({
            "user_id": self.user_id,
            "error_id": error_id,
            "session_id": session_id,
            "error_type": error_type,
            "error_category": error_category,
            "error_message": error_message,
            "error_stacktrace": error_stacktrace,
            "request_path": request_path,
            "request_method": request_method,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "additional_context": additional_context,
        }).execute()
        
        if not result.data:
            raise RuntimeError("Failed to insert error log")
        return result.data[0]["id"]

    def cleanup_expired_sessions(self) -> int:
        """Delete expired recovery sessions.

        Returns:
            Number of sessions deleted
        """
        result = self.client.table("recovery_sessions").delete().eq(
            "user_id", self.user_id
        ).lt("expires_at", datetime.utcnow().isoformat()).execute()
        
        return len(result.data) if result.data else 0

    # --- Run metadata & streaming state ---
    def create_run_metadata(self, job_id: str, client_id: str, status: str = "pending") -> None:
        """Insert or update run metadata for a job."""
        self.client.table("pipeline_runs").upsert({
            "user_id": self.user_id,
            "job_id": job_id,
            "client_id": client_id,
            "status": status,
        }, on_conflict="job_id").execute()

    def update_run_metadata(
        self,
        job_id: str,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        last_event_id: Optional[int] = None,
    ) -> None:
        """Update run metadata fields."""
        update_data = {}
        
        if status is not None:
            update_data["status"] = status
        if application_id is not None:
            update_data["application_id"] = application_id
        if last_event_id is not None:
            update_data["last_event_seq"] = last_event_id
        
        if not update_data:
            return
        
        self.client.table("pipeline_runs").update(update_data).eq(
            "job_id", job_id
        ).execute()

    def record_run_event(self, job_id: str, seq: int, event_dict: Dict[str, Any]) -> None:
        """Persist a streaming event for a job."""
        self.client.table("run_events").upsert({
            "user_id": self.user_id,
            "job_id": job_id,
            "seq": seq,
            "event_type": event_dict.get("type"),
            "payload": event_dict,
            "ts": event_dict.get("ts"),
        }, on_conflict="job_id,seq").execute()
        
        self.update_run_metadata(job_id, last_event_id=seq)

    def get_run_events(
        self,
        job_id: str,
        after_seq: Optional[int] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Fetch run events for a job."""
        query = self.client.table("run_events").select("seq, payload").eq(
            "job_id", job_id
        ).order("seq")
        
        if after_seq is not None:
            query = query.gt("seq", after_seq)
        
        result = query.limit(limit).execute()
        
        events = []
        for row in result.data:
            payload = row.get("payload", {})
            payload["event_id"] = row["seq"]
            events.append(payload)
        return events

    def get_last_run_event_seq(self, job_id: str) -> Optional[int]:
        """Return the last recorded event sequence for a job."""
        result = self.client.table("run_events").select("seq").eq(
            "job_id", job_id
        ).order("seq", desc=True).limit(1).execute()
        
        if not result.data:
            return None
        return result.data[0]["seq"]

    def get_run_metadata(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch run metadata for a job."""
        result = self.client.table("pipeline_runs").select("*").eq(
            "job_id", job_id
        ).execute()
        
        if not result.data:
            return None
        
        row = result.data[0]
        # Map to SQLite format for compatibility
        return {
            "job_id": row["job_id"],
            "client_id": row.get("client_id"),
            "status": row.get("status"),
            "application_id": row.get("application_id"),
            "last_event_id": row.get("last_event_seq"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def count_runs_for_client(self, client_id: str) -> int:
        """Count the number of runs associated with a client ID."""
        result = self.client.table("pipeline_runs").select(
            "id", count="exact"
        ).eq("client_id", client_id).execute()
        
        return result.count if result.count else 0

    def purge_run_events(self, job_id: str) -> None:
        """Delete persisted events for a job."""
        self.client.table("run_events").delete().eq("job_id", job_id).execute()

    # --- Saved Resumes API ---

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
        # If setting as default, clear existing defaults first
        if is_default:
            self.client.table("saved_resumes").update({"is_default": False}).eq(
                "user_id", self.user_id
            ).eq("is_default", True).execute()

        data = {
            "user_id": self.user_id,
            "label": label,
            "resume_text": resume_text,
            "is_default": is_default,
        }
        if filename:
            data["filename"] = filename
        if content_hash:
            data["content_hash"] = content_hash

        result = self.client.table("saved_resumes").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert saved resume")
        resume_id = result.data[0]["id"]
        if is_default:
            self.upsert_preferences(default_resume_id=resume_id)
        return resume_id

    def list_saved_resumes(self) -> List[Dict[str, Any]]:
        """List all saved resumes for this user (without full text), most recent first."""
        result = self.client.table("saved_resumes").select(
            "id, label, filename, content_hash, is_default, created_at, updated_at"
        ).eq("user_id", self.user_id).order("is_default", desc=True).order(
            "created_at", desc=True
        ).execute()

        return [
            {
                "id": r["id"],
                "label": r["label"],
                "filename": r.get("filename"),
                "content_hash": r.get("content_hash"),
                "is_default": r.get("is_default", False),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in result.data
        ]

    def get_saved_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Get a saved resume by ID (includes full text)."""
        result = self.client.table("saved_resumes").select("*").eq(
            "id", resume_id
        ).eq("user_id", self.user_id).execute()

        if not result.data:
            return None
        return result.data[0]

    def get_resume_by_content_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get a saved resume by content hash for this user."""
        result = self.client.table("saved_resumes").select("*").eq(
            "user_id", self.user_id
        ).eq("content_hash", content_hash).limit(1).execute()

        if not result.data:
            return None
        return result.data[0]

    def get_default_resume(self) -> Optional[Dict[str, Any]]:
        """Get the user's default saved resume."""
        result = self.client.table("saved_resumes").select("*").eq(
            "user_id", self.user_id
        ).eq("is_default", True).limit(1).execute()

        if not result.data:
            return None
        return result.data[0]

    def delete_saved_resume(self, resume_id: int) -> bool:
        """Delete a saved resume. Returns True if deleted."""
        # Clear preference reference if this was the default
        self.client.table("user_preferences").update({
            "default_resume_id": None,
        }).eq("user_id", self.user_id).eq("default_resume_id", resume_id).execute()

        result = self.client.table("saved_resumes").delete().eq(
            "id", resume_id
        ).eq("user_id", self.user_id).execute()

        return bool(result.data)

    def set_default_resume(self, resume_id: int) -> bool:
        """Set a resume as the default, clearing any existing default."""
        # Verify resume exists
        check = self.client.table("saved_resumes").select("id").eq(
            "id", resume_id
        ).eq("user_id", self.user_id).execute()
        if not check.data:
            return False

        # Clear existing defaults
        self.client.table("saved_resumes").update({"is_default": False}).eq(
            "user_id", self.user_id
        ).eq("is_default", True).execute()

        # Set new default
        self.client.table("saved_resumes").update({"is_default": True}).eq(
            "id", resume_id
        ).eq("user_id", self.user_id).execute()

        # Update preferences
        self.client.table("user_preferences").update({
            "default_resume_id": resume_id,
        }).eq("user_id", self.user_id).execute()

        return True

    # --- User Preferences API ---

    def get_preferences(self) -> Optional[Dict[str, Any]]:
        """Get user preferences. Returns None if no preferences set."""
        result = self.client.table("user_preferences").select("*").eq(
            "user_id", self.user_id
        ).execute()

        if not result.data:
            return None

        rec = result.data[0]
        # Join default resume info if available
        if rec.get("default_resume_id"):
            resume = self.get_saved_resume(rec["default_resume_id"])
            rec["default_resume"] = resume
        else:
            rec["default_resume"] = None

        return rec

    def upsert_preferences(
        self,
        *,
        default_linkedin_url: Any = _UNSET,
        default_github_username: Any = _UNSET,
        default_resume_id: Any = _UNSET,
    ) -> Dict[str, Any]:
        """Insert or update user preferences. Returns the upserted row."""
        data = {"user_id": self.user_id}
        if default_linkedin_url is not _UNSET:
            data["default_linkedin_url"] = default_linkedin_url
        if default_github_username is not _UNSET:
            data["default_github_username"] = default_github_username
        if default_resume_id is not _UNSET:
            data["default_resume_id"] = default_resume_id

        result = self.client.table("user_preferences").upsert(
            data, on_conflict="user_id"
        ).execute()

        if not result.data:
            raise RuntimeError("Failed to upsert user preferences")
        return result.data[0]

    # --- Provenance API ---

    def create_profile_snapshot(
        self,
        *,
        profile_index: Any,
        legacy_profile_id: Optional[int] = None,
        application_id: Optional[int] = None,
        pipeline_run_id: Optional[int] = None,
        source_fingerprint: Optional[str] = None,
        profile_text_hash: Optional[str] = None,
        builder_model: Optional[str] = None,
        prompt_name: Optional[str] = None,
        prompt_hash: Optional[str] = None,
    ) -> int:
        """Insert an immutable profile index snapshot.

        Args:
            profile_index: Agent-produced profile index (dict or JSON string).
            legacy_profile_id: Optional FK to profiles.id for cache compatibility.
            application_id: Optional FK to applications.id.
            pipeline_run_id: Optional FK to pipeline_runs.id.
            source_fingerprint: Hash of the raw input sources used to build the index.
            profile_text_hash: Hash of the raw profile text.
            builder_model: Model that produced the index.
            prompt_name: Prompt file used (e.g. 'profile_agent.md').
            prompt_hash: Hash of the prompt file content.

        Returns:
            profile_snapshots row ID.
        """
        pi_value = profile_index
        if isinstance(profile_index, str):
            try:
                pi_value = json.loads(profile_index)
            except (json.JSONDecodeError, TypeError):
                pi_value = profile_index

        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "profile_index": pi_value,
        }
        if legacy_profile_id is not None:
            data["legacy_profile_id"] = legacy_profile_id
        if application_id is not None:
            data["application_id"] = application_id
        if pipeline_run_id is not None:
            data["pipeline_run_id"] = pipeline_run_id
        if source_fingerprint is not None:
            data["source_fingerprint"] = source_fingerprint
        if profile_text_hash is not None:
            data["profile_text_hash"] = profile_text_hash
        if builder_model is not None:
            data["builder_model"] = builder_model
        if prompt_name is not None:
            data["prompt_name"] = prompt_name
        if prompt_hash is not None:
            data["prompt_hash"] = prompt_hash

        result = self.client.table("profile_snapshots").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert profile_snapshot")
        return result.data[0]["id"]

    def save_evidence_item(
        self,
        *,
        source_type: str,
        application_id: Optional[int] = None,
        profile_snapshot_id: Optional[int] = None,
        source_uri: Optional[str] = None,
        source_label: Optional[str] = None,
        content_excerpt: Optional[str] = None,
        content_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Insert a first-class source evidence item.

        Args:
            source_type: One of 'resume_upload', 'additional_profile_text',
                'linkedin_profile', 'github_repo', 'github_readme',
                'job_posting', 'manual_note'.
            application_id: Optional FK to applications.id.
            profile_snapshot_id: Optional FK to profile_snapshots.id.
            source_uri: URL or path identifying the source.
            source_label: Human-readable label for the source.
            content_excerpt: Short text excerpt from the source.
            content_hash: Hash of the full source content.
            metadata: Arbitrary JSON metadata (repo stats, parser version, etc.).

        Returns:
            evidence_items row ID.
        """
        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "source_type": source_type,
        }
        if application_id is not None:
            data["application_id"] = application_id
        if profile_snapshot_id is not None:
            data["profile_snapshot_id"] = profile_snapshot_id
        if source_uri is not None:
            data["source_uri"] = source_uri
        if source_label is not None:
            data["source_label"] = source_label
        if content_excerpt is not None:
            data["content_excerpt"] = content_excerpt
        if content_hash is not None:
            data["content_hash"] = content_hash
        if metadata is not None:
            data["metadata"] = metadata

        result = self.client.table("evidence_items").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert evidence_item")
        return result.data[0]["id"]

    def save_agent_step(
        self,
        *,
        application_id: int,
        agent_number: int,
        agent_name: str,
        pipeline_run_id: Optional[int] = None,
        job_id: Optional[str] = None,
        attempt_number: int = 1,
        status: str = "completed",
        input_hash: Optional[str] = None,
        output_hash: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_name: Optional[str] = None,
        prompt_hash: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> int:
        """Insert an immutable agent execution step record.

        Always inserts a new row — no upsert — to preserve full attempt history.

        Args:
            application_id: FK to applications.id.
            agent_number: Agent number in the pipeline (0–5).
            agent_name: Human-readable agent name.
            pipeline_run_id: Optional FK to pipeline_runs.id.
            job_id: Optional job UUID matching pipeline_runs.job_id.
            attempt_number: Retry attempt number (default 1).
            status: One of 'queued','running','completed','failed','cancelled'.
            input_hash: Hash of input_data for dedup/comparison.
            output_hash: Hash of output_data for dedup/comparison.
            input_data: Agent input payload.
            output_data: Agent output payload.
            model_provider: e.g. 'gemini', 'openrouter'.
            model_name: e.g. 'gemini-2.5-flash'.
            prompt_name: Prompt file name.
            prompt_hash: Hash of the prompt file content.
            params: Model/agent configuration parameters.
            input_tokens: Tokens consumed by the prompt.
            output_tokens: Tokens produced by the completion.
            cost_usd: Estimated cost in USD.
            started_at: When the agent started execution.
            completed_at: When the agent finished execution.

        Returns:
            agent_steps row ID.
        """
        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "application_id": application_id,
            "agent_number": agent_number,
            "agent_name": agent_name,
            "attempt_number": attempt_number,
            "status": status,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "params": params or {},
        }
        if pipeline_run_id is not None:
            data["pipeline_run_id"] = pipeline_run_id
        if job_id is not None:
            data["job_id"] = job_id
        if input_hash is not None:
            data["input_hash"] = input_hash
        if output_hash is not None:
            data["output_hash"] = output_hash
        if input_data is not None:
            data["input_data"] = input_data
        if output_data is not None:
            data["output_data"] = output_data
        if model_provider is not None:
            data["model_provider"] = model_provider
        if model_name is not None:
            data["model_name"] = model_name
        if prompt_name is not None:
            data["prompt_name"] = prompt_name
        if prompt_hash is not None:
            data["prompt_hash"] = prompt_hash
        if started_at is not None:
            data["started_at"] = started_at.isoformat()
        if completed_at is not None:
            data["completed_at"] = completed_at.isoformat()

        result = self.client.table("agent_steps").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert agent_step")
        return result.data[0]["id"]

    def save_resume_artifact(
        self,
        *,
        application_id: int,
        artifact_type: str,
        content_hash: str,
        pipeline_run_id: Optional[int] = None,
        agent_step_id: Optional[int] = None,
        parent_artifact_id: Optional[int] = None,
        plain_text: Optional[str] = None,
        markdown: Optional[str] = None,
        html: Optional[str] = None,
        filename: Optional[str] = None,
        summary_points: Optional[List] = None,
        is_current: bool = True,
    ) -> int:
        """Insert an immutable resume or review artifact.

        If is_current is True, any prior artifacts for the same application_id
        and artifact_type are marked is_current=False before inserting.

        Args:
            application_id: FK to applications.id.
            artifact_type: One of 'optimized_resume','final_review','refinement','export'.
            content_hash: Hash of the artifact text content.
            pipeline_run_id: Optional FK to pipeline_runs.id.
            agent_step_id: Optional FK to agent_steps.id.
            parent_artifact_id: Optional FK to resume_artifacts.id (for refinements).
            plain_text: Plain-text representation of the artifact.
            markdown: Markdown representation.
            html: HTML representation.
            filename: Suggested download filename.
            summary_points: Optional list of summary bullet points.
            is_current: Mark as the current artifact for this application/type.

        Returns:
            resume_artifacts row ID.
        """
        if is_current:
            self.client.table("resume_artifacts").update(
                {"is_current": False}
            ).eq("application_id", application_id).eq(
                "artifact_type", artifact_type
            ).eq("user_id", self.user_id).eq("is_current", True).execute()

        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "application_id": application_id,
            "artifact_type": artifact_type,
            "content_hash": content_hash,
            "is_current": is_current,
            "summary_points": summary_points or [],
        }
        if pipeline_run_id is not None:
            data["pipeline_run_id"] = pipeline_run_id
        if agent_step_id is not None:
            data["agent_step_id"] = agent_step_id
        if parent_artifact_id is not None:
            data["parent_artifact_id"] = parent_artifact_id
        if plain_text is not None:
            data["plain_text"] = plain_text
        if markdown is not None:
            data["markdown"] = markdown
        if html is not None:
            data["html"] = html
        if filename is not None:
            data["filename"] = filename

        result = self.client.table("resume_artifacts").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert resume_artifact")
        return result.data[0]["id"]

    def save_validation_finding(
        self,
        *,
        application_id: int,
        finding_type: str,
        agent_step_id: Optional[int] = None,
        resume_artifact_id: Optional[int] = None,
        evidence_item_id: Optional[int] = None,
        claim: Optional[str] = None,
        verdict: Optional[str] = None,
        confidence: Optional[float] = None,
        explanation: Optional[str] = None,
    ) -> int:
        """Insert a first-class validation finding.

        Args:
            application_id: FK to applications.id.
            finding_type: One of 'red_flag','recommendation','strength',
                'claim_check','ats_check'.
            agent_step_id: Optional FK to agent_steps.id.
            resume_artifact_id: Optional FK to resume_artifacts.id.
            evidence_item_id: Optional FK to evidence_items.id.
            claim: The claim or text being validated.
            verdict: One of 'pass','fail','warning','unknown'.
            confidence: Confidence score 0–100.
            explanation: Human-readable explanation of the finding.

        Returns:
            validation_findings row ID.
        """
        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "application_id": application_id,
            "finding_type": finding_type,
        }
        if agent_step_id is not None:
            data["agent_step_id"] = agent_step_id
        if resume_artifact_id is not None:
            data["resume_artifact_id"] = resume_artifact_id
        if evidence_item_id is not None:
            data["evidence_item_id"] = evidence_item_id
        if claim is not None:
            data["claim"] = claim
        if verdict is not None:
            data["verdict"] = verdict
        if confidence is not None:
            data["confidence"] = confidence
        if explanation is not None:
            data["explanation"] = explanation

        result = self.client.table("validation_findings").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert validation_finding")
        return result.data[0]["id"]

    def save_model_invocation(
        self,
        *,
        provider: str,
        model_name: str,
        application_id: Optional[int] = None,
        pipeline_run_id: Optional[int] = None,
        agent_step_id: Optional[int] = None,
        prompt_name: Optional[str] = None,
        prompt_hash: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        pricing_version: Optional[str] = None,
        latency_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> int:
        """Insert a request-level model invocation record.

        Args:
            provider: Model provider name (e.g. 'gemini', 'openrouter').
            model_name: Model identifier (e.g. 'gemini-2.5-flash').
            application_id: Optional FK to applications.id.
            pipeline_run_id: Optional FK to pipeline_runs.id.
            agent_step_id: Optional FK to agent_steps.id.
            prompt_name: Prompt file name.
            prompt_hash: Hash of the prompt file content.
            params: Model parameters (temperature, max_tokens, etc.).
            input_tokens: Tokens consumed by the prompt.
            output_tokens: Tokens produced by the completion.
            cost_usd: Estimated cost in USD.
            pricing_version: Pricing table version used for cost calculation.
            latency_ms: Round-trip latency in milliseconds.
            status: One of 'success','error','cancelled'.
            error_message: Error detail if status is 'error'.

        Returns:
            model_invocations row ID.
        """
        data: Dict[str, Any] = {
            "user_id": self.user_id,
            "provider": provider,
            "model_name": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "status": status,
            "params": params or {},
        }
        if application_id is not None:
            data["application_id"] = application_id
        if pipeline_run_id is not None:
            data["pipeline_run_id"] = pipeline_run_id
        if agent_step_id is not None:
            data["agent_step_id"] = agent_step_id
        if prompt_name is not None:
            data["prompt_name"] = prompt_name
        if prompt_hash is not None:
            data["prompt_hash"] = prompt_hash
        if pricing_version is not None:
            data["pricing_version"] = pricing_version
        if latency_ms is not None:
            data["latency_ms"] = latency_ms
        if error_message is not None:
            data["error_message"] = error_message

        result = self.client.table("model_invocations").insert(data).execute()

        if not result.data:
            raise RuntimeError("Failed to insert model_invocation")
        return result.data[0]["id"]

    def link_profile_snapshot_to_application(
        self, snapshot_id: int, application_id: int
    ) -> None:
        """Back-fill application_id on a profile_snapshot created before app_id was known.

        Step 0 profile building runs before create_application(), so snapshots are
        initially written with application_id=None.  Call this once app_id is available.
        """
        self.client.table("profile_snapshots").update(
            {"application_id": application_id}
        ).eq("id", snapshot_id).eq("user_id", self.user_id).execute()

    def link_evidence_items_to_application(
        self, evidence_ids: List[int], application_id: int
    ) -> None:
        """Back-fill application_id on evidence_items created before app_id was known.

        Mirrors link_profile_snapshot_to_application for evidence rows.
        Each update is user-scoped (user_id guard) for safety.
        """
        for eid in evidence_ids:
            self.client.table("evidence_items").update(
                {"application_id": application_id}
            ).eq("id", eid).eq("user_id", self.user_id).execute()

    def close(self):
        """Close database connection (no-op for Supabase)."""
        pass


def get_database(user_id: Optional[str] = None):
    """Factory function to get the appropriate database instance.
    
    Args:
        user_id: User ID for Supabase. If None, returns SQLite database.
        
    Returns:
        Database instance (SupabaseDatabase or ApplicationDatabase)
    """
    use_supabase = os.getenv("USE_SUPABASE_DB", "false").lower() == "true"
    
    if use_supabase and user_id:
        return SupabaseDatabase(user_id)
    else:
        from .db import ApplicationDatabase
        return ApplicationDatabase(user_id=user_id or "local")
