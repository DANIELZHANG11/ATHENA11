"""
格式转换任务

使用 Calibre 进行电子书格式转换（MOBI/AZW3 -> EPUB）。
"""

import subprocess
import tempfile
from pathlib import Path

import structlog
from celery import shared_task

from app.core.config import settings
from app.services.storage_service import StorageService

logger = structlog.get_logger()

# Calibre 容器中 ebook-convert 命令的超时时间（秒）
CONVERSION_TIMEOUT = 300  # 5 分钟


@shared_task(
    bind=True,
    name="app.tasks.conversion_tasks.convert_to_epub",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=240,
    time_limit=300,
)
def convert_to_epub(
    self,
    book_id: str,
    user_id: str,  # noqa: ARG001
    minio_key: str,
    original_format: str,
) -> dict:
    """
    将电子书转换为 EPUB 格式

    支持的输入格式：MOBI, AZW, AZW3, FB2, LIT, PDB, DJVU

    Args:
        book_id: 书籍 ID
        user_id: 用户 ID
        minio_key: MinIO 中的原始文件 Key
        original_format: 原始格式

    Returns:
        转换结果字典
    """
    logger.info(
        "Starting format conversion",
        book_id=book_id,
        original_format=original_format,
    )

    # 检查是否需要转换
    if original_format in ("epub", "pdf"):
        logger.info("No conversion needed", book_id=book_id, format=original_format)
        return {"success": True, "converted": False, "message": "No conversion needed"}

    storage = StorageService()
    _update_book_status(book_id, "converting")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / f"input.{original_format}"
            output_path = Path(tmpdir) / "output.epub"

            # 下载原始文件
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            # 执行转换
            result = _run_calibre_convert(input_path, output_path)

            if not result["success"]:
                _update_book_status(book_id, "failed", result.get("error"))
                return result

            # 上传转换后的文件
            epub_key = minio_key.rsplit(".", 1)[0] + ".epub"
            storage.upload_file(
                bucket=settings.minio.minio_bucket_books,
                key=epub_key,
                file_path=str(output_path),
                content_type="application/epub+zip",
            )

            # 更新数据库
            _update_book_conversion_complete(book_id, epub_key)

            logger.info(
                "Conversion completed",
                book_id=book_id,
                epub_key=epub_key,
            )

            return {
                "success": True,
                "converted": True,
                "epub_key": epub_key,
            }

    except subprocess.TimeoutExpired:
        error = "Conversion timeout exceeded"
        logger.error(error, book_id=book_id)
        _update_book_status(book_id, "failed", error)
        return {"success": False, "error": error}

    except Exception as e:
        logger.exception("Conversion failed", book_id=book_id)
        _update_book_status(book_id, "failed", str(e))
        raise self.retry(exc=e) from e


def _run_calibre_convert(input_path: Path, output_path: Path) -> dict:
    """
    调用 Calibre 的 ebook-convert 工具

    使用 Docker exec 在 Calibre 容器中执行转换。
    """
    try:
        # 构建转换命令
        # 在 Docker 环境中，直接使用 ebook-convert
        # 在开发环境中，可能需要配置 Calibre 路径
        cmd = [
            "ebook-convert",
            str(input_path),
            str(output_path),
            "--enable-heuristics",  # 启用启发式处理
            "--embed-all-fonts",  # 嵌入所有字体
            "--subset-embedded-fonts",  # 子集化嵌入字体
        ]

        logger.debug("Running Calibre convert", cmd=" ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            error = result.stderr or result.stdout or "Unknown error"
            logger.error("Calibre conversion failed", error=error)
            return {"success": False, "error": error}

        if not output_path.exists():
            return {"success": False, "error": "Output file not created"}

        return {"success": True}

    except FileNotFoundError:
        # ebook-convert 不可用，尝试使用 Docker exec
        return _run_calibre_docker_convert(input_path, output_path)

    except subprocess.TimeoutExpired:
        raise

    except Exception as e:
        return {"success": False, "error": str(e)}


def _run_calibre_docker_convert(input_path: Path, output_path: Path) -> dict:
    """
    通过 Docker exec 在 Calibre 容器中执行转换

    当本地没有 Calibre 时使用此方法。
    """
    try:
        # 使用 docker exec 在 calibre 容器中执行
        cmd = [
            "docker",
            "exec",
            "athena-calibre",
            "ebook-convert",
            f"/tmp/{input_path.name}",
            f"/tmp/{output_path.name}",
            "--enable-heuristics",
            "--embed-all-fonts",
        ]

        # 先复制文件到容器
        copy_in_cmd = [
            "docker",
            "cp",
            str(input_path),
            f"athena-calibre:/tmp/{input_path.name}",
        ]
        subprocess.run(copy_in_cmd, check=True, timeout=60)

        # 执行转换
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            error = result.stderr or result.stdout or "Unknown error"
            return {"success": False, "error": error}

        # 复制输出文件回来
        copy_out_cmd = [
            "docker",
            "cp",
            f"athena-calibre:/tmp/{output_path.name}",
            str(output_path),
        ]
        subprocess.run(copy_out_cmd, check=True, timeout=60)

        if not output_path.exists():
            return {"success": False, "error": "Output file not copied"}

        return {"success": True}

    except subprocess.TimeoutExpired:
        raise

    except Exception as e:
        return {"success": False, "error": str(e)}


@shared_task(name="app.tasks.conversion_tasks.extract_book_metadata")
def extract_book_metadata(book_id: str, minio_key: str, file_format: str) -> dict:
    """
    使用 Calibre 提取书籍元数据

    支持更多格式的元数据提取。
    """
    logger.info("Extracting metadata with Calibre", book_id=book_id)

    storage = StorageService()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / f"input.{file_format}"
            storage.download_file(
                bucket=settings.minio.minio_bucket_books,
                key=minio_key,
                file_path=str(input_path),
            )

            # 使用 ebook-meta 提取元数据
            cmd = ["ebook-meta", str(input_path)]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

                if result.returncode == 0:
                    meta = _parse_ebook_meta_output(result.stdout)
                    return {"success": True, "meta": meta}
                else:
                    return {"success": False, "error": result.stderr}

            except FileNotFoundError:
                # 尝试 Docker exec
                return _extract_metadata_docker(input_path)

    except Exception as e:
        return {"success": False, "error": str(e)}


def _extract_metadata_docker(input_path: Path) -> dict:
    """通过 Docker 提取元数据"""
    try:
        copy_cmd = [
            "docker",
            "cp",
            str(input_path),
            f"athena-calibre:/tmp/{input_path.name}",
        ]
        subprocess.run(copy_cmd, check=True, timeout=30)

        cmd = [
            "docker",
            "exec",
            "athena-calibre",
            "ebook-meta",
            f"/tmp/{input_path.name}",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.returncode == 0:
            meta = _parse_ebook_meta_output(result.stdout)
            return {"success": True, "meta": meta}
        else:
            return {"success": False, "error": result.stderr}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_ebook_meta_output(output: str) -> dict:
    """解析 ebook-meta 命令输出"""
    meta = {}
    for line in output.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            if key and value:
                meta[key] = value
    return meta


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


def _update_book_conversion_complete(book_id: str, epub_key: str) -> None:
    """更新书籍转换完成状态"""
    from sqlalchemy import create_engine, text

    from app.core.config import settings

    sync_url = settings.database.sync_database_url
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET processing_status = 'completed',
                    converted_epub_key = :epub_key,
                    reader_type = 'epub',
                    is_readable = TRUE,
                    updated_at = NOW()
                WHERE id = :book_id::uuid
            """),
            {"book_id": book_id, "epub_key": epub_key},
        )
        conn.commit()
