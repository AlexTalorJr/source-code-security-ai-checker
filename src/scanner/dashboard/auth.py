"""Dashboard JWT session management and password verification."""

import logging
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
SESSION_DURATION = timedelta(days=7)
COOKIE_NAME = "scanner_session"

_password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt via pwdlib.

    Args:
        password: Plain text password.

    Returns:
        Bcrypt hash string.
    """
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    return _password_hash.verify(plain_password, hashed_password)


def create_session_jwt(user_id: int, role: str, secret_key: str) -> str:
    """Create a JWT for dashboard session.

    Args:
        user_id: Database ID of the authenticated user.
        role: User's role string.
        secret_key: HMAC signing key.

    Returns:
        Encoded JWT string.
    """
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + SESSION_DURATION,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def verify_session_jwt(token: str, secret_key: str) -> dict | None:
    """Verify and decode a session JWT.

    Args:
        token: JWT string from cookie.
        secret_key: HMAC signing key.

    Returns:
        Decoded payload dict with 'sub' and 'role' keys, or None if invalid.
    """
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
