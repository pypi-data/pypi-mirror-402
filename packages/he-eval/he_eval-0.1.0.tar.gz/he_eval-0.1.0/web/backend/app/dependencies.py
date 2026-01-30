"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_access_token, get_user_by_api_key, get_user_by_id
from app.database import get_db
from app.models import User

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """Get the current authenticated user.

    Supports both JWT tokens (web UI) and API keys (CLI).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try as JWT first (shorter tokens)
    if not token.startswith("sk-"):
        user_id = decode_access_token(token)
        if user_id:
            user = await get_user_by_id(db, user_id)
            if user:
                return user

    # Try as API key
    user = await get_user_by_api_key(db, token)
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current user, requiring admin privileges."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    """Get the current user if authenticated, None otherwise.

    Use this for endpoints that work both authenticated and unauthenticated.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(db, credentials)
    except HTTPException:
        return None
