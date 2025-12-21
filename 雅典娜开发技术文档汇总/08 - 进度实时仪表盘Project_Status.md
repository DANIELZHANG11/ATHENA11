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
| **项目阶段** | 🔧 后端开发中 |
| **后端进度** | 70% - 核心 API 和模型已完成 |
| **前端进度** | 0% - 尚未开始编码 |
| **同步层进度** | 30% - PowerSync 配置已完成 |
| **基础设施** | 50% - Docker/CI 配置已完成 |
| **文档完成度** | ✅ 审计完成 |

---

## 📊 模块完成度追踪

| 模块 | 后端 API | 数据库 | 前端 UI | 同步规则 | 测试 | 总体 |
|------|----------|--------|---------|----------|------|------|
| **用户认证** | ✅ 100% | ✅ 100% | ⬜ 0% | ⬜ 0% | ✅ 100% | 🟨 60% |
| **书籍管理** | ✅ 100% | ✅ 100% | ⬜ 0% | 🟨 50% | 🟨 30% | 🟨 55% |
| **阅读器核心** | 🟨 50% | ✅ 100% | ⬜ 0% | 🟨 50% | ⬜ 0% | 🟨 40% |
| **阅读统计** | 🟨 50% | ✅ 100% | ⬜ 0% | 🟨 50% | ⬜ 0% | 🟨 40% |
| **AI 对话** | ✅ 100% | ✅ 100% | ⬜ 0% | N/A | ⬜ 0% | 🟨 50% |
| **付费订阅** | 🟨 30% | ✅ 100% | ⬜ 0% | ⬜ 0% | ⬜ 0% | 🟨 25% |
| **邀请裂变** | 🟨 30% | ✅ 100% | ⬜ 0% | ⬜ 0% | ⬜ 0% | 🟨 25% |

> **图例**：⬜ 未开始 | 🟨 进行中 | ✅ 已完成 | ⏸️ 暂停

---

## 📝 AI 编码变更日志

### 🔧 变更 #007 - 修复 CI Linter 错误
| 属性 | 值 |
|------|-----|
| **日期时间** | 2025-12-21 16:30 |
| **变更类型** | 代码质量优化 / Bug修复 |
| **触发来源** | CI Linter Logs |
| **影响模块** | Testing, CI |
| **破坏性变更** | 否 |

#### 📄 变更摘要
修复 `tests/conftest.py` 中的 Ruff Linter 错误（未使用的导入、参数命名、导入排序）及 Mypy 类型错误；修复 `app/api/deps.py` 导出问题。

#### 📁 修改文件清单

| 文件路径 | 操作 | 变更说明 |
|----------|------|----------|
| `api/tests/conftest.py` | 修改 | 清理未使用的导入，规范化参数命名，优化导入排序，修复 Mypy 类型注解 |
| `api/app/api/deps.py` | 修改 | 添加 `__all__` 明确导出 `get_db_session` 等依赖，修复 Mypy 导入错误 |
| `CI验证规则及错误日志.md` | 修改 | 移除已修复的 CI 错误日志 |

#### 🔗 关联变更
- 数据库迁移：否
- API 变更：否
- 配置变更：否
- 依赖变更：否

#### ⚠️ 待人工确认
- [ ] 确认 CI 流水线 (Ruff check & Mypy) 通过

#### 🧪 待测试项
- [x] `ruff check .` (All Passed)
- [x] `mypy tests/conftest.py` (Passed)
- [x] `pytest tests/test_auth.py` (All Passed)

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
