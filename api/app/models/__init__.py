"""
雅典娜数据库模型

导出所有 SQLAlchemy 模型，用于 Alembic 迁移和应用代码。
"""

# AI 相关
from app.models.ai import (
    AiConversation,
    AiConversationContext,
    AiMessage,
    AiModel,
    AiQueryCache,
    PromptTemplate,
)
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin

# 计费相关
from app.models.billing import (
    CreditAccount,
    CreditLedger,
    CreditProduct,
    FreeQuotaUsage,
    PaymentSession,
    PaymentWebhookEvent,
    PricingRule,
)

# 书籍相关
from app.models.book import (
    Book,
    ConversionJob,
    Shelf,
    ShelfBook,
)

# 笔记与高亮
from app.models.note import (
    Bookmark,
    Highlight,
    HighlightTag,
    Note,
    NoteTag,
    Tag,
)

# 阅读进度
from app.models.reading import (
    BookPosition,
    ReadingDaily,
    ReadingTimeLog,
)

# 系统配置
from app.models.system import (
    FeatureFlag,
    OcrJob,
    SystemSetting,
    Translation,
)

# 用户相关
from app.models.user import (
    Invite,
    User,
    UserOAuthAccount,
    UserReadingGoal,
    UserSession,
    UserSetting,
    UserStats,
    UserStreak,
)

# 向量存储
from app.models.vector import VectorDocument

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
    # Aliases for alternative naming conventions
    "AIMessage",
    "AISession",
    "DocumentVector",
]

# 别名支持不同的命名风格
AIMessage = AiMessage
AISession = AiConversation
DocumentVector = VectorDocument
