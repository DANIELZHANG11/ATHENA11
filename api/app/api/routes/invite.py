"""
邀请裂变 API 路由

处理邀请码、邀请统计、被邀请人列表等功能。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.api.schemas.invite import (
    InviteCodeResponse,
    InviteeItem,
    InviteeListResponse,
    InviteRewardRule,
    InviteRulesResponse,
    InviteStatsResponse,
)
from app.services.invite_service import InviteService

router = APIRouter(prefix="/invite", tags=["邀请裂变"])


@router.get("/code", response_model=InviteCodeResponse)
async def get_invite_code(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InviteCodeResponse:
    """获取或创建邀请码"""
    service = InviteService(db)
    result = await service.get_or_create_invite_code(str(current_user.id))

    return InviteCodeResponse(
        code=result["code"],
        share_url=result["share_url"],
        total_invited=result["total_invited"],
        total_rewarded=result["total_rewarded"],
    )


@router.get("/stats", response_model=InviteStatsResponse)
async def get_invite_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InviteStatsResponse:
    """获取邀请统计"""
    service = InviteService(db)
    stats = await service.get_invite_stats(str(current_user.id))

    return InviteStatsResponse(
        total_invited=stats["total_invited"],
        pending_count=stats["pending_count"],
        active_count=stats["active_count"],
        total_rewards_earned=stats["total_rewards_earned"],
        current_tier=stats["current_tier"],
        next_tier_threshold=stats["next_tier_threshold"],
    )


@router.get("/invitees", response_model=InviteeListResponse)
async def list_invitees(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> InviteeListResponse:
    """获取被邀请人列表"""
    service = InviteService(db)
    invitees, total = await service.get_invitees(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
    )

    return InviteeListResponse(
        items=[
            InviteeItem(
                id=i["id"],
                email_masked=i["email_masked"],
                status=i["status"],
                reward_earned=i["reward_earned"],
                invited_at=i["invited_at"],
                activated_at=i["activated_at"],
            )
            for i in invitees
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


@router.get("/rules", response_model=InviteRulesResponse)
async def get_invite_rules(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InviteRulesResponse:
    """获取邀请奖励规则"""
    service = InviteService(db)
    rules = service.get_reward_rules()

    return InviteRulesResponse(
        tiers=[
            InviteRewardRule(
                tier=t["tier"],
                min_invites=t["min_invites"],
                reward_per_invite=t["reward_per_invite"],
                bonus_credits=t["bonus_credits"],
            )
            for t in rules["tiers"]
        ],
        invitee_reward=rules["invitee_reward"],
        terms_url=rules["terms_url"],
    )
