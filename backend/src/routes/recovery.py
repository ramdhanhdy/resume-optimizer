"""Recovery and retry endpoints."""

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from ..database.db import ApplicationDatabase
from ..services.recovery_service import RecoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recovery"])


class RetryRequest(BaseModel):
    """Retry request payload."""
    sessionId: str
    formData: Optional[Dict[str, Any]] = None


@router.post("/optimize-retry")
async def optimize_retry(
    request: Request,
    retry_request: RetryRequest = Body(...),
):
    """Handle retry request with session recovery.

    Args:
        request: FastAPI request
        retry_request: Retry request data

    Returns:
        Recovery response with application ID
    """
    try:
        # Get database and recovery service from app state
        db: ApplicationDatabase = request.app.state.db
        recovery_service = RecoveryService(db)

        session_id = retry_request.sessionId

        # Load recovery session
        recovery_session = recovery_service.get_session(session_id)

        if not recovery_session:
            raise HTTPException(
                status_code=404,
                detail="Recovery session not found or expired"
            )

        # Check if can retry
        if not recovery_service.can_retry(session_id):
            raise HTTPException(
                status_code=400,
                detail="Maximum retry attempts exceeded"
            )

        # Increment retry count
        retry_count = recovery_service.increment_retry_count(session_id)

        logger.info(f"Retry attempt {retry_count} for session {session_id}")

        # Check for existing checkpoints
        checkpoints = recovery_service.get_checkpoints(session_id)
        resume_from_agent = recovery_service.get_resume_point(session_id)

        # Build response
        response = {
            "success": True,
            "sessionId": session_id,
            "resumeFromAgent": resume_from_agent,
            "hasCheckpoints": len(checkpoints) > 0,
            "retryCount": retry_count,
            "message": "Retry initiated. Processing will resume shortly."
        }

        # Note: Actual pipeline execution would be triggered here
        # For now, we're returning the resume point for the frontend to handle

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Retry failed: {str(e)}"
        )


@router.get("/recovery-session/{session_id}")
async def get_recovery_session(
    request: Request,
    session_id: str,
):
    """Get recovery session details.

    Args:
        request: FastAPI request
        session_id: Session ID

    Returns:
        Recovery session data
    """
    try:
        db: ApplicationDatabase = request.app.state.db
        recovery_service = RecoveryService(db)

        session = recovery_service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Recovery session not found"
            )

        # Get checkpoints
        checkpoints = recovery_service.get_checkpoints(session_id)

        return {
            "success": True,
            "session": {
                **session,
                "completedAgents": session.get('completed_agents', []),
                "checkpointCount": len(checkpoints),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recovery session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recovery session: {str(e)}"
        )


@router.delete("/recovery-session/{session_id}")
async def delete_recovery_session(
    request: Request,
    session_id: str,
):
    """Delete recovery session (user clicked Start Fresh).

    Args:
        request: FastAPI request
        session_id: Session ID

    Returns:
        Success message
    """
    try:
        db: ApplicationDatabase = request.app.state.db
        recovery_service = RecoveryService(db)

        # Delete session
        db.update_recovery_session(
            session_id=session_id,
            status='deleted'
        )

        logger.info(f"Deleted recovery session {session_id}")

        return {
            "success": True,
            "message": "Recovery session deleted"
        }

    except Exception as e:
        logger.error(f"Failed to delete recovery session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete recovery session: {str(e)}"
        )


__all__ = ['router']
