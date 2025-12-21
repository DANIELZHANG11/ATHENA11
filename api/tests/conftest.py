"""
测试配置

Pytest 配置和 fixtures。
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.core.database import get_db_session
from app.main import app
from app.models.base import Base

# 使用环境变量中的数据库 URL，如果不存在则使用 SQLite (仅用于简单的导入测试)
# 注意: SQLite 不支持 PostgreSQL 特有类型 (如 JSONB, UUID 等)
# CI 环境应始终设置 DATABASE_URL 指向 PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"  # 仅用于不需要数据库的测试
)

# SQLite 兼容性处理
if "sqlite" in TEST_DATABASE_URL:
    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
        return "JSON"

    @compiles(UUID, "sqlite")
    def compile_uuid_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
        return "VARCHAR(36)"

    @compiles(TSVECTOR, "sqlite")
    def compile_tsvector_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
        return "TEXT"


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """创建测试数据库引擎"""
    # 根据数据库类型设置不同的连接参数
    engine: AsyncEngine
    if "sqlite" in TEST_DATABASE_URL:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            pool_pre_ping=True,
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """认证头 (模拟)"""
    # 在实际测试中，需要创建真实的 JWT
    return {"Authorization": "Bearer test-token"}
