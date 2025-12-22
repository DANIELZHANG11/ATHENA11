"""
书籍管理 API 路由

处理书籍上传、下载、删除等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.book import (
    BookContentResponse,
    BookCoverResponse,
    BookDeleteResponse,
    BookListResponse,
    BookMetaResponse,
    BookResponse,
    DedupReferenceRequest,
    OcrStatusResponse,
    OcrTriggerRequest,
    UploadCompleteRequest,
    UploadInitRequest,
    UploadInitResponse,
)
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["书籍"])


@router.post("/upload_init", response_model=UploadInitResponse)
async def init_upload(
    request: UploadInitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UploadInitResponse:
    """
    初始化书籍上传

    返回 S3 Presigned Upload URL，客户端直接上传到 MinIO。
    如果提供了 SHA256 且文件已存在，返回秒传信息。
    """
    service = BookService(db)
    result = await service.init_upload(
        user=current_user,
        filename=request.filename,
        content_type=request.content_type,
        size=request.size,
        sha256=request.sha256,
    )

    return UploadInitResponse(
        upload_url=result["upload_url"],
        key=result["key"],
        expires_in=result["expires_in"],
        is_duplicate=result["is_duplicate"],
        canonical_book_id=result["canonical_book_id"],
    )


@router.post("/upload_complete", response_model=BookResponse)
async def complete_upload(
    request: UploadCompleteRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookResponse:
    """
    完成书籍上传

    在文件上传到 S3 后调用，创建书籍记录并触发后处理。
    """
    service = BookService(db)
    book = await service.complete_upload(
        user=current_user,
        key=request.key,
        etag=request.etag,
        title=request.title,
        author=request.author,
    )

    return _book_to_response(book)


@router.post("/dedup_reference", response_model=BookResponse)
async def create_dedup_reference(
    request: DedupReferenceRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookResponse:
    """
    创建秒传引用

    复用已存在的文件，创建新的书籍记录。
    """
    service = BookService(db)
    book = await service.create_dedup_reference(
        user=current_user,
        sha256=request.sha256,
        title=request.title,
        author=request.author,
    )

    return _book_to_response(book)


@router.get("", response_model=BookListResponse)
async def list_books(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, max_length=100, description="搜索关键词"),
    shelf_id: str | None = Query(None, description="书架 ID"),
) -> BookListResponse:
    """
    获取书籍列表

    支持分页、搜索和书架过滤。
    """
    service = BookService(db)
    books, total = await service.list_books(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
        search=search,
        shelf_id=shelf_id,
    )

    return BookListResponse(
        items=[_book_to_response(b) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookResponse:
    """获取书籍详情"""
    service = BookService(db)
    book = await service.get_book(book_id, str(current_user.id))
    return _book_to_response(book)


@router.get("/{book_id}/content", response_model=BookContentResponse)
async def get_book_content(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookContentResponse:
    """
    获取书籍内容下载 URL

    返回 S3 Presigned Download URL。
    """
    service = BookService(db)
    result = await service.get_content_url(book_id, str(current_user.id))

    return BookContentResponse(
        download_url=result["download_url"],
        expires_in=result["expires_in"],
        content_type=result["content_type"],
        size=result["size"],
    )


@router.get("/{book_id}/cover", response_model=BookCoverResponse)
async def get_book_cover(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookCoverResponse:
    """获取书籍封面 URL"""
    service = BookService(db)
    result = await service.get_cover_url(book_id, str(current_user.id))

    return BookCoverResponse(
        cover_url=result["cover_url"],
        expires_in=result["expires_in"],
    )


@router.delete("/{book_id}", response_model=BookDeleteResponse)
async def delete_book(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    permanent: bool = Query(False, description="是否永久删除"),
) -> BookDeleteResponse:
    """
    删除书籍

    默认软删除，30 天后自动清理。
    设置 permanent=true 立即永久删除。
    """
    service = BookService(db)
    await service.delete_book(
        book_id=book_id,
        user_id=str(current_user.id),
        permanent=permanent,
    )

    return BookDeleteResponse(
        id=book_id,
        deleted=True,
        message="book_deleted" if permanent else "book_soft_deleted",
    )


def _book_to_response(book) -> BookResponse:
    """转换书籍模型为响应"""
    meta = None
    if book.meta:
        meta = BookMetaResponse(
            page_count=book.meta.get("page_count"),
            toc=book.meta.get("toc"),
            cover_color=book.meta.get("cover_color"),
            is_scanned=book.meta.get("is_scanned"),
            dpi=book.meta.get("dpi"),
        )

    return BookResponse(
        id=str(book.id),
        user_id=str(book.user_id),
        title=book.title,
        author=book.author,
        language=book.language,
        original_format=book.original_format,
        size=book.size,
        cover_url=None,  # 需要单独请求
        processing_status=book.processing_status,
        processing_error=book.processing_error,
        reader_type=book.reader_type,
        is_readable=book.is_readable,
        is_interactive=book.is_interactive,
        has_text_layer=book.has_text_layer,
        is_image_based=book.is_image_based,
        ocr_status=book.ocr_status,
        metadata_confirmed=book.metadata_confirmed,
        meta=meta,
        created_at=book.created_at,
        updated_at=book.updated_at,
    )


# ============================================================================
# OCR 处理
# ============================================================================


@router.post("/{book_id}/ocr")
async def trigger_ocr(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: OcrTriggerRequest | None = None,
) -> dict:
    """
    触发 OCR 处理

    用户主动请求对图片型 PDF 进行 OCR 处理。
    支持 OCR 复用（假 OCR）以节省计算资源。
    """
    service = BookService(db)
    priority = request.priority if request else "normal"
    force = request.force if request else False

    result = await service.trigger_ocr(
        book_id=book_id,
        user_id=str(current_user.id),
        priority=priority,
        force=force,
    )

    return result


@router.get("/{book_id}/ocr/status", response_model=OcrStatusResponse)
async def get_ocr_status(
    book_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OcrStatusResponse:
    """获取 OCR 处理状态"""
    service = BookService(db)
    status = await service.get_ocr_status(book_id, str(current_user.id))

    return OcrStatusResponse(
        status=status["ocr_status"] or "none",
        progress=0,  # TODO: 从任务获取进度
        total_pages=0,
        processed_pages=0,
        error=status["error_message"],
        started_at=None,
        completed_at=status["completed_at"],
    )


