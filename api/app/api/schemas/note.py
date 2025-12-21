"""
笔记相关 Pydantic 模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# 位置信息
# ============================================================================


class PositionInfo(BaseModel):
    """文档内位置信息"""

    page: int | None = Field(None, description="页码 (PDF)")
    chapter: str | None = Field(None, description="章节 (EPUB)")
    paragraph: int | None = Field(None, description="段落索引")
    char_start: int | None = Field(None, description="字符起始位置")
    char_end: int | None = Field(None, description="字符结束位置")
    cfi: str | None = Field(None, description="EPUB CFI 定位")


# ============================================================================
# 笔记
# ============================================================================


class NoteCreate(BaseModel):
    """创建笔记请求"""

    book_id: str = Field(..., description="书籍 ID")
    position_json: dict[str, Any] = Field(..., description="位置信息")
    content: str = Field(..., min_length=1, max_length=50000, description="笔记内容")
    tags: list[str] = Field(default_factory=list, max_length=20, description="标签")
    color: str | None = Field(None, max_length=20, description="颜色标记")


class NoteUpdate(BaseModel):
    """更新笔记请求"""

    content: str | None = Field(None, min_length=1, max_length=50000)
    tags: list[str] | None = Field(None, max_length=20)
    color: str | None = Field(None, max_length=20)


class NoteResponse(BaseModel):
    """笔记响应"""

    id: str
    book_id: str
    position_json: dict[str, Any]
    content: str
    tags: list[str]
    color: str | None
    conflict_of: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """笔记列表响应"""

    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# 高亮
# ============================================================================


class HighlightCreate(BaseModel):
    """创建高亮请求"""

    book_id: str = Field(..., description="书籍 ID")
    position_json: dict[str, Any] = Field(..., description="位置信息")
    color: str = Field("yellow", max_length=20, description="高亮颜色")
    text_preview: str | None = Field(None, max_length=500, description="文字预览")


class HighlightUpdate(BaseModel):
    """更新高亮请求"""

    color: str | None = Field(None, max_length=20)


class HighlightResponse(BaseModel):
    """高亮响应"""

    id: str
    book_id: str
    position_json: dict[str, Any]
    color: str
    text_preview: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HighlightListResponse(BaseModel):
    """高亮列表响应"""

    items: list[HighlightResponse]
    total: int


# ============================================================================
# 书签
# ============================================================================


class BookmarkCreate(BaseModel):
    """创建书签请求"""

    book_id: str = Field(..., description="书籍 ID")
    position_json: dict[str, Any] = Field(..., description="位置信息")
    title: str | None = Field(None, max_length=255, description="书签标题")


class BookmarkResponse(BaseModel):
    """书签响应"""

    id: str
    book_id: str
    position_json: dict[str, Any]
    title: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    """书签列表响应"""

    items: list[BookmarkResponse]
    total: int


# ============================================================================
# 书架
# ============================================================================


class ShelfCreate(BaseModel):
    """创建书架请求"""

    name: str = Field(..., min_length=1, max_length=100, description="书架名称")
    color: str | None = Field(None, max_length=20, description="颜色")
    icon: str | None = Field(None, max_length=50, description="图标")
    sort_order: int = Field(0, description="排序顺序")


class ShelfUpdate(BaseModel):
    """更新书架请求"""

    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, max_length=20)
    icon: str | None = Field(None, max_length=50)
    sort_order: int | None = None


class ShelfResponse(BaseModel):
    """书架响应"""

    id: str
    name: str
    color: str | None
    icon: str | None
    sort_order: int
    book_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShelfListResponse(BaseModel):
    """书架列表响应"""

    items: list[ShelfResponse]
    total: int


class ShelfBookAdd(BaseModel):
    """添加书籍到书架"""

    book_ids: list[str] = Field(..., min_length=1, max_length=100, description="书籍 ID 列表")


class ShelfBookRemove(BaseModel):
    """从书架移除书籍"""

    book_ids: list[str] = Field(..., min_length=1, max_length=100, description="书籍 ID 列表")


# ============================================================================
# 通用删除响应
# ============================================================================


class DeleteResponse(BaseModel):
    """删除响应"""

    id: str
    deleted: bool
    message: str = "success"
