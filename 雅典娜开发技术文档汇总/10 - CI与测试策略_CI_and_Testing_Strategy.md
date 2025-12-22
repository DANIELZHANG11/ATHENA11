# 10 - CI 与测试策略 (CI and Testing Strategy)

> **版本**：v1.0
> **定位**：定义持续集成流水线、测试金字塔、覆盖率要求、质量门禁与合约测试规范。
> **更新日期**：2025-12-19

---

## 1. CI 流水线概览 (CI Pipeline Overview)

### 1.1 触发条件

| 触发事件 | 执行流水线 | 说明 |
|:---------|:----------|:-----|
| Push to `main` | Full Pipeline | 完整构建、测试、部署到 Staging |
| Push to `develop` | Build + Test | 构建和测试，不部署 |
| Pull Request | PR Pipeline | Lint + Unit Test + Contract Test |
| Tag `v*` | Release Pipeline | 完整测试 + 构建生产镜像 + 部署 |
| Schedule (每日 02:00) | Nightly | 完整测试 + 安全扫描 + 依赖检查 |

### 1.2 流水线阶段

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Install   │ -> │    Lint     │ -> │    Test     │ -> │    Build    │ -> │   Deploy    │
│ Dependencies│    │  & Format   │    │  & Coverage │    │   Artifacts │    │  (Staging)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 1.3 阶段详情

#### Stage 1: Install Dependencies
```yaml
# 后端 (Python)
- pip install -r requirements.txt -r requirements-dev.txt

# 前端 (Node.js)
- pnpm install --frozen-lockfile
```

#### Stage 2: Lint & Format
```yaml
# 后端
- ruff check .                    # Python linter
- ruff format --check .           # Python formatter
- mypy app/                       # Type checking

# 前端
- pnpm lint                       # ESLint
- pnpm format:check               # Prettier
- pnpm typecheck                  # TypeScript
```

#### Stage 3: Test & Coverage
```yaml
# 后端
- pytest --cov=app --cov-report=xml --cov-fail-under=85

# 前端
- pnpm test:coverage --coverage-threshold=80

# 合约测试
- pnpm test:contract
```

#### Stage 4: Build Artifacts
```yaml
# 后端 Docker 镜像
- docker build -t athena-api:$CI_COMMIT_SHA -f docker/api/Dockerfile .
- docker build -t athena-worker:$CI_COMMIT_SHA -f docker/worker/Dockerfile .

# 前端
- pnpm build
- docker build -t athena-web:$CI_COMMIT_SHA -f docker/web/Dockerfile .
```

#### Stage 5: Deploy (Staging)
```yaml
# 仅 main 分支
- docker compose -f docker-compose.staging.yml up -d
- ./scripts/run-smoke-tests.sh
```

---

## 2. 测试金字塔 (Testing Pyramid)

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲           <- 少量，高价值，慢
                 ╱──────╲
                ╱        ╲
               ╱Integration╲       <- 适量，API/DB 层
              ╱────────────╲
             ╱              ╲
            ╱   Unit Tests   ╲     <- 大量，快速，隔离
           ╱──────────────────╲
```

### 2.1 测试类型分布

| 测试类型 | 占比目标 | 执行时间 | 执行频率 |
|:---------|:--------|:---------|:---------|
| Unit Tests | 70% | < 5 分钟 | 每次 Commit |
| Integration Tests | 20% | < 15 分钟 | 每次 PR |
| E2E Tests | 10% | < 30 分钟 | 每日 + Release |

### 2.2 单元测试规范 (Unit Tests)

**后端 (Python/pytest)**：
```python
# 文件命名: test_<module>.py
# 函数命名: test_<function>_<scenario>_<expected>

def test_calculate_credits_sufficient_balance_returns_success():
    """当余额充足时，计算 Credits 应返回成功。"""
    # Arrange
    account = CreditAccount(balance=1000)
    
    # Act
    result = calculate_credits(account, amount=500)
    
    # Assert
    assert result.success is True
    assert result.remaining == 500
```

**前端 (TypeScript/Vitest)**：
```typescript
// 文件命名: <component>.test.tsx
// 描述命名: describe('<Component>') + it('should...')

describe('BalanceCard', () => {
  it('should display formatted balance with currency symbol', () => {
    // Arrange
    render(<BalanceCard balance={1234.56} currency="CNY" />)
    
    // Assert
    expect(screen.getByText('¥1,234.56')).toBeInTheDocument()
  })
})
```

### 2.3 集成测试规范 (Integration Tests)

**后端 API 集成测试**：
```python
@pytest.mark.integration
async def test_create_book_with_valid_file_returns_201(
    client: AsyncClient,
    auth_headers: dict,
    sample_pdf: bytes
):
    """上传有效文件应返回 201 Created。"""
    # Arrange
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    
    # Act
    response = await client.post(
        "/api/v1/books/upload_init",
        headers=auth_headers,
        files=files
    )
    
    # Assert
    assert response.status_code == 201
    assert "id" in response.json()
