"""
笔记与高亮相关模型

包含 Note, Highlight, Bookmark, Tag 等表。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.book import Book


class Note(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """用户笔记 (启用 RLS)"""

    __tablename__ = "notes"

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

    # 笔记内容
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 位置信息
    chapter: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)  # CFI 或页码
    pos_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 全文检索 (PostgreSQL TSVECTOR)
    tsv: Mapped[Any | None] = mapped_column(TSVECTOR, nullable=True)

    # 设备与冲突
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conflict_of: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 关系
    book: Mapped["Book"] = relationship("Book", back_populates="notes")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="note_tags",
        back_populates="notes",
    )
    conflict_source: Mapped["Note | None"] = relationship(
        "Note",
        remote_side="Note.id",
        foreign_keys=[conflict_of],
    )

    __table_args__ = (
        Index("idx_notes_user_book", "user_id", "book_id"),
        Index("idx_notes_tsv", "tsv", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Note {self.id} book={self.book_id}>"


class Highlight(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """高亮标注 (启用 RLS)"""

    __tablename__ = "highlights"

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

    # 高亮范围
    start_location: Mapped[str] = mapped_column(Text, nullable=False)
    end_location: Mapped[str] = mapped_column(Text, nullable=False)

    # 高亮内容 (选中的文本)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 样式
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # yellow/green/blue/pink/purple

    # 附加评论
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 全文检索
    tsv: Mapped[Any | None] = mapped_column(TSVECTOR, nullable=True)

    # 设备与冲突
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conflict_of: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("highlights.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 关系
    book: Mapped["Book"] = relationship("Book", back_populates="highlights")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="highlight_tags",
        back_populates="highlights",
    )
    conflict_source: Mapped["Highlight | None"] = relationship(
        "Highlight",
        remote_side="Highlight.id",
        foreign_keys=[conflict_of],
    )

    __table_args__ = (
        Index("idx_highlights_user_book", "user_id", "book_id"),
        Index("idx_highlights_tsv", "tsv", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Highlight {self.id} book={self.book_id}>"


class Bookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """书签"""

    __tablename__ = "bookmarks"

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

    # 位置信息
    location: Mapped[str] = mapped_column(Text, nullable=False)  # CFI 或页码
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 可选标题
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 设备
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 关系
    book: Mapped["Book"] = relationship("Book", back_populates="bookmarks")

    __table_args__ = (
        Index("idx_bookmarks_user_book", "user_id", "book_id"),
    )

    def __repr__(self) -> str:
        return f"<Bookmark {self.id} book={self.book_id}>"


class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """标签系统 (启用 RLS)"""

    __tablename__ = "tags"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # 关系
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        secondary="note_tags",
        back_populates="tags",
    )
    highlights: Mapped[list["Highlight"]] = relationship(
        "Highlight",
        secondary="highlight_tags",
        back_populates="tags",
    )

    __table_args__ = (
        Index("idx_tags_user_name", "user_id", "name", unique=True, postgresql_where="deleted_at IS NULL"),
    )

    def __repr__(self) -> str:
        return f"<Tag {self.id} '{self.name}'>"


class NoteTag(Base):
    """笔记-标签关联表"""

    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )


class HighlightTag(Base):
    """高亮-标签关联表"""

    __tablename__ = "highlight_tags"

    highlight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("highlights.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )
