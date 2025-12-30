"""Supabase JWT authentication middleware and dependencies."""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# HTTP Bearer scheme for extracting tokens
security = HTTPBearer(auto_error=False)


def _get_supabase_client():
    """Get Supabase client lazily to avoid import errors if not configured."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.warning(f"Failed to create Supabase client: {e}")
        return None


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Extract and validate user ID from Supabase JWT token.
    
    Supports:
    - Authorization: Bearer <token> header
    - access_token query parameter (for SSE/EventSource)
    
    Returns:
        User ID (uid) if authenticated, None if no token provided.
    
    Raises:
        HTTPException 401 if token is invalid.
    """
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    
    # Fall back to query parameter (for SSE which can't set headers)
    if not token:
        token = request.query_params.get("access_token")
    
    if not token:
        return None
    
    # Validate token using Supabase
    supabase = _get_supabase_client()
    if not supabase:
        logger.warning("Supabase not configured, skipping auth validation")
        return None
    
    try:
        # Use Supabase's get_user to validate the token
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            return user_response.user.id
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed")


async def require_auth(
    uid: Optional[str] = Depends(get_current_user_id),
) -> str:
    """
    Dependency that requires authentication.
    
    Returns:
        User ID (uid) if authenticated.
    
    Raises:
        HTTPException 401 if not authenticated.
    """
    if not uid:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return uid


def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Synchronous helper to extract user ID from request.
    Used for backward compatibility with existing code.
    
    Falls back to X-Client-Id header if no JWT token present.
    """
    # Try Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        supabase = _get_supabase_client()
        if supabase:
            try:
                user_response = supabase.auth.get_user(token)
                if user_response and user_response.user:
                    return user_response.user.id
            except Exception as e:
                logger.debug(f"Token validation failed: {e}")
    
    # Try access_token query param
    token = request.query_params.get("access_token")
    if token:
        supabase = _get_supabase_client()
        if supabase:
            try:
                user_response = supabase.auth.get_user(token)
                if user_response and user_response.user:
                    return user_response.user.id
            except Exception as e:
                logger.debug(f"Token validation failed: {e}")
    
    # Fall back to X-Client-Id for backward compatibility
    client_id = request.headers.get("x-client-id") or request.headers.get("X-Client-Id")
    if client_id:
        return f"client:{client_id}"
    
    # Fall back to IP address
    client_host = request.client.host if request.client else "anonymous"
    return f"ip:{client_host}"
