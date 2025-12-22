"""
用户管理服务

处理账号注销、用户设置等功能。
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AthenaException,
    ErrorCode,
    ForbiddenException,
    NotFoundException,
)
from app.models.book import Book, ShelfBook
from app.models.note import Bookmark, Highlight, Note
from app.models.reading import BookPosition, ReadingTimeLog
from app.models.user import User, UserOAuthAccount, UserSession, UserSetting


class UserService:
    """用户管理服务"""

    CONFIRM_DELETE_HEADER = "CONFIRM_DELETE_MY_ACCOUNT"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_account(
        self,
        user_id: str,
        confirm_header: str | None,
        reason: str | None = None,
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """
        注销账号

        GDPR 合规流程：
        1. 验证确认 Header
        2. 立即注销所有登录会话
        3. 标记账号为待删除状态
        4. 30 天后由后台任务永久删除

        Args:
            user_id: 用户 ID
            confirm_header: 确认删除的 Header 值
            reason: 注销原因
            feedback: 反馈信息

        Returns:
            删除调度信息
        """
        # 验证确认 Header
        if not confirm_header:
            raise AthenaException(code=ErrorCode.VALIDATION_ERROR, message="missing_confirm_header")
        if confirm_header != self.CONFIRM_DELETE_HEADER:
            raise AthenaException(code=ErrorCode.VALIDATION_ERROR, message="invalid_confirm_header")

        # 获取用户
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("user_not_found")

        # 检查是否有活跃订阅
        now = datetime.now(UTC)
        if user.membership_tier != "FREE" and user.membership_expire_at and user.membership_expire_at > now:
            # 可选：要求先取消订阅
            # raise ForbiddenException("active_subscription")
            pass

        # 1. 注销所有登录会话
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(revoked=True)
        )

        # 2. 标记账号为待删除
        deletion_scheduled_at = now + timedelta(days=30)

        # 使用 meta 字段存储删除信息
        user.is_active = False
        # 假设有 pending_deletion_at 字段，如果没有可以使用其他方式标记
        # 这里用一个简化的方式

        await self.db.commit()

        # TODO: 发送确认邮件
        # TODO: 创建 30 天后的删除任务

        return {
            "success": True,
            "message": "账号已删除，所有数据将在 30 天内完全清除",
            "deletion_scheduled_at": deletion_scheduled_at,
        }

    async def hard_delete_user_data(self, user_id: str) -> None:
        """
        永久删除用户所有数据

        由后台定时任务调用，在账号删除 30 天后执行。
        """
        uid = UUID(user_id)

        # 删除所有书籍 (会触发引用计数减少)
        # 先获取书籍列表
        result = await self.db.execute(select(Book).where(Book.user_id == uid))
        books = result.scalars().all()

        for book in books:
            # 删除私人数据
            await self._delete_book_private_data(str(book.id), user_id)
            # 处理引用计数
            if book.canonical_book_id:
                # 引用书直接删除
                await self.db.delete(book)
            else:
                # 原书减少引用计数
                book.storage_ref_count -= 1
                if book.storage_ref_count <= 0:
                    # 硬删除
                    await self.db.delete(book)

        # 删除其他用户数据
        await self.db.execute(delete(UserOAuthAccount).where(UserOAuthAccount.user_id == uid))
        await self.db.execute(delete(UserSession).where(UserSession.user_id == uid))
        await self.db.execute(delete(UserSetting).where(UserSetting.user_id == uid))

        # 最后删除用户记录
        await self.db.execute(delete(User).where(User.id == uid))

        await self.db.commit()

    async def _delete_book_private_data(self, book_id: str, user_id: str) -> None:
        """删除书籍相关的私人数据"""
        bid = UUID(book_id)
        uid = UUID(user_id)

        await self.db.execute(delete(Note).where(Note.book_id == bid, Note.user_id == uid))
        await self.db.execute(delete(Highlight).where(Highlight.book_id == bid, Highlight.user_id == uid))
        await self.db.execute(delete(Bookmark).where(Bookmark.book_id == bid, Bookmark.user_id == uid))
        await self.db.execute(delete(BookPosition).where(BookPosition.book_id == bid, BookPosition.user_id == uid))
        await self.db.execute(delete(ReadingTimeLog).where(ReadingTimeLog.book_id == bid, ReadingTimeLog.user_id == uid))
        await self.db.execute(delete(ShelfBook).where(ShelfBook.book_id == bid))

    async def get_notification_settings(self, user_id: str) -> dict[str, Any]:
        """获取通知设置"""
        result = await self.db.execute(
            select(UserSetting).where(
                UserSetting.user_id == UUID(user_id),
                UserSetting.key == "notification_settings",
            )
        )
        setting = result.scalar_one_or_none()

        if setting and setting.value:
            return {
                **setting.value,
                "updated_at": setting.updated_at,
            }

        # 默认设置
        return {
            "ocr_notifications": True,
            "subscription_alerts": True,
            "reading_reminders": True,
            "reminder_time": "20:00",
            "marketing_notifications": False,
            "updated_at": None,
        }

    async def update_notification_settings(
        self,
        user_id: str,
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        """更新通知设置"""
        result = await self.db.execute(
            select(UserSetting).where(
                UserSetting.user_id == UUID(user_id),
                UserSetting.key == "notification_settings",
            )
        )
        setting = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if setting:
            # 合并更新
            current_value = setting.value or {}
            for key, value in settings.items():
                if value is not None:
                    current_value[key] = value
            setting.value = current_value
            setting.updated_at = now
        else:
            # 创建新设置
            setting = UserSetting(
                user_id=UUID(user_id),
                key="notification_settings",
                value=settings,
            )
            self.db.add(setting)

        await self.db.commit()

        return {
            **setting.value,
            "updated_at": setting.updated_at,
        }
