"""
统一异常处理

定义自定义异常类和全局异常处理器。
错误码参考: 12 - 错误码中心化参考
"""

from enum import Enum

from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """错误码枚举"""

    # 认证相关
    UNAUTHORIZED = "unauthorized"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    AUTH_CODE_INVALID = "auth_code_invalid"
    AUTH_CODE_RATE_LIMITED = "auth_code_rate_limited"

    # 资源相关
    NOT_FOUND = "not_found"
    BOOK_NOT_FOUND = "book_not_found"
    FILE_NOT_FOUND = "file_not_found"

    # 权限相关
    FORBIDDEN = "forbidden"
    READONLY_MODE = "readonly_mode"

    # 配额相关
    QUOTA_EXCEEDED = "quota_exceeded"
    BOOK_LIMIT_REACHED = "book_limit_reached"

    # 付费相关
    INSUFFICIENT_CREDITS = "insufficient_credits"
    PAYMENT_FAILED = "payment_failed"

    # 外部服务
    EXTERNAL_SERVICE_ERROR = "external_service_error"

    # 通用
    INTERNAL_ERROR = "internal_error"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"


# 错误码到 HTTP 状态码的映射
ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_CODE_INVALID: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_CODE_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.BOOK_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.FILE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.READONLY_MODE: status.HTTP_403_FORBIDDEN,
    ErrorCode.QUOTA_EXCEEDED: status.HTTP_403_FORBIDDEN,
    ErrorCode.BOOK_LIMIT_REACHED: status.HTTP_403_FORBIDDEN,
    ErrorCode.INSUFFICIENT_CREDITS: status.HTTP_402_PAYMENT_REQUIRED,
    ErrorCode.PAYMENT_FAILED: status.HTTP_402_PAYMENT_REQUIRED,
    ErrorCode.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
}


class AthenaException(HTTPException):
    """雅典娜基础异常

    支持两种调用方式:
    1. AthenaException(status_code=400, detail="error")
    2. AthenaException(code=ErrorCode.NOT_FOUND, message="custom message")
    """

    def __init__(
        self,
        status_code: int | None = None,
        detail: str | None = None,
        code: ErrorCode | None = None,
        message: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        # 支持新的 code/message 风格
        if code is not None:
            status_code = ERROR_STATUS_MAP.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            detail = message or code.value

        if status_code is None:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if detail is None:
            detail = "internal_error"

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
