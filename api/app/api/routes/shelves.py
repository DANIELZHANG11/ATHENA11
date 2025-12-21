"""
书架 API 路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.note import (
    DeleteResponse,
    ShelfBookAdd,
    ShelfBookRemove,
    ShelfCreate,
    ShelfListResponse,
    ShelfResponse,
    ShelfUpdate,
)
from app.services.note_service import NoteService

router = APIRouter(prefix="/shelves", tags=["书架"])


@router.post("", response_model=ShelfResponse)
async def create_shelf(
    request: ShelfCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ShelfResponse:
    """创建书架"""
    service = NoteService(db)
    shelf = await service.create_shelf(
        user_id=str(current_user.id),
        name=request.name,
        color=request.color,
        icon=request.icon,
        sort_order=request.sort_order,
    )
    return _shelf_to_response(shelf)


@router.get("", response_model=ShelfListResponse)
async def list_shelves(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ShelfListResponse:
    """获取书架列表"""
    service = NoteService(db)
    shelves, total = await service.list_shelves(str(current_user.id))
    return ShelfListResponse(
        items=[_shelf_to_response(s) for s in shelves],
        total=total,
    )


@router.get("/{shelf_id}", response_model=ShelfResponse)
async def get_shelf(
    shelf_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ShelfResponse:
    """获取书架详情"""
    service = NoteService(db)
    shelf = await service.get_shelf(shelf_id, str(current_user.id))
    return _shelf_to_response(shelf)


@router.patch("/{shelf_id}", response_model=ShelfResponse)
async def update_shelf(
    shelf_id: str,
    request: ShelfUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ShelfResponse:
    """更新书架"""
    service = NoteService(db)
    shelf = await service.update_shelf(
        shelf_id=shelf_id,
        user_id=str(current_user.id),
        name=request.name,
        color=request.color,
        icon=request.icon,
        sort_order=request.sort_order,
    )
    return _shelf_to_response(shelf)


@router.delete("/{shelf_id}", response_model=DeleteResponse)
async def delete_shelf(
    shelf_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeleteResponse:
    """删除书架"""
    service = NoteService(db)
    await service.delete_shelf(shelf_id, str(current_user.id))
    return DeleteResponse(id=shelf_id, deleted=True)


@router.post("/{shelf_id}/books")
async def add_books_to_shelf(
    shelf_id: str,
    request: ShelfBookAdd,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """添加书籍到书架"""
    service = NoteService(db)
    added_count = await service.add_books_to_shelf(
        shelf_id=shelf_id,
        user_id=str(current_user.id),
        book_ids=request.book_ids,
    )
    return {"added_count": added_count}


@router.delete("/{shelf_id}/books")
async def remove_books_from_shelf(
    shelf_id: str,
    request: ShelfBookRemove,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """从书架移除书籍"""
    service = NoteService(db)
    removed_count = await service.remove_books_from_shelf(
        shelf_id=shelf_id,
        user_id=str(current_user.id),
        book_ids=request.book_ids,
    )
    return {"removed_count": removed_count}


def _shelf_to_response(shelf) -> ShelfResponse:
    return ShelfResponse(
        id=str(shelf.id),
        name=shelf.name,
        color=shelf.color,
        icon=shelf.icon,
        sort_order=shelf.sort_order,
        book_count=getattr(shelf, "book_count", 0),
        created_at=shelf.created_at,
        updated_at=shelf.updated_at,
    )


