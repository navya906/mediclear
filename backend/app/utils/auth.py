"""
FastAPI dependency: verify Supabase JWT and return the authenticated user id.

Usage in a route:
    @router.get("/")
    def my_route(user_id: str = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database.client import get_supabase

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Extract and verify the Supabase JWT from the Authorization header.
    Returns the authenticated user's UUID string on success.
    Raises HTTP 401 on failure.
    """
    token = credentials.credentials
    supabase = get_supabase()

    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response is None or response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(response.user.id)