```

**数据库集成测试**：
- 使用 `testcontainers` 启动临时 PostgreSQL
- 每个测试用例使用独立事务并回滚
- RLS 策略测试需要设置 `app.user_id`

### 2.4 E2E 测试规范 (End-to-End Tests)

**使用 Playwright**：
```typescript
// e2e/book-upload.spec.ts
test('user can upload a book and see it in library', async ({ page }) => {
  // Login
  await page.goto('/login')
  await page.fill('[data-testid="email-input"]', 'test@example.com')
  // ...
  
  // Upload book
  await page.goto('/library')
  await page.click('[data-testid="upload-button"]')
  await page.setInputFiles('input[type="file"]', 'fixtures/sample.epub')
  
  // Verify
  await expect(page.locator('[data-testid="book-card"]')).toBeVisible()
})
```

**E2E 冒烟测试清单**（必须通过）：
- [ ] 用户登录/注销流程
- [ ] 书籍上传 + 书架显示
- [ ] 阅读器打开 + 进度保存
- [ ] 笔记创建 + PowerSync 同步
- [ ] AI 对话 SSE 流式响应
- [ ] 支付流程（测试模式）

---

## 3. 覆盖率要求 (Coverage Requirements)

### 3.1 覆盖率门禁

| 指标 | 最低要求 | 目标 | 说明 |
|:-----|:--------|:-----|:-----|
| **总覆盖率** | ≥ 85% | 90% | 整个代码库 |
| **改动文件覆盖率** | ≥ 80% | 90% | 本次 PR 修改的文件 |
| **新增代码覆盖率** | ≥ 90% | 95% | 本次 PR 新增的代码 |
| **关键路径覆盖率** | 100% | 100% | 支付、认证、数据删除 |

### 3.2 关键路径定义

以下模块必须 100% 覆盖：
- `app/services/billing/` - 计费与支付
- `app/services/auth/` - 认证与授权
- `app/services/books/delete.py` - 书籍删除逻辑
- `app/services/credits/` - Credits 扣费逻辑

### 3.3 覆盖率排除

以下文件可排除覆盖率统计：
```ini
# .coveragerc
[run]
omit =
    */migrations/*
    */tests/*
    */__init__.py
    */config.py
    */main.py
```

---

## 4. 质量门禁 (Quality Gates)

### 4.1 PR 合并条件

所有 PR 必须满足以下条件才能合并：

| 检查项 | 要求 | 自动化 |
|:-------|:----|:-------|
| CI 流水线 | 全部通过 ✅ | GitHub Actions |
| 代码审查 | ≥ 1 Approval | GitHub |
| 覆盖率 | ≥ 85% | Codecov |
| Lint | 0 Error, 0 Warning | Ruff/ESLint |
| Type Check | 0 Error | MyPy/TypeScript |
| 合约测试 | 全部通过 | Pact/OpenAPI |
| 安全扫描 | 无 High/Critical | Snyk/Trivy |

### 4.2 分支保护规则

```yaml
# main 分支
- Require pull request reviews: 1
- Require status checks to pass: true
- Required checks:
  - lint
  - test
  - build
  - contract-test
- Require branches to be up to date: true
- Restrict who can push: [maintainers]
```

### 4.3 Commit 规范

遵循 Conventional Commits：
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Type 类型**：
| Type | 说明 |
|:-----|:-----|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（无功能变化） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |

---

## 5. 合约测试 (Contract Testing)

### 5.1 OpenAPI 契约验证

```yaml
# 验证实现与契约一致
- name: Validate API Contract
  run: |
    # 生成实际 OpenAPI spec
    python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > actual.json
    
    # 对比契约文件
    diff contracts/api/v1/openapi.yaml actual.json
```

### 5.2 PowerSync Sync Rules 测试

```typescript
// tests/sync-rules.test.ts
describe('PowerSync Sync Rules', () => {
  it('should only sync books belonging to current user', async () => {
    // 创建两个用户的书籍
    const userA_book = await createBook({ userId: 'user-a', title: 'Book A' })
    const userB_book = await createBook({ userId: 'user-b', title: 'Book B' })
    
    // 以 user-a 身份同步
    const syncedBooks = await syncWithUser('user-a')
    
    // 验证只能看到自己的书
    expect(syncedBooks).toContainEqual(expect.objectContaining({ id: userA_book.id }))
    expect(syncedBooks).not.toContainEqual(expect.objectContaining({ id: userB_book.id }))
  })
})
```

### 5.3 AI 模块合约测试

```python
# tests/contract/test_ai_contract.py

@pytest.mark.contract
async def test_ai_conversation_idempotency(client, auth_headers):
    """幂等键重放应返回相同结果。"""
    idempo_key = str(uuid4())
    body = {"title": "Test", "first_message": {"role": "user", "text": "Hello"}}
    
    # 第一次请求
    r1 = await client.post(
        "/api/v1/ai/conversations",
        json=body,
        headers={**auth_headers, "Idempotency-Key": idempo_key}
    )
    assert r1.status_code == 201
    
    # 重放请求
    r2 = await client.post(
        "/api/v1/ai/conversations",
        json=body,
        headers={**auth_headers, "Idempotency-Key": idempo_key}
    )
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]

