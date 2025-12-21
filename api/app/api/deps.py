"""
认证依赖项

提供 FastAPI 依赖注入的认证函数。
"""

from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
    UnauthorizedException,
)
from app.core.security import verify_token
from app.models.user import User

__all__ = [
    "get_db_session",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_admin_user",
    "get_device_id",
    "get_client_ip",
    "CurrentUser",
    "CurrentActiveUser",
    "CurrentAdminUser",
    "OptionalUser",
    "DeviceId",
]

# Bearer Token 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    获取当前认证用户

    从 Authorization Header 提取 JWT Token，验证并返回用户对象。

    Raises:
        UnauthorizedException: 缺少认证信息
        TokenInvalidException: Token 无效
        TokenExpiredException: Token 已过期
    """
    if credentials is None:
        raise UnauthorizedException()

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise TokenInvalidException()

    # 查询用户
    result = await db.execute(
        select(User).where(User.id == payload.sub, User.is_active)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise TokenInvalidException()

    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User | None:
    """
    获取当前用户 (可选)

    如果提供了有效的 Token 则返回用户，否则返回 None。
    用于可选认证的端点。
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except (UnauthorizedException, TokenInvalidException, TokenExpiredException):
        return None


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    获取当前活跃用户

    确保用户账户处于活跃状态。
    """
    if not current_user.is_active:
        raise UnauthorizedException("account_disabled")
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    获取当前管理员用户

    确保用户具有管理员权限。
    """
    if not current_user.is_admin:
        from app.core.exceptions import AdminRequiredException
        raise AdminRequiredException()
    return current_user


def get_device_id(
    x_device_id: Annotated[str | None, Header(alias="X-Device-ID")] = None,
) -> str | None:
    """
    获取设备 ID

    从请求头 X-Device-ID 获取设备标识。
    """
    return x_device_id


def get_client_ip(request: Request) -> str:
    """
    获取客户端 IP

    考虑代理服务器的 X-Forwarded-For 头。
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# 类型别名
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
DeviceId = Annotated[str | None, Depends(get_device_id)]
