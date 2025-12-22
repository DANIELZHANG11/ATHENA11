"""
阅读进度与统计 API 路由

处理阅读位置、时长记录、统计数据等功能。

注意：根据 App-First 架构，阅读进度数据主要通过 PowerSync 同步，
此 API 仅用于特殊场景（如获取统计数据、手动同步等）。
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.reading import (
    BookPositionResponse,
    BookPositionUpdate,
    BookReadingProgress,
    DailyReadingStats,
    ReadingHistoryItem,
    ReadingHistoryResponse,
    ReadingStatsResponse,
    ReadingTimeLogCreate,
    ReadingTimeLogResponse,
    ReadingTimeLogUpdate,
    RecentBooksResponse,
)
from app.services.reading_service import ReadingService

router = APIRouter(prefix="/reading", tags=["阅读"])


# ==========================================================================
# 阅读位置 (通常由 PowerSync 处理，此处为 REST 备用)
# ==========================================================================


@router.get("/position/{book_id}", response_model=BookPositionResponse)
async def get_book_position(
    book_id: Annotated[str, Path(description="书籍 ID")],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookPositionResponse:
    """
    获取书籍阅读位置

    注意：正常情况下，阅读位置通过 PowerSync 同步到客户端。
    此接口用于在线查询或手动同步场景。
    """
    service = ReadingService(db)
    position = await service.get_position(str(current_user.id), book_id)

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not_found",
        )

    return BookPositionResponse(
        user_id=str(position.user_id),
        book_id=str(position.book_id),
        progress=float(position.progress),
        last_cfi=position.last_cfi,
        last_page=position.last_page,
        total_pages=position.total_pages,
        finished_at=position.finished_at,
        updated_at=position.updated_at,
    )


@router.put("/position/{book_id}", response_model=BookPositionResponse)
async def update_book_position(
    book_id: Annotated[str, Path(description="书籍 ID")],
    request: BookPositionUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookPositionResponse:
    """
    更新书籍阅读位置

    注意：正常情况下，阅读位置通过 PowerSync 同步。
    此接口用于需要立即服务端确认的场景。
    """
    service = ReadingService(db)
    position = await service.update_position(
        user_id=str(current_user.id),
        book_id=book_id,
        progress=request.progress,
        last_cfi=request.last_cfi,
        last_page=request.last_page,
        total_pages=request.total_pages,
        device_id=request.device_id,
    )

    return BookPositionResponse(
        user_id=str(position.user_id),
        book_id=str(position.book_id),
        progress=float(position.progress),
        last_cfi=position.last_cfi,
        last_page=position.last_page,
        total_pages=position.total_pages,
        finished_at=position.finished_at,
        updated_at=position.updated_at,
    )


@router.post("/position/{book_id}/finish", response_model=BookPositionResponse)
async def mark_book_finished(
    book_id: Annotated[str, Path(description="书籍 ID")],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookPositionResponse:
    """标记书籍已读完"""
    service = ReadingService(db)
    position = await service.mark_finished(str(current_user.id), book_id)

    return BookPositionResponse(
        user_id=str(position.user_id),
        book_id=str(position.book_id),
        progress=float(position.progress),
        last_cfi=position.last_cfi,
        last_page=position.last_page,
        total_pages=position.total_pages,
        finished_at=position.finished_at,
        updated_at=position.updated_at,
    )


# ==========================================================================
# 阅读会话 (时长记录)
# ==========================================================================


@router.post("/session", response_model=ReadingTimeLogResponse)
async def start_reading_session(
    request: ReadingTimeLogCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadingTimeLogResponse:
    """
    开始阅读会话

    客户端打开阅读器时调用，创建新的时长记录。
    """
    service = ReadingService(db)
    session = await service.start_reading_session(
        user_id=str(current_user.id),
        book_id=request.book_id,
        device_id=request.device_id,
    )

    return ReadingTimeLogResponse(
        id=str(session.id),
        book_id=str(session.book_id),
        device_id=session.device_id,
        is_active=session.is_active,
        duration_ms=session.duration_ms,
        last_active_at=session.last_active_at,
        created_at=session.created_at,
    )


@router.get("/session/active", response_model=ReadingTimeLogResponse | None)
async def get_active_session(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadingTimeLogResponse | None:
    """获取当前活跃的阅读会话"""
    service = ReadingService(db)
    session = await service.get_active_session(str(current_user.id))

    if not session:
        return None

    return ReadingTimeLogResponse(
        id=str(session.id),
        book_id=str(session.book_id),
        device_id=session.device_id,
        is_active=session.is_active,
        duration_ms=session.duration_ms,
        last_active_at=session.last_active_at,
        created_at=session.created_at,
    )


@router.put("/session/{session_id}", response_model=ReadingTimeLogResponse)
async def update_reading_session(
    session_id: Annotated[str, Path(description="会话 ID")],
    request: ReadingTimeLogUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadingTimeLogResponse:
    """
    更新阅读会话

    用于心跳更新（定期汇报时长）或结束会话。
    建议客户端每 30 秒发送一次心跳。
    """
    service = ReadingService(db)
    session = await service.update_reading_session(
        session_id=session_id,
        user_id=str(current_user.id),
        duration_ms=request.duration_ms,
        is_active=request.is_active,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not_found",
        )

    return ReadingTimeLogResponse(
        id=str(session.id),
        book_id=str(session.book_id),
        device_id=session.device_id,
        is_active=session.is_active,
        duration_ms=session.duration_ms,
        last_active_at=session.last_active_at,
        created_at=session.created_at,
    )


@router.post("/session/{session_id}/end", response_model=ReadingTimeLogResponse)
async def end_reading_session(
    session_id: Annotated[str, Path(description="会话 ID")],
    request: ReadingTimeLogUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadingTimeLogResponse:
    """
    结束阅读会话

    客户端关闭阅读器时调用，记录最终时长。
    """
    service = ReadingService(db)
    session = await service.end_reading_session(
        session_id=session_id,
        user_id=str(current_user.id),
        final_duration_ms=request.duration_ms,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not_found",
        )

    return ReadingTimeLogResponse(
        id=str(session.id),
        book_id=str(session.book_id),
        device_id=session.device_id,
        is_active=session.is_active,
        duration_ms=session.duration_ms,
        last_active_at=session.last_active_at,
        created_at=session.created_at,
    )


# ==========================================================================
# 阅读统计
# ==========================================================================


@router.get("/stats", response_model=ReadingStatsResponse)
async def get_reading_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadingStatsResponse:
    """
    获取综合阅读统计

    包含今日、本周、本月数据，以及连续阅读天数。
    """
    service = ReadingService(db)
    stats = await service.get_comprehensive_stats(str(current_user.id))

    return ReadingStatsResponse(
        today=DailyReadingStats(**stats["today"]),
        this_week=stats["this_week"],
        this_month=stats["this_month"],
        streak_days=stats["streak_days"],
        total_books=stats["total_books"],
        finished_books=stats["finished_books"],
        total_duration_ms=stats["total_duration_ms"],
    )


@router.get("/stats/daily/{day}", response_model=DailyReadingStats)
async def get_daily_stats(
    day: Annotated[date, Path(description="日期 (YYYY-MM-DD)")],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DailyReadingStats:
    """获取指定日期的阅读统计"""
    service = ReadingService(db)
    stats = await service.get_daily_stats(str(current_user.id), day)
    return DailyReadingStats(**stats)


@router.get("/history", response_model=ReadingHistoryResponse)
async def get_reading_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=7, le=365, description="天数"),
) -> ReadingHistoryResponse:
    """
    获取阅读历史

    返回指定天数内的每日阅读数据，用于生成图表。
    """
    service = ReadingService(db)
    history = await service.get_reading_history(str(current_user.id), days)

    return ReadingHistoryResponse(
        items=[ReadingHistoryItem(**h) for h in history],
        total_days=len(history),
    )


@router.get("/recent", response_model=RecentBooksResponse)
async def get_recent_books(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(10, ge=1, le=50, description="数量"),
) -> RecentBooksResponse:
    """
    获取最近阅读的书籍

    按最后阅读时间排序。
    """
    service = ReadingService(db)
    books = await service.get_recent_books(str(current_user.id), limit)

    return RecentBooksResponse(
        items=[BookReadingProgress(**b) for b in books],
        total=len(books),
    )
