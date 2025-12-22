"""
雅典娜 API 应用配置

使用 Pydantic Settings 管理所有环境变量配置。
配置按模块分组，支持 .env 文件和环境变量覆盖。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """应用基础配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用信息
    app_name: str = "Athena"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    # 独立控制 API 文档是否可访问（方便开发调试）
    enable_docs: bool = True

    # API 服务
    api_host: str = "0.0.0.0"
    api_port: int = 48000
    api_workers: int = 1
    api_reload: bool = True

    # CORS
    cors_origins: str = "http://localhost:48173,http://localhost:3000"

    # 前端 URL（用于生成链接）
    frontend_url: str = "http://localhost:48173"

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://athena:athena_dev_password@localhost:45432/athena",
        description="PostgreSQL 异步连接 URL",
    )
    database_url_sync: str = Field(
        default="postgresql://athena:athena_dev_password@localhost:45432/athena",
        description="PostgreSQL 同步连接 URL (用于 Alembic)",
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False


class RedisSettings(BaseSettings):
    """Redis/Valkey 配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:46379/0"
    celery_broker_url: str = "redis://localhost:46379/1"
    celery_result_backend: str = "redis://localhost:46379/2"


class MinioSettings(BaseSettings):
    """MinIO 对象存储配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    minio_endpoint: str = "localhost:48333"
    # 外部访问地址（用于生成预签名 URL，浏览器可访问）
    minio_external_endpoint: str = ""
    minio_access_key: str = "athena_access_key"
    minio_secret_key: str = "athena_secret_key"
    minio_secure: bool = False
    minio_bucket_books: str = "athena-books"
    minio_bucket_covers: str = "athena-covers"
    minio_bucket_ocr: str = "athena-ocr"

    @computed_field
    @property
    def minio_url(self) -> str:
        protocol = "https" if self.minio_secure else "http"
        return f"{protocol}://{self.minio_endpoint}"

    @computed_field
    @property
    def minio_external_url(self) -> str:
        """获取外部访问 URL，如果未配置则使用内部地址"""
        endpoint = self.minio_external_endpoint or self.minio_endpoint
        protocol = "https" if self.minio_secure else "http"
        return f"{protocol}://{endpoint}"


class AuthSettings(BaseSettings):
    """认证配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # JWT 配置 - 与 PowerSync 共享
    auth_secret: str = Field(
        default="dev_powersync_secret_change_in_production_must_be_256_bits_long",
        min_length=32,
        description="JWT 签名密钥，必须与 PowerSync 一致",
    )
    auth_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 小时
    refresh_token_expire_days: int = 30

    # 验证码配置
    auth_code_expire_minutes: int = 10
    auth_code_max_attempts: int = 5


class PowerSyncSettings(BaseSettings):
    """PowerSync 配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    powersync_url: str = "http://localhost:48090"
    powersync_jwt_secret: str | None = None  # 默认使用 AUTH_SECRET
    powersync_upload_enabled: bool = True


class CelerySettings(BaseSettings):
    """Celery 配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    celery_worker_concurrency: int = 4
    celery_task_soft_time_limit: int = 300
    celery_task_time_limit: int = 360


class OcrSettings(BaseSettings):
    """OCR 配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ocr_enabled: bool = True
    ocr_gpu_enabled: bool = False
    ocr_max_pages: int = 2000
    ocr_timeout_seconds: int = 1800


class AiSettings(BaseSettings):
    """AI 配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536


class SmtpSettings(BaseSettings):
    """SMTP 邮件配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Athena <noreply@athena.app>"
    smtp_tls: bool = True


class StripeSettings(BaseSettings):
    """Stripe 支付配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro_monthly: str = ""
    stripe_price_pro_yearly: str = ""


class QuotaSettings(BaseSettings):
    """配额配置"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 免费用户配额
    free_storage_quota_mb: int = 500
    free_book_limit: int = 50
    free_ocr_pages_monthly: int = 100

    # Pro 用户配额
    pro_storage_quota_mb: int = 10240
    pro_book_limit: int = 1000


class Settings(BaseSettings):
    """全局配置聚合"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    powersync: PowerSyncSettings = Field(default_factory=PowerSyncSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    ocr: OcrSettings = Field(default_factory=OcrSettings)
    ai: AiSettings = Field(default_factory=AiSettings)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
    stripe: StripeSettings = Field(default_factory=StripeSettings)
    quota: QuotaSettings = Field(default_factory=QuotaSettings)


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()


# 导出便捷访问
settings = get_settings()
