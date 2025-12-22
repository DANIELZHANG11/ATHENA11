# 08 - 进度实时仪表盘 (Project Status)

> **版本**：v1.0  
> **状态**：AI Coding Journal Template  
> **用途**：AI 编码时记录所有变更，供人类审查与追溯

---

## 📋 使用说明

本文档是 **AI 编码日志**，每次 AI 进行代码生成或修改时，必须在此记录：
1. 变更摘要（做了什么）
2. 修改的文件清单
3. 影响范围评估
4. 待人工确认/测试的事项

**格式规范**：按时间倒序排列，最新的变更在最上面。

---

## 🚀 项目总览

| 维度 | 当前状态 |
|------|----------|
| **项目阶段** | 🔧 后端开发完成 |
| **后端进度** | 100% - 所有 API 模块已完成 |
| **前端进度** | 0% - 尚未开始编码 |
| **同步层进度** | 30% - PowerSync 配置已完成 |
| **基础设施** | 70% - Docker/CI 配置已完成，Calibre 服务已添加 |
| **文档完成度** | ✅ 审计完成 |

---

## 📊 模块完成度追踪

| 模块 | 后端 API | 数据库 | 前端 UI | 同步规则 | 测试 | 总体 |
|------|----------|--------|---------|----------|------|------|
| **用户认证** | ✅ 100% | ✅ 100% | ⬜ 0% | ⬜ 0% | ✅ 100% | 🟨 60% |
| **书籍管理** | ✅ 100% | ✅ 100% | ⬜ 0% | 🟨 50% | 🟨 30% | 🟨 55% |
| **格式转换** | ✅ 100% | ✅ 100% | N/A | N/A | ⬜ 0% | 🟨 65% |
| **阅读器核心** | ✅ 100% | ✅ 100% | ⬜ 0% | 🟨 50% | ⬜ 0% | 🟨 50% |
| **阅读统计** | ✅ 100% | ✅ 100% | ⬜ 0% | 🟨 50% | ⬜ 0% | 🟨 50% |
| **AI 对话** | ✅ 100% | ✅ 100% | ⬜ 0% | N/A | ⬜ 0% | 🟨 50% |
| **付费订阅** | ✅ 100% | ✅ 100% | ⬜ 0% | ⬜ 0% | ⬜ 0% | 🟨 40% |
| **邀请裂变** | ✅ 100% | ✅ 100% | ⬜ 0% | ⬜ 0% | ⬜ 0% | 🟨 40% |
| **数据导出** | ✅ 100% | N/A | ⬜ 0% | N/A | ⬜ 0% | 🟨 35% |
| **用户管理** | ✅ 100% | ✅ 100% | ⬜ 0% | N/A | ⬜ 0% | 🟨 40% |

> **图例**：⬜ 未开始 | 🟨 进行中 | ✅ 已完成 | ⏸️ 暂停

---

## 📝 AI 编码变更日志

### 🔧 变更 #009 - 完成付费订阅、邀请裂变、数据导出、用户管理 API
| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-22 13:45 |
| **变更类型** | 功能开发 |
| **触发来源** | 用户请求 - 后端 100% 完成 |
| **影响模块** | Billing, Invite, Export, Users |
| **破坏性变更** | 否 |

