"""
邀请裂变服务层

处理邀请码生成、邀请关系管理、奖励发放等业务逻辑。
"""

import secrets
import string
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AthenaException, ErrorCode, NotFoundException
from app.models.user import Invite, User
from app.services.billing_service import BillingService


class InviteService:
    """邀请裂变服务"""

    # 邀请奖励等级
    REWARD_TIERS = [
        {"tier": "新手", "min_invites": 0, "reward_per_invite": 100, "bonus_credits": 0},
        {"tier": "达人", "min_invites": 5, "reward_per_invite": 150, "bonus_credits": 200},
        {"tier": "精英", "min_invites": 20, "reward_per_invite": 200, "bonus_credits": 500},
        {"tier": "大师", "min_invites": 50, "reward_per_invite": 300, "bonus_credits": 1500},
    ]

    # 被邀请人奖励
    INVITEE_REWARD = 50

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # 邀请码管理
    # ========================================================================

    async def get_or_create_invite_code(self, user_id: str) -> dict[str, Any]:
        """获取或创建用户邀请码"""
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("user_not_found")

        # 如果没有邀请码，生成一个
        if not user.invite_code:
            user.invite_code = self._generate_invite_code()
            await self.db.commit()

        # 统计邀请数据
        stats = await self._get_invite_stats(user_id)

        share_url = f"{settings.app.frontend_url}/invite/{user.invite_code}"

        return {
            "code": user.invite_code,
            "share_url": share_url,
            "total_invited": stats["total_invited"],
            "total_rewarded": stats["active_count"],
        }

    def _generate_invite_code(self, length: int = 8) -> str:
        """生成随机邀请码"""
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    # ========================================================================
    # 邀请统计
    # ========================================================================

    async def get_invite_stats(self, user_id: str) -> dict[str, Any]:
        """获取邀请统计"""
        stats = await self._get_invite_stats(user_id)

        # 计算当前等级和下一等级
        current_tier = self.REWARD_TIERS[0]
        next_tier_threshold = None

        for i, tier in enumerate(self.REWARD_TIERS):
            if stats["active_count"] >= tier["min_invites"]:
                current_tier = tier
                if i + 1 < len(self.REWARD_TIERS):
                    next_tier_threshold = self.REWARD_TIERS[i + 1]["min_invites"]

        return {
            "total_invited": stats["total_invited"],
            "pending_count": stats["pending_count"],
            "active_count": stats["active_count"],
            "total_rewards_earned": stats["total_rewards_earned"],
            "current_tier": current_tier["tier"],
            "next_tier_threshold": next_tier_threshold,
        }

    async def _get_invite_stats(self, user_id: str) -> dict[str, int]:
        """获取邀请统计数据"""
        # 总邀请数
        total_result = await self.db.execute(
            select(func.count()).select_from(Invite).where(
                Invite.inviter_id == UUID(user_id)
            )
        )
        total_invited = total_result.scalar() or 0

        # 已激活数
        active_result = await self.db.execute(
            select(func.count()).select_from(Invite).where(
                Invite.inviter_id == UUID(user_id),
                Invite.status == "active",
            )
        )
        active_count = active_result.scalar() or 0

        # 待激活数
        pending_count = total_invited - active_count

        # 总奖励
        reward_result = await self.db.execute(
            select(func.coalesce(func.sum(Invite.inviter_reward), 0)).where(
                Invite.inviter_id == UUID(user_id)
            )
        )
        total_rewards_earned = reward_result.scalar() or 0

        return {
            "total_invited": total_invited,
            "pending_count": pending_count,
            "active_count": active_count,
            "total_rewards_earned": total_rewards_earned,
        }

    # ========================================================================
    # 被邀请人列表
    # ========================================================================

    async def get_invitees(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """获取被邀请人列表"""
        offset = (page - 1) * page_size

        # 查询总数
        count_result = await self.db.execute(
            select(func.count()).select_from(Invite).where(
                Invite.inviter_id == UUID(user_id)
            )
        )
        total = count_result.scalar() or 0

        # 查询列表
        result = await self.db.execute(
            select(Invite, User)
            .join(User, Invite.invitee_id == User.id)
            .where(Invite.inviter_id == UUID(user_id))
            .order_by(Invite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.all()

        invitees = []
        for invite, invitee_user in rows:
            # 脱敏邮箱
            email = invitee_user.email
            at_pos = email.find("@")
            if at_pos > 2:
                masked_email = email[:2] + "***" + email[at_pos:]
            else:
                masked_email = "***" + email[at_pos:]

            invitees.append({
                "id": str(invite.id),
                "email_masked": masked_email,
                "status": invite.status,
                "reward_earned": invite.inviter_reward or 0,
                "invited_at": invite.created_at,
                "activated_at": invite.activated_at,
            })

        return invitees, total

    # ========================================================================
    # 邀请处理
    # ========================================================================

    async def process_invite(
        self,
        invitee_id: str,
        invite_code: str,
    ) -> None:
        """
        处理邀请关系

        在用户注册时调用，建立邀请关系。
        """
        # 查找邀请人
        result = await self.db.execute(
            select(User).where(User.invite_code == invite_code)
        )
        inviter = result.scalar_one_or_none()

        if not inviter:
            raise AthenaException(code=ErrorCode.VALIDATION_ERROR, message="invalid_invite_code")

        # 不能邀请自己
        if str(inviter.id) == invitee_id:
            return

        # 检查是否已有邀请关系
        existing = await self.db.execute(
            select(Invite).where(Invite.invitee_id == UUID(invitee_id))
        )
        if existing.scalar_one_or_none():
            return  # 已有邀请关系，忽略

        # 创建邀请记录
        invite = Invite(
            inviter_id=inviter.id,
            invitee_id=UUID(invitee_id),
            invite_code=invite_code,
            status="pending",
        )
        self.db.add(invite)
        await self.db.commit()

    async def activate_invite(self, invitee_id: str) -> None:
        """
        激活邀请

        当被邀请人完成首次充值或达到激活条件时调用。
        发放双方奖励。
        """
        result = await self.db.execute(
            select(Invite).where(
                Invite.invitee_id == UUID(invitee_id),
                Invite.status == "pending",
            )
        )
        invite = result.scalar_one_or_none()

        if not invite:
            return  # 没有待激活的邀请

        # 计算邀请人当前等级
        stats = await self._get_invite_stats(str(invite.inviter_id))
        reward_per_invite = self.REWARD_TIERS[0]["reward_per_invite"]

        for tier in self.REWARD_TIERS:
            if stats["active_count"] >= tier["min_invites"]:
                reward_per_invite = tier["reward_per_invite"]

        # 更新邀请状态
        invite.status = "active"
        invite.activated_at = datetime.now(UTC)
        invite.inviter_reward = reward_per_invite
        invite.invitee_reward = self.INVITEE_REWARD

        # 发放邀请人奖励
        billing_service = BillingService(self.db)
        await billing_service.add_credits(
            user_id=str(invite.inviter_id),
            amount=reward_per_invite,
            transaction_type="invite_reward",
            description=f"邀请奖励：邀请新用户",
            reference_type="invite",
            reference_id=str(invite.id),
        )

        # 发放被邀请人奖励
        await billing_service.add_credits(
            user_id=invitee_id,
            amount=self.INVITEE_REWARD,
            transaction_type="invite_reward",
            description="新用户邀请奖励",
            reference_type="invite",
            reference_id=str(invite.id),
        )

        await self.db.commit()

    # ========================================================================
    # 奖励规则
    # ========================================================================

    def get_reward_rules(self) -> dict[str, Any]:
        """获取邀请奖励规则"""
        return {
            "tiers": self.REWARD_TIERS,
            "invitee_reward": self.INVITEE_REWARD,
            "terms_url": f"{settings.app.frontend_url}/terms/invite",
        }
