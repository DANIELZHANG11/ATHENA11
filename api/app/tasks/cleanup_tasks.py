"""
清理任务

处理软删除书籍的自动清理、孤立文件清理等。
"""


import structlog
from celery import shared_task
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.storage_service import StorageService

logger = structlog.get_logger()


@shared_task(name="app.tasks.cleanup_tasks.cleanup_expired_books")
def cleanup_expired_books() -> dict:
    """
    清理过期的软删除书籍

    软删除超过 30 天的书籍将被永久删除。
    """
    logger.info("Starting expired books cleanup")

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)
    storage = StorageService()

    deleted_count = 0
    failed_count = 0

    try:
        with engine.connect() as conn:
            # 查找过期的软删除书籍
            result = conn.execute(
                text("""
                    SELECT id, minio_key, cover_key, ocr_pdf_key, sha256, storage_ref_count
                    FROM books
                    WHERE deleted_at IS NOT NULL
                      AND deleted_at < NOW() - INTERVAL '30 days'
                    LIMIT 100
                """)
            )

            books = result.fetchall()

            for book in books:
                book_id = str(book.id)
                try:
                    # 减少引用计数
                    if book.storage_ref_count and book.storage_ref_count > 1:
                        # 还有其他引用，只减少计数
                        conn.execute(
                            text("""
                                UPDATE books
                                SET storage_ref_count = storage_ref_count - 1
                                WHERE sha256 = :sha256 AND id != :book_id::uuid
                            """),
                            {"sha256": book.sha256, "book_id": book_id},
                        )
                    else:
                        # 最后一个引用，删除存储文件
                        if book.minio_key:
                            storage.delete_file(
                                bucket=settings.minio.minio_bucket_books,
                                key=book.minio_key,
                            )
                        if book.cover_key:
                            storage.delete_file(
                                bucket=settings.minio.minio_bucket_covers,
                                key=book.cover_key,
                            )
                        if book.ocr_pdf_key:
                            storage.delete_file(
                                bucket=settings.minio.minio_bucket_books,
                                key=book.ocr_pdf_key,
                            )

                    # 删除书籍记录
                    conn.execute(
                        text("DELETE FROM books WHERE id = :book_id::uuid"),
                        {"book_id": book_id},
                    )

                    deleted_count += 1
                    logger.info("Deleted expired book", book_id=book_id)

                except Exception as e:
                    failed_count += 1
                    logger.error("Failed to delete book", book_id=book_id, error=str(e))

            conn.commit()

    except Exception as e:
        logger.exception("Cleanup expired books failed")
        return {"success": False, "error": str(e)}

    logger.info(
        "Expired books cleanup completed",
        deleted_count=deleted_count,
        failed_count=failed_count,
    )

    return {
        "success": True,
        "deleted_count": deleted_count,
        "failed_count": failed_count,
    }


@shared_task(name="app.tasks.cleanup_tasks.cleanup_orphan_files")
def cleanup_orphan_files() -> dict:
    """
    清理孤立的 MinIO 文件

    检查 MinIO 中的文件是否在数据库中有对应记录。
    """
    logger.info("Starting orphan files cleanup")

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)
    storage = StorageService()

    deleted_count = 0

    try:
        # 获取 MinIO 中的所有文件
        books_files = storage.list_files(settings.minio.minio_bucket_books)
        covers_files = storage.list_files(settings.minio.minio_bucket_covers)

        with engine.connect() as conn:
            # 检查书籍文件
            for file_key in books_files:
                # 跳过 OCR 文件（它们可能被多本书引用）
                if file_key.startswith("ocr/"):
                    continue

                result = conn.execute(
                    text("""
                        SELECT id FROM books
                        WHERE minio_key = :key OR ocr_pdf_key = :key
                        LIMIT 1
                    """),
                    {"key": file_key},
                )

                if result.fetchone() is None:
                    # 孤立文件，删除
                    logger.warning("Found orphan file", key=file_key)
                    storage.delete_file(settings.minio.minio_bucket_books, file_key)
                    deleted_count += 1

            # 检查封面文件
            for file_key in covers_files:
                result = conn.execute(
                    text("SELECT id FROM books WHERE cover_key = :key LIMIT 1"),
                    {"key": file_key},
                )

                if result.fetchone() is None:
                    logger.warning("Found orphan cover", key=file_key)
                    storage.delete_file(settings.minio.minio_bucket_covers, file_key)
                    deleted_count += 1

    except Exception as e:
        logger.exception("Cleanup orphan files failed")
        return {"success": False, "error": str(e)}

    logger.info("Orphan files cleanup completed", deleted_count=deleted_count)

    return {"success": True, "deleted_count": deleted_count}


@shared_task(name="app.tasks.cleanup_tasks.cleanup_expired_sessions")
def cleanup_expired_sessions() -> dict:
    """
    清理过期的用户会话
    """
    logger.info("Starting expired sessions cleanup")

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM user_sessions
                    WHERE expires_at < NOW()
                    RETURNING id
                """)
            )
            deleted_count = result.rowcount
            conn.commit()

        logger.info("Expired sessions cleanup completed", deleted_count=deleted_count)
        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.exception("Cleanup expired sessions failed")
        return {"success": False, "error": str(e)}


@shared_task(name="app.tasks.cleanup_tasks.cleanup_old_reading_logs")
def cleanup_old_reading_logs(days: int = 365) -> dict:
    """
    清理过旧的阅读日志

    默认保留 365 天的数据。
    """
    logger.info("Starting old reading logs cleanup", days=days)

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM reading_time_log
                    WHERE ended_at < NOW() - INTERVAL ':days days'
                    RETURNING id
                """.replace(":days", str(days)))
            )
            deleted_count = result.rowcount
            conn.commit()

        logger.info("Old reading logs cleanup completed", deleted_count=deleted_count)
        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.exception("Cleanup old reading logs failed")
        return {"success": False, "error": str(e)}


@shared_task(name="app.tasks.cleanup_tasks.vacuum_database")
def vacuum_database() -> dict:
    """
    执行数据库 VACUUM

    清理死元组，回收空间。
    建议在低峰期执行。
    """
    logger.info("Starting database vacuum")

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    try:
        with engine.connect() as conn:
            # VACUUM 不能在事务中执行
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("VACUUM ANALYZE"))

        logger.info("Database vacuum completed")
        return {"success": True}

    except Exception as e:
        logger.exception("Database vacuum failed")
        return {"success": False, "error": str(e)}
