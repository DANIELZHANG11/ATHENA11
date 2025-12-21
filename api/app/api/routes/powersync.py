"""
PowerSync 集成模块

提供 PowerSync Service 认证端点和同步规则。
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.config import settings


router = APIRouter(prefix="/powersync", tags=["PowerSync"])


# ============================================================================
# Pydantic 模型
# ============================================================================


class PowerSyncCredentials(BaseModel):
    """PowerSync 认证响应"""

    endpoint: str
    token: str
    expires_at: datetime


class PowerSyncTokenRequest(BaseModel):
    """PowerSync Token 请求 (可选)"""

    user_id: str | None = None


# ============================================================================
# PowerSync 令牌生成
# ============================================================================


def create_powersync_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """
    生成 PowerSync 专用 JWT Token

    PowerSync Service 使用与主 API 相同的 JWT_SECRET_KEY，
    但 Token 格式需符合 PowerSync 规范。

    Args:
        user_id: 用户 ID (UUID 字符串)
        expires_delta: 过期时间增量

    Returns:
        JWT Token 字符串
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    # PowerSync 标准 claims
    # https://docs.powersync.com/usage/self-hosting/backend-integration#jwt-authentication
    payload = {
        "sub": user_id,  # 用户 ID
        "iat": int(now.timestamp()),  # 签发时间
        "exp": int(expire.timestamp()),  # 过期时间
        # PowerSync 特定字段
        "user_id": user_id,  # 冗余，便于 sync rules 访问
    }

    return jwt.encode(
        payload,
        settings.auth.jwt_secret_key,
        algorithm=settings.auth.jwt_algorithm,
    )


# ============================================================================
# API 端点
# ============================================================================


@router.get("/credentials", response_model=PowerSyncCredentials)
async def get_powersync_credentials(
    current_user: CurrentUser,
) -> PowerSyncCredentials:
    """
    获取 PowerSync 连接凭证

    返回 PowerSync Service 的 WebSocket 端点和认证令牌。
    客户端使用这些信息初始化 PowerSync 连接。
    """
    # 生成 24 小时有效的 Token
    expires_delta = timedelta(hours=24)
    token = create_powersync_token(
        user_id=str(current_user.id),
        expires_delta=expires_delta,
    )

    expires_at = datetime.now(timezone.utc) + expires_delta
    return PowerSyncCredentials(
        endpoint=settings.powersync.powersync_url,
        token=token,
        expires_at=expires_at,
    )


@router.post("/token/refresh")
async def refresh_powersync_token(
    current_user: CurrentUser,
) -> PowerSyncCredentials:
    """
    刷新 PowerSync Token

    在当前 Token 即将过期时调用，获取新 Token。
    """
    expires_delta = timedelta(hours=24)
    token = create_powersync_token(
        user_id=str(current_user.id),
        expires_delta=expires_delta,
    )

    expires_at = datetime.now(timezone.utc) + expires_delta

    return PowerSyncCredentials(
        endpoint=settings.powersync.powersync_url,
        token=token,
        expires_at=expires_at,
    )


# ============================================================================
# PowerSync Backend Connector 端点 (供 PowerSync Service 调用)
# ============================================================================


@router.get("/auth")
async def powersync_auth_endpoint(request: Request) -> JSONResponse:
    """
    PowerSync Service 认证回调

    PowerSync Service 在建立连接时调用此端点验证 Token。
    此端点直接验证 JWT，不经过标准认证中间件。

    Response format:
    {
        "user_id": "uuid-string"
    }
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "Missing or invalid authorization header"},
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.auth.jwt_secret_key,
            algorithms=[settings.auth.jwt_algorithm],
        )
        user_id = payload.get("sub") or payload.get("user_id")

        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token: missing user_id"},
            )

        # 返回 PowerSync 期望的格式
        return JSONResponse(
            status_code=200,
            content={"user_id": user_id},
        )

    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"error": "Token expired"},
        )
    except jwt.InvalidTokenError as e:
        return JSONResponse(
            status_code=401,
            content={"error": f"Invalid token: {str(e)}"},
        )


# ============================================================================
# 同步规则配置
# ============================================================================


SYNC_RULES = """
# PowerSync Sync Rules for Athena
# 放置在 powersync/sync-rules.yaml

# 全局参数
parameters:
  user_id: token_parameters.user_id

# 同步的表定义
bucket_definitions:
  # 用户的书籍
  user_books:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, title, author, language, original_format, size,
               minio_key, cover_key, ocr_pdf_key, sha256, processing_status,
               reader_type, is_readable, is_interactive, has_text_layer,
               is_image_based, ocr_status, meta, created_at, updated_at,
               CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END AS is_deleted
        FROM books
        WHERE user_id = bucket.bucket_id

  # 阅读位置
  book_positions:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, book_id, chapter_or_page, scroll_position_json,
               updated_at
        FROM book_position
        WHERE user_id = bucket.bucket_id

  # 阅读时长记录
  reading_time_logs:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, book_id, started_at, ended_at, duration_sec, synced_at
        FROM reading_time_log
        WHERE user_id = bucket.bucket_id

  # 笔记
  user_notes:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, book_id, position_json, content, tags, color,
               conflict_of, created_at, updated_at,
               CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END AS is_deleted
        FROM notes
        WHERE user_id = bucket.bucket_id

  # 高亮
  user_highlights:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, book_id, position_json, color, text_preview,
               created_at, updated_at,
               CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END AS is_deleted
        FROM highlights
        WHERE user_id = bucket.bucket_id

  # 书签
  user_bookmarks:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, book_id, position_json, title, created_at,
               CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END AS is_deleted
        FROM bookmarks
        WHERE user_id = bucket.bucket_id

  # 书架
  user_shelves:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, name, color, icon, sort_order, created_at, updated_at,
               CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END AS is_deleted
        FROM shelves
        WHERE user_id = bucket.bucket_id

  # 书架-书籍关联
  shelf_book_relations:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT sb.id, sb.shelf_id, sb.book_id, sb.added_at
        FROM shelf_books sb
        JOIN shelves s ON sb.shelf_id = s.id
        WHERE s.user_id = bucket.bucket_id

  # 用户设置
  user_settings_bucket:
    parameters:
      - SELECT id AS bucket_id FROM users WHERE id = token_parameters.user_id
    data:
      - SELECT id, settings_json, updated_at
        FROM user_settings
        WHERE user_id = bucket.bucket_id
"""


@router.get("/sync-rules")
async def get_sync_rules() -> dict:
    """
    获取 PowerSync 同步规则

    仅用于开发调试，生产环境应直接配置 PowerSync Service。
    """
    return {
        "info": "This endpoint is for development reference only",
        "rules": SYNC_RULES,
    }
