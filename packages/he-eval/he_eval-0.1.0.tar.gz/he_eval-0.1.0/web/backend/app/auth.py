"""Authentication utilities for JWT and API key handling."""

import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey, User
from app.settings import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


# JWT tokens (for web UI)


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """Decode a JWT token and return the user ID, or None if invalid."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None


# API keys (for CLI)


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash.

    Returns:
        (key, key_hash): The raw key (to send to user) and its hash (to store).
    """
    key = f"sk-{secrets.token_urlsafe(32)}"
    key_hash = pwd_context.hash(key)
    return key, key_hash


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(plain_key, hashed_key)


async def get_user_by_api_key(db: AsyncSession, api_key: str) -> User | None:
    """Look up a user by their API key.

    Returns the user if the key is valid and not expired, None otherwise.
    """
    # Get all non-expired API keys
    result = await db.execute(
        select(ApiKey).where(ApiKey.expires_at > datetime.utcnow())
    )
    api_keys = result.scalars().all()

    # Check each key (we have to check all because we can't query by hash)
    for ak in api_keys:
        if verify_api_key(api_key, ak.key_hash):
            # Found matching key, get the user
            user_result = await db.execute(select(User).where(User.id == ak.user_id))
            return user_result.scalar_one_or_none()

    return None


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Look up a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
