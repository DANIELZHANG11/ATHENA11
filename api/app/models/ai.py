"""
AI 对话相关模型

包含 AiModel, AiConversation, AiMessage, AiQueryCache 等表。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    pass


class AiModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 模型配置表"""

    __tablename__ = "ai_models"

    # 模型标识
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # openai/anthropic/local

    # 模型参数
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)  # gpt-4o-mini
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    temperature: Mapped[float] = mapped_column(Numeric(3, 2), default=0.7, nullable=False)

    # 定价
    input_price_per_1k: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)
    output_price_per_1k: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 能力标记
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_function_call: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AiModel {self.name}>"


class AiConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 对话会话"""

    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 会话信息
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 会话类型
    conversation_type: Mapped[str] = mapped_column(
        String(20),
        default="chat",
        nullable=False,
    )  # chat/translate/summarize/explain

    # 统计
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)

    # 状态
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关系
    messages: Mapped[list["AiMessage"]] = relationship(
        "AiMessage",
        back_populates="conversation",
        lazy="dynamic",
        order_by="AiMessage.created_at",
    )
    contexts: Mapped[list["AiConversationContext"]] = relationship(
        "AiConversationContext",
        back_populates="conversation",
        lazy="dynamic",
    )

    __table_args__ = (
        Index("idx_ai_conversations_user_book", "user_id", "book_id"),
    )

    def __repr__(self) -> str:
        return f"<AiConversation {self.id} user={self.user_id}>"


class AiMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 对话消息"""

    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 消息内容
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant/system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Token 统计
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)

    # 元数据
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    finish_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)  # stop/length/content_filter
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 关系
    conversation: Mapped["AiConversation"] = relationship(
        "AiConversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<AiMessage {self.id} role={self.role}>"


class AiConversationContext(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 对话上下文 (关联的书籍片段)"""

    __tablename__ = "ai_conversation_contexts"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 上下文类型
    context_type: Mapped[str] = mapped_column(String(20), nullable=False)  # highlight/note/page/search

    # 关联信息
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    highlight_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    note_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # 上下文内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 关系
    conversation: Mapped["AiConversation"] = relationship(
        "AiConversation",
        back_populates="contexts",
    )

    def __repr__(self) -> str:
        return f"<AiConversationContext {self.id} type={self.context_type}>"


class AiQueryCache(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 查询缓存 (用于常见问题)"""

    __tablename__ = "ai_query_cache"

    # 缓存键
    query_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)

    # 缓存值
    response: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # 使用统计
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 过期时间
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AiQueryCache {self.query_hash[:8]}...>"


class PromptTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Prompt 模板"""

    __tablename__ = "prompt_templates"

    # 模板标识
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # chat/translate/summarize

    # 模板内容
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 参数
    variables: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<PromptTemplate {self.name}>"