@pytest.mark.contract
async def test_ai_version_conflict(client, auth_headers):
    """版本冲突应返回 409。"""
    # 创建会话
    conv = await create_conversation(client, auth_headers)
    
    # 使用错误的 ETag
    response = await client.patch(
        f"/api/v1/ai/conversations/{conv['id']}",
        json={"title": "New Title"},
        headers={**auth_headers, "If-Match": '"wrong-etag"'}
    )
    assert response.status_code == 409

@pytest.mark.contract
async def test_ai_sse_streaming(client, auth_headers):
    """SSE 流式响应应包含 meta/delta/done 事件。"""
    conv = await create_conversation(client, auth_headers)
    
    async with client.stream(
        "POST",
        f"/api/v1/ai/conversations/{conv['id']}/messages",
        json={"message": {"role": "user", "text": "Hello"}, "streaming": True},
        headers=auth_headers
    ) as response:
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
        
        event_types = [e["type"] for e in events]
        assert "meta" in event_types
        assert "delta" in event_types
        assert "done" in event_types
```

### 5.4 RLS 隔离测试

```python
@pytest.mark.contract
async def test_rls_user_isolation(db_session):
    """RLS 应确保用户只能访问自己的数据。"""
    # 创建两个用户的数据
    await db_session.execute(
        "SET LOCAL app.user_id = 'user-a';"
    )
    await db_session.execute(
        "INSERT INTO ai_conversations (id, user_id, title) VALUES ('conv-a', 'user-a', 'A');"
    )
    
    await db_session.execute(
        "SET LOCAL app.user_id = 'user-b';"
    )
    await db_session.execute(
        "INSERT INTO ai_conversations (id, user_id, title) VALUES ('conv-b', 'user-b', 'B');"
    )
    
    # 验证 user-a 只能看到自己的会话
    await db_session.execute("SET LOCAL app.user_id = 'user-a';")
    result = await db_session.execute("SELECT * FROM ai_conversations;")
    rows = result.fetchall()
    
    assert len(rows) == 1
    assert rows[0].id == 'conv-a'
```

---

## 6. 测试环境 (Test Environments)

### 6.1 环境矩阵

| 环境 | 用途 | 数据库 | 部署方式 |
|:-----|:----|:-------|:---------|
| **Local** | 开发调试 | SQLite/PostgreSQL | docker compose |
| **CI** | 自动化测试 | testcontainers | GitHub Actions |
| **Staging** | 集成验证 | PostgreSQL (独立) | docker compose |
| **Production** | 线上服务 | PostgreSQL (主备) | Kubernetes |

### 6.2 测试数据管理

```python
# conftest.py
@pytest.fixture
async def test_db():
    """创建测试数据库连接，每个测试使用独立事务。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()  # 自动回滚

@pytest.fixture
def sample_user(test_db):
    """创建测试用户。"""
    return User(
        id=uuid4(),
        email="test@example.com",
        display_name="Test User"
    )
```

---

## 7. 监控与告警 (Monitoring & Alerts)

### 7.1 CI 失败告警

| 告警级别 | 触发条件 | 通知渠道 |
|:---------|:---------|:---------|
| **P1 Critical** | main 分支 CI 失败 | Slack + 邮件 + PagerDuty |
| **P2 High** | PR CI 连续失败 3 次 | Slack + 邮件 |
| **P3 Medium** | 覆盖率下降 > 5% | Slack |
| **P4 Low** | Lint 警告增加 | Slack (静默) |

### 7.2 测试报告

- **单元测试报告**：JUnit XML → GitHub Actions Summary
- **覆盖率报告**：Codecov → PR Comment
- **E2E 测试报告**：Playwright HTML Report → Artifacts

---

## 8. 持续改进 (Continuous Improvement)

### 8.1 测试债务追踪

使用 `@pytest.mark.skip(reason="TODO: ...")` 标记待完善的测试：
```python
@pytest.mark.skip(reason="TODO: 等待 OCR 服务 Mock 完成")
def test_ocr_processing():
    pass
```

每月 Review 跳过的测试，制定修复计划。

### 8.2 Flaky Test 处理

1. 标记为 `@pytest.mark.flaky(reruns=3)`
2. 记录到 Flaky Test Backlog
3. 每周 Review 并修复

### 8.3 测试性能优化

- **并行执行**：`pytest -n auto`
- **测试分片**：CI 中按模块分片执行
- **缓存依赖**：使用 GitHub Actions Cache

---

## 附录 A: CI 配置示例

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy app/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=app --cov-fail-under=85

  contract-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest -m contract
```

---

## 附录 B: 相关文档链接

- **00 - AI 编码宪法**：测试规范与代码标准
- **05 - API 契约**：OpenAPI 规范定义
- **07 - DevOps 手册**：部署与运维指南
- **08 - 进度仪表盘**：变更日志与待测试项
