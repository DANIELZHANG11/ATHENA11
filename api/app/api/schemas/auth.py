"""
认证相关 API Schema

Pydantic 模型定义请求和响应结构。
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# =============================================================================
# 请求模型
# =============================================================================


class EmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""

    email: EmailStr = Field(..., description="邮箱地址")


class EmailVerifyRequest(BaseModel):
    """邮箱验证码验证请求"""

    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")
    device_id: str | None = Field(None, max_length=64, description="设备ID")
    device_name: str | None = Field(None, max_length=100, description="设备名称")
    invite_code: str | None = Field(None, max_length=20, description="邀请码")


class TokenRefreshRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., description="刷新令牌")


class PasswordLoginRequest(BaseModel):
    """密码登录请求 (预留)"""

    email: EmailStr
    password: str = Field(..., min_length=8)


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调请求"""

    code: str = Field(..., description="OAuth 授权码")
    state: str = Field(..., description="OAuth 状态参数")
    redirect_uri: str = Field(..., description="重定向 URI")


# =============================================================================
# 响应模型
# =============================================================================


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class UserResponse(BaseModel):
    """用户信息响应"""

    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="邮箱")
    display_name: str | None = Field(None, description="显示名称")
    avatar_url: str | None = Field(None, description="头像URL")
    membership_tier: str = Field(..., description="会员等级")
    membership_expire_at: datetime | None = Field(None, description="会员过期时间")
    language: str = Field(..., description="语言")
    timezone: str = Field(..., description="时区")
    invite_code: str | None = Field(None, description="邀请码")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """认证响应 (包含令牌和用户信息)"""

    tokens: TokenResponse
    user: UserResponse


class CodeSentResponse(BaseModel):
    """验证码发送成功响应"""

    message: str = Field(default="code_sent", description="消息")
    expires_in: int = Field(..., description="验证码有效期(秒)")


class SessionResponse(BaseModel):
    """会话信息响应"""

    id: str
    device_id: str | None
    device_name: str | None
    device_type: str | None
    ip_address: str | None
    created_at: datetime
    last_active_at: datetime | None
    is_current: bool = Field(default=False, description="是否为当前会话")

    model_config = {"from_attributes": True}


class OAuthProviderInfo(BaseModel):
    """OAuth 提供商信息"""

    provider: str
    provider_email: str | None
    linked_at: datetime

    model_config = {"from_attributes": True}
