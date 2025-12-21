"""
雅典娜数据库模型

导出所有 SQLAlchemy 模型，用于 Alembic 迁移和应用代码。
"""

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin

# 用户相关
from app.models.user import (
    User,
    UserSession,
    UserOAuthAccount,
    UserStats,
    Invite,
    UserReadingGoal,
    UserStreak,
    UserSetting,
)

# 书籍相关
from app.models.book import (
    Book,
    Shelf,
    ShelfBook,
    ConversionJob,
)

# 笔记与高亮
from app.models.note import (
    Note,
    Highlight,
    Bookmark,
    Tag,
    NoteTag,
    HighlightTag,
)

# 阅读进度
from app.models.reading import (
    BookPosition,
    ReadingTimeLog,
    ReadingDaily,
)

# AI 相关
from app.models.ai import (
    AiModel,
    AiConversation,
    AiMessage,
    AiConversationContext,
    AiQueryCache,
    PromptTemplate,
)

# 计费相关
from app.models.billing import (
    CreditAccount,
    CreditLedger,
    CreditProduct,
    PaymentSession,
    PaymentWebhookEvent,
    PricingRule,
    FreeQuotaUsage,
)

# 向量存储
from app.models.vector import VectorDocument

# 系统配置
from app.models.system import (
    SystemSetting,
    FeatureFlag,
    Translation,
    OcrJob,
)

__all__ = [
    # Base
    "Base",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "VersionMixin",
    # User
    "User",
    "UserSession",
    "UserOAuthAccount",
    "UserStats",
    "Invite",
    "UserReadingGoal",
    "UserStreak",
    "UserSetting",
    # Book
    "Book",
    "Shelf",
    "ShelfBook",
    "ConversionJob",
    # Note
    "Note",
    "Highlight",
    "Bookmark",
    "Tag",
    "NoteTag",
    "HighlightTag",
    # Reading
    "BookPosition",
    "ReadingTimeLog",
    "ReadingDaily",
    # AI
    "AiModel",
    "AiConversation",
    "AiMessage",
    "AiConversationContext",
    "AiQueryCache",
    "PromptTemplate",
    # Billing
    "CreditAccount",
    "CreditLedger",
    "CreditProduct",
    "PaymentSession",
    "PaymentWebhookEvent",
    "PricingRule",
    "FreeQuotaUsage",
    # Vector
    "VectorDocument",
    # System
    "SystemSetting",
    "FeatureFlag",
    "Translation",
    "OcrJob",
]
