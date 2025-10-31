"""Error interceptor middleware for automatic error handling and recovery."""

import uuid
import traceback
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..utils.error_classification import (
    classify_error,
    get_error_type,
    get_user_message,
    sanitize_error_message,
    generate_error_id,
)
from ..services.recovery_service import RecoveryService

logger = logging.getLogger(__name__)


class ErrorInterceptorMiddleware(BaseHTTPMiddleware):
    """Middleware to intercept and handle all errors with recovery support."""

    def __init__(self, app, recovery_service: RecoveryService):
        super().__init__(app)
        self.recovery_service = recovery_service

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any errors."""
        start_time = time.time()
        session_id = request.headers.get("X-Session-ID")

        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            # Calculate request duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log the error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True
            )

            # Classify error
            category = classify_error(exc)
            error_type = get_error_type(exc)

            # Get request metadata
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # Sanitize error message
            error_message = sanitize_error_message(exc)
            user_message = get_user_message(category, error_type)
            retryable = category.value in ["TRANSIENT", "RECOVERABLE"]
            auto_retryable = category.value == "TRANSIENT"

            # Additional context
            additional_context = {
                "request_method": request.method,
                "request_path": str(request.url.path),
                "duration_ms": duration_ms,
                "error_class": type(exc).__name__,
                "error_message": error_message,
            }

            # Log error to database
            error_context = None
            try:
                error_context = self.recovery_service.log_error(
                    exc=exc,
                    session_id=session_id,
                    request_path=str(request.url.path),
                    request_method=request.method,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    additional_context=additional_context,
                )
            except Exception as log_error:
                logger.error(f"Failed to log error to database: {log_error}")

            error_id = error_context.get("error_id") if error_context else None
            if error_context:
                user_message = error_context.get("user_message", user_message)
                retryable = error_context.get("retryable", retryable)
                auto_retryable = error_context.get("auto_retryable", auto_retryable)
            if not error_id:
                error_id = generate_error_id()

            # Build error response
            error_response = {
                "success": False,
                "error_id": error_id,
                "error_type": error_type.value,
                "category": category.value,
                "message": user_message,
                "retryable": retryable,
                "auto_retryable": auto_retryable,
            }

            # Add recovery metadata if session exists
            if session_id:
                try:
                    session = self.recovery_service.get_session(session_id)
                    if session:
                        checkpoints = self.recovery_service.get_checkpoints(session_id)
                        error_response["recovery_metadata"] = {
                            "session_id": session_id,
                            "checkpoint_available": len(checkpoints) > 0,
                            "completed_agents": session.get("completed_agents", []),
                            "can_retry": self.recovery_service.can_retry(session_id),
                        }
                except Exception as recovery_error:
                    logger.error(f"Failed to get recovery metadata: {recovery_error}")

            # Determine status code
            status_code = 500
            if hasattr(exc, "status_code"):
                status_code = exc.status_code
            elif category.value == "PERMANENT":
                status_code = 400

            return JSONResponse(
                status_code=status_code,
                content=error_response
            )


__all__ = ["ErrorInterceptorMiddleware"]
