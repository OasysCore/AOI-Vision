"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: SQLAlchemy 异步引擎 + SQLite/PostgreSQL 双模
"""
import uuid as _uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, CHAR
from app.core.config import settings

class GUID(TypeDecorator):
    impl = CHAR; cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36)) if dialect.name == "sqlite" else dialect.type_descriptor(self.impl)
    def process_bind_param(self, value, dialect):
        if value is None: return value
        return str(value) if dialect.name == "sqlite" else value
    def process_result_value(self, value, dialect):
        if value is None: return value
        return _uuid.UUID(value) if not isinstance(value, _uuid.UUID) else value

if "sqlite" in settings.DATABASE_URL:
    import sqlalchemy.dialects.sqlite as _sq
    _sq.base.ischema_names["uuid"] = GUID

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

if "sqlite" in settings.DATABASE_URL:
    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_fk(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

class Base(DeclarativeBase): pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """创建表 + 种子数据"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from app.modules.admin.service import seed_default_options
    from app.modules.auth.service import seed_all
    
    async with async_session() as db:
        await seed_default_options(db)
        await seed_all(db)
        await db.commit()