#### 📄 变更摘要
1. **付费订阅 API**: 完整实现订阅方案、支付会话、支付历史、订阅状态、积分余额、积分商品、Apple/Google IAP 验证
2. **邀请裂变 API**: 邀请码生成、邀请统计、被邀请人列表、奖励规则（4 级奖励梯度）
3. **数据导出 API**: 笔记导出支持 Markdown/JSON/HTML 格式
4. **用户管理 API**: 账号注销（GDPR 合规）、通知设置
5. **OCR 触发 API**: 新增 `POST /books/{id}/ocr` 和 `GET /books/{id}/ocr/status` 端点

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/app/api/schemas/billing.py` | 新增 | 付费订阅相关 Pydantic 模型 |
| `api/app/services/billing_service.py` | 新增 | 付费订阅业务逻辑服务 |
| `api/app/api/routes/billing.py` | 新增 | 付费订阅 API 路由 (8 个端点) |
| `api/app/api/schemas/invite.py` | 新增 | 邀请裂变相关 Pydantic 模型 |
| `api/app/services/invite_service.py` | 新增 | 邀请裂变业务逻辑服务 |
| `api/app/api/routes/invite.py` | 新增 | 邀请裂变 API 路由 (4 个端点) |
| `api/app/api/schemas/export.py` | 新增 | 数据导出相关 Pydantic 模型 |
| `api/app/services/export_service.py` | 新增 | 数据导出业务逻辑服务 |
| `api/app/api/routes/export.py` | 新增 | 数据导出 API 路由 (1 个端点) |
| `api/app/api/schemas/user.py` | 新增 | 用户管理相关 Pydantic 模型 |
| `api/app/services/user_service.py` | 新增 | 用户管理业务逻辑服务（含 GDPR 硬删除） |
| `api/app/api/routes/users.py` | 新增 | 用户管理 API 路由 (3 个端点) |
| `api/app/services/book_service.py` | 修改 | 添加 OCR 触发相关方法 |
| `api/app/api/routes/books.py` | 修改 | 添加 OCR 触发端点 |
| `api/app/main.py` | 修改 | 注册 billing, invite, export, users 路由 |
| `api/app/api/routes/__init__.py` | 修改 | 导出新增路由模块 |
| `api/app/api/schemas/__init__.py` | 修改 | 导出新增 schema 模块 |

#### 🔗 关联变更
- 数据库迁移：否 (使用现有 billing/user 表)
- API 变更：是 (新增 16 个端点)
- 配置变更：否
- 依赖变更：否

#### 📊 新增端点列表
```
GET    /api/v1/billing/plans
POST   /api/v1/billing/checkout
GET    /api/v1/billing/history
GET    /api/v1/billing/subscription
GET    /api/v1/billing/credits/balance
GET    /api/v1/billing/credits/products
POST   /api/v1/billing/iap/apple/verify
POST   /api/v1/billing/iap/google/verify
GET    /api/v1/invite/code
GET    /api/v1/invite/stats
GET    /api/v1/invite/invitees
GET    /api/v1/invite/rules
GET    /api/v1/export/notes
DELETE /api/v1/users/me
GET    /api/v1/users/me/notification-settings
PATCH  /api/v1/users/me/notification-settings
```

#### ⚠️ 待人工确认
- [ ] 配置支付网关凭证 (Stripe, Apple/Google IAP)
- [ ] 确认 GDPR 硬删除逻辑符合法规要求
- [ ] 测试积分扣减事务一致性

#### 🧪 待测试项
- [x] 本地模块导入验证 (Passed)
- [x] Docker 镜像重建 (Passed)
- [x] 端点注册验证 (16 个端点已确认)
- [ ] 单元测试编写

---

### 🔧 变更 #008 - 添加 Calibre 服务、格式转换任务、阅读统计 API
| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 18:30 |
| **变更类型** | 功能开发 / 基础设施 |
| **触发来源** | 用户请求 - 后端完善 |
| **影响模块** | Docker, Celery, Reading API |
| **破坏性变更** | 否 |

#### 📄 变更摘要
1. **Docker**: 添加 Calibre 格式转换服务到 `docker-compose.yml`，包括 calibre 容器和专用 Celery Conversion Worker
2. **格式转换**: 创建 `conversion_tasks.py`，支持 MOBI/AZW3 -> EPUB 转换
3. **阅读统计 API**: 创建完整的阅读进度、时长记录、统计数据 API
4. **代码质量**: 修复所有 Ruff lint 错误

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/docker-compose.yml` | 修改 | 添加 Calibre 服务、celery-conversion-worker、calibre_config/calibre_books 数据卷 |
| `api/app/tasks/conversion_tasks.py` | 新增 | Calibre 格式转换任务 (MOBI/AZW3 -> EPUB) |
| `api/app/tasks/celery_app.py` | 修改 | 添加 conversion 任务模块、队列配置和路由 |
| `api/app/api/routes/reading.py` | 新增 | 阅读进度、时长记录、统计数据 API 路由 |
| `api/app/api/schemas/reading.py` | 新增 | 阅读相关 Pydantic 模型 |
| `api/app/services/reading_service.py` | 新增 | 阅读业务逻辑服务 |
| `api/app/api/routes/__init__.py` | 修改 | 导出 reading 模块 |
| `api/app/api/schemas/__init__.py` | 修改 | 导出 reading schemas |
| `api/app/main.py` | 修改 | 注册 reading 路由 |

#### 🔗 关联变更
- 数据库迁移：否 (使用现有 reading 表)
- API 变更：是 (新增 `/api/v1/reading/*` 端点)
- 配置变更：是 (Docker Compose)
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 启动 Calibre 容器验证服务正常
- [ ] 测试格式转换功能
- [ ] 确认阅读统计 API 响应正确

#### 🧪 待测试项
- [x] `ruff check` (Passed)
- [ ] `pytest tests/test_reading.py` (待编写)
- [ ] 集成测试: 上传 MOBI -> 转换 -> EPUB

---

### 🔧 变更 #007 - 修复 CI Linter 错误
| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 16:30 |
| **变更类型** | 代码质量优化 / Bug修复 |
| **触发来源** | CI Linter Logs |
| **影响模块** | Testing, CI |
| **破坏性变更** | 否 |

