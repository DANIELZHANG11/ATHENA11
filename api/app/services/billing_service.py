"""
付费订阅服务层

处理订阅、支付、积分等业务逻辑。
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InsufficientCreditsException,
    NotFoundException,
    PaymentFailedException,
)
from app.models.billing import (
    CreditAccount,
    CreditLedger,
    CreditProduct,
    PaymentSession,
)
from app.models.user import User


class BillingService:
    """付费订阅服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # 订阅方案
    # ========================================================================

    async def get_plans(self) -> list[dict[str, Any]]:
        """获取所有可用订阅方案

        注：当前使用硬编码方案，后续可迁移到数据库表
        """
        # 硬编码订阅方案（实际生产中应从数据库或配置中读取）
        plans = [
            {
                "id": "free",
                "name": "免费版",
                "description": "基础阅读功能",
                "price": Decimal("0"),
                "currency": "CNY",
                "period": "monthly",
                "features": ["无限图书存储", "基础阅读功能", "每月 100 AI 对话额度"],
                "stripe_price_id": None,
                "is_active": True,
            },
            {
                "id": "pro_monthly",
                "name": "专业版 (月付)",
                "description": "解锁全部功能",
                "price": Decimal("29.9"),
                "currency": "CNY",
                "period": "monthly",
                "features": [
                    "无限图书存储",
                    "无限 AI 对话",
                    "OCR 识别 50 页/月",
                    "多端同步",
                    "优先支持",
                ],
                "stripe_price_id": "price_pro_monthly",
                "is_active": True,
            },
            {
                "id": "pro_yearly",
                "name": "专业版 (年付)",
                "description": "解锁全部功能，年付更优惠",
                "price": Decimal("299"),
                "currency": "CNY",
                "period": "yearly",
                "features": [
                    "无限图书存储",
                    "无限 AI 对话",
                    "OCR 识别 100 页/月",
                    "多端同步",
                    "优先支持",
                    "年付优惠 2 个月",
                ],
                "stripe_price_id": "price_pro_yearly",
                "is_active": True,
            },
        ]

        return plans

    # ========================================================================
    # 支付会话
    # ========================================================================

    async def create_checkout_session(
        self,
        user_id: str,
        product_type: str,
        product_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """
        创建支付会话

        目前支持 Stripe，后续可扩展 WeChat Pay / Alipay。
        """
        # 1. 验证商品
        if product_type == "subscription":
            result = await self.db.execute(
                select(PricingRule).where(
                    PricingRule.id == UUID(product_id),
                    PricingRule.is_active.is_(True),
                )
            )
            product = result.scalar_one_or_none()
            if not product:
                raise NotFoundException("plan_not_found")
            amount = product.unit_price
            stripe_price_id = product.stripe_price_id

        elif product_type == "credits":
            result = await self.db.execute(
                select(CreditProduct).where(
                    CreditProduct.id == UUID(product_id),
                    CreditProduct.is_active.is_(True),
                )
            )
            product = result.scalar_one_or_none()
            if not product:
                raise NotFoundException("product_not_found")
            amount = Decimal(str(product.price))
            stripe_price_id = product.stripe_price_id

        else:
            raise PaymentFailedException("invalid_product_type")

        # 2. 创建 Stripe Checkout Session (模拟)
        # TODO: 实际集成 Stripe SDK
        import secrets
        session_id = f"cs_{secrets.token_hex(16)}"
        checkout_url = f"https://checkout.stripe.com/pay/{session_id}"
        expires_at = datetime.now(UTC).replace(hour=23, minute=59, second=59)

        # 3. 保存支付会话记录
        payment_session = PaymentSession(
            user_id=UUID(user_id),
            gateway="stripe",
            gateway_session_id=session_id,
            product_type=product_type,
            product_id=UUID(product_id),
            amount=amount,
            currency="CNY",
            status="pending",
            meta={
                "success_url": success_url,
                "cancel_url": cancel_url,
                "stripe_price_id": stripe_price_id,
            },
        )
        self.db.add(payment_session)
        await self.db.commit()

        return {
            "session_id": session_id,
            "checkout_url": checkout_url,
            "expires_at": expires_at,
        }

    async def get_payment_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Any], int]:
        """获取支付历史"""
        offset = (page - 1) * page_size

        # 查询总数
        from sqlalchemy import func
        count_result = await self.db.execute(
            select(func.count()).select_from(PaymentSession).where(
                PaymentSession.user_id == UUID(user_id),
            )
        )
        total = count_result.scalar() or 0

        # 查询列表
        result = await self.db.execute(
            select(PaymentSession)
            .where(PaymentSession.user_id == UUID(user_id))
            .order_by(PaymentSession.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        sessions = result.scalars().all()

        return sessions, total

    # ========================================================================
    # 订阅状态
    # ========================================================================

    async def get_subscription_status(self, user_id: str) -> dict[str, Any]:
        """获取用户订阅状态"""
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("user_not_found")

        now = datetime.now(UTC)
        is_active = (
            user.membership_tier != "FREE" and
            user.membership_expire_at is not None and
            user.membership_expire_at > now
        )

        return {
            "is_active": is_active,
            "tier": user.membership_tier,
            "expires_at": user.membership_expire_at,
            "auto_renew": False,  # TODO: 从订阅记录读取
            "cancel_at_period_end": False,
            "payment_method": None,
        }

    # ========================================================================
    # 积分
    # ========================================================================

    async def get_credit_balance(self, user_id: str) -> dict[str, Any]:
        """获取积分余额"""
        result = await self.db.execute(
            select(CreditAccount).where(CreditAccount.user_id == UUID(user_id))
        )
        account = result.scalar_one_or_none()

        if not account:
            # 自动创建账户
            account = CreditAccount(user_id=UUID(user_id), balance=0)
            self.db.add(account)
            await self.db.commit()

        return {
            "balance": account.balance,
            "free_credits_remaining": account.free_credits_monthly,
            "free_credits_reset_at": account.free_credits_reset_at,
        }

    async def get_credit_products(self) -> list[dict[str, Any]]:
        """获取积分商品列表"""
        result = await self.db.execute(
            select(CreditProduct).where(
                CreditProduct.is_active.is_(True),
            ).order_by(CreditProduct.sort_order)
        )
        products = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "credits": p.credits,
                "bonus_credits": p.bonus_credits,
                "price": p.price,
                "currency": p.currency,
                "is_active": p.is_active,
            }
            for p in products
        ]

    async def deduct_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> int:
        """
        扣减积分

        Args:
            user_id: 用户 ID
            amount: 扣减数量 (正数)
            transaction_type: 交易类型
            description: 描述
            reference_type: 关联类型
            reference_id: 关联 ID

        Returns:
            扣减后的余额

        Raises:
            InsufficientCreditsException: 余额不足
        """
        result = await self.db.execute(
            select(CreditAccount).where(CreditAccount.user_id == UUID(user_id))
        )
        account = result.scalar_one_or_none()

        if not account or account.balance < amount:
            raise InsufficientCreditsException("insufficient_credits")

        # 扣减余额
        account.balance -= amount
        balance_after = account.balance

        # 记录流水
        ledger = CreditLedger(
            user_id=UUID(user_id),
            amount=-amount,
            balance_after=balance_after,
            transaction_type=transaction_type,
            description=description,
            reference_type=reference_type,
            reference_id=UUID(reference_id) if reference_id else None,
        )
        self.db.add(ledger)
        await self.db.commit()

        return balance_after

    async def add_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> int:
        """
        增加积分

        Returns:
            增加后的余额
        """
        result = await self.db.execute(
            select(CreditAccount).where(CreditAccount.user_id == UUID(user_id))
        )
        account = result.scalar_one_or_none()

        if not account:
            account = CreditAccount(user_id=UUID(user_id), balance=0)
            self.db.add(account)

        # 增加余额
        account.balance += amount
        balance_after = account.balance

        # 记录流水
        ledger = CreditLedger(
            user_id=UUID(user_id),
            amount=amount,
            balance_after=balance_after,
            transaction_type=transaction_type,
            description=description,
            reference_type=reference_type,
            reference_id=UUID(reference_id) if reference_id else None,
        )
        self.db.add(ledger)
        await self.db.commit()

        return balance_after

    # ========================================================================
    # IAP 验证 (iOS/Android)
    # ========================================================================

    async def verify_apple_iap(
        self,
        user_id: str,
        transaction_id: str,
        original_transaction_id: str,
        signed_payload: str,
        product_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """
        验证 Apple App Store 内购凭证

        TODO: 实际实现需要:
        1. 解析 JWS signed_payload
        2. 验证证书链
        3. 调用 App Store Server API
        4. 更新用户会员状态
        """
        # 模拟验证成功
        from datetime import timedelta
        expires_at = datetime.now(UTC) + timedelta(days=30)

        # 更新用户会员状态
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            user.membership_tier = "PRO"
            user.membership_expire_at = expires_at
            await self.db.commit()

        return {
            "valid": True,
            "product_id": product_id,
            "expires_at": expires_at,
            "is_trial_period": False,
            "membership_updated": True,
        }

    async def verify_google_iap(
        self,
        user_id: str,
        purchase_token: str,
        product_id: str,
        package_name: str,
        is_subscription: bool,
    ) -> dict[str, Any]:
        """
        验证 Google Play 内购凭证

        TODO: 实际实现需要:
        1. 使用 Google Play Developer API
        2. 验证购买状态
        3. 确认购买
        4. 更新用户会员状态
        """
        # 模拟验证成功
        from datetime import timedelta
        expires_at = datetime.now(UTC) + timedelta(days=30) if is_subscription else None

        # 更新用户会员状态
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            user.membership_tier = "PRO"
            user.membership_expire_at = expires_at
            await self.db.commit()

        return {
            "valid": True,
            "product_id": product_id,
            "expires_at": expires_at,
            "auto_renewing": is_subscription,
            "membership_updated": True,
        }
