"""
Celery 应用配置

配置 Celery 任务队列，使用 Valkey (Redis) 作为 Broker。

OCR 优先级队列说明：
- 使用单一 'ocr' 队列，通过 priority 参数区分付费/免费用户
- priority 范围: 0-9，数字越小优先级越高
- 付费用户: priority=0-3
- 免费用户: priority=6-9
- 同优先级按 FIFO（先进先出）顺序处理
"""

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "athena",
    broker=settings.redis.celery_broker_url,
    backend=settings.redis.celery_result_backend,
    include=[
        "app.tasks.ocr_tasks",
        "app.tasks.book_tasks",
        "app.tasks.cleanup_tasks",
        "app.tasks.conversion_tasks",
    ],
)

# 定义交换机
default_exchange = Exchange("default", type="direct")
ocr_exchange = Exchange("ocr", type="direct")
processing_exchange = Exchange("processing", type="direct")
conversion_exchange = Exchange("conversion", type="direct")
metadata_exchange = Exchange("metadata", type="direct")
indexing_exchange = Exchange("indexing", type="direct")
cleanup_exchange = Exchange("cleanup", type="direct")

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果
    result_expires=3600,  # 1 小时后过期
    result_extended=True,

    # 任务执行
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker 丢失时拒绝任务
    task_track_started=True,  # 跟踪任务开始状态

    # 并发控制
    worker_prefetch_multiplier=1,  # 每次只预取 1 个任务
    worker_max_tasks_per_child=100,  # 每个 Worker 处理 100 个任务后重启

    # 任务队列配置（使用 kombu Queue 对象支持优先级）
    task_queues=[
        Queue("default", default_exchange, routing_key="default"),
        # OCR 队列启用优先级支持（0-9，共 10 个优先级）
        Queue("ocr", ocr_exchange, routing_key="ocr", queue_arguments={"x-max-priority": 10}),
        Queue("processing", processing_exchange, routing_key="processing"),
        Queue("conversion", conversion_exchange, routing_key="conversion"),
        Queue("metadata", metadata_exchange, routing_key="metadata"),
        Queue("indexing", indexing_exchange, routing_key="indexing"),
        Queue("cleanup", cleanup_exchange, routing_key="cleanup"),
    ],

    # 任务路由
    task_routes={
        "app.tasks.ocr_tasks.*": {"queue": "ocr"},
        "app.tasks.book_tasks.*": {"queue": "processing"},
        "app.tasks.conversion_tasks.*": {"queue": "conversion"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },

    # 定时任务
    beat_schedule={
        "cleanup-expired-books": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_books",
            "schedule": 3600.0,  # 每小时
        },
        "cleanup-orphan-files": {
            "task": "app.tasks.cleanup_tasks.cleanup_orphan_files",
            "schedule": 86400.0,  # 每天
        },
    },

    # Redis 优先级队列配置
    broker_transport_options={
        "priority_steps": list(range(10)),  # 0-9 优先级
        "sep": ":",
        "queue_order_strategy": "priority",
    },
)


# OCR 优先级常量
class OCRPriority:
    """OCR 任务优先级常量"""
    PAID_URGENT = 0      # 付费用户 - 紧急
    PAID_HIGH = 1        # 付费用户 - 高
    PAID_NORMAL = 2      # 付费用户 - 普通
    PAID_LOW = 3         # 付费用户 - 低
    FREE_HIGH = 6        # 免费用户 - 高
    FREE_NORMAL = 7      # 免费用户 - 普通
    FREE_LOW = 8         # 免费用户 - 低
    FREE_LOWEST = 9      # 免费用户 - 最低


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
