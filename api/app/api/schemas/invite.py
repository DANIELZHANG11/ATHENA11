"""
邀请裂变相关 Pydantic 模型
"""

from datetime import datetime

from pydantic import BaseModel, Field


class InviteCodeResponse(BaseModel):
    """邀请码信息"""

    code: str = Field(description="邀请码")
    share_url: str = Field(description="分享链接")
    total_invited: int = Field(description="已邀请人数")
    total_rewarded: int = Field(description="已获得奖励人数")


class InviteStatsResponse(BaseModel):
    """邀请统计"""

    total_invited: int = Field(description="总邀请人数")
    pending_count: int = Field(description="待激活数量")
    active_count: int = Field(description="已激活数量")
    total_rewards_earned: int = Field(description="累计获得奖励 (Credits)")
    current_tier: str = Field(description="当前等级")
    next_tier_threshold: int | None = Field(description="下一等级门槛")


class InviteeItem(BaseModel):
    """被邀请人信息"""

    id: str
    email_masked: str = Field(description="脱敏邮箱")
    status: str = Field(description="状态: pending/active")
    reward_earned: int = Field(description="获得的奖励")
    invited_at: datetime
    activated_at: datetime | None = None


class InviteeListResponse(BaseModel):
    """被邀请人列表"""

    items: list[InviteeItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class InviteRewardRule(BaseModel):
    """邀请奖励规则"""

    tier: str = Field(description="等级名称")
    min_invites: int = Field(description="最少邀请数")
    reward_per_invite: int = Field(description="每邀请奖励 (Credits)")
    bonus_credits: int = Field(description="达到等级额外奖励")


class InviteRulesResponse(BaseModel):
    """邀请规则"""

    tiers: list[InviteRewardRule]
    invitee_reward: int = Field(description="被邀请人奖励 (Credits)")
    terms_url: str = Field(description="活动条款链接")
