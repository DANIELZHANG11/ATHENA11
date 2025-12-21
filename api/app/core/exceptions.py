"""
统一异常处理

定义自定义异常类和全局异常处理器。
错误码参考: 12 - 错误码中心化参考
"""

from typing import Any

from fastapi import HTTPException, status


class AthenaException(HTTPException):
    """雅典娜基础异常"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# =============================================================================
# 认证相关异常 (auth_*)
# =============================================================================


class UnauthorizedException(AthenaException):
    """未认证"""

    def __init__(self, detail: str = "unauthorized") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenExpiredException(AthenaException):
    """令牌过期"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")


class TokenInvalidException(AthenaException):
    """令牌无效"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_invalid")


class AuthCodeInvalidException(AthenaException):
    """验证码无效或过期"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="auth_code_invalid")


class AuthCodeRateLimitedException(AthenaException):
    """验证码发送过于频繁"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="auth_code_rate_limited")


class EmailAlreadyRegisteredException(AthenaException):
    """邮箱已注册"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="email_already_registered")


class PasswordTooWeakException(AthenaException):
    """密码强度不足"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="password_too_weak")


# =============================================================================
# 权限相关异常 (permission_*)
# =============================================================================


class ForbiddenException(AthenaException):
    """权限不足"""

    def __init__(self, detail: str = "forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ReadOnlyModeException(AthenaException):
    """只读模式"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="readonly_mode")


class AdminRequiredException(AthenaException):
    """需要管理员权限"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")


# =============================================================================
# 资源相关异常 (resource_*)
# =============================================================================


class NotFoundException(AthenaException):
    """资源不存在"""

    def __init__(self, detail: str = "not_found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BookNotFoundException(AthenaException):
    """书籍不存在"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="book_not_found")


class FileNotFoundException(AthenaException):
    """文件不存在"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="file_not_found")


# =============================================================================
# 配额相关异常 (quota_*)
# =============================================================================


class QuotaExceededException(AthenaException):
    """配额超限"""

    def __init__(self, detail: str = "quota_exceeded") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UploadForbiddenQuotaExceededException(AthenaException):
    """上传被禁止：配额超限"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="upload_forbidden_quota_exceeded",
        )


class BookLimitReachedException(AthenaException):
    """书籍数量上限"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="book_limit_reached")


# =============================================================================
# 付费相关异常 (payment_*)
# =============================================================================


class InsufficientCreditsException(AthenaException):
    """积分不足"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="insufficient_credits")


class PaymentFailedException(AthenaException):
    """支付失败"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="payment_failed")


class SubscriptionExpiredException(AthenaException):
    """订阅过期"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="subscription_expired")


# =============================================================================
# OCR 相关异常 (ocr_*)
# =============================================================================


class OcrQuotaExceededException(AthenaException):
    """OCR 配额不足"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="ocr_quota_exceeded")


class OcrMaxPagesExceededException(AthenaException):
    """OCR 页数超限"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="ocr_max_pages_exceeded")


class OcrInProgressException(AthenaException):
    """OCR 正在处理中"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="ocr_in_progress")


class AlreadyDigitalizedException(AthenaException):
    """书籍已是文字型"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="already_digitalized")


# =============================================================================
# 乐观锁相关异常 (version_*)
# =============================================================================


class MissingIfMatchException(AthenaException):
    """缺少 If-Match 头"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="missing_if_match")


class InvalidIfMatchException(AthenaException):
    """If-Match 格式错误"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_if_match")


class VersionConflictException(AthenaException):
    """版本冲突"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="version_conflict")


# =============================================================================
# 通用异常
# =============================================================================


class RateLimitedException(AthenaException):
    """请求频率过高"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")


class InternalErrorException(AthenaException):
    """服务器内部错误"""

    def __init__(self, detail: str = "internal_error") -> None:
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class MissingFilenameException(AthenaException):
    """缺少文件名"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_filename")


class MissingKeyException(AthenaException):
    """缺少 S3 Object Key"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_key")


class CanonicalNotFoundException(AthenaException):
    """秒传时原书不存在"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="canonical_not_found")


class DeviceIdRequiredException(AthenaException):
    """缺少设备 ID"""

    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="device_id_required")
