"""
数据导出相关 Pydantic 模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ExportHighlight(BaseModel):
    """导出高亮"""

    id: str
    content: str
    location: dict | None = None
    color: str | None = None
    created_at: datetime
    tags: list[str] = []


class ExportNote(BaseModel):
    """导出笔记"""

    id: str
    title: str | None = None
    content: str
    location: dict | None = None
    linked_highlight_id: str | None = None
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []


class ExportBook(BaseModel):
    """导出书籍"""

    id: str
    title: str
    author: str | None = None
    highlights: list[ExportHighlight] = []
    notes: list[ExportNote] = []


class ExportSummary(BaseModel):
    """导出摘要"""

    total_notes: int
    total_highlights: int
    total_books: int


class NotesExportResponse(BaseModel):
    """笔记导出响应"""

    exported_at: datetime
    version: str = "1.0"
    format: str
    summary: ExportSummary
    books: list[ExportBook] = []
    markdown_content: str | None = Field(None, description="Markdown 格式时的内容")
