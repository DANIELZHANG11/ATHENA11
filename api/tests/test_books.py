"""
书籍 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_books_unauthorized(client: AsyncClient):
    """测试未认证获取书籍列表"""
    response = await client.get("/api/v1/books")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_init_unauthorized(client: AsyncClient):
    """测试未认证初始化上传"""
    response = await client.post(
        "/api/v1/books/upload_init",
        json={
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024000,
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_book_not_found(client: AsyncClient, auth_headers: dict):
    """测试获取不存在的书籍"""
    # 这个测试需要真实的认证
    # 暂时跳过
    pass
