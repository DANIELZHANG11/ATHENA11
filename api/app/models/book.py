"""
书籍与资产相关模型

包含 Book, Shelf, ShelfBook 等表。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    BigInteger,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.note import Note, Highlight, Bookmark
    from app.models.reading import BookPosition, ReadingTimeLog


class Book(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """核心书籍表"""

    __tablename__ = "books"

    # 所属用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 基本信息
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # 文件信息
    original_format: Mapped[str | None] = mapped_column(String(20), nullable=True)  # epub/pdf/mobi
    minio_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 文件大小 (bytes)
    cover_image_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_etag: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 上传幂等性

    # 文字层检测
    # True=文字型, False=图片型, None=未检测
    has_text_layer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    text_layer_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    # 格式转换
    converted_epub_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 处理状态
    processing_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )  # pending/processing/converting/ocr_pending/ocr_processing/ready/failed
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    reader_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # pdf/epub
    is_readable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_interactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OCR 相关
    ocr_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # deprecated
    ocr_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ocr_pdf_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # 双层 PDF

    # 向量索引
    vector_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    digitalize_report_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 元数据确认
    metadata_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # SHA256 去重
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    storage_ref_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    canonical_book_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 扩展元数据
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="books")
    canonical_book: Mapped["Book | None"] = relationship(
        "Book",
        remote_side="Book.id",
        foreign_keys=[canonical_book_id],
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        back_populates="book",
        lazy="dynamic",
    )
    highlights: Mapped[list["Highlight"]] = relationship(
        "Highlight",
        back_populates="book",
        lazy="dynamic",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="book",
        lazy="dynamic",
    )
    shelf_books: Mapped[list["ShelfBook"]] = relationship(
        "ShelfBook",
        back_populates="book",
        lazy="dynamic",
    )
    position: Mapped["BookPosition | None"] = relationship(
        "BookPosition",
        back_populates="book",
        uselist=False,
    )
    reading_logs: Mapped[list["ReadingTimeLog"]] = relationship(
        "ReadingTimeLog",
        back_populates="book",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("idx_books_content_sha256", "content_sha256", postgresql_where=content_sha256.isnot(None)),
        Index("idx_books_user_deleted", "user_id", "deleted_at"),
    )

    @property
    def is_image_based(self) -> bool:
        """判断是否为图片型书籍 (需要 OCR)"""
        if self.has_text_layer is False:
            return True
        if self.has_text_layer is True and self.text_layer_confidence is not None:
            return float(self.text_layer_confidence) < 0.8
        return self.has_text_layer is None

    @property
    def is_reference(self) -> bool:
        """判断是否为去重引用书"""
        return self.canonical_book_id is not None

    def __repr__(self) -> str:
        return f"<Book {self.id} '{self.title}'>"


class Shelf(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """书架"""

    __tablename__ = "shelves"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 系统书架标记
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    system_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # favorites/want_to_read/reading/finished

    # 关系
    shelf_books: Mapped[list["ShelfBook"]] = relationship(
        "ShelfBook",
        back_populates="shelf",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Shelf {self.id} '{self.name}'>"


class ShelfBook(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """书架-书籍关联表"""

    __tablename__ = "shelf_books"

    shelf_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shelves.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 冗余存储用户 ID，用于 PowerSync 同步过滤
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # 关系
    shelf: Mapped["Shelf"] = relationship("Shelf", back_populates="shelf_books")
    book: Mapped["Book"] = relationship("Book", back_populates="shelf_books")

    __table_args__ = (
        Index("idx_shelf_books_unique", "shelf_id", "book_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ShelfBook shelf={self.shelf_id} book={self.book_id}>"


class ConversionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """书籍格式转换任务"""

    __tablename__ = "conversion_jobs"

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

    source_key: Mapped[str] = mapped_column(Text, nullable=False)
    target_format: Mapped[str] = mapped_column(String(20), nullable=False)
    output_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending/processing/completed/failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 进度追踪
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ConversionJob {self.id} {self.status}>"
