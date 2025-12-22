"""
书籍服务

处理书籍上传、管理、删除等业务逻辑。
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BookLimitReachedException,
    BookNotFoundException,
    CanonicalNotFoundException,
    UploadForbiddenQuotaExceededException,
)
from app.models.book import Book, ShelfBook
from app.models.note import Bookmark, Highlight, Note
from app.models.reading import BookPosition, ReadingTimeLog
from app.models.user import User, UserStats
from app.services.storage_service import get_storage_service


class BookService:
    """书籍服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_service()

    async def init_upload(
        self,
        user: User,
        filename: str,
        content_type: str,
        size: int,
        sha256: str | None = None,
    ) -> dict[str, Any]:
        """
        初始化书籍上传

        1. 检查配额
        2. 如果提供了 sha256，检查是否可以秒传
        3. 生成预签名上传 URL

        Returns:
            {
                "upload_url": str,
                "key": str,
                "expires_in": int,
                "is_duplicate": bool,
                "canonical_book_id": str | None
            }
        """
        # 检查配额
        await self._check_quota(user, size)

        # 检查秒传
        if sha256:
            canonical = await self._find_canonical_by_sha256(sha256)
            if canonical:
                return {
                    "upload_url": "",
                    "key": "",
                    "expires_in": 0,
                    "is_duplicate": True,
                    "canonical_book_id": str(canonical.id),
                }

        # 生成上传 URL
        upload_url, object_key = self.storage.generate_presigned_upload_url(
            filename=filename,
            content_type=content_type,
            user_id=str(user.id),
        )

        return {
            "upload_url": upload_url,
            "key": object_key,
            "expires_in": 3600,
            "is_duplicate": False,
            "canonical_book_id": None,
        }

    async def complete_upload(
        self,
        user: User,
        key: str,
        etag: str | None = None,
        title: str | None = None,
        author: str | None = None,
    ) -> Book:
        """
        完成书籍上传

        1. 验证文件已上传
        2. 提取元数据
        3. 创建书籍记录
        4. 触发后处理任务
        """
        # 获取文件信息
        file_info = self.storage.get_object_info(key)
        if not file_info:
            raise BookNotFoundException()

        # 从文件名推断格式
        ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
        format_map = {
            "epub": "epub",
            "pdf": "pdf",
            "mobi": "mobi",
            "azw3": "azw3",
            "azw": "azw",
            "txt": "txt",
        }
        original_format = format_map.get(ext, "unknown")

        # 创建书籍记录
        book = Book(
            user_id=user.id,
            title=title or key.rsplit("/", 1)[-1].rsplit(".", 1)[0],
            author=author,
            minio_key=key,
            size=file_info["size"],
            original_format=original_format,
            source_etag=etag,
            processing_status="pending",
            reader_type="epub" if original_format == "epub" else "pdf",
        )
        self.db.add(book)

        # 更新用户统计
        await self._update_user_stats(user.id, size_delta=file_info["size"], count_delta=1)

        await self.db.commit()
        await self.db.refresh(book)

        # TODO: 触发后处理任务 (Celery)
        # from app.tasks.book_processing import process_book
        # process_book.delay(str(book.id))

        return book

    async def create_dedup_reference(
        self,
        user: User,
        sha256: str,
        title: str | None = None,
        author: str | None = None,
    ) -> Book:
        """
        创建秒传引用书籍

        复用已存在的文件，只创建新的书籍记录。
        """
        # 查找原书
        canonical = await self._find_canonical_by_sha256(sha256)
        if not canonical:
            raise CanonicalNotFoundException()

        # 检查配额
        await self._check_quota(user, 0)  # 秒传不占用存储

        # 创建引用书籍
        book = Book(
            user_id=user.id,
            title=title or canonical.title,
            author=author or canonical.author,
            language=canonical.language,
            original_format=canonical.original_format,
            minio_key=canonical.minio_key,
            size=canonical.size,
            cover_image_key=canonical.cover_image_key,
            content_sha256=sha256,
            canonical_book_id=canonical.id,
            has_text_layer=canonical.has_text_layer,
            text_layer_confidence=canonical.text_layer_confidence,
            converted_epub_key=canonical.converted_epub_key,
            ocr_pdf_key=canonical.ocr_pdf_key,
            processing_status=canonical.processing_status,
            reader_type=canonical.reader_type,
            is_readable=canonical.is_readable,
            is_interactive=canonical.is_interactive,
            meta=canonical.meta,
        )
        self.db.add(book)

        # 增加原书引用计数
        canonical.storage_ref_count += 1

        # 更新用户统计 (不增加存储使用，只增加书籍数)
        await self._update_user_stats(user.id, size_delta=0, count_delta=1)

        await self.db.commit()
        await self.db.refresh(book)

        return book

    async def get_book(self, book_id: str, user_id: str) -> Book:
        """获取书籍详情"""
        result = await self.db.execute(
            select(Book).where(
                Book.id == book_id,
                Book.user_id == user_id,
                Book.deleted_at.is_(None),
            )
        )
        book = result.scalar_one_or_none()
        if not book:
            raise BookNotFoundException()
        return book

    async def list_books(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        shelf_id: str | None = None,
    ) -> tuple[list[Book], int]:
        """
        获取书籍列表

        Returns:
            (books, total)
        """
        query = select(Book).where(
            Book.user_id == user_id,
            Book.deleted_at.is_(None),
        )

        # 搜索过滤
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term),
                )
            )

        # 书架过滤
        if shelf_id:
            query = query.join(ShelfBook).where(ShelfBook.shelf_id == shelf_id)

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.order_by(Book.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        books = list(result.scalars().all())

        return books, total

    async def delete_book(self, book_id: str, user_id: str, permanent: bool = False) -> bool:
        """
        删除书籍

        Args:
            book_id: 书籍 ID
            user_id: 用户 ID
            permanent: 是否永久删除

        软删除: 设置 deleted_at，保留文件
        永久删除: 删除私人数据，清理存储引用
        """
        book = await self.get_book(book_id, user_id)

        # 1. 始终删除私人数据
        await self._delete_private_data(book_id, user_id)

        if book.canonical_book_id:
            # 引用书：直接删除，减少原书引用计数
            canonical_result = await self.db.execute(
                select(Book).where(Book.id == book.canonical_book_id)
            )
            canonical = canonical_result.scalar_one_or_none()
            if canonical:
                canonical.storage_ref_count -= 1

                # 如果原书已软删除且没有其他引用，硬删除原书
                if canonical.deleted_at and canonical.storage_ref_count <= 1:
                    await self._hard_delete_book(canonical)

            # 删除引用书记录
            await self.db.delete(book)

        else:
            # 原书
            if permanent or book.storage_ref_count <= 1:
                # 硬删除
                await self._hard_delete_book(book)
            else:
                # 软删除
                book.deleted_at = datetime.now(UTC)

        # 更新用户统计
        size_delta = -(book.size or 0) if not book.canonical_book_id else 0
        await self._update_user_stats(user_id, size_delta=size_delta, count_delta=-1)

        await self.db.commit()
        return True

    async def get_content_url(self, book_id: str, user_id: str) -> dict[str, Any]:
        """获取书籍内容下载 URL"""
        book = await self.get_book(book_id, user_id)

        if not book.minio_key:
            raise BookNotFoundException()

        # 优先使用转换后的 EPUB
        key = book.converted_epub_key or book.minio_key
        content_type = "application/epub+zip" if book.converted_epub_key else "application/pdf"

        url = self.storage.generate_presigned_download_url(
            object_key=key,
            expires=timedelta(hours=2),
        )

        return {
            "download_url": url,
            "expires_in": 7200,
            "content_type": content_type,
            "size": book.size,
        }

    async def get_cover_url(self, book_id: str, user_id: str) -> dict[str, Any]:
        """获取封面 URL"""
        book = await self.get_book(book_id, user_id)

        if not book.cover_image_key:
            raise BookNotFoundException()

        url = self.storage.generate_presigned_download_url(
            object_key=book.cover_image_key,
            bucket=settings.minio.minio_bucket_covers,
            expires=timedelta(hours=24),
        )

        return {
            "cover_url": url,
            "expires_in": 86400,
        }

    # =========================================================================
    # 私有方法
    # =========================================================================

    async def _check_quota(self, user: User, size: int) -> None:
        """检查用户配额"""
        result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user.id)
        )
        stats = result.scalar_one_or_none()

        if not stats:
            return

        # 获取配额限制
        is_pro = user.membership_tier != "FREE"
        storage_limit = (
            settings.quota.pro_storage_quota_mb if is_pro
            else settings.quota.free_storage_quota_mb
        ) * 1024 * 1024  # 转为字节

        book_limit = (
            settings.quota.pro_book_limit if is_pro
            else settings.quota.free_book_limit
        )

        # 检查存储配额
        if stats.storage_used + size > storage_limit:
            raise UploadForbiddenQuotaExceededException()

        # 检查书籍数量
        if stats.book_count >= book_limit:
            raise BookLimitReachedException()

    async def _find_canonical_by_sha256(self, sha256: str) -> Book | None:
        """根据 SHA256 查找原书"""
        result = await self.db.execute(
            select(Book).where(
                Book.content_sha256 == sha256,
                Book.canonical_book_id.is_(None),
                Book.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _update_user_stats(
        self,
        user_id: str,
        size_delta: int = 0,
        count_delta: int = 0,
    ) -> None:
        """更新用户统计"""
        await self.db.execute(
            update(UserStats)
            .where(UserStats.user_id == user_id)
            .values(
                storage_used=UserStats.storage_used + size_delta,
                book_count=UserStats.book_count + count_delta,
                updated_at=datetime.now(UTC),
            )
        )

    async def _delete_private_data(self, book_id: str, user_id: str) -> None:
        """删除用户私人数据"""
        from sqlalchemy import delete

        # 删除笔记
        await self.db.execute(
            delete(Note).where(Note.book_id == book_id, Note.user_id == user_id)
        )
        # 删除高亮
        await self.db.execute(
            delete(Highlight).where(Highlight.book_id == book_id, Highlight.user_id == user_id)
        )
        # 删除书签
        await self.db.execute(
            delete(Bookmark).where(Bookmark.book_id == book_id, Bookmark.user_id == user_id)
        )
        # 删除阅读位置
        await self.db.execute(
            delete(BookPosition).where(
                BookPosition.book_id == book_id,
                BookPosition.user_id == user_id,
            )
        )
        # 删除阅读时长记录
        await self.db.execute(
            delete(ReadingTimeLog).where(
                ReadingTimeLog.book_id == book_id,
                ReadingTimeLog.user_id == user_id,
            )
        )
        # 删除书架关联
        await self.db.execute(
            delete(ShelfBook).where(ShelfBook.book_id == book_id)
        )

    async def _hard_delete_book(self, book: Book) -> None:
        """硬删除书籍 (包括存储文件)"""
        # 删除 MinIO 文件
        if book.minio_key:
            self.storage.delete_object(book.minio_key)
        if book.cover_image_key:
            self.storage.delete_object(
                book.cover_image_key,
                bucket=settings.minio.minio_bucket_covers,
            )
        if book.ocr_pdf_key:
            self.storage.delete_object(
                book.ocr_pdf_key,
                bucket=settings.minio.minio_bucket_ocr,
            )
        if book.converted_epub_key:
            self.storage.delete_object(book.converted_epub_key)

        # TODO: 删除向量索引
        # await self._delete_vectors(book.id)

        # 删除书籍记录
        await self.db.delete(book)

    # ========================================================================
    # OCR 相关
    # ========================================================================

    async def trigger_ocr(
        self,
        book_id: str,
        user_id: str,
        priority: str = "normal",
        force: bool = False,
    ) -> dict[str, Any]:
        """
        触发 OCR 处理

        Args:
            book_id: 书籍 ID
            user_id: 用户 ID
            priority: 优先级 (normal/high)
            force: 是否强制重新 OCR

        Returns:
            {
                "status": "queued" | "instant_completed" | "already_processing",
                "queue_position": int | None,
                "estimated_minutes": int | None,
            }
        """
        from uuid import UUID

        from app.core.exceptions import (
            AlreadyDigitalizedException,
            OcrInProgressException,
            OcrQuotaExceededException,
        )
        from app.models.system import OcrJob

        # 获取书籍
        book = await self.get_book(book_id, user_id)

        # 检查是否已是文字型
        if book.has_text_layer and not force:
            raise AlreadyDigitalizedException()

        # 检查是否正在处理
        if book.ocr_status == "processing":
            raise OcrInProgressException()

        # 检查配额
        await self._check_ocr_quota(user_id)

        # 检查是否可复用 (假 OCR)
        if book.content_sha256:
            existing_ocr = await self._find_existing_ocr(book.content_sha256)
            if existing_ocr and not force:
                # 直接复用 OCR 结果
                book.ocr_pdf_key = existing_ocr["ocr_pdf_key"]
                book.has_text_layer = True
                book.ocr_status = "completed"
                book.is_interactive = True
                await self.db.commit()

                # 扣减配额 (即使复用也扣)
                await self._deduct_ocr_quota(user_id)

                return {
                    "status": "instant_completed",
                    "ocr_result_key": existing_ocr["ocr_pdf_key"],
                    "message": "OCR 结果已复用，处理完成。",
                }

        # 创建 OCR 任务
        ocr_job = OcrJob(
            book_id=UUID(book_id),
            user_id=UUID(user_id),
            status="pending",
            priority=1 if priority == "high" else 0,
        )
        self.db.add(ocr_job)

        # 更新书籍状态
        book.ocr_status = "pending"
        await self.db.commit()

        # 提交 Celery 任务
        from app.tasks.ocr_tasks import process_ocr

        process_ocr.delay(
            book_id=book_id,
            user_id=user_id,
            minio_key=book.minio_key,
            sha256=book.content_sha256 or "",
        )

        # 计算队列位置
        queue_position = await self._get_ocr_queue_position(book_id)

        return {
            "status": "queued",
            "queue_position": queue_position,
            "estimated_minutes": queue_position * 5,  # 估算每本 5 分钟
            "message": f"OCR 任务已进入排队，预计 {queue_position * 5} 分钟后完成。",
        }

    async def get_ocr_status(self, book_id: str, user_id: str) -> dict[str, Any]:
        """获取 OCR 处理状态"""
        from app.models.system import OcrJob

        book = await self.get_book(book_id, user_id)

        # 查询 OCR 任务
        result = await self.db.execute(
            select(OcrJob)
            .where(OcrJob.book_id == book.id)
            .order_by(OcrJob.created_at.desc())
            .limit(1)
        )
        ocr_job = result.scalar_one_or_none()

        return {
            "book_id": book_id,
            "is_digitalized": book.has_text_layer,
            "ocr_status": book.ocr_status,
            "queue_position": await self._get_ocr_queue_position(book_id) if book.ocr_status == "pending" else None,
            "estimated_minutes": None,
            "completed_at": ocr_job.completed_at if ocr_job else None,
            "error_message": ocr_job.error_message if ocr_job and ocr_job.status == "failed" else None,
        }

    async def _check_ocr_quota(self, user_id: str) -> None:
        """检查 OCR 配额"""
        from uuid import UUID

        from app.core.exceptions import OcrQuotaExceededException
        from app.models.user import User

        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise OcrQuotaExceededException()

        # 免费用户每月 3 次
        monthly_limit = 3 if user.membership_tier == "FREE" else 100

        if user.free_ocr_usage >= monthly_limit:
            raise OcrQuotaExceededException()

    async def _deduct_ocr_quota(self, user_id: str) -> None:
        """扣减 OCR 配额"""
        from uuid import UUID

        await self.db.execute(
            update(User)
            .where(User.id == UUID(user_id))
            .values(free_ocr_usage=User.free_ocr_usage + 1)
        )

    async def _find_existing_ocr(self, sha256: str) -> dict[str, Any] | None:
        """查找已存在的 OCR 结果"""
        result = await self.db.execute(
            select(Book)
            .where(
                Book.content_sha256 == sha256,
                Book.ocr_pdf_key.isnot(None),
            )
            .limit(1)
        )
        book = result.scalar_one_or_none()

        if book:
            return {"ocr_pdf_key": book.ocr_pdf_key}
        return None

    async def _get_ocr_queue_position(self, book_id: str) -> int:
        """获取 OCR 队列位置"""
        from uuid import UUID

        from app.models.system import OcrJob

        result = await self.db.execute(
            select(func.count())
            .select_from(OcrJob)
            .where(
                OcrJob.status == "pending",
                OcrJob.created_at <= select(OcrJob.created_at).where(OcrJob.book_id == UUID(book_id)).scalar_subquery(),
            )
        )
        return result.scalar() or 1

