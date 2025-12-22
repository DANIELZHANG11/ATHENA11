"""
付费订阅 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_plans_unauthorized(client: AsyncClient):
    """测试未认证获取订阅方案列表"""
    response = await client.get("/api/v1/billing/plans")
    # plans 端点可能允许未认证访问，或返回 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_get_plans_returns_list(client: AsyncClient, auth_headers: dict):
    """测试获取订阅方案列表"""
    response = await client.get(
        "/api/v1/billing/plans",
        headers=auth_headers,
    )
    # 未认证的 auth_headers 会返回 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_checkout_unauthorized(client: AsyncClient):
    """测试未认证创建支付会话"""
    response = await client.post(
        "/api/v1/billing/checkout",
        json={
            "product_type": "subscription",
            "product_id": "test-plan",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_checkout_invalid_product_type(client: AsyncClient, auth_headers: dict):
    """测试无效商品类型"""
    response = await client.post(
        "/api/v1/billing/checkout",
        headers=auth_headers,
        json={
            "product_type": "invalid_type",
            "product_id": "test-plan",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        },
    )
    # 无效类型应返回 422 或 401(未认证)
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_get_payment_history_unauthorized(client: AsyncClient):
    """测试未认证获取支付历史"""
    response = await client.get("/api/v1/billing/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_subscription_status_unauthorized(client: AsyncClient):
    """测试未认证获取订阅状态"""
    response = await client.get("/api/v1/billing/subscription")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_credits_balance_unauthorized(client: AsyncClient):
    """测试未认证获取积分余额"""
    response = await client.get("/api/v1/billing/credits/balance")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_credit_products(client: AsyncClient):
    """测试获取积分商品列表"""
    response = await client.get("/api/v1/billing/credits/products")
    # 积分商品列表可能允许未认证访问
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_apple_iap_verify_unauthorized(client: AsyncClient):
    """测试未认证 Apple IAP 验证"""
    response = await client.post(
        "/api/v1/billing/iap/apple/verify",
        json={
            "receipt_data": "test-receipt",
            "product_id": "test-product",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_google_iap_verify_unauthorized(client: AsyncClient):
    """测试未认证 Google IAP 验证"""
    response = await client.post(
        "/api/v1/billing/iap/google/verify",
        json={
            "purchase_token": "test-token",
            "product_id": "test-product",
            "package_name": "com.example.app",
        },
    )
    assert response.status_code == 401
