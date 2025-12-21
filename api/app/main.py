"""
雅典娜 API 主应用

FastAPI 应用入口，配置中间件、路由和生命周期事件。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import AthenaException

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.app.is_production else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Athena API", env=settings.app.app_env)
    await init_db()
    logger.info("Database connection pool initialized")

    yield

    # 关闭时
    logger.info("Shutting down Athena API")
    await close_db()
    logger.info("Database connection pool closed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="雅典娜 API",
        description="App-First 阅读应用后端 API",
        version="0.1.0",
        docs_url="/docs" if settings.app.debug else None,
        redoc_url="/redoc" if settings.app.debug else None,
        openapi_url="/openapi.json" if settings.app.debug else None,
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    )

    # 注册异常处理器
    @app.exception_handler(AthenaException)
    async def athena_exception_handler(
        _request: Request, exc: AthenaException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # 注册路由
    from app.api.routes import ai, auth, books, notes, powersync, shelves

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(books.router, prefix="/api/v1")
    app.include_router(notes.router, prefix="/api/v1")
    app.include_router(shelves.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(powersync.router, prefix="/api/v1")

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "Athena API",
            "version": "0.1.0",
            "docs": "/docs" if settings.app.debug else "disabled",
        }

    return app


# 创建应用实例
app = create_app()
