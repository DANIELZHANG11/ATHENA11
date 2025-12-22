"""
付费订阅 API 路由

处理订阅方案、支付、积分、IAP 验证等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.billing import (
    AppleIAPVerifyRequest,
    CheckoutRequest,
    CheckoutResponse,
    CreditBalanceResponse,
    CreditProductListResponse,
    CreditProductResponse,
    GoogleIAPVerifyRequest,
    IAPVerifyResponse,
    PaymentHistoryItem,
    PaymentHistoryResponse,
    PlanListResponse,
    PlanResponse,
    SubscriptionResponse,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["付费订阅"])


# ============================================================================
# 订阅方案
# ============================================================================


@router.get("/plans", response_model=PlanListResponse)
async def get_plans(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlanListResponse:
    """获取所有可用订阅方案"""
    service = BillingService(db)
    plans = await service.get_plans()
    return PlanListResponse(
        items=[
            PlanResponse(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                price=p["price"],
                currency=p["currency"],
                period=p["period"],
                features=p["features"],
                stripe_price_id=p["stripe_price_id"],
                is_active=p["is_active"],
            )
            for p in plans
        ]
    )


# ============================================================================
# 支付
# ============================================================================


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CheckoutResponse:
    """
    创建支付会话

    返回支付网关的结账 URL，客户端跳转完成支付。
    """
    service = BillingService(db)
    result = await service.create_checkout_session(
        user_id=str(current_user.id),
        product_type=request.product_type,
        product_id=request.product_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )

    return CheckoutResponse(
        session_id=result["session_id"],
        checkout_url=result["checkout_url"],
        expires_at=result["expires_at"],
    )


@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaymentHistoryResponse:
    """获取支付历史"""
    service = BillingService(db)
    sessions, total = await service.get_payment_history(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
    )

    return PaymentHistoryResponse(
        items=[
            PaymentHistoryItem(
                id=str(s.id),
                gateway=s.gateway,
                product_type=s.product_type,
                amount=s.amount,
                currency=s.currency,
                status=s.status,
                created_at=s.created_at,
                completed_at=s.completed_at,
            )
            for s in sessions
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


# ============================================================================
# 订阅状态
# ============================================================================


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_status(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionResponse:
    """获取当前订阅状态"""
    service = BillingService(db)
    status = await service.get_subscription_status(str(current_user.id))

    return SubscriptionResponse(
        is_active=status["is_active"],
        tier=status["tier"],
        expires_at=status["expires_at"],
        auto_renew=status["auto_renew"],
        cancel_at_period_end=status["cancel_at_period_end"],
        payment_method=status["payment_method"],
    )


# ============================================================================
# 积分
# ============================================================================


@router.get("/credits/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CreditBalanceResponse:
    """获取积分余额"""
    service = BillingService(db)
    balance = await service.get_credit_balance(str(current_user.id))

    return CreditBalanceResponse(
        balance=balance["balance"],
        free_credits_remaining=balance["free_credits_remaining"],
        free_credits_reset_at=balance["free_credits_reset_at"],
    )


@router.get("/credits/products", response_model=CreditProductListResponse)
async def get_credit_products(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CreditProductListResponse:
    """获取积分商品列表"""
    service = BillingService(db)
    products = await service.get_credit_products()

    return CreditProductListResponse(
        items=[
            CreditProductResponse(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                credits=p["credits"],
                bonus_credits=p["bonus_credits"],
                price=p["price"],
                currency=p["currency"],
                is_active=p["is_active"],
            )
            for p in products
        ]
    )


# ============================================================================
# IAP 验证
# ============================================================================


@router.post("/iap/apple/verify", response_model=IAPVerifyResponse)
async def verify_apple_iap(
    request: AppleIAPVerifyRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> IAPVerifyResponse:
    """
    Apple App Store 内购凭证验证

    服务端验证 Apple IAP 凭证并更新用户会员状态。
    """
    service = BillingService(db)
    result = await service.verify_apple_iap(
        user_id=str(current_user.id),
        transaction_id=request.transaction_id,
        original_transaction_id=request.original_transaction_id,
        signed_payload=request.signed_payload,
        product_id=request.product_id,
        environment=request.environment,
    )

    return IAPVerifyResponse(
        valid=result["valid"],
        product_id=result["product_id"],
        expires_at=result["expires_at"],
        is_trial_period=result["is_trial_period"],
        membership_updated=result["membership_updated"],
    )


@router.post("/iap/google/verify", response_model=IAPVerifyResponse)
async def verify_google_iap(
    request: GoogleIAPVerifyRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> IAPVerifyResponse:
    """
    Google Play 内购凭证验证

    服务端验证 Google Play IAP 凭证并更新用户会员状态。
    """
    service = BillingService(db)
    result = await service.verify_google_iap(
        user_id=str(current_user.id),
        purchase_token=request.purchase_token,
        product_id=request.product_id,
        package_name=request.package_name,
        is_subscription=request.is_subscription,
    )

    return IAPVerifyResponse(
        valid=result["valid"],
        product_id=result["product_id"],
        expires_at=result.get("expires_at"),
        membership_updated=result["membership_updated"],
    )
