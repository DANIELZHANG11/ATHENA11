"""
AI API 路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.api.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIMessageListResponse,
    AIMessageResponse,
    AISessionCreate,
    AISessionListResponse,
    AISessionResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from app.api.schemas.note import DeleteResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI 助手"])


# ============================================================================
# 会话管理
# ============================================================================


@router.post("/sessions", response_model=AISessionResponse)
async def create_session(
    request: AISessionCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AISessionResponse:
    """创建 AI 会话"""
    service = AIService(db)
    session = await service.create_session(
        user_id=str(current_user.id),
        book_id=request.book_id,
        title=request.title,
        model=request.model,
    )
    return _session_to_response(session)


@router.get("/sessions", response_model=AISessionListResponse)
async def list_sessions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    book_id: str | None = Query(None, description="按书籍筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AISessionListResponse:
    """获取 AI 会话列表"""
    service = AIService(db)
    sessions, total = await service.list_sessions(
        user_id=str(current_user.id),
        book_id=book_id,
        page=page,
        page_size=page_size,
    )
    return AISessionListResponse(
        items=[_session_to_response(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.get("/sessions/{session_id}", response_model=AISessionResponse)
async def get_session(
    session_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AISessionResponse:
    """获取 AI 会话详情"""
    service = AIService(db)
    session = await service.get_session(session_id, str(current_user.id))
    return _session_to_response(session)


@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteResponse:
    """删除 AI 会话"""
    service = AIService(db)
    await service.delete_session(session_id, str(current_user.id))
    return DeleteResponse(id=session_id, deleted=True)


# ============================================================================
# 消息
# ============================================================================


@router.get("/sessions/{session_id}/messages", response_model=AIMessageListResponse)
async def get_session_messages(
    session_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIMessageListResponse:
    """获取会话的所有消息"""
    service = AIService(db)
    messages = await service.get_session_messages(
        session_id=session_id,
        user_id=str(current_user.id),
    )
    return AIMessageListResponse(
        items=[_message_to_response(m) for m in messages],
        total=len(messages),
    )


# ============================================================================
# 对话
# ============================================================================


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    request: AIChatRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    发送聊天消息

    如果不提供 session_id，会自动创建新会话。
    如果设置 stream=true，返回 SSE 流。
    """
    service = AIService(db)

    if request.stream:
        # 流式响应
        return StreamingResponse(
            service.chat_stream(
                user_id=str(current_user.id),
                message=request.message,
                session_id=request.session_id,
                book_id=request.book_id,
            ),
            media_type="text/event-stream",
        )

    # 普通响应
    result = await service.chat(
        user_id=str(current_user.id),
        message=request.message,
        session_id=request.session_id,
        book_id=request.book_id,
    )

    return AIChatResponse(
        session_id=result["session_id"],
        message=_message_to_response(result["message"]),
        tokens_used=result["tokens_used"],
    )


# ============================================================================
# 向量检索
# ============================================================================


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VectorSearchResponse:
    """
    语义搜索

    在用户的书籍中进行向量相似度搜索。
    """
    service = AIService(db)
    results = await service.vector_search(
        user_id=str(current_user.id),
        query=request.query,
        book_ids=request.book_ids,
        top_k=request.top_k,
    )

    return VectorSearchResponse(
        query=request.query,
        results=[
            VectorSearchResult(
                book_id=r["book_id"],
                book_title=r["book_title"],
                chunk_index=r["chunk_index"],
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ],
        total=len(results),
    )


# ============================================================================
# 转换函数
# ============================================================================


def _session_to_response(session) -> AISessionResponse:
    return AISessionResponse(
        id=str(session.id),
        book_id=str(session.book_id) if session.book_id else None,
        title=session.title,
        model=session.model,
        message_count=getattr(session, "message_count", 0),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _message_to_response(message) -> AIMessageResponse:
    return AIMessageResponse(
        id=str(message.id),
        session_id=str(message.session_id),
        role=message.role,
        content=message.content,
        tokens_used=message.tokens_used,
        created_at=message.created_at,
    )
