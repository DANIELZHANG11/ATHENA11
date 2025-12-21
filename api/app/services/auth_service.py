"""
认证服务

处理用户认证、验证码、Token 管理等业务逻辑。
"""

import secrets
from datetime import UTC, datetime

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthCodeInvalidException,
    AuthCodeRateLimitedException,
    TokenInvalidException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_auth_code,
    verify_token,
)
from app.models.user import User, UserSession, UserStats


class AuthService:
    """认证服务"""

    # Redis Key 前缀
    CODE_PREFIX = "auth:code:"
    CODE_ATTEMPTS_PREFIX = "auth:attempts:"
    CODE_RATE_LIMIT_PREFIX = "auth:rate:"

    def __init__(self, db: AsyncSession, redis_client: redis.Redis | None = None):
        self.db = db
        self.redis = redis_client

    async def send_email_code(self, email: str) -> tuple[str, int]:
        """
        发送邮箱验证码

        Args:
            email: 邮箱地址

        Returns:
            (code, expires_in) - 验证码和有效期(秒)

        Raises:
            AuthCodeRateLimitedException: 发送过于频繁
        """
        email = email.lower().strip()
        expires_in = settings.auth.auth_code_expire_minutes * 60

        if self.redis:
            # 检查发送频率限制 (每分钟最多1次)
            rate_key = f"{self.CODE_RATE_LIMIT_PREFIX}{email}"
            if await self.redis.exists(rate_key):
                raise AuthCodeRateLimitedException()

            # 生成验证码
            code = generate_auth_code()

            # 存储验证码
            code_key = f"{self.CODE_PREFIX}{email}"
            await self.redis.setex(code_key, expires_in, code)

            # 设置发送频率限制 (60秒)
            await self.redis.setex(rate_key, 60, "1")

            # 重置尝试次数
            attempts_key = f"{self.CODE_ATTEMPTS_PREFIX}{email}"
            await self.redis.delete(attempts_key)

            # TODO: 实际发送邮件
            # await send_email(email, "验证码", f"您的验证码是: {code}")

            return code, expires_in
        else:
            # 开发模式：不使用 Redis
            code = generate_auth_code()
            return code, expires_in

    async def verify_email_code(
        self,
        email: str,
        code: str,
        device_id: str | None = None,
        device_name: str | None = None,
        ip_address: str | None = None,
        invite_code: str | None = None,
    ) -> tuple[User, str, str]:
        """
        验证邮箱验证码并登录/注册

        Args:
            email: 邮箱地址
            code: 验证码
            device_id: 设备ID
            device_name: 设备名称
            ip_address: IP地址
            invite_code: 邀请码

        Returns:
            (user, access_token, refresh_token)

        Raises:
            AuthCodeInvalidException: 验证码无效或过期
        """
        email = email.lower().strip()

        if self.redis:
            # 检查尝试次数
            attempts_key = f"{self.CODE_ATTEMPTS_PREFIX}{email}"
            attempts = await self.redis.incr(attempts_key)
            await self.redis.expire(attempts_key, 300)  # 5分钟过期

            if attempts > settings.auth.auth_code_max_attempts:
                raise AuthCodeInvalidException()

            # 验证验证码
            code_key = f"{self.CODE_PREFIX}{email}"
            stored_code = await self.redis.get(code_key)

            if not stored_code or stored_code.decode() != code:
                raise AuthCodeInvalidException()

            # 验证成功，删除验证码
            await self.redis.delete(code_key)
            await self.redis.delete(attempts_key)
        else:
            # 开发模式：接受任何 6 位数字验证码
            if len(code) != 6 or not code.isdigit():
                raise AuthCodeInvalidException()

        # 查找或创建用户
        user = await self._get_or_create_user(email, invite_code)

        # 创建会话
        await self._create_session(
            user=user,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
        )

        # 生成令牌
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            (new_access_token, new_refresh_token)

        Raises:
            TokenInvalidException: Token 无效或过期
        """
        payload = verify_token(refresh_token, token_type="refresh")
        if payload is None:
            raise TokenInvalidException()

        # 验证用户存在且活跃
        result = await self.db.execute(
            select(User).where(User.id == payload.sub, User.is_active)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise TokenInvalidException()

        # 生成新令牌
        new_access_token = create_access_token(str(user.id))
        new_refresh_token = create_refresh_token(str(user.id))

        return new_access_token, new_refresh_token

    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """
        撤销会话

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            是否成功撤销
        """
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                not UserSession.revoked,
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.revoked = True
            await self.db.commit()
            return True
        return False

    async def _get_or_create_user(
        self,
        email: str,
        invite_code: str | None = None,
    ) -> User:
        """获取或创建用户"""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            return user

        # 创建新用户
        user = User(
            email=email,
            display_name=email.split("@")[0],
            invite_code=self._generate_invite_code(),
        )
        self.db.add(user)
        await self.db.flush()

        # 创建用户统计
        stats = UserStats(user_id=user.id)
        self.db.add(stats)

        # 处理邀请码
        if invite_code:
            await self._process_invite(user, invite_code)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def _create_session(
        self,
        user: User,
        device_id: str | None = None,
        device_name: str | None = None,
        device_type: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        """创建用户会话"""
        session = UserSession(
            user_id=user.id,
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            last_active_at=datetime.now(UTC),
        )
        self.db.add(session)
        await self.db.commit()
        return session

    async def _process_invite(self, invitee: User, invite_code: str) -> None:
        """处理邀请码"""
        from app.models.user import Invite

        # 查找邀请人
        result = await self.db.execute(
            select(User).where(User.invite_code == invite_code)
        )
        inviter = result.scalar_one_or_none()

        if inviter and inviter.id != invitee.id:
            # 创建邀请记录
            invite = Invite(
                inviter_id=inviter.id,
                invitee_id=invitee.id,
                code_used=invite_code,
                status="completed",
                completed_at=datetime.now(UTC),
            )
            self.db.add(invite)

            # 更新邀请人统计
            result = await self.db.execute(
                select(UserStats).where(UserStats.user_id == inviter.id)
            )
            inviter_stats = result.scalar_one_or_none()
            if inviter_stats:
                inviter_stats.invite_count += 1
                # TODO: 发放邀请奖励

    def _generate_invite_code(self) -> str:
        """生成邀请码"""
        # 生成 8 位大写字母数字组合
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 排除易混淆字符
        return "".join(secrets.choice(alphabet) for _ in range(8))
