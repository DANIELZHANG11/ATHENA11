# Athena API

雅典娜阅读应用后端 API，基于 FastAPI + SQLAlchemy 2.0 构建。

## 技术栈

- **Python 3.11+**
- **FastAPI 0.115+** - 高性能 Web 框架
- **SQLAlchemy 2.0+** - 异步 ORM
- **PostgreSQL + pgvector** - 数据库 + 向量搜索
- **Celery 5.4+** - 异步任务队列
- **Valkey/Redis** - 缓存 + 消息队列
- **MinIO** - S3 兼容对象存储

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件配置数据库等参数
```

### 3. 启动开发服务器

```bash
# 启动 API
uvicorn app.main:app --host 0.0.0.0 --port 48000 --reload

# 或使用
python -m uvicorn app.main:app --host 0.0.0.0 --port 48000 --reload
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:48000/docs
- ReDoc: http://localhost:48000/redoc

## 项目结构

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── deps.py          # 依赖注入
│   │   ├── routes/          # API 路由
│   │   │   ├── auth.py      # 认证路由
│   │   │   ├── books.py     # 书籍路由
│   │   │   └── ...
│   │   └── schemas/         # Pydantic 模型
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── security.py      # 安全工具
│   │   └── exceptions.py    # 异常定义
│   ├── models/              # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── book.py
│   │   └── ...
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── book_service.py
│   │   └── ...
│   └── tasks/               # Celery 任务
│       ├── ocr.py
│       └── ...
├── migrations/              # Alembic 迁移
├── tests/                   # 测试
├── docker/                  # Docker 配置
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## 开发指南

### 代码规范

使用 Ruff 进行代码检查和格式化：

```bash
# 检查代码
ruff check .

# 格式化代码
ruff format .

# 类型检查
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/test_auth.py -v
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## API 端点

### 认证 (`/api/v1/auth`)

- `POST /email/send_code` - 发送邮箱验证码
- `POST /email/verify_code` - 验证验证码并登录
- `POST /token/refresh` - 刷新访问令牌
- `GET /me` - 获取当前用户信息
- `POST /logout` - 登出

### 书籍 (`/api/v1/books`)

- `POST /upload_init` - 初始化上传
- `POST /upload_complete` - 完成上传
- `GET /` - 获取书籍列表
- `GET /{id}` - 获取书籍详情
- `DELETE /{id}` - 删除书籍

## 许可证

MIT
