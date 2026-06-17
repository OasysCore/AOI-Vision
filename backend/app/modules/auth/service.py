"""AOI-Vision v0.1 — 认证服务
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.modules.auth.models import User, UserGroup
from app.modules.auth.schemas import UserCreate, UserLogin, GroupCreate

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user

async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=data.username, hashed_password=hash_password(data.password), full_name=data.full_name)
    if data.group_id:
        user.group_id = uuid.UUID(data.group_id)
    db.add(user)
    await db.flush()
    return user

async def login_user(db: AsyncSession, data: UserLogin) -> dict:
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return {"access_token": token, "user": user}

async def create_group(db: AsyncSession, data: GroupCreate) -> UserGroup:
    existing = await db.execute(select(UserGroup).where(UserGroup.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Group name already exists")
    group = UserGroup(name=data.name, permissions=data.permissions)
    db.add(group)
    await db.flush()
    return group

async def list_groups(db: AsyncSession) -> list[UserGroup]:
    result = await db.execute(select(UserGroup).order_by(UserGroup.name))
    return list(result.scalars().all())

async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.username))
    return list(result.scalars().all())
