"""
阅读进度与统计 Schemas

定义 BookPosition, ReadingTimeLog, ReadingStats 等数据结构。
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

# ==========================================================================
# 阅读位置 (BookPosition)
# ==========================================================================


class BookPositionBase(BaseModel):
    """阅读位置基础字段"""

    progress: float = Field(0, ge=0, le=1, description="阅读进度 (0-1)")
    last_cfi: str | None = Field(None, description="EPUB CFI 位置")
    last_page: int | None = Field(None, ge=1, description="当前页码 (PDF)")
    total_pages: int | None = Field(None, ge=1, description="总页数 (PDF)")


class BookPositionUpdate(BookPositionBase):
    """更新阅读位置请求"""

    device_id: str | None = Field(None, max_length=64, description="设备 ID")


class BookPositionResponse(BookPositionBase):
    """阅读位置响应"""

    user_id: str
    book_id: str
    finished_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==========================================================================
# 阅读时长记录 (ReadingTimeLog)
# ==========================================================================


class ReadingTimeLogCreate(BaseModel):
    """创建阅读会话记录"""

    book_id: str = Field(..., description="书籍 ID")
    device_id: str | None = Field(None, max_length=64, description="设备 ID")


class ReadingTimeLogUpdate(BaseModel):
    """更新阅读会话 (心跳/结束)"""

    duration_ms: int = Field(..., ge=0, description="阅读时长 (毫秒)")
    is_active: bool = Field(True, description="会话是否活跃")


class ReadingTimeLogResponse(BaseModel):
    """阅读会话响应"""

    id: str
    book_id: str
    device_id: str | None
    is_active: bool
    duration_ms: int
    last_active_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ==========================================================================
# 阅读统计 (ReadingStats)
# ==========================================================================


class DailyReadingStats(BaseModel):
    """单日阅读统计"""

    day: date
    total_duration_ms: int = Field(0, description="总阅读时长 (毫秒)")
    books_read: int = Field(0, description="阅读书籍数")
    pages_read: int = Field(0, description="阅读页数")


class WeeklyReadingStats(BaseModel):
    """周阅读统计"""

    week_start: date
    week_end: date
    total_duration_ms: int
    daily_average_ms: int
    books_read: int
    days_active: int


class MonthlyReadingStats(BaseModel):
    """月阅读统计"""

    year: int
    month: int
    total_duration_ms: int
    books_read: int
    books_finished: int
    days_active: int


class ReadingStatsResponse(BaseModel):
    """阅读统计综合响应"""

    today: DailyReadingStats
    this_week: WeeklyReadingStats
    this_month: MonthlyReadingStats
    streak_days: int = Field(0, description="连续阅读天数")
    total_books: int = Field(0, description="总书籍数")
    finished_books: int = Field(0, description="已读完书籍数")
    total_duration_ms: int = Field(0, description="累计阅读时长 (毫秒)")


class ReadingHistoryItem(BaseModel):
    """阅读历史记录项"""

    day: date
    duration_ms: int
    books_read: int


class ReadingHistoryResponse(BaseModel):
    """阅读历史响应"""

    items: list[ReadingHistoryItem]
    total_days: int


# ==========================================================================
# 阅读目标 (ReadingGoal)
# ==========================================================================


class ReadingGoalBase(BaseModel):
    """阅读目标基础字段"""

    goal_type: str = Field(..., pattern="^(daily_minutes|weekly_books|yearly_books)$")
    target_value: int = Field(..., ge=1, description="目标值")


class ReadingGoalCreate(ReadingGoalBase):
    """创建阅读目标"""

    pass


class ReadingGoalResponse(ReadingGoalBase):
    """阅读目标响应"""

    id: str
    current_value: int = Field(0, description="当前进度")
    is_achieved: bool = Field(False, description="是否达成")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==========================================================================
# 书籍阅读进度列表
# ==========================================================================


class BookReadingProgress(BaseModel):
    """书籍阅读进度摘要"""

    book_id: str
    title: str
    author: str | None
    cover_url: str | None
    progress: float
    last_read_at: datetime
    finished_at: datetime | None = None


class RecentBooksResponse(BaseModel):
    """最近阅读书籍列表"""

    items: list[BookReadingProgress]
    total: int
