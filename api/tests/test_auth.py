"""
认证 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_email_code_invalid_email(client: AsyncClient):
    """测试无效邮箱请求验证码"""
    response = await client.post(
        "/api/v1/auth/email/send_code",
        json={"email": "invalid-email"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_request_email_code_valid(client: AsyncClient):
    """测试有效邮箱请求验证码"""
    response = await client.post(
        "/api/v1/auth/email/send_code",
        json={"email": "test@example.com"},
    )
    # 在测试环境可能返回 200 或 503 (如果邮件服务未配置)
    assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_verify_email_code_invalid(client: AsyncClient):
    """测试无效验证码格式"""
    response = await client.post(
        "/api/v1/auth/email/verify_code",
        json={
            "email": "test@example.com",
            "code": "12345",  # 无效格式 (非6位)
        },
    )
    # 应该返回 401 或 400 或 422 (参数校验失败)
    assert response.status_code in [400, 401, 422]


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """测试未认证获取用户信息"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """测试无效刷新令牌"""
    response = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code in [400, 401]
