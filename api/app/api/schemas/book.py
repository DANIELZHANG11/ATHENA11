"""
书籍相关 API Schema

Pydantic 模型定义请求和响应结构。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# 请求模型
# =============================================================================


class UploadInitRequest(BaseModel):
    """上传初始化请求"""

    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    content_type: str = Field(..., description="MIME 类型")
    size: int = Field(..., gt=0, description="文件大小(字节)")
    sha256: str | None = Field(None, min_length=64, max_length=64, description="文件 SHA256 哈希")


class UploadCompleteRequest(BaseModel):
    """上传完成请求"""

    key: str = Field(..., description="S3 Object Key")
    etag: str | None = Field(None, description="S3 ETag")
    title: str | None = Field(None, max_length=500, description="书名")
    author: str | None = Field(None, max_length=200, description="作者")


class DedupReferenceRequest(BaseModel):
    """秒传引用请求"""

    sha256: str = Field(..., min_length=64, max_length=64, description="文件 SHA256 哈希")
    title: str | None = Field(None, max_length=500, description="书名")
    author: str | None = Field(None, max_length=200, description="作者")


class BookUpdateRequest(BaseModel):
    """书籍更新请求"""

    title: str | None = Field(None, max_length=500, description="书名")
    author: str | None = Field(None, max_length=200, description="作者")
    metadata_confirmed: bool | None = Field(None, description="元数据已确认")


class OcrTriggerRequest(BaseModel):
    """OCR 触发请求"""

    priority: str = Field(default="normal", description="优先级: normal/high")
    force: bool = Field(default=False, description="强制重新 OCR")


# =============================================================================
# 响应模型
# =============================================================================


class UploadInitResponse(BaseModel):
    """上传初始化响应"""

    upload_url: str = Field(..., description="S3 Presigned Upload URL")
    key: str = Field(..., description="S3 Object Key")
    expires_in: int = Field(..., description="URL 有效期(秒)")
    # 秒传信息
    is_duplicate: bool = Field(default=False, description="是否为重复文件")
    canonical_book_id: str | None = Field(None, description="原书 ID (秒传时)")


class BookMetaResponse(BaseModel):
    """书籍元数据 (从 meta JSONB 字段提取)"""

    page_count: int | None = None
    toc: list[dict[str, Any]] | None = None
    cover_color: str | None = None
    is_scanned: bool | None = None
    dpi: int | None = None


class BookResponse(BaseModel):
    """书籍响应"""

    id: str
    user_id: str
    title: str
    author: str | None
    language: str | None

    # 文件信息
    original_format: str | None
    size: int | None
    cover_url: str | None

    # 处理状态
    processing_status: str
    processing_error: str | None
    reader_type: str | None
    is_readable: bool
    is_interactive: bool

    # 文字层
    has_text_layer: bool | None
    is_image_based: bool

    # OCR
    ocr_status: str | None

    # 元数据
    metadata_confirmed: bool
    meta: BookMetaResponse | None

    # 时间戳
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    """书籍列表响应"""

    items: list[BookResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BookContentResponse(BaseModel):
    """书籍内容访问响应"""

    download_url: str = Field(..., description="S3 Presigned Download URL")
    expires_in: int = Field(..., description="URL 有效期(秒)")
    content_type: str
    size: int | None


class BookCoverResponse(BaseModel):
    """书籍封面响应"""

    cover_url: str = Field(..., description="封面图片 URL")
    expires_in: int = Field(..., description="URL 有效期(秒)")


class OcrStatusResponse(BaseModel):
    """OCR 状态响应"""

    status: str  # pending/processing/completed/failed
    progress: int  # 0-100
    total_pages: int
    processed_pages: int
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None


class BookDeleteResponse(BaseModel):
    """书籍删除响应"""

    id: str
    deleted: bool
    message: str
