"""
认证 API 路由

处理用户认证、登录、注册等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DeviceId, get_client_ip, get_db
from app.api.schemas.auth import (
    AuthResponse,
    CodeSentResponse,
    EmailCodeRequest,
    EmailVerifyRequest,
    SessionResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.core.config import settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/email/send_code", response_model=CodeSentResponse)
async def send_email_code(
    request: EmailCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CodeSentResponse:
    """
    发送邮箱验证码

    向指定邮箱发送 6 位数字验证码，有效期 10 分钟。
    每分钟最多发送一次。
    """
    service = AuthService(db)
    _, expires_in = await service.send_email_code(request.email)

    return CodeSentResponse(
        message="code_sent",
        expires_in=expires_in,
    )


@router.post("/email/verify_code", response_model=AuthResponse)
async def verify_email_code(
    request: EmailVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    http_request: Request,
) -> AuthResponse:
    """
    验证邮箱验证码并登录

    验证成功后：
    - 如果是新用户，自动创建账户
    - 返回访问令牌和用户信息
    - 如果提供了邀请码，自动关联邀请关系
    """
    service = AuthService(db)
    ip_address = get_client_ip(http_request)

    user, access_token, refresh_token = await service.verify_email_code(
        email=request.email,
        code=request.code,
        device_id=request.device_id,
        device_name=request.device_name,
        ip_address=ip_address,
        invite_code=request.invite_code,
    )

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.auth.access_token_expire_minutes * 60,
        ),
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            membership_tier=user.membership_tier,
            membership_expire_at=user.membership_expire_at,
            language=user.language,
            timezone=user.timezone,
            invite_code=user.invite_code,
            created_at=user.created_at,
        ),
    )


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌。
    """
    service = AuthService(db)
    access_token, refresh_token = await service.refresh_tokens(request.refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.auth.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """
    获取当前用户信息

    返回当前认证用户的详细信息。
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        membership_tier=current_user.membership_tier,
        membership_expire_at=current_user.membership_expire_at,
        language=current_user.language,
        timezone=current_user.timezone,
        invite_code=current_user.invite_code,
        created_at=current_user.created_at,
    )


@router.post("/logout")
async def logout(
    current_user: CurrentUser,
    device_id: DeviceId,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """
    登出当前会话

    撤销当前设备的会话。
    """
    if device_id:
        from sqlalchemy import select, update
        from app.models.user import UserSession

        await db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == current_user.id,
                UserSession.device_id == device_id,
                UserSession.revoked == False,
            )
            .values(revoked=True)
        )
        await db.commit()

    return {"message": "logged_out"}


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    device_id: DeviceId,
) -> list[SessionResponse]:
    """
    获取所有活跃会话

    返回当前用户的所有活跃登录会话。
    """
    from sqlalchemy import select
    from app.models.user import UserSession

    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.revoked == False,
        )
        .order_by(UserSession.created_at.desc())
    )
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=str(s.id),
            device_id=s.device_id,
            device_name=s.device_name,
            device_type=s.device_type,
            ip_address=s.ip_address,
            created_at=s.created_at,
            last_active_at=s.last_active_at,
            is_current=s.device_id == device_id if device_id else False,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """
    撤销指定会话

    登出指定设备的会话。
    """
    service = AuthService(db)
    await service.revoke_session(session_id, str(current_user.id))

    return {"message": "session_revoked"}
