"""AOI-Vision v0.2 — RBAC 路由
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.schemas import *
from app.modules.auth.service import *
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, data)
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin, "perms": {}})
    return _build_token_response(token, user)

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, data)

@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return _user_to_dict(user)

# ====== 用户管理 (Admin) ======

@router.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db), _admin=require_permission("users", "manage")):
    return await list_users(db)

@router.post("/users", response_model=UserResponse)
async def add_user(data: UserCreate, db: AsyncSession = Depends(get_db), _admin=require_permission("users", "manage")):
    return await create_user(db, data)

@router.put("/users/{user_id}", response_model=UserResponse)
async def edit_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db), _admin=require_permission("users", "manage")):
    return await update_user(db, user_id, data)

@router.delete("/users/{user_id}", status_code=204)
async def remove_user(user_id: str, db: AsyncSession = Depends(get_db), _admin=require_permission("users", "manage")):
    await delete_user(db, user_id)

# ====== 账号组管理 ======

@router.get("/account-groups", response_model=list[AccountGroupResponse])
async def get_account_groups(db: AsyncSession = Depends(get_db), _admin=require_permission("groups", "read")):
    return await list_account_groups(db)

@router.post("/account-groups", response_model=AccountGroupResponse)
async def add_account_group(data: AccountGroupCreate, db: AsyncSession = Depends(get_db), _admin=require_permission("groups", "manage")):
    return await create_account_group(db, data)

@router.put("/account-groups/{group_id}", response_model=AccountGroupResponse)
async def edit_account_group(group_id: str, data: AccountGroupCreate, db: AsyncSession = Depends(get_db), _admin=require_permission("groups", "manage")):
    return await update_account_group(db, group_id, data)

@router.delete("/account-groups/{group_id}", status_code=204)
async def remove_account_group(group_id: str, db: AsyncSession = Depends(get_db), _admin=require_permission("groups", "manage")):
    await delete_account_group(db, group_id)

# ====== 权限组管理 ======

@router.get("/permissions", response_model=list[PermissionResponse])
async def get_permissions(db: AsyncSession = Depends(get_db), _admin=require_permission("permissions", "read")):
    return await list_permissions(db)

@router.post("/permissions", response_model=PermissionResponse)
async def add_permission(data: PermissionCreate, db: AsyncSession = Depends(get_db), _admin=require_permission("permissions", "manage")):
    return await create_permission(db, data)

def _build_token_response(token, user):
    return {"access_token": token, "token_type": "bearer", "user": _user_to_dict(user)}
