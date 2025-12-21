"""
OCR 任务

处理图像型 PDF 和扫描文档的 OCR 识别。
使用 OCRmyPDF + PaddleOCR 生成双层 PDF。
"""

import subprocess
import tempfile
from pathlib import Path

import structlog
from celery import shared_task

from app.core.config import settings
from app.services.storage_service import StorageService

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="app.tasks.ocr_tasks.process_ocr",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def process_ocr(
    self,  # noqa: ARG001
    book_id: str,
    user_id: str,  # noqa: ARG001
    minio_key: str,
    sha256: str,
) -> dict:
    """
    处理 OCR 任务

    下载原始 PDF，使用 OCRmyPDF 生成双层 PDF，上传结果。

    Args:
        book_id: 书籍 ID
        user_id: 用户 ID
        minio_key: MinIO 中原始文件的 Key
        sha256: 文件 SHA256 哈希

    Returns:
        处理结果字典
    """
    logger.info(
        "Starting OCR processing",
        book_id=book_id,
        minio_key=minio_key,
    )

    storage = StorageService()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"
            output_path = Path(tmpdir) / "output.pdf"

            # 1. 下载原始文件
            logger.info("Downloading original file", minio_key=minio_key)
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            # 2. 运行 OCRmyPDF
            logger.info("Running OCRmyPDF", input_path=str(input_path))
            result = _run_ocrmypdf(input_path, output_path)

            if not result["success"]:
                logger.error("OCR failed", error=result["error"])
                _update_book_status(book_id, "ocr_failed", result["error"])
                return result

            # 3. 上传 OCR 结果
            # 使用 SHA256 作为 Key 前缀，支持去重复用
            ocr_pdf_key = f"ocr/{sha256[:2]}/{sha256[2:4]}/{sha256}.pdf"

            logger.info("Uploading OCR result", ocr_pdf_key=ocr_pdf_key)
            storage.upload_file(
                bucket=settings.minio.minio_bucket_books,
                key=ocr_pdf_key,
                file_path=str(output_path),
                content_type="application/pdf",
            )

            # 4. 更新数据库
            _update_book_ocr_complete(book_id, ocr_pdf_key)

            logger.info(
                "OCR processing completed",
                book_id=book_id,
                ocr_pdf_key=ocr_pdf_key,
            )

            return {
                "success": True,
                "book_id": book_id,
                "ocr_pdf_key": ocr_pdf_key,
            }

    except Exception as e:
        logger.exception("OCR processing failed", book_id=book_id)
        _update_book_status(book_id, "ocr_failed", str(e))
        raise


def _run_ocrmypdf(input_path: Path, output_path: Path) -> dict:
    """
    运行 OCRmyPDF 命令

    使用 PaddleOCR 作为 OCR 引擎（通过插件）。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径

    Returns:
        执行结果字典
    """
    try:
        # OCRmyPDF 命令参数
        # --output-type pdf: 输出 PDF 格式
        # --deskew: 自动纠正歪斜
        # --optimize 1: 轻度优化
        # --pdf-renderer hocr: 使用 hOCR 渲染器
        # --tesseract-timeout 180: Tesseract 超时时间
        # --jobs 4: 并行处理
        # --skip-text: 跳过已有文字层的页面
        cmd = [
            "ocrmypdf",
            "--output-type", "pdf",
            "--deskew",
            "--optimize", "1",
            "--pdf-renderer", "hocr",
            "--tesseract-timeout", "180",
            "--jobs", "4",
            "--skip-text",
            # 语言设置（中文+英文）
            "-l", "chi_sim+eng",
            str(input_path),
            str(output_path),
        ]

        # 如果配置了 PaddleOCR 插件
        if settings.celery.ocr_use_paddle:
            cmd.insert(1, "--plugin")
            cmd.insert(2, "paddleocr_plugin")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 小时超时
        )

        if result.returncode == 0:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": result.stderr or "OCR process failed",
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "OCR process timed out (1 hour)",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "ocrmypdf command not found. Please install it.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _update_book_status(book_id: str, status: str, error: str | None = None) -> None:
    """更新书籍处理状态"""
    # 使用同步数据库连接（Celery 任务中）
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    # 创建同步引擎
    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET ocr_status = :status,
                    processing_error = :error,
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "status": status, "error": error},
        )
        conn.commit()


def _update_book_ocr_complete(book_id: str, ocr_pdf_key: str) -> None:
    """更新书籍 OCR 完成状态"""
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET ocr_status = 'completed',
                    ocr_pdf_key = :ocr_pdf_key,
                    has_text_layer = TRUE,
                    processing_status = 'completed',
                    processing_error = NULL,
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "ocr_pdf_key": ocr_pdf_key},
        )
        conn.commit()


@shared_task(
    name="app.tasks.ocr_tasks.check_text_layer",
    max_retries=2,
)
def check_text_layer(book_id: str, minio_key: str) -> dict:
    """
    检查 PDF 是否包含文字层

    用于判断是否需要 OCR 处理。

    Args:
        book_id: 书籍 ID
        minio_key: MinIO 中的文件 Key

    Returns:
        检查结果
    """
    storage = StorageService()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"

            # 下载文件
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            # 使用 pdfminer 检查文字层
            try:
                from pdfminer.high_level import extract_text

                text = extract_text(str(input_path), maxpages=5)
                has_text = len(text.strip()) > 100  # 至少 100 个字符

                return {
                    "book_id": book_id,
                    "has_text_layer": has_text,
                    "sample_length": len(text.strip()),
                }
            except ImportError:
                logger.warning("pdfminer not installed, assuming no text layer")
                return {
                    "book_id": book_id,
                    "has_text_layer": False,
                    "error": "pdfminer not installed",
                }

    except Exception as e:
        logger.exception("Failed to check text layer", book_id=book_id)
        return {
            "book_id": book_id,
            "has_text_layer": False,
            "error": str(e),
        }
