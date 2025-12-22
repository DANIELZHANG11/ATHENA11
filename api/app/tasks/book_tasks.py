"""
书籍处理任务

处理书籍上传后的元数据提取、格式转换等。
"""

import json
import tempfile
from pathlib import Path

import structlog
from celery import shared_task

from app.core.config import settings
from app.services.storage_service import StorageService

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="app.tasks.book_tasks.process_book_upload",
    max_retries=3,
    default_retry_delay=30,
)
def process_book_upload(
    self,
    book_id: str,
    user_id: str,
    minio_key: str,
    original_format: str,
) -> dict:
    """
    处理书籍上传后的后处理

    1. 提取元数据（页数、目录等）
    2. 生成封面
    3. 判断是否需要 OCR
    4. 触发 OCR 任务（如需要）

    Args:
        book_id: 书籍 ID
        user_id: 用户 ID
        minio_key: MinIO 中的文件 Key
        original_format: 原始格式 (pdf, epub, etc.)

    Returns:
        处理结果
    """
    logger.info(
        "Processing book upload",
        book_id=book_id,
        original_format=original_format,
    )

    storage = StorageService()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 下载文件
            input_path = Path(tmpdir) / f"input.{original_format}"
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            # 根据格式处理
            if original_format == "pdf":
                result = _process_pdf(book_id, input_path, storage)
            elif original_format in ("epub", "mobi"):
                result = _process_ebook(book_id, input_path, storage, original_format)
            else:
                result = {"success": False, "error": f"Unsupported format: {original_format}"}

            # 更新处理状态
            if result["success"]:
                _update_book_processing_complete(book_id, result.get("meta", {}))

                # 如果是扫描 PDF，触发 OCR
                if result.get("needs_ocr"):
                    from app.tasks.ocr_tasks import process_ocr

                    process_ocr.delay(
                        book_id=book_id,
                        user_id=user_id,
                        minio_key=minio_key,
                        sha256=result.get("sha256", ""),
                    )
            else:
                _update_book_status(book_id, "failed", result.get("error"))

            return result

    except Exception as e:
        logger.exception("Book processing failed", book_id=book_id)
        _update_book_status(book_id, "failed", str(e))
        raise self.retry(exc=e) from e


