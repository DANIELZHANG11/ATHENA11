"""
数据库连接与会话管理

使用 SQLAlchemy 2.0 异步引擎，支持连接池和 RLS 上下文设置。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def create_engine(
    database_url: str | None = None,
    pool_size: int | None = None,
    max_overflow: int | None = None,
    echo: bool | None = None,
    poolclass: type | None = None,
) -> AsyncEngine:
    """
    创建 SQLAlchemy 异步引擎

    Args:
        database_url: 数据库连接 URL
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
        echo: 是否打印 SQL
        poolclass: 连接池类型 (用于测试时使用 NullPool)
    """
    url = database_url or settings.database.database_url

    engine_kwargs: dict[str, Any] = {
        "echo": echo if echo is not None else settings.database.database_echo,
    }

    if poolclass is not None:
        engine_kwargs["poolclass"] = poolclass
    else:
        engine_kwargs["pool_size"] = pool_size or settings.database.database_pool_size
        engine_kwargs["max_overflow"] = max_overflow or settings.database.database_max_overflow
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600  # 1 小时回收

    return create_async_engine(url, **engine_kwargs)


# 全局引擎实例
engine = create_engine()

# 会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入：获取数据库会话

    用法:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    上下文管理器：获取数据库会话

    用法:
        async with get_db_context() as db:
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_with_user(user_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    带 RLS 用户上下文的数据库会话

    在会话开始时设置 app.user_id，用于 PostgreSQL RLS 策略。

    Args:
        user_id: 当前用户 ID

    用法:
        async for db in get_db_with_user(current_user.id):
            # RLS 策略会自动过滤用户数据
            ...
    """
    async with async_session_factory() as session:
        try:
            # 设置 RLS 上下文
            await session.execute(
                text("SET LOCAL app.user_id = :user_id"),
                {"user_id": str(user_id)},
            )
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_with_user_context(user_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    带 RLS 用户上下文的上下文管理器

    Args:
        user_id: 当前用户 ID
    """
    async with async_session_factory() as session:
        try:
            await session.execute(
                text("SET LOCAL app.user_id = :user_id"),
                {"user_id": str(user_id)},
            )
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库连接池"""
    # 测试连接
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    """关闭数据库连接池"""
    await engine.dispose()
