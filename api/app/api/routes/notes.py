"""
笔记/高亮/书签 API 路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.api.schemas.note import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
    DeleteResponse,
    HighlightCreate,
    HighlightListResponse,
    HighlightResponse,
    HighlightUpdate,
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)
from app.services.note_service import NoteService

router = APIRouter(tags=["笔记与标注"])


# ============================================================================
# 笔记
# ============================================================================


@router.post("/notes", response_model=NoteResponse)
async def create_note(
    request: NoteCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteResponse:
    """创建笔记"""
    service = NoteService(db)
    note = await service.create_note(
        user_id=str(current_user.id),
        book_id=request.book_id,
        position_json=request.position_json,
        content=request.content,
        tags=request.tags,
        color=request.color,
    )
    return _note_to_response(note)


@router.get("/notes", response_model=NoteListResponse)
async def list_notes(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    book_id: str | None = Query(None, description="按书籍筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NoteListResponse:
    """获取笔记列表"""
    service = NoteService(db)
    notes, total = await service.list_notes(
        user_id=str(current_user.id),
        book_id=book_id,
        page=page,
        page_size=page_size,
    )
    return NoteListResponse(
        items=[_note_to_response(n) for n in notes],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteResponse:
    """获取笔记详情"""
    service = NoteService(db)
    note = await service.get_note(note_id, str(current_user.id))
    return _note_to_response(note)


@router.patch("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    request: NoteUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteResponse:
    """更新笔记"""
    service = NoteService(db)
    note = await service.update_note(
        note_id=note_id,
        user_id=str(current_user.id),
        content=request.content,
        tags=request.tags,
        color=request.color,
    )
    return _note_to_response(note)


@router.delete("/notes/{note_id}", response_model=DeleteResponse)
async def delete_note(
    note_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteResponse:
    """删除笔记"""
    service = NoteService(db)
    await service.delete_note(note_id, str(current_user.id))
    return DeleteResponse(id=note_id, deleted=True)


# ============================================================================
# 高亮
# ============================================================================


@router.post("/highlights", response_model=HighlightResponse)
async def create_highlight(
    request: HighlightCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HighlightResponse:
    """创建高亮"""
    service = NoteService(db)
    highlight = await service.create_highlight(
        user_id=str(current_user.id),
        book_id=request.book_id,
        position_json=request.position_json,
        color=request.color,
        text_preview=request.text_preview,
    )
    return _highlight_to_response(highlight)


@router.get("/books/{book_id}/highlights", response_model=HighlightListResponse)
async def list_book_highlights(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HighlightListResponse:
    """获取书籍的所有高亮"""
    service = NoteService(db)
    highlights, total = await service.list_highlights(
        user_id=str(current_user.id),
        book_id=book_id,
    )
    return HighlightListResponse(
        items=[_highlight_to_response(h) for h in highlights],
        total=total,
    )


@router.patch("/highlights/{highlight_id}", response_model=HighlightResponse)
async def update_highlight(
    highlight_id: str,
    request: HighlightUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HighlightResponse:
    """更新高亮"""
    service = NoteService(db)
    highlight = await service.update_highlight(
        highlight_id=highlight_id,
        user_id=str(current_user.id),
        color=request.color,
    )
    return _highlight_to_response(highlight)


@router.delete("/highlights/{highlight_id}", response_model=DeleteResponse)
async def delete_highlight(
    highlight_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteResponse:
    """删除高亮"""
    service = NoteService(db)
    await service.delete_highlight(highlight_id, str(current_user.id))
    return DeleteResponse(id=highlight_id, deleted=True)


# ============================================================================
# 书签
# ============================================================================


@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    request: BookmarkCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookmarkResponse:
    """创建书签"""
    service = NoteService(db)
    bookmark = await service.create_bookmark(
        user_id=str(current_user.id),
        book_id=request.book_id,
        position_json=request.position_json,
        title=request.title,
    )
    return _bookmark_to_response(bookmark)


@router.get("/books/{book_id}/bookmarks", response_model=BookmarkListResponse)
async def list_book_bookmarks(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookmarkListResponse:
    """获取书籍的所有书签"""
    service = NoteService(db)
    bookmarks, total = await service.list_bookmarks(
        user_id=str(current_user.id),
        book_id=book_id,
    )
    return BookmarkListResponse(
        items=[_bookmark_to_response(b) for b in bookmarks],
        total=total,
    )


@router.delete("/bookmarks/{bookmark_id}", response_model=DeleteResponse)
async def delete_bookmark(
    bookmark_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeleteResponse:
    """删除书签"""
    service = NoteService(db)
    await service.delete_bookmark(bookmark_id, str(current_user.id))
    return DeleteResponse(id=bookmark_id, deleted=True)


# ============================================================================
# 转换函数
# ============================================================================


def _note_to_response(note) -> NoteResponse:
    return NoteResponse(
        id=str(note.id),
        book_id=str(note.book_id),
        position_json=note.position_json,
        content=note.content,
        tags=note.tags or [],
        color=note.color,
        conflict_of=str(note.conflict_of) if note.conflict_of else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _highlight_to_response(highlight) -> HighlightResponse:
    return HighlightResponse(
        id=str(highlight.id),
        book_id=str(highlight.book_id),
        position_json=highlight.position_json,
        color=highlight.color,
        text_preview=highlight.text_preview,
        created_at=highlight.created_at,
        updated_at=highlight.updated_at,
    )


def _bookmark_to_response(bookmark) -> BookmarkResponse:
    return BookmarkResponse(
        id=str(bookmark.id),
        book_id=str(bookmark.book_id),
        position_json=bookmark.position_json,
        title=bookmark.title,
        created_at=bookmark.created_at,
    )
