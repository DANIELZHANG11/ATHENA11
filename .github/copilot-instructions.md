# 雅典娜 (Athena) - AI 编码指南

> 本文档为 AI 编码代理提供项目关键信息，确保生成的代码符合项目架构规范。

## 🏗️ 核心架构：App-First / 离线优先

雅典娜是一款**离线优先阅读应用**，采用 **SQLite + PowerSync** 架构实现多端数据同步。

```
前端 (SQLite) ←→ PowerSync SDK ←→ PowerSync Service ←→ PostgreSQL (后端)
```

### 数据流黄金法则

| 场景 | 负责方 | 示例 |
|------|--------|------|
| UI 数据读取 | **PowerSync (SQLite)** | `useLiveQuery(powersync.books.all())` |
| CUD 操作 | **PowerSync (SQLite)** | `db.execute('UPDATE books SET title=?')` |
| 文件上传/下载 | **REST API + S3** | `POST /api/v1/books/upload_init` |
| 认证/支付/AI对话 | **REST API** | `POST /api/v1/auth/*`, `POST /api/v1/ai/chat` |

⚠️ **严禁**：前端使用 `useEffect` + `api.get()` 获取数据并 `setState()` 渲染（实时搜索/支付除外）。

## 📁 项目结构

```
api/                    # Python 后端
├── app/
│   ├── main.py         # FastAPI 入口
│   ├── api/routes/     # API 路由 (auth, books, notes, ai, powersync...)
│   ├── api/schemas/    # Pydantic 请求/响应模型
│   ├── core/           # 配置、数据库、安全、异常
│   ├── models/         # SQLAlchemy ORM 模型
│   ├── services/       # 业务逻辑层
│   └── tasks/          # Celery 异步任务 (OCR, 转换...)
├── tests/              # pytest 测试
├── alembic/            # 数据库迁移
└── powersync/          # PowerSync 同步规则

雅典娜开发技术文档汇总/   # 📚 技术规范 (00-12 号文档)
```

## 🔧 开发命令

```bash
# 后端开发
cd api
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 48000 --reload

# 代码检查
ruff check .          # Lint
ruff format .         # Format

# 测试 (需要 PostgreSQL + Redis)
pytest --cov=app
```

## 🎯 编码规范

### 后端 (Python/FastAPI)

1. **分层架构**：`routes/` → `services/` → `models/`，路由层禁止直接操作数据库
2. **异步优先**：所有数据库操作使用 `async/await` + `AsyncSession`
3. **Pydantic 模型**：请求/响应必须定义 Schema，位于 `api/schemas/`
4. **异常处理**：使用 `app/core/exceptions.py` 中定义的 `AthenaException` 子类
5. **配置管理**：环境变量通过 `app/core/config.py` 的 `settings` 对象访问

```python
# ✅ 正确示例 - 服务层
class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_book(self, book_id: UUID) -> Book:
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()
```

### 数据库迁移 (Alembic)

```bash
cd api
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

### PowerSync 同步表

支持双向同步的 9 张表：`books`, `reading_progress`, `reading_sessions`, `notes`, `highlights`, `bookmarks`, `shelves`, `shelf_books`, `user_settings`

修改同步规则需更新：
- `api/powersync/sync-rules.yaml` - 服务端同步规则
- `web/src/lib/powersync/schema.ts` - 客户端 Schema (前端项目)

## ⚠️ 关键约束

1. **SQLite Schema 只增不减**：移动端兼容性要求，禁止删除/重命名字段
2. **软删除优先**：使用 `deleted_at` 字段，硬删除通过 REST API 单独处理
3. **books 表写入混合**：创建通过 API，元数据修改通过 PowerSync
4. **高频操作节流**：阅读进度更新需前端实现 30s 节流，防止电量消耗

## 🔐 安全要点

- **RLS (Row Level Security)**：所有业务表启用 PostgreSQL RLS，禁止手动拼接 `WHERE user_id`
- **JWT 统一认证**：REST API 和 PowerSync 使用相同 JWT Secret

## 📖 必读文档

深入开发前请阅读 `雅典娜开发技术文档汇总/` 目录：

| 文档 | 内容 |
|------|------|
| `00 - AI 编码宪法` | **必读** - 离线优先铁律、PowerSync 规范 |
| `03 - 系统架构与ADR` | 技术栈、架构决策记录 |
| `04 - 数据库全景` | Schema 设计、字段说明 |
| `05 - API 契约` | REST API 规范、错误码 |
| `10 - CI与测试策略` | 测试金字塔、覆盖率要求 |

## 🚫 常见错误

```typescript
// ❌ 错误 - 直接调 API 获取数据
const [books, setBooks] = useState([])
useEffect(() => {
  api.get('/books').then(res => setBooks(res.data))
}, [])

// ✅ 正确 - 通过 PowerSync 读取本地数据
const books = useLiveQuery(powersync.books.all())
```

```typescript
// ❌ 错误 - 用 API 修改元数据
await fetch(`/api/v1/books/${id}/metadata`, { method: 'PATCH', body: {...} })

// ✅ 正确 - 通过 PowerSync 写入本地 SQLite
await db.execute('UPDATE books SET title=?, updated_at=? WHERE id=?', [title, now, id])
```
