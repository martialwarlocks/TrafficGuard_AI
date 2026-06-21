from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from backend.app.database import get_db
from backend.app.models import User, Role
from backend.app.schemas import UserCreate, UserLogin, UserResponse, Token, PasswordResetRequest
from backend.app.auth import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, get_current_user,
)
from backend.app.services.audit import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])

ROLE_MAP = {
    "admin": "Admin",
    "supervisor": "Supervisor",
    "officer": "Officer",
    "analyst": "Analyst",
}


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    role_result = await db.execute(select(Role).where(Role.name == ROLE_MAP.get(user_data.role.value, "Officer")))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role_id=role.id,
    )
    db.add(user)
    await db.flush()
    await log_audit(db, "user.signup", user_id=user.id, resource_type="user", resource_id=str(user.id))
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        role=role.name, is_active=user.is_active, created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.utcnow()
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    await log_audit(
        db, "user.login", user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return Token(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = role_result.scalar_one()
    return UserResponse(
        id=current_user.id, email=current_user.email, full_name=current_user.full_name,
        role=role.name, is_active=current_user.is_active,
        avatar_url=current_user.avatar_url, last_login=current_user.last_login,
        created_at=current_user.created_at,
    )


@router.post("/forgot-password")
async def forgot_password(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user:
        await log_audit(db, "user.password_reset_requested", user_id=user.id)
    return {"message": "If the email exists, a reset link has been sent"}
