"""
阅读进度与统计相关模型

包含 BookPosition, ReadingTimeLog, ReadingDaily 等表。
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.book import Book


class BookPosition(Base, TimestampMixin):
    """阅读位置记录 (PowerSync 同步)"""

    __tablename__ = "book_position"

    # 复合主键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 阅读进度
    progress: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)  # 0-1

    # 位置信息
    last_cfi: Mapped[str | None] = mapped_column(Text, nullable=True)  # EPUB CFI
    last_page: Mapped[int | None] = mapped_column(Integer, nullable=True)  # PDF 页码
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 完成状态
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 版本追踪 (用于增量同步)
    ocr_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vector_index_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 设备信息
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 关系
    book: Mapped["Book"] = relationship("Book", back_populates="position")

    def __repr__(self) -> str:
        return f"<BookPosition user={self.user_id} book={self.book_id} progress={self.progress}>"


class ReadingTimeLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """阅读时长记录 (每次打开阅读器创建一条)"""

    __tablename__ = "reading_time_log"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 设备信息
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 会话状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 阅读时长 (毫秒)
    duration_ms: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # 最后活跃时间
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # 关系
    book: Mapped["Book"] = relationship("Book", back_populates="reading_logs")

    __table_args__ = (
        Index("idx_reading_time_log_user_book", "user_id", "book_id"),
        Index("idx_reading_time_log_active", "is_active", postgresql_where="is_active = true"),
    )

    def __repr__(self) -> str:
        return f"<ReadingTimeLog {self.id} user={self.user_id} duration={self.duration_ms}ms>"


class ReadingDaily(Base):
    """每日阅读统计 (仅服务端，不同步)"""

    __tablename__ = "reading_daily"

    # 复合主键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)

    # 统计数据
    total_duration_ms: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    books_read: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_read: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    __table_args__ = (
        Index("idx_reading_daily_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<ReadingDaily user={self.user_id} day={self.day}>"
