"""
笔记服务

处理笔记、高亮、书签、书架的业务逻辑。
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AthenaException, ErrorCode
from app.models import (
    Book,
    Bookmark,
    Highlight,
    Note,
    Shelf,
    ShelfBook,
)

logger = structlog.get_logger()


class NoteService:
    """笔记相关服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # 笔记
    # ========================================================================

    async def create_note(
        self,
        user_id: str,
        book_id: str,
        position_json: dict[str, Any],
        content: str,
        tags: list[str] | None = None,
        color: str | None = None,
    ) -> Note:
        """创建笔记"""
        # 验证书籍存在且属于用户
        await self._verify_book_ownership(book_id, user_id)

        note = Note(
            user_id=UUID(user_id),
            book_id=UUID(book_id),
            position_json=position_json,
            content=content,
            tags=tags or [],
            color=color,
        )

        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)

        logger.info("Note created", note_id=str(note.id), book_id=book_id)
        return note

    async def get_note(self, note_id: str, user_id: str) -> Note:
        """获取笔记"""
        result = await self.db.execute(
            select(Note).where(
                Note.id == UUID(note_id),
                Note.user_id == UUID(user_id),
                Note.deleted_at.is_(None),
            )
        )
        note = result.scalar_one_or_none()

        if not note:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Note not found",
            )

        return note

    async def list_notes(
        self,
        user_id: str,
        book_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Note], int]:
        """列出笔记"""
        query = select(Note).where(
            Note.user_id == UUID(user_id),
            Note.deleted_at.is_(None),
        )

        if book_id:
            query = query.where(Note.book_id == UUID(book_id))

        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # 分页
        query = query.order_by(Note.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        notes = list(result.scalars().all())

        return notes, total

    async def update_note(
        self,
        note_id: str,
        user_id: str,
        content: str | None = None,
        tags: list[str] | None = None,
        color: str | None = None,
    ) -> Note:
        """更新笔记"""
        note = await self.get_note(note_id, user_id)

        if content is not None:
            note.content = content
        if tags is not None:
            note.tags = tags
        if color is not None:
            note.color = color

        note.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def delete_note(self, note_id: str, user_id: str) -> None:
        """软删除笔记"""
        note = await self.get_note(note_id, user_id)
        note.deleted_at = datetime.now(UTC)

        await self.db.commit()
        logger.info("Note deleted", note_id=note_id)

    # ========================================================================
    # 高亮
    # ========================================================================

    async def create_highlight(
        self,
        user_id: str,
        book_id: str,
        position_json: dict[str, Any],
        color: str = "yellow",
        text_preview: str | None = None,
    ) -> Highlight:
        """创建高亮"""
        await self._verify_book_ownership(book_id, user_id)

        highlight = Highlight(
            user_id=UUID(user_id),
            book_id=UUID(book_id),
            position_json=position_json,
            color=color,
            text_preview=text_preview,
        )

        self.db.add(highlight)
        await self.db.commit()
        await self.db.refresh(highlight)

        return highlight

    async def get_highlight(self, highlight_id: str, user_id: str) -> Highlight:
        """获取高亮"""
        result = await self.db.execute(
            select(Highlight).where(
                Highlight.id == UUID(highlight_id),
                Highlight.user_id == UUID(user_id),
                Highlight.deleted_at.is_(None),
            )
        )
        highlight = result.scalar_one_or_none()

        if not highlight:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Highlight not found",
            )

        return highlight

    async def list_highlights(
        self,
        user_id: str,
        book_id: str,
    ) -> tuple[list[Highlight], int]:
        """列出书籍的所有高亮"""
        query = select(Highlight).where(
            Highlight.user_id == UUID(user_id),
            Highlight.book_id == UUID(book_id),
            Highlight.deleted_at.is_(None),
        ).order_by(Highlight.created_at)

        result = await self.db.execute(query)
        highlights = list(result.scalars().all())

        return highlights, len(highlights)

    async def update_highlight(
        self,
        highlight_id: str,
        user_id: str,
        color: str | None = None,
    ) -> Highlight:
        """更新高亮"""
        highlight = await self.get_highlight(highlight_id, user_id)

        if color is not None:
            highlight.color = color

        highlight.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(highlight)

        return highlight

    async def delete_highlight(self, highlight_id: str, user_id: str) -> None:
        """软删除高亮"""
        highlight = await self.get_highlight(highlight_id, user_id)
        highlight.deleted_at = datetime.now(UTC)

        await self.db.commit()

    # ========================================================================
    # 书签
    # ========================================================================

    async def create_bookmark(
        self,
        user_id: str,
        book_id: str,
        position_json: dict[str, Any],
        title: str | None = None,
    ) -> Bookmark:
        """创建书签"""
        await self._verify_book_ownership(book_id, user_id)

        bookmark = Bookmark(
            user_id=UUID(user_id),
            book_id=UUID(book_id),
            position_json=position_json,
            title=title,
        )

        self.db.add(bookmark)
        await self.db.commit()
        await self.db.refresh(bookmark)

        return bookmark

    async def get_bookmark(self, bookmark_id: str, user_id: str) -> Bookmark:
        """获取书签"""
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.id == UUID(bookmark_id),
                Bookmark.user_id == UUID(user_id),
                Bookmark.deleted_at.is_(None),
            )
        )
        bookmark = result.scalar_one_or_none()

        if not bookmark:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Bookmark not found",
            )

        return bookmark

    async def list_bookmarks(
        self,
        user_id: str,
        book_id: str,
    ) -> tuple[list[Bookmark], int]:
        """列出书籍的所有书签"""
        query = select(Bookmark).where(
            Bookmark.user_id == UUID(user_id),
            Bookmark.book_id == UUID(book_id),
            Bookmark.deleted_at.is_(None),
        ).order_by(Bookmark.created_at)

        result = await self.db.execute(query)
        bookmarks = list(result.scalars().all())

        return bookmarks, len(bookmarks)

    async def delete_bookmark(self, bookmark_id: str, user_id: str) -> None:
        """软删除书签"""
        bookmark = await self.get_bookmark(bookmark_id, user_id)
        bookmark.deleted_at = datetime.now(UTC)

        await self.db.commit()

    # ========================================================================
    # 书架
    # ========================================================================

    async def create_shelf(
        self,
        user_id: str,
        name: str,
        color: str | None = None,
        icon: str | None = None,
        sort_order: int = 0,
    ) -> Shelf:
        """创建书架"""
        shelf = Shelf(
            user_id=UUID(user_id),
            name=name,
            color=color,
            icon=icon,
            sort_order=sort_order,
        )

        self.db.add(shelf)
        await self.db.commit()
        await self.db.refresh(shelf)

        logger.info("Shelf created", shelf_id=str(shelf.id), name=name)
        return shelf

    async def get_shelf(self, shelf_id: str, user_id: str) -> Shelf:
        """获取书架"""
        result = await self.db.execute(
            select(Shelf).where(
                Shelf.id == UUID(shelf_id),
                Shelf.user_id == UUID(user_id),
                Shelf.deleted_at.is_(None),
            )
        )
        shelf = result.scalar_one_or_none()

        if not shelf:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Shelf not found",
            )

        return shelf

    async def list_shelves(self, user_id: str) -> tuple[list[Shelf], int]:
        """列出用户的所有书架"""
        query = select(Shelf).where(
            Shelf.user_id == UUID(user_id),
            Shelf.deleted_at.is_(None),
        ).order_by(Shelf.sort_order, Shelf.created_at)

        result = await self.db.execute(query)
        shelves = list(result.scalars().all())

        # 获取每个书架的书籍数量
        for shelf in shelves:
            count_result = await self.db.execute(
                select(func.count()).where(ShelfBook.shelf_id == shelf.id)
            )
            shelf.book_count = count_result.scalar() or 0

        return shelves, len(shelves)

    async def update_shelf(
        self,
        shelf_id: str,
        user_id: str,
        name: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
    ) -> Shelf:
        """更新书架"""
        shelf = await self.get_shelf(shelf_id, user_id)

        if name is not None:
            shelf.name = name
        if color is not None:
            shelf.color = color
        if icon is not None:
            shelf.icon = icon
        if sort_order is not None:
            shelf.sort_order = sort_order

        shelf.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(shelf)

        return shelf

    async def delete_shelf(self, shelf_id: str, user_id: str) -> None:
        """软删除书架"""
        shelf = await self.get_shelf(shelf_id, user_id)
        shelf.deleted_at = datetime.now(UTC)

        # 同时删除书架-书籍关联
        await self.db.execute(
            delete(ShelfBook).where(ShelfBook.shelf_id == UUID(shelf_id))
        )

        await self.db.commit()
        logger.info("Shelf deleted", shelf_id=shelf_id)

    async def add_books_to_shelf(
        self,
        shelf_id: str,
        user_id: str,
        book_ids: list[str],
    ) -> int:
        """添加书籍到书架"""
        await self.get_shelf(shelf_id, user_id)  # 验证书架存在

        added_count = 0
        for book_id in book_ids:
            # 验证书籍存在且属于用户
            try:
                await self._verify_book_ownership(book_id, user_id)
            except AthenaException:
                continue

            # 检查是否已存在
            existing = await self.db.execute(
                select(ShelfBook).where(
                    ShelfBook.shelf_id == UUID(shelf_id),
                    ShelfBook.book_id == UUID(book_id),
                )
            )
            if existing.scalar_one_or_none():
                continue

            # 添加关联
            shelf_book = ShelfBook(
                shelf_id=UUID(shelf_id),
                book_id=UUID(book_id),
            )
            self.db.add(shelf_book)
            added_count += 1

        await self.db.commit()
        logger.info("Books added to shelf", shelf_id=shelf_id, count=added_count)

        return added_count

    async def remove_books_from_shelf(
        self,
        shelf_id: str,
        user_id: str,
        book_ids: list[str],
    ) -> int:
        """从书架移除书籍"""
        await self.get_shelf(shelf_id, user_id)  # 验证书架存在

        result = await self.db.execute(
            delete(ShelfBook).where(
                ShelfBook.shelf_id == UUID(shelf_id),
                ShelfBook.book_id.in_([UUID(bid) for bid in book_ids]),
            )
        )

        await self.db.commit()
        removed_count = result.rowcount

        logger.info("Books removed from shelf", shelf_id=shelf_id, count=removed_count)
        return removed_count

    # ========================================================================
    # 辅助方法
    # ========================================================================

    async def _verify_book_ownership(self, book_id: str, user_id: str) -> Book:
        """验证书籍存在且属于用户"""
        result = await self.db.execute(
            select(Book).where(
                Book.id == UUID(book_id),
                Book.user_id == UUID(user_id),
                Book.deleted_at.is_(None),
            )
        )
        book = result.scalar_one_or_none()

        if not book:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Book not found",
            )

        return book
