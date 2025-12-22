"""
AI 相关 Pydantic 模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ============================================================================
# AI 会话
# ============================================================================


class AISessionCreate(BaseModel):
    """创建 AI 会话"""

    book_id: str | None = Field(None, description="关联的书籍 ID")
    title: str | None = Field(None, max_length=255, description="会话标题")
    model: str = Field("gpt-4o-mini", max_length=50, description="使用的模型")


class AISessionResponse(BaseModel):
    """AI 会话响应"""

    id: str
    book_id: str | None
    title: str | None
    model: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AISessionListResponse(BaseModel):
    """AI 会话列表响应"""

    items: list[AISessionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# AI 消息
# ============================================================================


class AIMessageCreate(BaseModel):
    """发送 AI 消息"""

    content: str = Field(..., min_length=1, max_length=100000, description="消息内容")


class AIMessageResponse(BaseModel):
    """AI 消息响应"""

    id: str
    session_id: str
    role: str  # user, assistant, system
    content: str
    tokens_used: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class AIMessageListResponse(BaseModel):
    """AI 消息列表响应"""

    items: list[AIMessageResponse]
    total: int


class AIChatRequest(BaseModel):
    """AI 聊天请求"""

    session_id: str | None = Field(None, description="会话 ID，不提供则创建新会话")
    book_id: str | None = Field(None, description="关联的书籍 ID（新会话时使用）")
    message: str = Field(..., min_length=1, max_length=100000, description="用户消息")
    stream: bool = Field(False, description="是否流式响应")


class AIChatResponse(BaseModel):
    """AI 聊天响应"""

    session_id: str
    message: AIMessageResponse
    tokens_used: int


# ============================================================================
# 向量检索
# ============================================================================


class VectorSearchRequest(BaseModel):
    """向量检索请求"""

    query: str = Field(..., min_length=1, max_length=1000, description="查询文本")
    book_ids: list[str] | None = Field(None, description="限定书籍范围")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")


class VectorSearchResult(BaseModel):
    """向量检索结果"""

    book_id: str
    book_title: str
    chunk_index: int
    content: str
    score: float
    metadata: dict | None


class VectorSearchResponse(BaseModel):
    """向量检索响应"""

    query: str
    results: list[VectorSearchResult]
    total: int
