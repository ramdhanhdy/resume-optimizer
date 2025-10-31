"""Recovery service for handling session recovery and retry logic."""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..database.db import ApplicationDatabase
from ..utils.error_classification import (
    create_error_context,
    should_auto_retry,
    calculate_backoff,
    ErrorCategory
)


class RecoveryService:
    """Service for managing recovery sessions and retry logic."""

    def __init__(self, db: ApplicationDatabase):
        """Initialize recovery service.

        Args:
            db: Database instance
        """
        self.db = db

    def create_session(
        self,
        form_data: Dict[str, Any],
        file_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Create a new recovery session.

        Args:
            form_data: User form data
            file_metadata: File metadata
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        self.db.create_recovery_session(
            session_id=session_id,
            form_data=form_data,
            file_metadata=file_metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery session.

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        return self.db.get_recovery_session(session_id)

    def update_session_status(
        self,
        session_id: str,
        status: str,
        current_agent: Optional[int] = None,
        completed_agents: Optional[List[int]] = None,
    ) -> None:
        """Update session status.

        Args:
            session_id: Session ID
            status: New status
            current_agent: Current agent index
            completed_agents: List of completed agent indices
        """
        update_data = {'status': status}

        if current_agent is not None:
            update_data['current_agent'] = current_agent

        if completed_agents is not None:
            update_data['completed_agents'] = completed_agents

        self.db.update_recovery_session(session_id, **update_data)

    def save_checkpoint(
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
            agent_index: Agent index
            agent_name: Agent name
            agent_output: Agent output
            execution_time_ms: Execution time in ms
            model_used: Model used
            tokens_used: Tokens used
            cost_usd: Cost in USD

        Returns:
            Checkpoint ID
        """
        checkpoint_id = self.db.save_agent_checkpoint(
            session_id=session_id,
            agent_index=agent_index,
            agent_name=agent_name,
            agent_output=agent_output,
            execution_time_ms=execution_time_ms,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        )

        # Update session completed agents
        session = self.get_session(session_id)
        if session:
            completed = session.get('completed_agents', [])
            if agent_index not in completed:
                completed.append(agent_index)
                completed.sort()
                self.update_session_status(
                    session_id=session_id,
                    status='processing',
                    completed_agents=completed,
                    current_agent=agent_index + 1 if agent_index < 4 else None,
                )

        return checkpoint_id

    def get_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for a session.

        Args:
            session_id: Session ID

        Returns:
            List of checkpoints
        """
        return self.db.get_agent_checkpoints(session_id)

    def log_error(
        self,
        exc: Exception,
        session_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Log error and update session.

        Args:
            exc: Exception
            session_id: Session ID
            request_path: Request path
            request_method: Request method
            user_agent: User agent
            ip_address: IP address
            additional_context: Additional context

        Returns:
            Error context
        """
        # Create error context
        error_context = create_error_context(
            exc=exc,
            session_id=session_id,
            request_path=request_path,
            request_method=request_method,
            additional_context=additional_context,
        )

        # Log to database
        self.db.log_error(
            error_id=error_context['error_id'],
            error_type=error_context['error_type'],
            error_category=error_context['error_category'],
            error_message=error_context['error_message'],
            session_id=session_id,
            error_stacktrace=error_context['error_stacktrace'],
            request_path=request_path,
            request_method=request_method,
            user_agent=user_agent,
            ip_address=ip_address,
            additional_context=error_context['additional_context'],
        )

        # Update session if exists
        if session_id:
            session = self.get_session(session_id)
            if session:
                self.db.update_recovery_session(
                    session_id=session_id,
                    status='failed',
                    error_id=error_context['error_id'],
                    error_type=error_context['error_type'],
                    error_category=error_context['error_category'],
                    error_message=error_context['user_message'],
                )

        return error_context

    def can_retry(self, session_id: str) -> bool:
        """Check if session can be retried.

        Args:
            session_id: Session ID

        Returns:
            True if retry is possible
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Check if expired
        expires_at = session.get('expires_at')
        if expires_at:
            try:
                expiry = datetime.fromisoformat(str(expires_at))
                if datetime.now() > expiry:
                    return False
            except:
                pass

        # Check retry count
        retry_count = session.get('retry_count', 0)
        max_retries = session.get('max_retries', 3)

        return retry_count < max_retries

    def increment_retry_count(self, session_id: str) -> int:
        """Increment retry count for session.

        Args:
            session_id: Session ID

        Returns:
            New retry count
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        new_count = session.get('retry_count', 0) + 1

        self.db.update_recovery_session(
            session_id=session_id,
            retry_count=new_count,
            last_retry_at=datetime.now(),
        )

        return new_count

    def get_resume_point(self, session_id: str) -> Optional[int]:
        """Get agent index to resume from.

        Args:
            session_id: Session ID

        Returns:
            Agent index to resume from, or None if starting fresh
        """
        checkpoints = self.get_checkpoints(session_id)

        if not checkpoints:
            return None

        # Resume from next agent after last checkpoint
        last_checkpoint = max(checkpoints, key=lambda x: x['agent_index'])
        last_agent_index = last_checkpoint['agent_index']

        # If we've completed all agents, something is wrong
        if last_agent_index >= 4:
            return None

        return last_agent_index + 1

    def reconstruct_state(self, session_id: str) -> Dict[str, Any]:
        """Reconstruct processing state from checkpoints.

        Args:
            session_id: Session ID

        Returns:
            Dictionary of agent outputs by index
        """
        checkpoints = self.get_checkpoints(session_id)

        state = {}
        for checkpoint in checkpoints:
            state[checkpoint['agent_index']] = checkpoint['agent_output']

        return state

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired recovery sessions.

        Returns:
            Number of sessions cleaned up
        """
        return self.db.cleanup_expired_sessions()

    def mark_recovered(self, session_id: str, application_id: int) -> None:
        """Mark session as successfully recovered.

        Args:
            session_id: Session ID
            application_id: Application ID
        """
        self.db.update_recovery_session(
            session_id=session_id,
            status='recovered',
            application_id=application_id,
        )


__all__ = ['RecoveryService']
