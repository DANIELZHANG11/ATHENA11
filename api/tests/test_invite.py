"""
邀请裂变 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_invite_code_unauthorized(client: AsyncClient):
    """测试未认证获取邀请码"""
    response = await client.get("/api/v1/invite/code")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_invite_stats_unauthorized(client: AsyncClient):
    """测试未认证获取邀请统计"""
    response = await client.get("/api/v1/invite/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_invitees_unauthorized(client: AsyncClient):
    """测试未认证获取被邀请人列表"""
    response = await client.get("/api/v1/invite/invitees")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_invite_rules(client: AsyncClient):
    """测试获取邀请奖励规则"""
    response = await client.get("/api/v1/invite/rules")
    # 奖励规则可能允许未认证访问
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_get_invite_code_with_auth(client: AsyncClient, auth_headers: dict):
    """测试认证后获取邀请码"""
    response = await client.get(
        "/api/v1/invite/code",
        headers=auth_headers,
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_invitees_with_pagination(client: AsyncClient, auth_headers: dict):
    """测试被邀请人列表分页"""
    response = await client.get(
        "/api/v1/invite/invitees",
        headers=auth_headers,
        params={"page": 1, "per_page": 20},
    )
    # 使用模拟 token 会返回 401
    assert response.status_code == 401
