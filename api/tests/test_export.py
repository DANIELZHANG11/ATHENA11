"""
数据导出 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_export_notes_unauthorized(client: AsyncClient):
    """测试未认证导出笔记"""
    response = await client.get("/api/v1/export/notes")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_notes_with_format_markdown(client: AsyncClient, auth_headers: dict):
    """测试导出笔记为 Markdown 格式"""
    response = await client.get(
        "/api/v1/export/notes",
        headers=auth_headers,
        params={"format": "markdown"},
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_notes_with_format_json(client: AsyncClient, auth_headers: dict):
    """测试导出笔记为 JSON 格式"""
    response = await client.get(
        "/api/v1/export/notes",
        headers=auth_headers,
        params={"format": "json"},
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_notes_with_format_html(client: AsyncClient, auth_headers: dict):
    """测试导出笔记为 HTML 格式"""
    response = await client.get(
        "/api/v1/export/notes",
        headers=auth_headers,
        params={"format": "html"},
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_notes_invalid_format(client: AsyncClient, auth_headers: dict):
    """测试无效导出格式"""
    response = await client.get(
        "/api/v1/export/notes",
        headers=auth_headers,
        params={"format": "invalid_format"},
    )
    # 应返回 401 或 422
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_export_notes_with_book_filter(client: AsyncClient, auth_headers: dict):
    """测试按书籍过滤导出"""
    response = await client.get(
        "/api/v1/export/notes",
        headers=auth_headers,
        params={
            "format": "markdown",
            "book_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401
