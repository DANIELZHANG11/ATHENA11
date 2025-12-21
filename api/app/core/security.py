"""
安全相关工具

包含密码哈希、JWT 令牌生成与验证等功能。
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT 令牌载荷"""

    sub: str  # user_id
    aud: str = "authenticated"  # PowerSync Supabase 模式要求
    exp: datetime
    iat: datetime
    type: str = "access"  # access / refresh


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    创建访问令牌

    Args:
        subject: 令牌主体 (通常是 user_id)
        expires_delta: 过期时间增量
        extra_claims: 额外的 JWT claims

    Returns:
        JWT 字符串
    """
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.auth.access_token_expire_minutes)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "aud": "authenticated",  # 必须：PowerSync Supabase 模式要求
        "iat": now,
        "exp": expire,
        "type": "access",
    }

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(
        to_encode,
        settings.auth.auth_secret,
        algorithm=settings.auth.auth_algorithm,
    )


def create_refresh_token(subject: str) -> str:
    """
    创建刷新令牌

    Args:
        subject: 令牌主体 (通常是 user_id)

    Returns:
        JWT 字符串
    """
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.auth.refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "aud": "authenticated",
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        to_encode,
        settings.auth.auth_secret,
        algorithm=settings.auth.auth_algorithm,
    )


def decode_token(token: str) -> TokenPayload | None:
    """
    解码并验证 JWT 令牌

    Args:
        token: JWT 字符串

    Returns:
        TokenPayload 或 None (验证失败)
    """
    try:
        payload = jwt.decode(
            token,
            settings.auth.auth_secret,
            algorithms=[settings.auth.auth_algorithm],
            audience="authenticated",
        )
        return TokenPayload(
            sub=payload["sub"],
            aud=payload.get("aud", "authenticated"),
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            type=payload.get("type", "access"),
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_token(token: str, token_type: str = "access") -> TokenPayload | None:
    """
    验证 JWT 令牌

    Args:
        token: JWT 字符串
        token_type: 期望的令牌类型 (access/refresh)

    Returns:
        TokenPayload 或 None (验证失败)
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.type != token_type:
        return None
    return payload


def generate_auth_code() -> str:
    """生成 6 位数字验证码"""
    import secrets

    return f"{secrets.randbelow(1000000):06d}"
