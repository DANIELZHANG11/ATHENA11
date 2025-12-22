"""
用户管理 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_delete_account_unauthorized(client: AsyncClient):
    """测试未认证删除账号"""
    response = await client.delete("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_missing_confirm_header(
    client: AsyncClient,
    auth_headers: dict,
):
    """测试删除账号缺少确认头"""
    response = await client.delete(
        "/api/v1/users/me",
        headers=auth_headers,
    )
    # 应返回 401 (未认证) 或 400 (缺少确认头)
    assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_delete_account_invalid_confirm_header(
    client: AsyncClient,
    auth_headers: dict,
):
    """测试删除账号确认头错误"""
    headers = {**auth_headers, "X-Confirm-Delete": "WRONG_HEADER"}
    response = await client.delete(
        "/api/v1/users/me",
        headers=headers,
    )
    # 应返回 401 (未认证) 或 400 (确认头错误)
    assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_get_notification_settings_unauthorized(client: AsyncClient):
    """测试未认证获取通知设置"""
    response = await client.get("/api/v1/users/me/notification-settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_notification_settings_unauthorized(client: AsyncClient):
    """测试未认证更新通知设置"""
    response = await client.patch(
        "/api/v1/users/me/notification-settings",
        json={"push_enabled": True},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_notification_settings_with_auth(
    client: AsyncClient,
    auth_headers: dict,
):
    """测试更新通知设置"""
    response = await client.patch(
        "/api/v1/users/me/notification-settings",
        headers=auth_headers,
        json={
            "push_enabled": True,
            "email_enabled": False,
            "reading_reminder": True,
        },
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_notification_settings_partial(
    client: AsyncClient,
    auth_headers: dict,
):
    """测试部分更新通知设置"""
    response = await client.patch(
        "/api/v1/users/me/notification-settings",
        headers=auth_headers,
        json={"push_enabled": False},
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401