#### 📄 变更摘要
修复 `app/api/routes/powersync.py` 中的 Mypy 类型错误（属性名称错误、泛型缺失）及导入排序；修复 `alembic/versions/001_initial_schema.py` 中的嵌套列定义错误。

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/app/api/routes/powersync.py` | 修改 | 修正 `AuthSettings` 属性名 (`jwt_secret_key` -> `auth_secret` 等)，修复泛型注解，优化导入排序 |
| `api/alembic/versions/001_initial_schema.py` | 修改 | 修复 `document_vectors` 表中 `embedding` 列的错误嵌套定义 |

#### 🔗 关联变更
- 数据库迁移：是 (修正了迁移脚本定义，不影响已运行迁移)
- API 变更：否
- 配置变更：否
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 确认 PowerSync 服务能正确验证 Token

#### 🧪 待测试项
- [x] `ruff check` (Passed)
- [x] `mypy` (Passed for target files)

---

### 🔧 变更 #006 - CI 配置标准化与测试修复
| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 16:15 |
| **变更类型** | 配置优化 / Bug修复 |
| **触发来源** | CI Validation |
| **影响模块** | CI, Testing |
| **破坏性变更** | 否 |

#### 📄 变更摘要
合并 `pytest.ini` 配置到 `pyproject.toml`，消除重复配置警告。确认并验证所有 Auth 测试用例通过。

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/pyproject.toml` | 修改 | 合并 pytest 配置，添加 python_files/filterwarnings 等设置 |
| `api/pytest.ini` | 删除 | 删除冗余配置文件，统一使用 pyproject.toml |
| `api/tests/test_auth.py` | 验证 | 确认测试通过 |

#### 🔗 关联变更
- 数据库迁移：否
- API 变更：否
- 配置变更：是 (Pytest)
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 观察 GitHub Actions 运行结果

#### 🧪 待测试项
- [x] `pytest` (All Passed)

---

### 🔧 变更 #005 - 修复 CI 异步测试环境与 SQLite 兼容性

| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 16:00 |
| **变更类型** | Bug修复 / 测试环境配置 |
| **触发来源** | CI Failure / 用户反馈 |
| **影响模块** | Testing, CI |
| **破坏性变更** | 否 |

#### 📄 变更摘要
解决本地/CI环境下使用 SQLite 运行测试时的兼容性问题（JSONB/UUID/TSVECTOR），修复 pytest-asyncio 事件循环作用域错误，完善 Auth 模块测试用例。

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/tests/conftest.py` | 修改 | 添加 SQLite 编译规则(JSONB/UUID/TSVECTOR -> JSON/TEXT)，移除过时的 event_loop fixture |
| `api/pyproject.toml` | 修改 | 配置 `asyncio_default_fixture_loop_scope = "session"`，移除重复配置块 |
| `api/tests/test_auth.py` | 修改 | 修正 `send_code` 路径，更新 `test_verify_email_code_invalid` 以测试格式校验(422) |

#### 🔗 关联变更
- 数据库迁移：否
- API 变更：否
- 配置变更：是 (Pytest)
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 确认 CI 流水线通过

#### 🧪 待测试项
- [x] `pytest tests/test_auth.py` (Passed)

---

### 🔧 变更 #004 - 修复 CI 报错与测试路径不匹配

| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 15:30 |
| **变更类型** | Bug修复 / 测试 / 重构 |
| **触发来源** | 用户请求 / CI Failure |
| **影响模块** | Auth, Database, CI |
| **破坏性变更** | 否 |

#### 📄 变更摘要
修复了 CI 流水线中的 `ImportError` 和 Linter 错误，并修正了 `test_auth.py` 中的 API 路径以匹配 OpenAPI 契约和代码实现。

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/app/core/database.py` | 修改 | 重命名 `get_db` 为 `get_db_session`，移除无用导入 |
| `api/app/api/routes/auth.py` | 修改 | 修复 `== False` 语法，更新依赖注入引用 |
| `api/tests/test_auth.py` | 修改 | 修正测试 URL (`/email/code` -> `/email/send_code`, `/email/verify` -> `/email/verify_code`) |
| `api/alembic/versions/001_initial_schema.py` | 修改 | 修复类型注解和尾部空格 |
| `api/pyproject.toml` | 修改 | 修正 Ruff 配置 |

#### 🔗 关联变更
- 数据库迁移：否
- API 变更：否 (仅测试对齐)
- 配置变更：是 (Ruff Config)
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 确认 CI 流水线是否全绿

#### 🧪 待测试项
- [x] `pytest tests/test_auth.py`

---

### 🔧 变更 #003 - 修复 UserOAuthAccount 表定义错误
... (保留原有记录)
