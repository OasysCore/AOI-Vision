"""AOI-Vision v0.1 — 认证路由
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, GroupCreate, GroupResponse
from app.modules.auth.service import register_user, login_user, create_group, list_groups, list_users, get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, data)
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return {"access_token": token, "user": user}

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, data)

@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return {"id": str(user.id), "username": user.username, "full_name": user.full_name or "",
            "is_admin": user.is_admin, "group_id": str(user.group_id) if user.group_id else None, "is_active": user.is_active}

@router.get("/groups", response_model=list[GroupResponse])
async def get_groups(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    return await list_groups(db)

@router.post("/groups", response_model=GroupResponse)
async def add_group(data: GroupCreate, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    return await create_group(db, data)

@router.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    return await list_users(db)
