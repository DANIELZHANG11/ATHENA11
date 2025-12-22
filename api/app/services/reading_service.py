"""
阅读服务

处理阅读进度、时长记录、阅读统计等业务逻辑。
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundException
from app.models.book import Book
from app.models.reading import BookPosition, ReadingDaily, ReadingTimeLog


class ReadingService:
    """阅读服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================================================
    # 阅读位置 (BookPosition)
    # ==========================================================================

    async def get_position(self, user_id: str, book_id: str) -> BookPosition | None:
        """获取书籍阅读位置"""
        result = await self.db.execute(
            select(BookPosition).where(
                BookPosition.user_id == user_id,
                BookPosition.book_id == book_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_position(
        self,
        user_id: str,
        book_id: str,
        progress: float,
        last_cfi: str | None = None,
        last_page: int | None = None,
        total_pages: int | None = None,
        device_id: str | None = None,
    ) -> BookPosition:
        """更新阅读位置 (Upsert)"""
        # 验证书籍存在
        await self._get_book_or_404(book_id, user_id)

        # 计算是否读完
        finished_at = None
        if progress >= 0.99:
            finished_at = datetime.now(UTC)

        # Upsert 操作
        stmt = insert(BookPosition).values(
            user_id=user_id,
            book_id=book_id,
            progress=progress,
            last_cfi=last_cfi,
            last_page=last_page,
            total_pages=total_pages,
            device_id=device_id,
            finished_at=finished_at,
            updated_at=datetime.now(UTC),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "book_id"],
            set_={
                "progress": stmt.excluded.progress,
                "last_cfi": stmt.excluded.last_cfi,
                "last_page": stmt.excluded.last_page,
                "total_pages": stmt.excluded.total_pages,
                "device_id": stmt.excluded.device_id,
                "finished_at": func.coalesce(
                    BookPosition.finished_at, stmt.excluded.finished_at
                ),
                "updated_at": stmt.excluded.updated_at,
            },
        )

        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_position(user_id, book_id)  # type: ignore

    async def mark_finished(self, user_id: str, book_id: str) -> BookPosition:
        """标记书籍已读完"""
        position = await self.get_position(user_id, book_id)
        if not position:
            # 创建新记录
            position = BookPosition(
                user_id=user_id,
                book_id=book_id,
                progress=1.0,
                finished_at=datetime.now(UTC),
            )
            self.db.add(position)
        else:
            position.progress = 1.0
            position.finished_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(position)
        return position

    # ==========================================================================
    # 阅读时长记录 (ReadingTimeLog)
    # ==========================================================================

    async def start_reading_session(
        self,
        user_id: str,
        book_id: str,
        device_id: str | None = None,
    ) -> ReadingTimeLog:
        """开始阅读会话"""
        # 验证书籍
        await self._get_book_or_404(book_id, user_id)

        # 关闭该用户之前未关闭的会话
        await self.db.execute(
            update(ReadingTimeLog)
            .where(
                ReadingTimeLog.user_id == user_id,
                ReadingTimeLog.is_active == True,  # noqa: E712
            )
            .values(is_active=False)
        )

        # 创建新会话
        session = ReadingTimeLog(
            user_id=user_id,
            book_id=book_id,
            device_id=device_id,
            is_active=True,
            duration_ms=0,
            last_active_at=datetime.now(UTC),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def update_reading_session(
        self,
        session_id: str,
        user_id: str,
        duration_ms: int,
        is_active: bool = True,
    ) -> ReadingTimeLog | None:
        """更新阅读会话 (心跳/结束)"""
        result = await self.db.execute(
            select(ReadingTimeLog).where(
                ReadingTimeLog.id == session_id,
                ReadingTimeLog.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.duration_ms = duration_ms
        session.is_active = is_active
        session.last_active_at = datetime.now(UTC)

        # 如果会话结束，更新每日统计
        if not is_active:
            await self._update_daily_stats(user_id, duration_ms)

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def end_reading_session(
        self,
        session_id: str,
        user_id: str,
        final_duration_ms: int,
    ) -> ReadingTimeLog | None:
        """结束阅读会话"""
        return await self.update_reading_session(
            session_id=session_id,
            user_id=user_id,
            duration_ms=final_duration_ms,
            is_active=False,
        )

    async def get_active_session(self, user_id: str) -> ReadingTimeLog | None:
        """获取当前活跃会话"""
        result = await self.db.execute(
            select(ReadingTimeLog)
            .where(
                ReadingTimeLog.user_id == user_id,
                ReadingTimeLog.is_active == True,  # noqa: E712
            )
            .order_by(ReadingTimeLog.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ==========================================================================
    # 阅读统计 (ReadingStats)
    # ==========================================================================

    async def get_daily_stats(self, user_id: str, day: date) -> dict[str, Any]:
        """获取单日阅读统计"""
        result = await self.db.execute(
            select(ReadingDaily).where(
                ReadingDaily.user_id == user_id,
                ReadingDaily.day == day,
            )
        )
        daily = result.scalar_one_or_none()

        if daily:
            return {
                "day": daily.day,
                "total_duration_ms": daily.total_duration_ms,
                "books_read": daily.books_read,
                "pages_read": daily.pages_read,
            }
        return {
            "day": day,
            "total_duration_ms": 0,
            "books_read": 0,
            "pages_read": 0,
        }

    async def get_weekly_stats(self, user_id: str, week_start: date) -> dict[str, Any]:
        """获取周阅读统计"""
        week_end = week_start + timedelta(days=6)

        result = await self.db.execute(
            select(
                func.sum(ReadingDaily.total_duration_ms).label("total_ms"),
                func.sum(ReadingDaily.books_read).label("books"),
                func.count(ReadingDaily.day).label("days_active"),
            ).where(
                ReadingDaily.user_id == user_id,
                ReadingDaily.day >= week_start,
                ReadingDaily.day <= week_end,
            )
        )
        row = result.one()

        total_ms = row.total_ms or 0
        days_active = row.days_active or 0

        return {
            "week_start": week_start,
            "week_end": week_end,
            "total_duration_ms": total_ms,
            "daily_average_ms": total_ms // 7 if total_ms > 0 else 0,
            "books_read": row.books or 0,
            "days_active": days_active,
        }

    async def get_monthly_stats(self, user_id: str, year: int, month: int) -> dict[str, Any]:
        """获取月阅读统计"""
        # 计算月份范围
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # 统计阅读时长和天数
        result = await self.db.execute(
            select(
                func.sum(ReadingDaily.total_duration_ms).label("total_ms"),
                func.sum(ReadingDaily.books_read).label("books"),
                func.count(ReadingDaily.day).label("days_active"),
            ).where(
                ReadingDaily.user_id == user_id,
                ReadingDaily.day >= month_start,
                ReadingDaily.day <= month_end,
            )
        )
        row = result.one()

        # 统计读完的书
        finished_result = await self.db.execute(
            select(func.count(BookPosition.book_id)).where(
                BookPosition.user_id == user_id,
                BookPosition.finished_at >= datetime.combine(month_start, datetime.min.time()),
                BookPosition.finished_at < datetime.combine(
                    month_end + timedelta(days=1), datetime.min.time()
                ),
            )
        )
        books_finished = finished_result.scalar() or 0

        return {
            "year": year,
            "month": month,
            "total_duration_ms": row.total_ms or 0,
            "books_read": row.books or 0,
            "books_finished": books_finished,
            "days_active": row.days_active or 0,
        }

    async def get_reading_streak(self, user_id: str) -> int:
        """获取连续阅读天数"""
        today = date.today()

        # 获取最近的阅读记录
        result = await self.db.execute(
            select(ReadingDaily.day)
            .where(ReadingDaily.user_id == user_id)
            .order_by(ReadingDaily.day.desc())
            .limit(365)  # 最多查一年
        )
        days = [row.day for row in result.all()]

        if not days:
            return 0

        # 计算连续天数
        streak = 0
        expected_day = today

        for day in days:
            if day == expected_day:
                streak += 1
                expected_day -= timedelta(days=1)
            elif day == expected_day - timedelta(days=1):
                # 今天还没阅读，从昨天开始算
                streak += 1
                expected_day = day - timedelta(days=1)
            else:
                break

        return streak

    async def get_comprehensive_stats(self, user_id: str) -> dict[str, Any]:
        """获取综合阅读统计"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # 并行获取各项统计
        today_stats = await self.get_daily_stats(user_id, today)
        week_stats = await self.get_weekly_stats(user_id, week_start)
        month_stats = await self.get_monthly_stats(user_id, today.year, today.month)
        streak = await self.get_reading_streak(user_id)

        # 总计统计
        total_result = await self.db.execute(
            select(func.sum(ReadingDaily.total_duration_ms)).where(
                ReadingDaily.user_id == user_id
            )
        )
        total_duration = total_result.scalar() or 0

        # 书籍统计
        books_result = await self.db.execute(
            select(func.count(Book.id)).where(
                Book.user_id == user_id,
                Book.deleted_at.is_(None),
            )
        )
        total_books = books_result.scalar() or 0

        finished_result = await self.db.execute(
            select(func.count(BookPosition.book_id)).where(
                BookPosition.user_id == user_id,
                BookPosition.finished_at.isnot(None),
            )
        )
        finished_books = finished_result.scalar() or 0

        return {
            "today": today_stats,
            "this_week": week_stats,
            "this_month": month_stats,
            "streak_days": streak,
            "total_books": total_books,
            "finished_books": finished_books,
            "total_duration_ms": total_duration,
        }

    async def get_reading_history(
        self,
        user_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """获取阅读历史"""
        start_date = date.today() - timedelta(days=days - 1)

        result = await self.db.execute(
            select(ReadingDaily)
            .where(
                ReadingDaily.user_id == user_id,
                ReadingDaily.day >= start_date,
            )
            .order_by(ReadingDaily.day.desc())
        )
        records = result.scalars().all()

        return [
            {
                "day": r.day,
                "duration_ms": r.total_duration_ms,
                "books_read": r.books_read,
            }
            for r in records
        ]

    async def get_recent_books(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取最近阅读的书籍"""
        result = await self.db.execute(
            select(BookPosition, Book)
            .join(Book, BookPosition.book_id == Book.id)
            .where(
                BookPosition.user_id == user_id,
                Book.deleted_at.is_(None),
            )
            .order_by(BookPosition.updated_at.desc())
            .limit(limit)
        )
        rows = result.all()

        return [
            {
                "book_id": str(pos.book_id),
                "title": book.title,
                "author": book.author,
                "cover_url": book.cover_key,  # 需要前端转换为实际 URL
                "progress": float(pos.progress),
                "last_read_at": pos.updated_at,
                "finished_at": pos.finished_at,
            }
            for pos, book in rows
        ]

    # ==========================================================================
    # 私有方法
    # ==========================================================================

    async def _get_book_or_404(self, book_id: str, user_id: str) -> Book:
        """获取书籍或抛出 404"""
        result = await self.db.execute(
            select(Book).where(
                Book.id == book_id,
                Book.user_id == user_id,
                Book.deleted_at.is_(None),
            )
        )
        book = result.scalar_one_or_none()
        if not book:
            raise BookNotFoundException()
        return book

    async def _update_daily_stats(self, user_id: str, duration_ms: int) -> None:
        """更新每日统计 (Upsert)"""
        today = date.today()

        stmt = insert(ReadingDaily).values(
            user_id=user_id,
            day=today,
            total_duration_ms=duration_ms,
            books_read=1,
            pages_read=0,
            updated_at=datetime.now(UTC),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "day"],
            set_={
                "total_duration_ms": ReadingDaily.total_duration_ms + duration_ms,
                "updated_at": stmt.excluded.updated_at,
            },
        )

        await self.db.execute(stmt)
