"""Pydantic schemas for authentication requests and responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Dashboard login form data."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    """Create user request."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=200)
    role: str = Field(default="viewer", pattern="^(admin|scanner|viewer)$")


class UserUpdate(BaseModel):
    """Update user request."""
    username: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    role: str | None = Field(default=None, pattern="^(admin|scanner|viewer)$")


class UserResponse(BaseModel):
    """User response (no password hash)."""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime | None = None


class TokenCreate(BaseModel):
    """Create API token request."""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class TokenResponse(BaseModel):
    """API token response (masked)."""
    id: int
    name: str
    token_prefix: str
    created_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


class TokenCreatedResponse(BaseModel):
    """Response after token creation -- includes raw token (shown once)."""
    id: int
    name: str
    raw_token: str
    expires_at: datetime | None = None
