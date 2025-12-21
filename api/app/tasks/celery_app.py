"""
Celery 应用配置

配置 Celery 任务队列，使用 Valkey (Redis) 作为 Broker。
"""

from celery import Celery

from app.core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "athena",
    broker=settings.celery.celery_broker_url,
    backend=settings.celery.celery_result_backend,
    include=[
        "app.tasks.ocr_tasks",
        "app.tasks.book_tasks",
        "app.tasks.cleanup_tasks",
    ],
)

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

    # 任务队列配置
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "ocr": {
            "exchange": "ocr",
            "routing_key": "ocr",
        },
        "processing": {
            "exchange": "processing",
            "routing_key": "processing",
        },
        "cleanup": {
            "exchange": "cleanup",
            "routing_key": "cleanup",
        },
    },

    # 任务路由
    task_routes={
        "app.tasks.ocr_tasks.*": {"queue": "ocr"},
        "app.tasks.book_tasks.*": {"queue": "processing"},
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
)


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
