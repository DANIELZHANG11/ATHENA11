"""
付费订阅相关 Pydantic 模型
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ============================================================================
# 订阅方案
# ============================================================================


class PlanResponse(BaseModel):
    """订阅方案"""

    id: str
    name: str
    description: str | None = None
    price: Decimal
    currency: str = "CNY"
    period: str  # monthly/yearly
    features: list[str] = []
    stripe_price_id: str | None = None
    is_active: bool = True


class PlanListResponse(BaseModel):
    """订阅方案列表"""

    items: list[PlanResponse]


# ============================================================================
# 支付
# ============================================================================


class CheckoutRequest(BaseModel):
    """创建支付会话请求"""

    product_type: str = Field(description="商品类型: subscription/credits")
    product_id: str = Field(description="商品 ID")
    success_url: str = Field(description="支付成功跳转 URL")
    cancel_url: str = Field(description="支付取消跳转 URL")


class CheckoutResponse(BaseModel):
    """创建支付会话响应"""

    session_id: str
    checkout_url: str
    expires_at: datetime


class PaymentHistoryItem(BaseModel):
    """支付历史项"""

    id: str
    gateway: str
    product_type: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class PaymentHistoryResponse(BaseModel):
    """支付历史列表"""

    items: list[PaymentHistoryItem]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# 订阅状态
# ============================================================================


class SubscriptionResponse(BaseModel):
    """订阅状态"""

    is_active: bool
    tier: str
    expires_at: datetime | None = None
    auto_renew: bool = False
    cancel_at_period_end: bool = False
    payment_method: str | None = None


# ============================================================================
# Credits
# ============================================================================


class CreditBalanceResponse(BaseModel):
    """积分余额"""

    balance: int
    free_credits_remaining: int
    free_credits_reset_at: datetime | None = None


class CreditProductResponse(BaseModel):
    """积分商品"""

    id: str
    name: str
    description: str | None = None
    credits: int
    bonus_credits: int = 0
    price: Decimal
    currency: str = "CNY"
    is_active: bool = True


class CreditProductListResponse(BaseModel):
    """积分商品列表"""

    items: list[CreditProductResponse]


# ============================================================================
# IAP 校验
# ============================================================================


class AppleIAPVerifyRequest(BaseModel):
    """Apple IAP 验证请求"""

    transaction_id: str
    original_transaction_id: str
    signed_payload: str
    product_id: str
    environment: str = Field(default="Production", pattern="^(Production|Sandbox)$")


class GoogleIAPVerifyRequest(BaseModel):
    """Google Play IAP 验证请求"""

    purchase_token: str
    product_id: str
    package_name: str
    is_subscription: bool = True


class IAPVerifyResponse(BaseModel):
    """IAP 验证响应"""

    valid: bool
    product_id: str
    expires_at: datetime | None = None
    is_trial_period: bool = False
    membership_updated: bool = False
    error: str | None = None
