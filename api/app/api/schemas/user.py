"""
用户管理相关 Pydantic 模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AccountDeleteRequest(BaseModel):
    """账号注销请求"""

    reason: str | None = Field(None, max_length=500, description="注销原因")
    feedback: str | None = Field(None, max_length=2000, description="反馈信息")


class AccountDeleteResponse(BaseModel):
    """账号注销响应"""

    success: bool
    message: str
    deletion_scheduled_at: datetime


class NotificationSettingsUpdate(BaseModel):
    """通知设置更新"""

    ocr_notifications: bool | None = None
    subscription_alerts: bool | None = None
    reading_reminders: bool | None = None
    reminder_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    marketing_notifications: bool | None = None


class NotificationSettingsResponse(BaseModel):
    """通知设置响应"""

    ocr_notifications: bool = True
    subscription_alerts: bool = True
    reading_reminders: bool = True
    reminder_time: str = "20:00"
    marketing_notifications: bool = False
    updated_at: datetime | None = None
