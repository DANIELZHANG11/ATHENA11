"""
数据导出 API 路由

处理笔记、高亮等数据的导出功能。
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.export import (
    ExportBook,
    ExportHighlight,
    ExportNote,
    ExportSummary,
    NotesExportResponse,
)
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.get("/notes", response_model=NotesExportResponse)
async def export_notes(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    format: str = Query("markdown", pattern="^(markdown|json|html)$", description="导出格式"),
    book_id: str | None = Query(None, description="筛选指定书籍"),
    include_highlights: bool = Query(True, description="是否包含高亮"),
    date_from: datetime | None = Query(None, description="筛选起始日期"),
    date_to: datetime | None = Query(None, description="筛选结束日期"),
) -> NotesExportResponse:
    """
    导出笔记和高亮

    支持多种格式：Markdown、JSON、HTML。
    """
    service = ExportService(db)
    data = await service.export_notes(
        user_id=str(current_user.id),
        format=format,
        book_id=book_id,
        include_highlights=include_highlights,
        date_from=date_from,
        date_to=date_to,
    )

    return NotesExportResponse(
        exported_at=data["exported_at"],
        version=data["version"],
        format=data["format"],
        summary=ExportSummary(**data["summary"]),
        books=[
            ExportBook(
                id=b["id"],
                title=b["title"],
                author=b.get("author"),
                highlights=[
                    ExportHighlight(
                        id=h["id"],
                        content=h["content"],
                        location=h.get("location"),
                        color=h.get("color"),
                        created_at=h["created_at"],
                        tags=h.get("tags", []),
                    )
                    for h in b.get("highlights", [])
                ],
                notes=[
                    ExportNote(
                        id=n["id"],
                        title=n.get("title"),
                        content=n["content"],
                        location=n.get("location"),
                        linked_highlight_id=n.get("linked_highlight_id"),
                        created_at=n["created_at"],
                        updated_at=n["updated_at"],
                        tags=n.get("tags", []),
                    )
                    for n in b.get("notes", [])
                ],
            )
            for b in data.get("books", [])
        ],
        markdown_content=data.get("markdown_content"),
    )
