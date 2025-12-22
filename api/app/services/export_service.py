"""
数据导出服务

处理笔记、高亮等数据的导出。
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.note import Highlight, Note


class ExportService:
    """数据导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_notes(
        self,
        user_id: str,
        format: str = "markdown",
        book_id: str | None = None,
        include_highlights: bool = True,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any]:
        """
        导出笔记和高亮

        Args:
            user_id: 用户 ID
            format: 导出格式 (markdown/json/html)
            book_id: 可选，筛选指定书籍
            include_highlights: 是否包含高亮
            date_from: 可选，筛选起始日期
            date_to: 可选，筛选结束日期

        Returns:
            导出数据
        """
        # 查询书籍
        book_query = select(Book).where(
            Book.user_id == UUID(user_id),
            Book.deleted_at.is_(None),
        )
        if book_id:
            book_query = book_query.where(Book.id == UUID(book_id))

        result = await self.db.execute(book_query)
        books = result.scalars().all()

        export_books = []
        total_notes = 0
        total_highlights = 0

        for book in books:
            book_data = {
                "id": str(book.id),
                "title": book.title,
                "author": book.author,
                "highlights": [],
                "notes": [],
            }

            # 查询笔记
            note_query = select(Note).where(
                Note.book_id == book.id,
                Note.user_id == UUID(user_id),
                Note.deleted_at.is_(None),
            )
            if date_from:
                note_query = note_query.where(Note.created_at >= date_from)
            if date_to:
                note_query = note_query.where(Note.created_at <= date_to)

            note_result = await self.db.execute(note_query.order_by(Note.created_at))
            notes = note_result.scalars().all()

            for note in notes:
                book_data["notes"].append({
                    "id": str(note.id),
                    "title": None,
                    "content": note.content,
                    "location": note.position_json,
                    "linked_highlight_id": str(note.highlight_id) if note.highlight_id else None,
                    "created_at": note.created_at,
                    "updated_at": note.updated_at,
                    "tags": note.tags or [],
                })
                total_notes += 1

            # 查询高亮
            if include_highlights:
                highlight_query = select(Highlight).where(
                    Highlight.book_id == book.id,
                    Highlight.user_id == UUID(user_id),
                    Highlight.deleted_at.is_(None),
                )
                if date_from:
                    highlight_query = highlight_query.where(Highlight.created_at >= date_from)
                if date_to:
                    highlight_query = highlight_query.where(Highlight.created_at <= date_to)

                highlight_result = await self.db.execute(highlight_query.order_by(Highlight.created_at))
                highlights = highlight_result.scalars().all()

                for highlight in highlights:
                    book_data["highlights"].append({
                        "id": str(highlight.id),
                        "content": highlight.text_preview or "",
                        "location": highlight.position_json,
                        "color": highlight.color,
                        "created_at": highlight.created_at,
                        "tags": [],
                    })
                    total_highlights += 1

            if book_data["notes"] or book_data["highlights"]:
                export_books.append(book_data)

        exported_at = datetime.now(UTC)

        result_data = {
            "exported_at": exported_at,
            "version": "1.0",
            "format": format,
            "summary": {
                "total_notes": total_notes,
                "total_highlights": total_highlights,
                "total_books": len(export_books),
            },
            "books": export_books,
        }

        # 生成 Markdown 内容
        if format == "markdown":
            result_data["markdown_content"] = self._generate_markdown(
                export_books, exported_at, total_notes, total_highlights
            )

        return result_data

    def _generate_markdown(
        self,
        books: list[dict],
        exported_at: datetime,
        total_notes: int,
        total_highlights: int,
    ) -> str:
        """生成 Markdown 格式导出内容"""
        lines = [
            "# 我的阅读笔记",
            "",
            f"> 导出时间：{exported_at.isoformat()}",
            f"> 笔记总数：{total_notes} 条",
            f"> 高亮总数：{total_highlights} 条",
            "",
            "---",
            "",
        ]

        for book in books:
            lines.append(f"## 📖 {book['title']}")
            if book.get("author"):
                lines.append(f"*作者：{book['author']}*")
            lines.append("")

            # 高亮
            if book.get("highlights"):
                lines.append("### 💡 高亮")
                for highlight in book["highlights"]:
                    lines.append(f"> \"{highlight['content']}\"")
                    if highlight.get("location"):
                        loc = highlight["location"]
                        if loc.get("page"):
                            lines.append(f"> — 位置: 第 {loc['page']} 页")
                    lines.append("")

            # 笔记
            if book.get("notes"):
                lines.append("### 📝 笔记")
                for note in book["notes"]:
                    created = note["created_at"].strftime("%Y-%m-%d") if note.get("created_at") else ""
                    title = note.get("title") or "无标题"
                    lines.append(f"**{title}** ({created})")
                    lines.append(note["content"])
                    lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)
