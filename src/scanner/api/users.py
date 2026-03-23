"""User management API endpoints (admin only)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from scanner.api.auth import Role, require_role
from scanner.dashboard.auth import hash_password
from scanner.models.user import User
from scanner.schemas.auth import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Create a new user account.

    Args:
        body: User creation data (username, password, role).
        request: FastAPI request.
        current_user: Authenticated admin user.

    Returns:
        Created user response.
    """
    async with request.app.state.session_factory() as session:
        # Check username uniqueness
        existing = await session.execute(
            select(User).where(User.username == body.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already exists")

        user = User(
            username=body.username,
            password_hash=hash_password(body.password),
            role=body.role,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("User created: %s (role=%s) by %s", body.username, body.role, current_user.username)
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )


@router.get("", response_model=list[UserResponse])
async def list_users(
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """List all user accounts.

    Args:
        request: FastAPI request.
        current_user: Authenticated admin user.

    Returns:
        List of user responses.
    """
    async with request.app.state.session_factory() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        return [
            UserResponse(
                id=u.id,
                username=u.username,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in users
        ]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN, Role.SCANNER, Role.VIEWER)),
):
    """Get current user profile.

    Args:
        request: FastAPI request.
        current_user: Authenticated user.

    Returns:
        Current user response.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Update a user account.

    Args:
        user_id: ID of user to update.
        body: Update data (partial).
        request: FastAPI request.
        current_user: Authenticated admin user.

    Returns:
        Updated user response.
    """
    async with request.app.state.session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Admin cannot change own role (prevent lockout)
        if user.id == current_user.id and body.role and body.role != user.role:
            raise HTTPException(status_code=400, detail="Cannot change your own role")

        if body.username is not None:
            # Check uniqueness
            existing = await session.execute(
                select(User).where(User.username == body.username, User.id != user_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Username already exists")
            user.username = body.username

        if body.password is not None:
            user.password_hash = hash_password(body.password)

        if body.role is not None:
            user.role = body.role

        await session.commit()
        await session.refresh(user)
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Deactivate a user account (soft delete).

    Args:
        user_id: ID of user to deactivate.
        request: FastAPI request.
        current_user: Authenticated admin user.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    async with request.app.state.session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = False
        await session.commit()
        logger.info("User deactivated: %s by %s", user.username, current_user.username)
