"""AOI-Vision v0.2 — RBAC 认证服务
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 多对多 RBAC — 登录/注册/用户CRUD/组管理/权限检查
"""
import uuid
from functools import wraps
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.modules.auth.models import User, AccountGroup, Permission, account_group_permissions

bearer_scheme = HTTPBearer(auto_error=False)

# ====== 认证 ======

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(
        select(User).options(selectinload(User.account_groups)).where(User.id == payload["sub"])
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ====== 权限检查装饰器 ======

def require_permission(resource: str, action: str = "read"):
    """检查当前用户是否有指定资源的操作权限。
    Usage: @router.get("/admin/users") → require_permission("admin", "manage")
    """
    async def checker(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if user.is_admin:
            return user  # Admin 全权限
        # 遍历用户所有账号组 → 遍历每个组的权限组 → 检查是否有对应权限
        group_ids = [g.id for g in user.account_groups]
        if not group_ids:
            raise HTTPException(status_code=403, detail="No permission groups assigned")
        result = await db.execute(
            select(Permission).join(Permission.account_groups).where(
                AccountGroup.id.in_(group_ids), Permission.is_active == True
            )
        )
        perms = result.scalars().all()
        effective = {}
        for p in perms:
            for k, v in (p.permissions or {}).items():
                if v == "manage" or (k == resource and (v == action or v == "manage")):
                    effective[k] = v
        if resource not in effective:
            raise HTTPException(status_code=403, detail=f"Permission denied: {resource}.{action}")
        return user
    return Depends(checker)


# ====== 登录/注册 ======

async def register_user(db: AsyncSession, data) -> User:
    from app.modules.auth.schemas import UserCreate
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username exists")
    user = User(username=data.username, hashed_password=hash_password(data.password), full_name=data.full_name)
    db.add(user); await db.flush()
    if data.account_group_ids:
        groups = (await db.execute(select(AccountGroup).where(AccountGroup.id.in_([uuid.UUID(g) for g in data.account_group_ids])))).scalars().all()
        user.account_groups = groups; await db.flush()
    return user

async def login_user(db: AsyncSession, data) -> dict:
    result = await db.execute(select(User).options(selectinload(User.account_groups)).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    # 收集所有权限
    perms = {}
    for g in user.account_groups:
        g_result = await db.execute(select(Permission).join(Permission.account_groups).where(AccountGroup.id == g.id))
        for p in g_result.scalars().all():
            perms.update(p.permissions or {})
    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin, "perms": perms})
    return {"access_token": token, "user": _user_to_dict(user)}

# ====== 用户 CRUD (Admin) ======

async def list_users(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(User).options(selectinload(User.account_groups)).order_by(User.username))
    return [_user_to_dict(u) for u in result.scalars().all()]

async def create_user(db: AsyncSession, data) -> dict:
    from app.modules.auth.schemas import UserCreate
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username exists")
    user = User(username=data.username, hashed_password=hash_password(data.password), full_name=data.full_name)
    db.add(user); await db.flush()
    if data.account_group_ids:
        groups = (await db.execute(select(AccountGroup).where(AccountGroup.id.in_([uuid.UUID(g) for g in data.account_group_ids])))).scalars().all()
        user.account_groups = groups; await db.flush()
    return _user_to_dict(user)

async def update_user(db: AsyncSession, user_id: str, data) -> dict:
    result = await db.execute(select(User).options(selectinload(User.account_groups)).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.full_name is not None: user.full_name = data.full_name
    if data.password is not None: user.hashed_password = hash_password(data.password)
    if data.is_active is not None: user.is_active = data.is_active
    if data.is_admin is not None: user.is_admin = data.is_admin
    if data.account_group_ids is not None:
        groups = (await db.execute(select(AccountGroup).where(AccountGroup.id.in_([uuid.UUID(g) for g in data.account_group_ids])))).scalars().all()
        user.account_groups = groups
    await db.flush()
    return _user_to_dict(user)

async def delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False; await db.flush()

# ====== 账号组 CRUD ======

async def list_account_groups(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(AccountGroup).options(selectinload(AccountGroup.permissions)).order_by(AccountGroup.name))
    return [_group_to_dict(g) for g in result.scalars().all()]

async def create_account_group(db: AsyncSession, data) -> dict:
    existing = await db.execute(select(AccountGroup).where(AccountGroup.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Group name exists")
    g = AccountGroup(name=data.name, description=data.description)
    db.add(g); await db.flush()
    if data.permission_ids:
        perms = (await db.execute(select(Permission).where(Permission.id.in_([uuid.UUID(pid) for pid in data.permission_ids])))).scalars().all()
        g.permissions = perms; await db.flush()
    return _group_to_dict(g)

async def update_account_group(db: AsyncSession, group_id: str, data) -> dict:
    result = await db.execute(select(AccountGroup).options(selectinload(AccountGroup.permissions)).where(AccountGroup.id == uuid.UUID(group_id)))
    g = result.scalar_one_or_none()
    if not g: raise HTTPException(status_code=404, detail="Group not found")
    if data.name: g.name = data.name
    if data.description: g.description = data.description
    if data.permission_ids is not None:
        perms = (await db.execute(select(Permission).where(Permission.id.in_([uuid.UUID(pid) for pid in data.permission_ids])))).scalars().all()
        g.permissions = perms
    await db.flush()
    return _group_to_dict(g)

async def delete_account_group(db: AsyncSession, group_id: str):
    result = await db.execute(select(AccountGroup).where(AccountGroup.id == uuid.UUID(group_id)))
    g = result.scalar_one_or_none()
    if not g: raise HTTPException(status_code=404, detail="Group not found")
    g.is_active = False; await db.flush()

# ====== 权限组 CRUD ======

async def list_permissions(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Permission).order_by(Permission.name))
    return [_perm_to_dict(p) for p in result.scalars().all()]

async def create_permission(db: AsyncSession, data) -> dict:
    p = Permission(name=data.name, description=data.description, permissions=data.permissions)
    db.add(p); await db.flush()
    return _perm_to_dict(p)

# ====== 工具函数 ======

def _user_to_dict(u: User) -> dict:
    return {"id":str(u.id),"username":u.username,"full_name":u.full_name or"","is_admin":u.is_admin,"is_active":u.is_active,
            "account_groups":[{"id":str(g.id),"name":g.name} for g in (u.account_groups or[])]}

def _group_to_dict(g: AccountGroup) -> dict:
    return {"id":str(g.id),"name":g.name,"description":g.description or"","is_active":g.is_active,
            "permissions":[{"id":str(p.id),"name":p.name,"permissions":p.permissions} for p in (g.permissions or[])]}

def _perm_to_dict(p: Permission) -> dict:
    return {"id":str(p.id),"name":p.name,"description":p.description or"","permissions":p.permissions,"is_active":p.is_active}

# ====== 种子数据 ======

async def seed_admin_user(db: AsyncSession):
    existing = await db.execute(select(User).where(User.username == "admin"))
    if existing.scalar_one_or_none(): return
    admin = User(username="admin", hashed_password=hash_password("admin123"), full_name="Administrator", is_admin=True)
    db.add(admin); await db.flush()

async def seed_default_rbac(db: AsyncSession):
    # 权限组
    perms_data = [
        ("全权限管理", "所有功能的管理权限", {"inspection":"manage","measurement":"manage","defects":"manage","reports":"manage","device":"manage","admin":"manage","users":"manage","groups":"manage","permissions":"manage"}),
        ("质检员权限", "检测/量测/报表读写权限", {"inspection":"manage","measurement":"manage","defects":"manage","reports":"read","device":"read","admin":"read"}),
        ("操作员权限", "检测执行+只读报表", {"inspection":"write","measurement":"read","defects":"read","reports":"read"}),
        ("只读权限", "仅查看", {"inspection":"read","measurement":"read","defects":"read","reports":"read","device":"read"}),
    ]
    perm_objs = {}
    for name, desc, perms in perms_data:
        result = await db.execute(select(Permission).where(Permission.name == name))
        existing = result.scalar_one_or_none()
        if not existing:
            p = Permission(name=name, description=desc, permissions=perms)
            db.add(p); await db.flush()
            perm_objs[name] = p
        else:
            perm_objs[name] = existing

    # 账号组
    groups_data = [
        ("管理员组", "系统管理员", ["全权限管理"]),
        ("质检员组", "质量检测人员", ["质检员权限"]),
        ("操作员组", "产线操作员", ["操作员权限"]),
        ("访客组", "仅查看权限", ["只读权限"]),
    ]
    for name, desc, perm_names in groups_data:
        existing = await db.execute(select(AccountGroup).where(AccountGroup.name == name))
        if not existing.scalar_one_or_none():
            g = AccountGroup(name=name, description=desc)
            db.add(g); await db.flush()
            # Insert M2M directly — avoid lazy load
            for pn in perm_names:
                if pn in perm_objs:
                    await db.execute(
                        account_group_permissions.insert().values(
                            account_group_id=g.id, permission_id=perm_objs[pn].id
                        )
                    )
            await db.flush()

async def seed_all(db: AsyncSession):
    await seed_default_rbac(db)
    await seed_admin_user(db)
    # 把 admin 加入管理员组
    result = await db.execute(select(User).options(selectinload(User.account_groups)).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if admin and not admin.account_groups:
        grp_result = await db.execute(select(AccountGroup).where(AccountGroup.name == "管理员组"))
        admin_group = grp_result.scalar_one_or_none()
        if admin_group:
            from app.modules.auth.models import user_account_groups
            await db.execute(
                user_account_groups.insert().values(user_id=admin.id, account_group_id=admin_group.id)
            )
            await db.flush()
