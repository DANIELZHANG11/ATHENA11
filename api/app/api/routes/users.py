"""
用户管理 API 路由

处理账号注销、用户设置等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.user import (
    AccountDeleteRequest,
    AccountDeleteResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.delete("/me", response_model=AccountDeleteResponse)
async def delete_account(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_confirm_delete: Annotated[str | None, Header()] = None,
    request: AccountDeleteRequest | None = None,
) -> AccountDeleteResponse:
    """
    注销账号 (GDPR 合规)

    永久删除用户账号及所有关联数据。此操作不可逆。

    需要设置 Header: X-Confirm-Delete: CONFIRM_DELETE_MY_ACCOUNT
    """
    service = UserService(db)
    result = await service.delete_account(
        user_id=str(current_user.id),
        confirm_header=x_confirm_delete,
        reason=request.reason if request else None,
        feedback=request.feedback if request else None,
    )

    return AccountDeleteResponse(
        success=result["success"],
        message=result["message"],
        deletion_scheduled_at=result["deletion_scheduled_at"],
    )


@router.get("/me/notification-settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationSettingsResponse:
    """获取用户通知设置"""
    service = UserService(db)
    settings = await service.get_notification_settings(str(current_user.id))

    return NotificationSettingsResponse(
        ocr_notifications=settings.get("ocr_notifications", True),
        subscription_alerts=settings.get("subscription_alerts", True),
        reading_reminders=settings.get("reading_reminders", True),
        reminder_time=settings.get("reminder_time", "20:00"),
        marketing_notifications=settings.get("marketing_notifications", False),
        updated_at=settings.get("updated_at"),
    )


@router.patch("/me/notification-settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: NotificationSettingsUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationSettingsResponse:
    """更新用户通知设置"""
    service = UserService(db)
    settings = await service.update_notification_settings(
        user_id=str(current_user.id),
        settings=request.model_dump(exclude_none=True),
    )

    return NotificationSettingsResponse(
        ocr_notifications=settings.get("ocr_notifications", True),
        subscription_alerts=settings.get("subscription_alerts", True),
        reading_reminders=settings.get("reading_reminders", True),
        reminder_time=settings.get("reminder_time", "20:00"),
        marketing_notifications=settings.get("marketing_notifications", False),
        updated_at=settings.get("updated_at"),
    )
