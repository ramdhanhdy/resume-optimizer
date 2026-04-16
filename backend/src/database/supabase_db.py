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
        return result.data[0]["id"]

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
        default_linkedin_url: Optional[str] = None,
        default_github_username: Optional[str] = None,
        default_resume_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Insert or update user preferences. Returns the upserted row."""
        data = {"user_id": self.user_id}
        if default_linkedin_url is not None:
            data["default_linkedin_url"] = default_linkedin_url
        if default_github_username is not None:
            data["default_github_username"] = default_github_username
        if default_resume_id is not None:
            data["default_resume_id"] = default_resume_id

        result = self.client.table("user_preferences").upsert(
            data, on_conflict="user_id"
        ).execute()

        if not result.data:
            raise RuntimeError("Failed to upsert user preferences")
        return result.data[0]

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
        return ApplicationDatabase()
