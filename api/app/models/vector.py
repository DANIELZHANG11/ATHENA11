"""
向量存储与搜索相关模型

使用 PostgreSQL pgvector 扩展存储向量数据。
"""

import uuid

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# pgvector 类型需要特殊处理
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # 如果 pgvector 未安装，使用占位符
    Vector = None  # type: ignore


class VectorDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """向量文档存储表"""

    __tablename__ = "vectors"

    # 关联信息
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 文档内容
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 位置信息
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter: Mapped[str | None] = mapped_column(Text, nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)  # CFI

    # 向量嵌入 (1536 维度，text-embedding-3-small)
    # 注意: 实际的 Vector 类型需要在迁移中定义
    # embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)

    # 元数据
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_vectors_book", "book_id"),
        Index("idx_vectors_user_book", "user_id", "book_id"),
        # HNSW 索引需要在迁移中单独创建:
        # CREATE INDEX idx_vectors_embedding_hnsw ON vectors
        # USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
    )

    def __repr__(self) -> str:
        return f"<VectorDocument {self.id} book={self.book_id} chunk={self.chunk_index}>"
