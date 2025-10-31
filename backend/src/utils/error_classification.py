"""Error classification and handling utilities."""

import uuid
import re
import traceback
from typing import Dict, Any, Optional, Literal
from enum import Enum


class ErrorCategory(str, Enum):
    """Error categories for retry logic."""
    TRANSIENT = "TRANSIENT"        # Auto-retry appropriate
    RECOVERABLE = "RECOVERABLE"    # Manual retry recommended
    PERMANENT = "PERMANENT"        # No retry will help


class ErrorType(str, Enum):
    """Specific error types."""
    # Network errors
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    CONNECTION_LOST = "CONNECTION_LOST"

    # LLM/API errors
    LLM_API_ERROR = "LLM_API_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    CONTEXT_LENGTH_EXCEEDED = "CONTEXT_LENGTH_EXCEEDED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"

    # Agent errors
    AGENT_PROCESSING_ERROR = "AGENT_PROCESSING_ERROR"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PARSING_ERROR = "PARSING_ERROR"

    # File errors
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"

    # System errors
    DATABASE_ERROR = "DATABASE_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"

    # Auth/Config errors
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


def classify_error(exc: Exception) -> ErrorCategory:
    """Classify exception into error category.

    Args:
        exc: Exception to classify

    Returns:
        Error category (TRANSIENT, RECOVERABLE, or PERMANENT)
    """
    error_str = str(exc).lower()
    error_type = type(exc).__name__

    # Transient errors (auto-retry appropriate)
    transient_indicators = [
        'timeout',
        'timed out',
        'connection refused',
        'connection reset',
        'network',
        'temporary',
        '503',
        '504',
        '429',  # Rate limit
        'rate limit',
        'too many requests',
        'service unavailable',
        'temporarily unavailable',
    ]

    for indicator in transient_indicators:
        if indicator in error_str or indicator in error_type.lower():
            return ErrorCategory.TRANSIENT

    # Permanent errors (no retry will help)
    permanent_indicators = [
        'authentication',
        'unauthorized',
        '401',
        '403',
        'forbidden',
        'invalid api key',
        'missing api key',
        'configuration',
        'not found' if '404' in error_str else None,
        'invalid input',
    ]

    for indicator in permanent_indicators:
        if indicator and (indicator in error_str or indicator in error_type.lower()):
            return ErrorCategory.PERMANENT

    # Default to recoverable (manual retry may help)
    return ErrorCategory.RECOVERABLE


def get_error_type(exc: Exception) -> ErrorType:
    """Determine specific error type.

    Args:
        exc: Exception to analyze

    Returns:
        Specific error type
    """
    error_str = str(exc).lower()
    error_type = type(exc).__name__

    # Network errors
    if 'timeout' in error_str or 'timeout' in error_type.lower():
        return ErrorType.NETWORK_TIMEOUT
    if 'connection' in error_str:
        if 'refused' in error_str or 'reset' in error_str:
            return ErrorType.CONNECTION_LOST
        return ErrorType.NETWORK_FAILURE

    # Rate limiting
    if 'rate limit' in error_str or '429' in error_str:
        return ErrorType.RATE_LIMIT

    # Context length
    if 'context' in error_str and ('length' in error_str or 'exceeded' in error_str):
        return ErrorType.CONTEXT_LENGTH_EXCEEDED

    # Model errors
    if 'model' in error_str and 'unavailable' in error_str:
        return ErrorType.MODEL_UNAVAILABLE

    # LLM API errors
    if any(x in error_str for x in ['llm', 'openai', 'anthropic', 'gemini', 'api']):
        return ErrorType.LLM_API_ERROR

    # Agent errors
    if 'agent' in error_str:
        if 'timeout' in error_str:
            return ErrorType.AGENT_TIMEOUT
        if 'validation' in error_str:
            return ErrorType.VALIDATION_ERROR
        if 'parse' in error_str or 'parsing' in error_str:
            return ErrorType.PARSING_ERROR
        return ErrorType.AGENT_PROCESSING_ERROR

    # File errors
    if 'file' in error_str:
        if 'too large' in error_str or 'size' in error_str:
            return ErrorType.FILE_TOO_LARGE
        if 'format' in error_str or 'type' in error_str:
            return ErrorType.UNSUPPORTED_FORMAT
        return ErrorType.FILE_PROCESSING_ERROR

    # Database errors
    if 'database' in error_str or 'sqlite' in error_str:
        return ErrorType.DATABASE_ERROR

    # Memory errors
    if 'memory' in error_str or 'MemoryError' in error_type:
        return ErrorType.MEMORY_ERROR

    # Storage errors
    if 'storage' in error_str or 'disk' in error_str:
        return ErrorType.STORAGE_ERROR

    # Auth/Config errors
    if 'auth' in error_str or '401' in error_str or '403' in error_str:
        if 'authentication' in error_str or '401' in error_str:
            return ErrorType.AUTHENTICATION_ERROR
        return ErrorType.AUTHORIZATION_ERROR

    if 'config' in error_str:
        return ErrorType.CONFIGURATION_ERROR

    return ErrorType.UNKNOWN_ERROR


def get_user_message(category: ErrorCategory, error_type: ErrorType) -> str:
    """Get user-friendly error message.

    Args:
        category: Error category
        error_type: Specific error type

    Returns:
        User-friendly message
    """
    messages = {
        # Transient errors
        (ErrorCategory.TRANSIENT, ErrorType.NETWORK_TIMEOUT):
            "The network connection timed out. This is usually temporary.",
        (ErrorCategory.TRANSIENT, ErrorType.NETWORK_FAILURE):
            "Network connection lost. Please check your internet connection.",
        (ErrorCategory.TRANSIENT, ErrorType.RATE_LIMIT):
            "The AI service is currently experiencing high demand. This should resolve itself shortly.",
        (ErrorCategory.TRANSIENT, ErrorType.CONNECTION_LOST):
            "Connection to the server was lost. Retrying automatically...",

        # Recoverable errors
        (ErrorCategory.RECOVERABLE, ErrorType.LLM_API_ERROR):
            "An error occurred while processing your request with the AI service.",
        (ErrorCategory.RECOVERABLE, ErrorType.CONTEXT_LENGTH_EXCEEDED):
            "The job posting or resume is too long for the AI model. Try shortening the content.",
        (ErrorCategory.RECOVERABLE, ErrorType.MODEL_UNAVAILABLE):
            "The AI model is currently unavailable. Trying an alternative model...",
        (ErrorCategory.RECOVERABLE, ErrorType.AGENT_PROCESSING_ERROR):
            "An error occurred during processing. Your data has been saved.",
        (ErrorCategory.RECOVERABLE, ErrorType.FILE_PROCESSING_ERROR):
            "We had trouble reading your resume file. Please try a different format (PDF or DOCX).",
        (ErrorCategory.RECOVERABLE, ErrorType.VALIDATION_ERROR):
            "Validation failed. Please check your input and try again.",
        (ErrorCategory.RECOVERABLE, ErrorType.DATABASE_ERROR):
            "A database error occurred. Please try again.",

        # Permanent errors
        (ErrorCategory.PERMANENT, ErrorType.AUTHENTICATION_ERROR):
            "Authentication failed. Please check your API configuration.",
        (ErrorCategory.PERMANENT, ErrorType.UNSUPPORTED_FORMAT):
            "Unsupported file format. Please upload a PDF or DOCX file.",
        (ErrorCategory.PERMANENT, ErrorType.FILE_TOO_LARGE):
            "File too large. Maximum file size is 10MB.",
        (ErrorCategory.PERMANENT, ErrorType.CONFIGURATION_ERROR):
            "System configuration error. Please contact support.",
    }

    # Try exact match
    key = (category, error_type)
    if key in messages:
        return messages[key]

    # Fallback based on category
    category_fallbacks = {
        ErrorCategory.TRANSIENT: "A temporary error occurred. Retrying automatically...",
        ErrorCategory.RECOVERABLE: "An error occurred during processing. Your data has been preserved.",
        ErrorCategory.PERMANENT: "An error occurred that requires manual intervention. Please check your input and try again.",
    }

    return category_fallbacks.get(category, "An unexpected error occurred.")


def sanitize_error_message(error: Exception) -> str:
    """Remove PII from error messages.

    Args:
        error: Exception to sanitize

    Returns:
        Sanitized error message
    """
    message = str(error)

    # Remove email addresses
    message = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[EMAIL]',
        message
    )

    # Remove phone numbers
    message = re.sub(
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        '[PHONE]',
        message
    )

    # Remove file paths (may contain usernames)
    message = re.sub(
        r'[A-Za-z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]*',
        '[PATH]',
        message
    )
    message = re.sub(
        r'/(?:[^/\s]+/)*[^/\s]+',
        '[PATH]',
        message
    )

    # Remove IP addresses
    message = re.sub(
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        '[IP]',
        message
    )

    # Remove potential API keys/tokens (long alphanumeric strings)
    message = re.sub(
        r'\b[A-Za-z0-9]{32,}\b',
        '[REDACTED]',
        message
    )

    return message


def generate_error_id() -> str:
    """Generate unique error ID.

    Returns:
        Unique error ID
    """
    return f"ERR-{uuid.uuid4().hex[:12].upper()}"


def create_error_context(
    exc: Exception,
    session_id: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create comprehensive error context.

    Args:
        exc: Exception
        session_id: Session ID
        request_path: Request path
        request_method: Request method
        additional_context: Additional context data

    Returns:
        Error context dictionary
    """
    category = classify_error(exc)
    error_type = get_error_type(exc)
    error_id = generate_error_id()

    return {
        'error_id': error_id,
        'error_type': error_type.value,
        'error_category': category.value,
        'error_message': sanitize_error_message(exc),
        'user_message': get_user_message(category, error_type),
        'error_stacktrace': traceback.format_exc(),
        'session_id': session_id,
        'request_path': request_path,
        'request_method': request_method,
        'retryable': category in [ErrorCategory.TRANSIENT, ErrorCategory.RECOVERABLE],
        'auto_retryable': category == ErrorCategory.TRANSIENT,
        'additional_context': additional_context or {},
    }


def should_auto_retry(category: ErrorCategory, retry_count: int, max_retries: int = 3) -> bool:
    """Determine if automatic retry should be attempted.

    Args:
        category: Error category
        retry_count: Current retry count
        max_retries: Maximum retries allowed

    Returns:
        True if auto-retry should be attempted
    """
    return category == ErrorCategory.TRANSIENT and retry_count < max_retries


def calculate_backoff(retry_count: int, base_delay: float = 2.0) -> float:
    """Calculate exponential backoff delay.

    Args:
        retry_count: Current retry count (0-indexed)
        base_delay: Base delay in seconds

    Returns:
        Delay in seconds
    """
    return base_delay ** (retry_count + 1)


__all__ = [
    'ErrorCategory',
    'ErrorType',
    'classify_error',
    'get_error_type',
    'get_user_message',
    'sanitize_error_message',
    'generate_error_id',
    'create_error_context',
    'should_auto_retry',
    'calculate_backoff',
]