def _process_pdf(book_id: str, input_path: Path, storage: StorageService) -> dict:
    """
    处理 PDF 文件

    提取元数据、生成封面、检查是否需要 OCR。
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(input_path))

        # 提取元数据
        meta = {
            "page_count": doc.page_count,
            "title": doc.metadata.get("title"),
            "author": doc.metadata.get("author"),
            "toc": [],
        }

        # 提取目录
        toc = doc.get_toc()
        if toc:
            meta["toc"] = [
                {"level": level, "title": title, "page": page}
                for level, title, page in toc[:100]  # 限制 100 条
            ]

        # 检查是否是扫描 PDF（图像型）
        is_scanned = _check_is_scanned_pdf(doc)
        meta["is_scanned"] = is_scanned

        # 生成封面
        cover_key = _extract_cover(book_id, doc, storage)

        # 更新封面 Key
        if cover_key:
            _update_book_cover(book_id, cover_key)

        doc.close()

        return {
            "success": True,
            "meta": meta,
            "cover_key": cover_key,
            "needs_ocr": is_scanned,
        }

    except ImportError:
        logger.warning("PyMuPDF not installed, skipping PDF processing")
        return {"success": True, "meta": {}, "needs_ocr": False}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _process_ebook(
    book_id: str,
    input_path: Path,
    storage: StorageService,
    format: str,  # noqa: ARG001
) -> dict:
    """
    处理电子书文件 (EPUB, MOBI)

    提取元数据和封面。
    """
    try:
        from ebooklib import epub

        book = epub.read_epub(str(input_path))

        # 提取元数据
        meta = {
            "title": book.get_metadata("DC", "title")[0][0] if book.get_metadata("DC", "title") else None,
            "author": book.get_metadata("DC", "creator")[0][0] if book.get_metadata("DC", "creator") else None,
            "language": book.get_metadata("DC", "language")[0][0] if book.get_metadata("DC", "language") else None,
            "toc": [],
        }

        # 提取目录
        toc_items = []
        for item in book.toc:
            if isinstance(item, tuple):
                section, children = item
                toc_items.append({"level": 1, "title": section.title, "href": section.href})
                for child in children:
                    toc_items.append({"level": 2, "title": child.title, "href": child.href})
            else:
                toc_items.append({"level": 1, "title": item.title, "href": item.href})

        meta["toc"] = toc_items[:100]

        # 提取封面
        cover_key = _extract_epub_cover(book_id, book, storage)
        if cover_key:
            _update_book_cover(book_id, cover_key)

        return {
            "success": True,
            "meta": meta,
            "cover_key": cover_key,
            "needs_ocr": False,  # EPUB 不需要 OCR
        }

    except ImportError:
        logger.warning("ebooklib not installed, skipping EPUB processing")
        return {"success": True, "meta": {}, "needs_ocr": False}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _check_is_scanned_pdf(doc) -> bool:
    """
    检查 PDF 是否是扫描件（图像型）

    通过检查前几页的文字内容判断。
    """
    total_text = ""
    pages_to_check = min(5, doc.page_count)

    for i in range(pages_to_check):
        page = doc[i]
        text = page.get_text()
        total_text += text

    # 如果文字太少，可能是扫描件
    # 平均每页少于 50 个字符视为扫描件
    avg_chars = len(total_text) / pages_to_check if pages_to_check > 0 else 0
    return avg_chars < 50


def _extract_cover(book_id: str, doc, storage: StorageService) -> str | None:
    """
    从 PDF 提取封面

    将第一页渲染为 JPEG 图像。
    """
    try:
        import fitz

        if doc.page_count == 0:
            return None

        page = doc[0]
        # 渲染为图像 (2x 缩放)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        # 转换为 JPEG
        img_data = pix.tobytes("jpeg")

        # 上传到 MinIO
        cover_key = f"covers/{book_id}.jpg"
        storage.upload_bytes(
            bucket=settings.minio.minio_bucket_covers,
            key=cover_key,
            data=img_data,
            content_type="image/jpeg",
        )

        return cover_key

    except Exception as e:
        logger.warning("Failed to extract cover", error=str(e))
        return None


def _extract_epub_cover(book_id: str, book, storage: StorageService) -> str | None:
    """
    从 EPUB 提取封面
    """
    try:
        import ebooklib

        # 尝试获取封面
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                cover_data = item.get_content()
                content_type = item.media_type or "image/jpeg"
                ext = "jpg" if "jpeg" in content_type else "png"

                cover_key = f"covers/{book_id}.{ext}"
                storage.upload_bytes(
                    bucket=settings.minio.minio_bucket_covers,
                    key=cover_key,
                    data=cover_data,
                    content_type=content_type,
                )
                return cover_key

        return None

    except Exception as e:
        logger.warning("Failed to extract EPUB cover", error=str(e))
        return None


def _update_book_status(book_id: str, status: str, error: str | None = None) -> None:
    """更新书籍处理状态"""
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET processing_status = :status,
                    processing_error = :error,
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "status": status, "error": error},
        )
        conn.commit()


def _update_book_processing_complete(book_id: str, meta: dict) -> None:
    """更新书籍处理完成状态"""
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET processing_status = 'completed',
                    meta = :meta::jsonb,
                    is_readable = TRUE,
                    has_text_layer = NOT COALESCE((meta->>'is_scanned')::boolean, FALSE),
                    is_image_based = COALESCE((meta->>'is_scanned')::boolean, FALSE),
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "meta": json.dumps(meta)},
        )
        conn.commit()


def _update_book_cover(book_id: str, cover_key: str) -> None:
    """更新书籍封面"""
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET cover_key = :cover_key,
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "cover_key": cover_key},
        )
        conn.commit()


@shared_task(name="app.tasks.book_tasks.extract_metadata")
def extract_metadata(book_id: str, minio_key: str) -> dict:
    """
    单独提取元数据任务

    用于重新提取或更新元数据。
    """
    logger.info("Extracting metadata", book_id=book_id)

    storage = StorageService()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            import fitz
            doc = fitz.open(str(input_path))

            meta = {
                "page_count": doc.page_count,
                "title": doc.metadata.get("title"),
                "author": doc.metadata.get("author"),
            }

            doc.close()

            return {"success": True, "meta": meta}

    except Exception as e:
        return {"success": False, "error": str(e)}
