# 02 - 功能规格与垂直切片 (Functional Specifications PRD)

> **版本**：v2.1 (App-First Edition)
> **定位**：产品功能需求文档（PRD），定义各功能模块的实现规格与 App-First 架构约束。

## 1. 核心功能概览
- User & Auth（登录/注册/JWT）
- Books & Shelves（上传/列表/OCR 触发/书架）
- Reader Core（阅读器与 PowerSync 进度同步）
- Notes & Highlights（笔记/高亮/标签/搜索）
- AI Knowledge Engine（RAG 对话/流式输出）
- Billing & Account（充值/配额/只读锁逻辑）

说明：接口定义以 05 号文档（API 契约）为准；数据库结构以 04 号文档（DB）为准。响应格式以《00_AI_Coding_Constitution_and_Rules.md》的错误码 Schema 为准；成功响应以 05 契约为准（通常为 `{ data: ... }`）。

### 1.1 App-First 实施原则

1. **数据总线**：所有业务数据必须遵循 `UI → SQLite (PowerSync SDK) → PowerSync Service → PostgreSQL` 的闭环。前端组件禁止直接依赖 REST API 渲染。
2. **本地优先写入**：CUD 操作通过 PowerSync Repository 写入本地 SQLite 并由 SDK 自动上传，REST API 仅保留鉴权、计费、AI SSE、上传初始化等场景。
3. **Feature Flag**：`APP_FIRST_ENABLED` 控制 PowerSync Provider 注入（已启用）。
4. **冲突策略**：阅读进度使用 LWW，笔记/高亮采用 Conflict Copy，书架/设置字段按列合并。
5. **端差异化**：
  * Mobile：通过 `capacitor-community/sqlite` 调用原生 SQLite 引擎。
  * Web：通过 `sqlite-wasm` + OPFS 提供一致体验。
6. **观测**：PowerSync Service 必须接入 Prometheus/Grafana 监控。

### 1.2 App-First 用户故事 (App-First User Stories)

> **核心价值**：极致的响应速度与无缝的离线体验。

#### Story 1: 无网环境下的沉浸阅读
**场景**：用户在飞往纽约的航班上（无网络）。
- **行为**：用户打开雅典娜 App，**零延迟**进入书架，打开《Thinking Fast and Slow》。
- **操作**：用户阅读了 50 页，并添加了 3 条笔记和 5 个高亮。
- **系统**：所有数据直接写入本地 SQLite，界面无任何 Loading。
- **结果**：飞机降落连接 Wi-Fi 后，PowerSync 后台自动静默同步，进度和笔记出现在用户的 iPad 上。

#### Story 2: 多端冲突的优雅处理
**场景**：用户同时在 iPhone（离线）和 Web（在线）上修改了同一条笔记。
- **行为**：
  1. iPhone 上修改笔记："这是一本好书。" -> "这是一本**绝妙的**书。"（离线保存）
  2. Web 上修改笔记："这是一本好书。" -> "这是一本**充满智慧的**书。"（在线保存）
- **系统**：当 iPhone 恢复上线时，PowerSync 检测到版本冲突，不覆盖任何一方，而是创建一个 "Conflict Copy"。
- **结果**：用户在笔记列表看到两条笔记，并附带 "⚠️ 版本冲突" 标记，用户点击 "合并"，手动整合成 "这是一本**绝妙且充满智慧的**书。"

#### Story 3: 秒级启动与全局搜索
**场景**：用户拥有 10,000 条笔记。
- **行为**：用户在搜索框输入 "经济学"。
- **系统**：使用 SQLite FTS5 本地全文检索，**10ms 内** 返回结果，无需网络请求。
- **结果**：结果即时展示，点击任意搜索结果直接跳转到书籍对应段落，体验如原生 App 般丝滑。

#### Story 4: 跨设备无缝接力
**场景**：用户在通勤地铁上使用手机阅读。
- **行为**：用户看到第 125 页，地铁到站，用户锁屏手机。
- **系统**：PowerSync 在后台（或下次打开时）极速上传最后阅读位置 CFI。
- **结果**：用户回到家打开 iPad，书籍封面显示进度条已更新，点击直接跳转到第 125 页，无需手动刷新。


## 2. 垂直切片详情（Vertical Slices）

### 2.1 User & Auth

#### A. 数据库模型（Database Schema）
- `users`：
  - 字段：`id (UUID, PK)`、`email (LOWERCASE, UNIQUE)`、`display_name (TEXT)`、`avatar_url (TEXT, Nullable)`、`is_active (BOOL)`、`language (TEXT)`、`timezone (TEXT)`、`membership_expire_at (TIMESTAMPTZ)`、`monthly_gift_reset_at (TIMESTAMPTZ)`、`free_ocr_usage (INT DEFAULT 0)`、`updated_at (TIMESTAMPTZ)`。
  - 权限字段：`user_id` 不适用（用户主表）；RLS 依赖会话变量 `app.user_id`。
- `user_sessions`：
  - 字段：`id (UUID, PK)`、`user_id (UUID, FK users.id)`、`revoked (BOOL)`、`created_at (TIMESTAMPTZ)`。
  - 关系：`users (1) — (N) user_sessions`。
- `user_oauth_accounts` 🆕：
  - 字段：`id (UUID, PK)`、`user_id (UUID, FK users.id)`、`provider (VARCHAR(20))`、`provider_user_id (TEXT)`、`provider_email (TEXT, Nullable)`、`access_token (TEXT, Encrypted)`、`refresh_token (TEXT, Nullable, Encrypted)`、`token_expires_at (TIMESTAMPTZ, Nullable)`、`raw_profile (JSONB)`、`created_at (TIMESTAMPTZ)`、`updated_at (TIMESTAMPTZ)`。
  - 约束：UNIQUE (`provider`, `provider_user_id`)；UNIQUE (`user_id`, `provider`)。
  - 关系：`users (1) — (N) user_oauth_accounts`。
  - **Provider 枚举**：`wechat`、`google`、`microsoft`、`apple`。

#### B. 后端逻辑与 API 契约（Backend & Contract）

##### B.1 邮箱验证码登录
- 端点：`POST /auth/email/send-code`、`POST /auth/email/verify-code`、`POST /auth/refresh`、`POST /auth/logout`、`GET /auth/sessions`、`GET /auth/me`。
- **新增端点**：`DELETE /auth/sessions/{id}` (踢出指定设备)。
- 规则：成功登录后创建 `user_sessions` 并签发 `access_token/refresh_token`；受保护端点需 `Authorization: Bearer`。

##### B.2 第三方 OAuth 登录 🆕

> **支持平台**：微信（WeChat）、Google、Microsoft、Apple

**OAuth 认证端点**：
| 端点 | 方法 | 说明 |
|:-----|:----|:-----|
| `/auth/oauth/{provider}/authorize` | GET | 获取 OAuth 授权 URL（重定向到第三方） |
| `/auth/oauth/{provider}/callback` | GET | OAuth 回调端点（处理授权码） |
| `/auth/oauth/{provider}/token` | POST | 移动端用：直接交换 OAuth Token |

**支持的 Provider 枚举**：
```typescript
type OAuthProvider = 'wechat' | 'google' | 'microsoft' | 'apple';
```

**各平台特殊处理**：
| 平台 | 特殊配置 | 说明 |
|:-----|:--------|:-----|
| **微信** | 需区分 App/Web | App 使用 `open.weixin.qq.com`，Web 使用 `api.weixin.qq.com` |
| **Google** | ID Token 验证 | 移动端可直接发送 Google ID Token |
| **Microsoft** | Azure AD B2C | 支持个人账号和工作账号 |
| **Apple** | Sign in with Apple | iOS 必须支持（App Store 审核要求）|

**OAuth 登录流程**：
```
┌─────────┐      ┌─────────────┐      ┌──────────────┐
│ 客户端   │ ──→  │ /authorize  │ ──→  │ 第三方 OAuth │
│         │      │ 获取授权 URL │      │ 授权页面     │
└─────────┘      └─────────────┘      └──────┬───────┘
                                             │
                                             ↓ 用户授权
┌─────────┐      ┌─────────────┐      ┌──────────────┐
│ 客户端   │ ←──  │ /callback   │ ←──  │ 回调 + code  │
│ 获取 JWT│      │ 验证 + 签发  │      │              │
└─────────┘      └─────────────┘      └──────────────┘
```

**移动端 Token 交换**（适用于 Google/Apple 原生 SDK）：
```json
POST /auth/oauth/google/token
{
  "id_token": "<Google ID Token from native SDK>",
  "device_id": "uuid"
}

Response 200:
{
  "access_token": "...",
  "refresh_token": "...",
  "user": { "id": "...", "email": "...", "is_new": true }
}
```

**账号绑定规则**：
1. **首次登录**：自动创建账号，OAuth ID 作为主标识
2. **邮箱匹配**：如果 OAuth 邮箱已注册，自动绑定到现有账号
3. **多渠道绑定**：同一账号可绑定多个 OAuth 渠道
4. **解绑限制**：至少保留一种登录方式（邮箱或 OAuth）

#### F. 前端组件契约（Frontend Contract）
- 组件：`AuthForm`
  - Props：
    ```ts
    interface AuthFormProps {
      onSuccess: (tokens: { accessToken: string; refreshToken: string }) => void
      onError: (message: string) => void
      /** 当触发 429 时调用，UI 应冻结发送按钮并显示倒计时 */
      onRateLimit: (retryAfterSeconds: number) => void
    }
    ```
  - 交互：输入邮箱→发送验证码→**弹出"邮箱确认"对话框**→输入验证码→验证→成功回调并跳转；失败展示错误。
  - **防输错机制 (Heads-up Confirmation)**：
    - 用户点击"获取验证码"后，**不立即发送**。
    - UI 弹出模态框，背景变暗，以**超大字号**显示刚才输入的邮箱 `bob@exampl.com`。
    - 询问："我们将向此邮箱发送验证码，请确认拼写无误？"
    - 按钮：[写错了，去修改] [确认无误，发送]
    - *设计目的*：增加一步"有益摩擦"，强制用户检查拼写，防止僵尸号产生。

#### D. 业务规则（Business Rules）
- 所有 POST 必须携带 `Idempotency-Key`。
- 所有 PATCH 必须携带 `If-Match`。
- 所有 PATCH 必须携带 `If-Match`。
- 所有 GET 建议携带 `If-None-Match`（弱缓存）。
- **免注册机制 (Auto-Registration)**：
  - 用户输入邮箱验证码通过后，若数据库中不存在该邮箱，则自动创建新用户。
  - **风险提示**：前端必须在登录页显式声明 "登录即代表您同意《服务条款》与《隐私协议》"。
- **频率限制 (Rate Limiting)**：
  - 发送验证码：单 IP/单邮箱 60秒内 1 次，1小时内 10 次。
  - 验证失败：连续 5 次失败锁定 15 分钟。

### ✔ Definition of Done (DoD)
- [ ] API 契约已更新并通过合规校验
- [ ] RLS 测试覆盖登录态与多租户隔离
- [ ] ETag/Idempotency 规范在前后端一致
- [ ] 前端组件契约与错误码映射对齐
- [ ] 数据库迁移脚本（如会话表变更）齐备
- [ ] 单元/集成测试覆盖登录/刷新/注销

---

### 2.2 Books & Shelves

#### A. 数据库模型（Database Schema）
- `books`：
  - 字段：`id (UUID, PK)`、`user_id (UUID, FK)`、`title (TEXT)`、`author (TEXT)`、`language (TEXT)`、`original_format (TEXT)`、`minio_key (TEXT)`、`size (BIGINT)`、`has_text_layer (BOOL)`、`text_layer_confidence (FLOAT)`、`source_etag (TEXT)`、`meta (JSONB)`、`digitalize_report_key (TEXT)`、`cover_image_key (TEXT)`、`converted_epub_key (TEXT)`、`updated_at (TIMESTAMPTZ)`。
  - 权限字段：`user_id`（RLS）。
  - **去重相关字段 (SHA256)**：
    - `content_sha256 (VARCHAR(64))`：文件内容 SHA256 哈希，用于全局去重
    - `storage_ref_count (INTEGER, DEFAULT 1)`：存储引用计数，初始值 1 代表原书自己
    - `canonical_book_id (UUID, FK books.id)`：去重引用指向的原始书籍 ID，非空表示是引用书
    - `deleted_at (TIMESTAMPTZ)`：软删除时间戳，非空表示已软删除
  - **OCR 相关字段**：
    - `ocr_status (VARCHAR(20))`：OCR 状态 (NULL/pending/processing/completed/failed)
    - `ocr_requested_at (TIMESTAMPTZ)`：用户请求 OCR 的时间
    - `ocr_pdf_key (TEXT)`：OCR 产出的**双层 PDF**（Dual-Layer PDF）文件在 MinIO 中的 Key（废弃原 JSON Sidecar 方案）
    - `vector_indexed_at (TIMESTAMPTZ)`：向量索引完成时间
  - **元数据字段**：
    - `metadata_confirmed (BOOLEAN, DEFAULT FALSE)`：用户是否已确认元数据
    - `metadata_confirmed_at (TIMESTAMPTZ)`：元数据确认时间
  - 其他字段说明：
    - `cover_image_key`：封面图片在 MinIO 中的存储路径（WebP 格式，400×600）
    - `converted_epub_key`：Calibre 转换后的 EPUB 路径（标记已转换）
- `shelves`：
  - 字段：`id (UUID, PK)`、`user_id (UUID, FK users.id)`、`name (TEXT)`、`parent_shelf_id (UUID, NULLABLE, FK shelves.id)`、`updated_at (TIMESTAMPTZ)`、`version (INT)`。
  - 关系：`users (1) — (N) shelves`；支持层级结构（父子架）。
- `shelf_books`（关联表）：
  - 字段：`id (UUID, PK)`、`book_id (UUID, FK books.id)`、`shelf_id (UUID, FK shelves.id)`、`user_id (UUID, FK users.id)`、`sort_order (INT)`、`added_at (TIMESTAMPTZ)`。
  - 约束：唯一约束（`book_id`, `shelf_id`）；`ON CONFLICT DO NOTHING` 用于去重。
> Status: Backend Implemented（Books 上传、转换、封面提取、元数据提取）；Shelves = Implemented。

#### B. 后端逻辑与 API 契约（Backend & Contract）
- 端点：`POST /books/upload_init`、`POST /books/upload_complete`、`GET /books`、`GET /books/{id}`、`DELETE /books/{id}`。
- 规则：
  - 上传前校验配额；完成后落库与索引同步；支持 `Idempotency-Key`。
  - @if (`user_stats.is_readonly`)：
    - `POST /books/upload_init` → 403 `quota_exceeded`
    - Shelves 全量 CRUD 禁止（`POST/PUT/PATCH/DELETE` 返回 403）

#### B.1 书籍上传与处理流水线（Upload & Processing Pipeline）

**完整流程图**：
```
前端选择文件
    ↓
计算 SHA256 指纹 (content_sha256)
    ↓
POST /books/upload_init { content_sha256, filename, size }
    ↓
PUT 直传 MinIO (If distinct)
    ↓
POST /books/upload_complete
    ↓
Server Processing (Calibre, etc.)
    ↓
Server Updates `books` table (PostgreSQL)
    ↓
PowerSync Pushes update to Client `books` table (SQLite)
    ↓
UI Reacts to SQLite change (Book appears in Library)
```

#### B.1.1 SHA256 全局去重机制（ADR-008）

**核心原则**：
1. **存储去重**：相同文件只存储一份，通过引用计数管理
2. **OCR 复用**：相同文件只需一次真实 OCR，后续用户秒级复用
3. **智能删除**：区分公共数据和私人数据，实现软删除/硬删除分层

**数据库字段**：
```sql
-- 核心字段定义
content_sha256 VARCHAR(64)     -- 文件内容 SHA256 哈希
storage_ref_count INTEGER      -- 存储引用计数（初始值 1）
canonical_book_id UUID         -- 去重引用指向的原始书籍 ID
deleted_at TIMESTAMPTZ         -- 软删除时间戳

-- 部分索引
CREATE INDEX idx_books_content_sha256 ON books(content_sha256) 
    WHERE content_sha256 IS NOT NULL;
```

**去重检查流程**：
```
POST /books/upload_init
    ↓
检查 content_sha256 是否存在
    ↓
┌─────────────────────────────┬──────────────────────────────────┐
│ 无命中                       │ 有命中                            │
├─────────────────────────────┼──────────────────────────────────┤
│ dedup_available: false      │ 检查是否是当前用户的书             │
│ 返回 presigned URL          │ ├─ 是 → dedup_hit: "own"          │
│ 继续正常上传流程              │ │     返回已有书籍 ID             │
│                             │ └─ 否 → dedup_available: true     │
│                             │         canonical_id: 原书 ID     │
└─────────────────────────────┴──────────────────────────────────┘
```

**秒传接口**：
```
POST /api/v1/books/dedup_reference
├─ 请求体：
│   {
│     "filename": "小说的艺术.pdf",
│     "content_sha256": "6f4c24abd60a55d3...",
│     "size": 12345678
│   }
├─ 处理逻辑：
│   1. 查找 canonical_book（原始书籍）
│   2. 增加原书 storage_ref_count
│   3. 创建新书籍记录，设置 canonical_book_id
│   4. 复制原书的：minio_key, cover_image_key, meta
│   5. 如果原书已 OCR：
│      - 设置 has_text_layer = true, text_layer_confidence = 0.1
│      - 用户可点击 OCR 触发"假 OCR"复用
├─ 响应 201：
│   {
│     "id": "new-book-uuid",
│     "dedup_type": "global",
│     "canonical_book_id": "original-book-uuid",
│     "has_ocr": true
│   }
└─ 响应 404：CANONICAL_NOT_FOUND (原书不存在)
```

**引用计数规则**：
| 操作 | storage_ref_count 变化 |
|-----|----------------------|
| 原书上传完成 | 初始值 = 1（代表自己） |
| 秒传创建引用书 | 原书 +1 |
| 引用书删除 | 原书 -1 |
| 判断是否有引用 | `> 1` 表示有其他用户共享 |

#### B.1.2 书籍删除策略（Soft Delete & Hard Delete）

**删除决策流程**：
```
用户删除书籍
    ↓
判断书籍类型
    ├─ 引用书 (canonical_book_id IS NOT NULL)
    │   ├─ 删除用户私有数据（笔记/进度/书架）
    │   ├─ 物理删除书籍记录
    │   ├─ 减少原书 storage_ref_count
    │   └─ 检查原书是否需要清理
    │       └─ 如果原书已软删除 + ref_count ≤ 1 → 物理删除原书
    │
    └─ 原书 (canonical_book_id IS NULL)
        ├─ 删除用户私有数据
        └─ 检查引用计数
            ├─ ref_count > 1 → 软删除
            │   └─ 设置 deleted_at，保留公共数据
            └─ ref_count ≤ 1 → 硬删除
                ├─ 删除 MinIO 文件（PDF/封面/双层 PDF）
                ├─ 删除向量索引
                └─ 物理删除数据库记录
```

**公共数据 vs 私人数据**：
| 数据类型 | 所有者 | 软删除时 | 硬删除时 |
|---------|-------|---------|---------|
| MinIO/EPUB 文件 | 共享 | ✅ 保留 | ❌ 删除 |
| 封面图片 | 共享 | ✅ 保留 | ❌ 删除 |
| OCR 双层 PDF | 共享 | ✅ 保留 | ❌ 删除 |
| 向量索引 | 共享 | ✅ 保留 | ❌ 删除 |
| 笔记/高亮 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |
| 阅读进度 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |
| 书架关联 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |

#### B.1.3 最近删除功能（Recently Deleted）

**功能概述**：
- 用户删除书籍后，书籍进入"最近删除"状态（软删除）
- 书籍保留 30 天，期间可恢复
- 超过 30 天后由后台任务自动清理

**页面入口**：侧边栏 → 最近删除

**页面功能**：
| 功能 | 操作 | 业务逻辑 |
|-----|------|---------|
| 查看已删除书籍 | 显示列表 | 查询 `deleted_at IS NOT NULL` |
| 恢复书籍 | 单选/批量 | 设置 `deleted_at = NULL` |
| 永久删除 | 单选/批量 | 见下方详细逻辑 |
| 清空全部 | 批量 | 对所有书籍执行永久删除 |

**⚠️ 永久删除业务逻辑（仅删除私人数据）**：

> **重要决策**：永久删除**不会**删除共享资源（MinIO 文件、OCR 结果、向量索引），  
> 因为其他用户可能通过秒传引用了相同文件。只删除当前用户的私人数据。

```
用户点击"永久删除"
    ↓
1. 删除私人数据（立即执行）
    ├─ notes: DELETE WHERE book_id = :id AND user_id = :uid
    ├─ highlights: DELETE WHERE book_id = :id AND user_id = :uid
    ├─ bookmarks: DELETE WHERE book_id = :id AND user_id = :uid
    ├─ book_position: DELETE WHERE book_id = :id AND user_id = :uid
    ├─ reading_time_log: DELETE WHERE book_id = :id AND user_id = :uid
    └─ shelf_books: DELETE WHERE book_id = :id AND user_id = :uid
    ↓
2. 更新书籍记录
    └─ books: 物理删除记录 (DELETE WHERE id = :id)
    ↓
3. 更新引用计数（如果是引用书）
    └─ 原书 storage_ref_count -= 1
    ↓
4. 不执行的操作（共享资源保护）
    ├─ ❌ 不删除 MinIO 文件 (minio_key)
    ├─ ❌ 不删除封面 (cover_image_key)
    ├─ ❌ 不删除 OCR 双层 PDF (ocr_pdf_key)
    └─ ❌ 不删除向量索引 (PostgreSQL pgvector)
```

**共享资源清理规则**（由后台定时任务执行）：
```sql
-- 每日凌晨执行，清理孤立的共享资源
DELETE FROM books_storage_cleanup_queue
WHERE content_sha256 IN (
    SELECT content_sha256 
    FROM books 
    WHERE deleted_at < NOW() - INTERVAL '30 days'
    GROUP BY content_sha256
    HAVING COUNT(*) = SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END)
);
-- 即：只有当该 SHA256 的所有书籍都已软删除超过30天，才清理存储
```

**API 端点**：
| 端点 | 方法 | 说明 |
|-----|------|------|
| `/api/v1/books/deleted` | GET | 获取已删除书籍列表 |
| `/api/v1/books/{id}/restore` | POST | 恢复单本书籍 |
| `/api/v1/books/restore` | POST | 批量恢复 `{ids: []}` |
| `/api/v1/books/{id}/permanent` | DELETE | 永久删除单本 |
| `/api/v1/books/permanent` | DELETE | 批量永久删除 `{ids: []}` |

**前端实现要点**：
1. 通过 PowerSync 查询 `SELECT * FROM books WHERE deleted_at IS NOT NULL`
2. 恢复操作：PowerSync UPDATE `deleted_at = NULL`
3. 永久删除：**必须调用 REST API**（非 PowerSync），因为需要处理私人数据和引用计数

#### B.2 OCR 与向量索引触发机制（⚠️ 重要架构决策）

**核心原则**：
1. **向量索引是免费服务**，对所有书籍自动执行
2. **OCR 是收费/限额服务**，由用户主动触发
3. 图片型 PDF 未经 OCR 前，无法生成向量索引
4. **OCR 结果可复用**：相同文件只需一次真实 OCR（ADR-008）

**书籍类型判断**：
| 类型 | 判断条件 | 后续处理 |
|-----|---------|---------|
| 文字型 EPUB | `original_format = 'epub'` | 直接向量索引 |
| 文字型 PDF | 初检有文字层 (`has_text_layer = true, text_layer_confidence >= 0.8`) | 直接向量索引 |
| 图片型 PDF | 初检无文字层 (`has_text_layer = true, text_layer_confidence < 0.8`) | 等待用户触发 OCR |
| 转换后 EPUB | MOBI/AZW3/FB2 转换而来 | 直接向量索引 |
| 秒传引用书 | `canonical_book_id IS NOT NULL` | 继承原书状态，可触发假 OCR |

**is_image_based 判断逻辑**（前端用于显示 OCR 按钮）：
```python
# 需要显示 OCR 按钮的条件
is_image_based = (
    (has_text_layer == True AND text_layer_confidence < 0.8)  # 图片型 PDF
    OR ocr_status == 'completed'  # 已完成 OCR 的书籍（可能需要重做）
)
```

**图片型 PDF 处理流程**：
```
初检发现图片型 PDF (has_text_layer = true, text_layer_confidence < 0.8)
    ↓
PowerSync Service 推送 `ocr_detection` 事件到客户端
    ↓
前端弹出提示对话框：
┌──────────────────────────────────────────────────────────────┐
│  📖 书籍初检完成                                              │
│                                                              │
│  您上传的《经济学原理》经过雅典娜初步检查，此书为图片形式的      │
│  PDF 电子书。为了获得更好的阅读、笔记以及 AI 提问体验，        │
│  我们建议您对此书进行图片转文本（OCR）服务。                   │
│                                                              │
│  [稍后再处理]                            [🚀 马上转换]        │
└──────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────┬───────────────────────────────────────┐
│ 用户点击"马上转换"   │ 用户点击"稍后再处理"                    │
├─────────────────────┼───────────────────────────────────────┤
│ POST /books/{id}/ocr│ 关闭对话框                             │
│       ↓             │       ↓                               │
│ 检查用户 OCR 配额    │ 书籍卡片 ⋮ 菜单显示 "OCR 服务" 选项    │
│       ↓             │       ↓                               │
│ 任务进入队列         │ 用户随时可从菜单触发 OCR               │
│       ↓             │                                       │
│ 前端提示：           │                                       │
│ "OCR 已进入排队，    │                                       │
│  预计 XX 分钟完成，  │                                       │
│  现在可继续阅读，    │                                       │
│  但暂无法做笔记和    │                                       │
│  使用 AI 服务"      │                                       │
│       ↓             │                                       │
│ OCR 完成后自动触发   │                                       │
│ 向量索引             │                                       │
└─────────────────────┴───────────────────────────────────────┘
```

**API 端点**：
```
POST /api/v1/books/{book_id}/ocr
├─ 权限：用户已登录
├─ 前置检查：
│   ├─ 书籍存在且属于当前用户
│   ├─ 书籍是图片型 (has_text_layer = true AND text_layer_confidence < 0.8)
│   │   或 has_text_layer = false (未检测)
│   └─ 用户 OCR 配额充足 (阶梯计费规则)
├─ OCR 复用检查：
│   SELECT id, ocr_pdf_key FROM books 
│   WHERE content_sha256 = :sha256 
│   AND ocr_status = 'completed' LIMIT 1
│   ├─ 找到 → 假 OCR，复制双层 PDF Key，秒级完成
│   └─ 未找到 → 真实 OCR (OCRmyPDF + PaddleOCR)，提交 Celery 任务
├─ 响应 200 (假 OCR)：
│   {
│     "status": "instant_completed",
│     "ocr_pdf_key": "books/{user_id}/{book_id}/ocr.pdf",
│     "message": "已复用相同书籍的双层 PDF"
│   }
├─ 响应 200 (真实 OCR)：
│   {
│     "status": "queued",
│     "queue_position": 3,
│     "estimated_minutes": 15
│   }
├─ 响应 403：quota_exceeded (OCR 配额不足)
├─ 响应 400：already_digitalized (confidence >= 0.8，已是文字型)
└─ 响应 400：ocr_max_pages_exceeded (超过 2000 页)
```

**OCR 复用机制（假 OCR）**：
> **商业逻辑（⚠️ 重要）**：
> - 用户**必须**点击 OCR 按钮才能看到 OCR 结果（商业闭环）
> - 即使是复用，也**必须**扣除配额（维护商业公平性）
> - 但不消耗 GPU 算力（降低运营成本）

```
用户点击 OCR 按钮
    ↓
正常配额检查和扣费
    ↓
检查是否可复用（相同 SHA256 已有双层 PDF）
    ├─ 可复用 → 复制双层 PDF 到用户目录，返回 instant_completed
    └─ 不可复用 → 提交 Celery OCR 任务（OCRmyPDF + PaddleOCR），返回 queued
```

> **双层 PDF (Dual-Layer PDF) 技术说明**：
> - **定义**：双层 PDF 包含可见图像层和不可见文字层，前端可直接使用 PDF.js 获取文字内容
> - **优势**：无需维护独立 JSON Sidecar，文字与坐标天然关联，阅读器渲染更简洁
> - **生成**：OCRmyPDF (CLI) 调用 PaddleOCR (识别引擎)，输出自带文字层的 PDF
> - **前端读取**：PDF.js `page.getTextContent()` 直接提取文字，无需额外请求
> - **复用**：双层 PDF 本身可复制到新用户目录，无隐私问题（纯 PDF，无额外元数据）

```sql
-- OCR 状态字段
ocr_status VARCHAR(20) DEFAULT NULL;
-- 可选值: NULL (未检测/文字型), 'pending' (待处理), 'processing' (处理中), 'completed' (已完成), 'failed' (失败)

ocr_requested_at TIMESTAMPTZ;
ocr_pdf_key TEXT;  -- OCR 产出的双层 PDF (Dual-Layer PDF) MinIO Key
vector_indexed_at TIMESTAMPTZ;

-- SHA256 去重相关字段（ADR-008）
content_sha256 VARCHAR(64);
storage_ref_count INTEGER DEFAULT 1;  -- ⚠️ 更新此字段必须使用行级锁 (SELECT FOR UPDATE)
canonical_book_id UUID REFERENCES books(id);
deleted_at TIMESTAMPTZ;

-- 索引
CREATE INDEX idx_books_content_sha256 ON books(content_sha256) WHERE content_sha256 IS NOT NULL;
CREATE INDEX idx_books_canonical_book_id ON books(canonical_book_id) WHERE canonical_book_id IS NOT NULL;
```

**任务链触发规则**：
| 触发条件 | 执行任务 |
|---------|---------|
| 文字型书籍上传完成 | `tasks.index_book_vectors` |
| OCR 任务完成 | `tasks.index_book_vectors` (链式调用) |
| 用户手动重建索引 | `tasks.reindex_book_vectors` (管理员功能) |

#### B.3 元数据确认机制（Metadata Confirmation）

**核心原则**：
1. **所有书籍上传后都需要用户确认元数据**
2. 元数据（书名、作者）会影响 AI 对话的准确性
3. 用户可以选择不填写（私人资料场景），但需明确告知影响

**触发时机**：
- 后台任务 `extract_book_metadata` 完成后
- 无论是否成功提取到元数据，都通知前端弹出确认对话框

**前端交互流程**：
```
元数据提取任务完成
    ↓
PowerSync Service 推送 `metadata_extracted` 事件
    ↓
前端弹出元数据确认对话框（根据提取结果显示不同内容）

┌─────────────────────────────────────────────────────────────────┐
│  📚 请确认书籍信息                                               │
│                                                                 │
│  [情况 A: 成功提取到元数据]                                       │
│  雅典娜已从您上传的文件中提取到以下信息，请确认是否正确：           │
│                                                                 │
│  书籍名称: [经济学原理________________] ← 可编辑                  │
│  作者:     [曼昆____________________] ← 可编辑                   │
│                                                                 │
│  [情况 B: 未提取到元数据]                                         │
│  雅典娜未能从您上传的文件中提取到书籍信息。                        │
│  为了获得更好的 AI 对话体验，建议您填写以下信息：                   │
│                                                                 │
│  书籍名称: [________________________] ← 空，建议填写              │
│  作者:     [________________________] ← 空，可选                  │
│                                                                 │
│  ℹ️ 提示：书籍名称和作者信息将帮助 AI 提供更精准的回答。           │
│      如果这是私人资料而非书籍，可跳过此步骤。                       │
│                                                                 │
│  [跳过]                                          [✓ 确认]        │
└─────────────────────────────────────────────────────────────────┘
```

**API 端点**：
```
PATCH /api/v1/books/{book_id}/metadata
├─ 权限：用户已登录，书籍属于当前用户
├─ 请求体：
│   {
│     "title": "经济学原理",       // 可选
│     "author": "曼昆",            // 可选
│     "confirmed": true            // 标记用户已确认
│   }
├─ 响应 200：
│   {
│     "id": "uuid",
│     "title": "经济学原理",
│     "author": "曼昆",
│     "metadata_confirmed": true,
│     "metadata_version": "sha256:abc123"
│   }
└─ 支持 If-Match 乐观锁
```

**数据库模型更新**：
```sql
metadata_confirmed BOOLEAN DEFAULT FALSE; -- books 表字段
metadata_confirmed_at TIMESTAMPTZ;        -- books 表字段
```

**书籍卡片菜单逻辑**：
```typescript
// BookCard 组件的 ⋮ 下拉菜单
const menuItems = [
  { label: '查看详情', action: 'view' },
  { label: '添加到书架', action: 'shelf' },
  // 编辑元数据选项（始终显示）
  {
    label: '✏️ 编辑书籍信息',
    action: 'edit_metadata',
    description: '修改书籍名称和作者'
  },
  // 仅当 has_text_layer = false 且 ocr_status != 'processing' 时显示
  book.has_text_layer === false && book.ocr_status !== 'processing' && {
    label: '🔤 OCR 服务',
    action: 'ocr',
    description: '将图片转换为可选择文本'
  },
  // 仅当 ocr_status = 'processing' 时显示
  book.ocr_status === 'processing' && {
    label: '⏳ OCR 处理中...',
    disabled: true
  },
  { label: '删除', action: 'delete', danger: true },
].filter(Boolean);
```

**与 AI 对话的关系**：
> ⚠️ **重要**：书籍的 `title` 和 `author` 字段会作为上下文发送给上游 AI 模型。
> 
> 在 AI 对话的系统提示词中，我们会包含：
> ```
> 用户正在阅读的书籍：《{book.title}》，作者：{book.author}
> ```
> 
> 这有助于 AI 模型：
> 1. 理解用户问题的背景上下文
> 2. 提供与书籍内容相关的精准回答
> 3. 避免混淆同名但不同版本的书籍
>
> 如果用户上传的是私人资料（非书籍），可以跳过元数据确认，此时 AI 对话将仅基于文档内容本身。

**元数据提取规则**：
- 标题更新判断条件（满足任一则覆盖）：
  1. 当前标题为空
  2. 当前标题包含下划线 (`_`)
  3. 当前标题以扩展名结尾 (`.epub`, `.pdf`, `.mobi`, `.azw3`)
  4. 当前标题为 `书名-作者名` 格式，而提取的标题更短且不含连字符
- 作者仅在当前为空时更新

**存储策略**：
- 最终 MinIO 中只保留 EPUB 和 PDF 格式
- 非 EPUB/PDF 在 Calibre 转换成功后自动删除原始文件
- `minio_key` 始终指向可阅读文件

**支持格式**：
| 格式 | 处理方式 |
|:---|:---|
| EPUB | 直接存储，提取封面和元数据 |
| PDF | 直接存储，提取封面和元数据 |
| MOBI | Calibre 转换为 EPUB，删除原始文件 |
| AZW3 | Calibre 转换为 EPUB，删除原始文件 |
| FB2 | Calibre 转换为 EPUB，删除原始文件 |

#### F. 前端组件契约（Frontend Contract）
- 组件：`UploadManager`
  - Props：
    ```ts
    interface UploadManagerProps {
      onUploaded?: (book: { id: string; downloadUrl: string }) => void
      onError?: (code: 'quota_exceeded' | 'init_failed' | 'put_failed' | 'complete_failed' | 'unknown') => void
    }
    ```
  - 交互：选择文件→计算指纹→初始化→PUT 上传→完成→回调；403 超限映射到文案键。
  - 状态：`idle | hashing | initializing | uploading | completing | done | error`
- 组件：`ShelfList` / `ShelfEditor`（已实现）。

### ✔ Definition of Done (DoD)
- [x] API 契约覆盖上传 init/complete 与 Shelves CRUD
- [x] 上传幂等与分片重试用例通过
- [x] Calibre 转换流水线实现与测试
- [x] 封面提取与 WebP 优化实现
- [x] 元数据智能提取与标题更新逻辑
- [x] RLS 策略与只读锁拦截测试通过
- [x] 前端上传组件与状态管理对齐
- [x] **SHA256 全局去重机制实现与测试（ADR-008）**
- [x] **秒传接口 dedup_reference 实现**
- [x] **OCR 复用（假 OCR）机制实现**
- [x] **软删除/硬删除分层策略实现**
- [x] **引用计数与删除联动测试通过**
- [ ] Shelves 树形结构前端完善（待实现）

---

### 2.3 Reader Core

#### A. 数据库模型（Database Schema）
- **Core Principle**: **App-First & Local-First**. 
- **Server Database**: `book_position` (PostgreSQL) - Source of Truth for "Last Read Position" across devices.
- **Local Database**: `book_position` (SQLite) - The only DB the UI interacts with directly.
- **Sync**: PowerSync syncs `book_position` (Server) <--> `book_position` (Local). 阅读时长通过 `reading_time_log` 表单独记录。

#### B. 后端逻辑与 API 契约（Backend & Contract）
- **Sync Architecture (PowerSync)**:
  - 后端不提供直接的 Restful API 给阅读器 UI。
  - **Reading Position** 通过 PowerSync 流式写入 PostgreSQL `book_position` 表。
  - **Time Log Sync**: 阅读时长 (`reading_time_log`) 不需要显式调用 API。前端组件将心跳数据写入本地 SQLite，由 PowerSync 后台自动同步至 PostgreSQL。
  
#### F. 前端组件契约（Frontend Contract）
- 组件：`Reader`
  - Props:
    ```ts
    interface ReaderProps {
      bookId: string
      initialLocation?: string // From SQLite
    }
    ```
  - **Interaction**:
    - **Page Turn**: Writes `cfi` to SQLite `book_position` table immediately.
    - **Sync**: PowerSync SDK watches SQLite changes and pushes to server automatically.
    - **Offline**: No extra logic needed; SQLite is always available.
  
### ✔ Definition of Done (DoD)
- [ ] SQLite Schema defined for `book_position`
- [ ] PowerSync Sync Rules configured for `book_position` and `reading_time_log`
- [ ] Reader component reading/writing from/to SQLite
- [ ] Conflict resolution (LWW) verified via PowerSync configuration

---

### 2.4 Notes & Highlights

#### A. 数据库模型（Database Schema）
- `notes`：`id`、`user_id`、`book_id`、`content`、`chapter`、`location`、`pos_offset`、`tsv`、`updated_at`、`version`、`deleted_at`。
- `tags`：`id`、`user_id`、`name`、`updated_at`、`version`、`deleted_at`。
- `note_tags`：连接表，`note_id`、`tag_id`；`ON CONFLICT DO NOTHING`。
- 权限字段：`user_id`；并发字段：`version`。

#### B. 后端逻辑与 API 契约（Backend & Contract）
- **PowerSync Surface**：`download_config` 同步 `notes`, `highlights`, `tags`, `note_tags`, `highlight_tags`；`upload_config` 允许携带 `device_id`, `updated_at`, `is_deleted` 字段的 UPSERT。
- **REST 端点**：`/api/v1/notes/*`, `/api/v1/highlights/*`, `/api/v1/tags/*` 仅保留下列用途：管理员工具、外部集成、PowerSync 失效时的应急回退。
- **一致性规则**：
  - 只读锁依旧通过 RLS/触发器阻断写入；PowerSync 上传失败会返回对应的 4xx 代码。
  - 软删除依赖 `_deleted` + `_deleted_at` 字段；服务端接收删除后通过 PowerSync 下发。
  - 冲突：笔记/高亮采用 Conflict Copy（由触发器写 `conflict_of`）。

#### F. 前端组件契约（Frontend Contract）
- 组件：`NoteEditor`
  - Props 同上。
  - 交互：保存→写 SQLite (`notes` 表)→PowerSync 自动同步；在 `onError` 中只处理本地验证或 PowerSync 失败事件。
- 组件：`TagPicker`
  - Props：
    ```ts
    interface TagPickerProps {
      tags: Array<{ id: string; name: string; etag: string }>
      onCreate: (name: string) => void
      onUpdate: (id: string, name: string, etag: string) => void
    }
    ```

### ✔ Definition of Done (DoD)
- [ ] PowerSync 下载/上传规则涵盖 Notes/Tags CRUD 与搜索所需字段
- [ ] 软删除与 `_deleted` 投递及前端处理用例
- [ ] `tsv` 索引生成与检索测试覆盖
- [ ] ETag/Idempotency 一致性校验
- [ ] RLS 与多租户隔离测试
- [ ] 迁移脚本与回滚计划齐备
---

### 2.5 AI Knowledge Engine

> **架构决策**：AI 功能**必须**通过 REST API 实现（非 PowerSync），因为：
> 1. AI 功能需要网络连接才能使用
> 2. SSE 流式响应无法通过 PowerSync 实现
> 3. 需要服务端计费和限流控制
>
> **对话记录存储**：AI 对话历史通过 PowerSync 同步到本地 SQLite，实现离线查看历史对话。

#### A. 技术栈
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | **FastAPI** | 异步支持、SSE 流式响应 |
| RAG 框架 | **LlamaIndex** | 向量检索、Query Rewrite、Rerank |
| PDF 解析 | **IBM Docling** | 提取章节结构、表格、图表 |
| 前端 AI SDK | **Vercel AI SDK** | 统一流式接口、`onFinish` Token 计数 |
| 向量存储 | **PostgreSQL + pgvector** | 与主数据库统一 |
| LLM 调用 | **OpenAI / Claude API** | 可配置模型 |

#### B. 三种 AI 模式

| 模式 | 触发场景 | 技术实现 | 费用 |
|------|---------|----------|------|
| **聊天模式** | 通用对话/闲聊 | 纯 LLM，无 RAG，无书库上下文 | 低 (约 0.3-1 Credits/次) |
| **翻译模式** | 选中文本 → 翻译 | 纯 LLM，无 RAG | 低 (约 0.5 Credits/次) |
| **问答模式** | 书籍内对话/提问 | RAG Pipeline | 中 (约 2-5 Credits/次) |

**聊天模式流程**：
```
用户在 AI 助手界面发起对话（未关联书籍）
    ↓
POST /api/v1/ai/chat
    ↓
直接调用 LLM (无向量检索，无书库上下文)
    ↓
SSE 流式返回回答
```

> **聊天模式说明**：
> - 不涉及用户书库内容，纯通用 AI 对话
> - 适用于：写作辅助、知识问答、头脑风暴等通用场景
> - 入口：AI 助手面板 → 新建对话（不关联书籍）

**翻译模式流程**：
```
用户选中文本 → 点击"翻译"按钮
    ↓
POST /api/v1/ai/translate
    ↓
直接调用 LLM (无向量检索)
    ↓
SSE 流式返回翻译结果
```

**问答模式 RAG 流程**：
```
用户提问
    ↓
1. Query Rewrite (基于上下文重写查询)
    ↓
2. Vector Search (pgvector Top-K 检索)
    ↓
3. IBM Docling 解析 (提取章节/表格结构)
    ↓
4. Rerank (Cross-Encoder 重排序)
    ↓
5. LLM 生成回答 (含引用与跳转锚点)
    ↓
6. SSE 流式输出
    ↓
7. onFinish: Token 计数 → Credits 扣费
```

#### C. IBM Docling 集成

> **用途**：将 PDF 解析为结构化文档，提取章节、表格、图表。

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

def parse_book_for_rag(book_id: str, pdf_path: str) -> list[dict]:
    """解析书籍为 RAG 可用的结构化块"""
    result = converter.convert(pdf_path)
    document = result.document
    
    chunks = []
    for item in document.iterate_items():
        if item.label in ["paragraph", "table", "figure"]:
            chunks.append({
                "book_id": book_id,
                "content": item.text,
                "type": item.label,
                "page": item.prov[0].page if item.prov else None,
                "bbox": item.prov[0].bbox if item.prov else None,
            })
    return chunks
```

#### D. Vercel AI SDK 前端集成

> **Token 计数**：使用 `onFinish` 回调获取真实 Token 消耗，用于 Credits 扣费。

```typescript
import { useChat } from 'ai/react';

function AIChat({ conversationId }: { conversationId: string }) {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: '/api/v1/ai/conversations/' + conversationId + '/messages',
    onFinish: (message, { usage }) => {
      // usage.totalTokens 包含真实 Token 消耗
      console.log('Token usage:', usage?.totalTokens);
      // 后端已在 SSE 结束时扣费，此处仅用于 UI 显示
    },
  });
  
  return (/* UI 组件 */);
}
```

#### A. 数据库模型（Database Schema）

**`ai_conversations` 表**（启用 RLS）：
| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `id` | UUID, PK | 会话 ID |
| `user_id` | UUID, FK | 用户 ID |
| `title` | TEXT | 会话标题 |
| `book_id` | UUID, Nullable | 关联书籍（可选） |
| `related_context` | JSONB | 上下文（选中文本、笔记引用等） |
| `conversation_history` | JSONB | 消息历史数组 |
| `version` | INTEGER, Default: 1 | 乐观锁版本号（用于 ETag/If-Match） |
| `deleted_at` | TIMESTAMPTZ, Nullable | 软删除时间 |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | 更新时间 |

**消息结构**（存储在 `conversation_history` JSONB 中）：
```typescript
interface AIMessage {
  role: 'user' | 'assistant' | 'system';
  text: string;
  refs?: Array<{
    type: 'highlight' | 'note' | 'location';
    cfi?: string;
    bookId?: string;
    content?: string;
  }>;
  created_at: string; // ISO8601
}
```

**RLS 策略**（用户隔离）：
```sql
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_conversations_user ON ai_conversations
  FOR ALL USING (user_id = current_setting('app.user_id')::uuid);
```

#### B. 后端逻辑与 API 契约（Backend & Contract）

**端点清单**（详见 05 契约）：
| 端点 | 方法 | 说明 |
|:-----|:-----|:-----|
| `/api/v1/ai/conversations` | GET | 列出会话（分页，cursor-based） |
| `/api/v1/ai/conversations` | POST | 创建会话 + 首条消息 |
| `/api/v1/ai/conversations/{id}` | GET | 获取会话详情（返回 ETag） |
| `/api/v1/ai/conversations/{id}` | PATCH | 修改标题/元数据（需 If-Match） |
| `/api/v1/ai/conversations/{id}` | DELETE | 软删除会话 |
| `/api/v1/ai/conversations/{id}/messages` | POST | 追加消息（触发 AI 回复，SSE 流式） |
- 规则：
  - AI Chat 不受只读锁影响。
  - Credits 不足 → 返回 `INSUFFICIENT_CREDITS`。
  - 计费顺序：月度赠礼 → 加油包 → Wallet → 拒绝。
  - 会话版本冲突：使用 `ETag/If-Match` 或 Session Version，冲突返回 409。
- RAG 流程：
  1) Query Rewrite：基于用户上下文重写查询 (LlamaIndex QueryTransform)。
  2) Vector Search：PostgreSQL pgvector 检索 Top-K 片段。
  3) Docling Parse：对 PDF 源提取章节/表格结构。
  4) Re-rank：LlamaIndex Reranker + Cross-Encoder 重排序。
  4) LLM 生成：以重排后的证据生成回答，包含引用与跳转锚点。
  5) 流式输出：使用 SSE/WebSocket 推送；支持“停止/继续”。
  7) Token 计费：onFinish 回调获取 Token 数，扣除 Credits。
> Status: Contract Available；Backend = To Implement（按此管线实现）。

#### F. 前端组件契约（Frontend Contract）
- 组件：`AIConversationsPanel`
  - Props：
    ```ts
    interface AIConversationsPanelProps {
      sessionId?: string
      onMessage?: (msg: { id: string; role: 'user' | 'assistant'; content: string }) => void
      onStop?: () => void
    }
    ```

### ✔ Definition of Done (DoD)
- [ ] API 契约与 SSE/WebSocket 行为对齐
- [ ] Credits 扣费顺序与不足错误用例
- [ ] RAG 各阶段可替换/Mock 的测试策略
- [ ] ETag/Session Version 冲突处理测试
- [ ] 前端消息流与停止/继续契约实现
- [ ] 账单联动与台账记录验证
---

### 2.6 Billing & Account

#### A. 数据库模型（Database Schema）
- `credit_accounts`、`credit_ledger`、`payment_sessions`、`payment_webhook_events`、`user_stats`（字段详见 04 号文档）。

#### B. 后端逻辑与 API 契约（Backend & Contract）
- 端点：`GET /billing/balance`、`GET /billing/ledger`、`POST /billing/sessions`、`POST /billing/webhook/{gateway}`。
- 规则：只读锁由 `user_stats` 与 `system_settings` 计算；OCR 阶梯扣费与台账记载；Webhook 入账与签名校验。

#### F. 前端组件契约（Frontend Contract）
- 组件：`BalanceCard`
  - Props：
    ```ts
    interface BalanceCardProps {
      balance: number
      currency: string
      walletAmount?: number
      walletCurrency?: string
    }
    ```
- 组件：`CheckoutPanel`
  - Props：
    ```ts
    interface CheckoutPanelProps {
      gateway: 'stripe' | 'wechat' | 'alipay' | string
      amountMinor: number
      currency: string
      onSessionCreated: (session: { id: string; paymentUrl: string }) => void
    }
    ```
  - 交互：创建会话→跳转第三方→Webhook 入账→刷新余额与台账。
- **数据导出 (Escape Hatch)**：在设置页提供“导出全部数据”按钮，打包下载所有笔记 (Markdown) 和元数据 (JSON)，生成过程纯本地进行。

### 2.7 全局搜索与索引 (Global Search & Local FTS)
#### A. 技术方案
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 搜索引擎 | **SQLite FTS5** | 本地全文搜索，离线可用 |
| 中文分词 | **Intl.Segmenter** | 浏览器/iOS 原生 API |
| 索引存储 | **local SQLite** | 本地表，不参与 PowerSync 同步 |

#### B. 中文分词策略 (Smart Segmentation)
*   **问题**：SQLite FTS5 默认不支持中文分词。
*   **解决方案**：**前端预分词**。写入 SQLite 前，使用 `Intl.Segmenter` (现代浏览器/iOS原生) 将中文切分为带空格的词组。
*   **示例**：用户输入“经济学原理” -> 存入 `segmented_text` 为 “经济 经济学 原理”。


#### C. 数据库模型 (Local-Only SQLite)
```sql
CREATE TABLE global_search_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    book_id TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    raw_text TEXT NOT NULL,
    segmented_text TEXT NOT NULL,
    location_data TEXT,
    UNIQUE(source_type, source_id, chunk_index)
);

CREATE VIRTUAL TABLE global_search_fts USING fts5(
    segmented_text, content='global_search_index', content_rowid='id'
);
```

### Definition of Done - Global Search
- [ ] FTS5 索引创建成功
- [ ] 中文预分词正常

---

### 2.8 Admin & Operations (后台管理)
#### A. 功能概览
- **商业参数配置**：实时调整汇率 (`wallet_exchange_rate`)、OCR 阶梯阈值 (`ocr_page_thresholds`)、免费配额 (`free_book_limit`) 等（详见 01 文档第 5 节）。
- **合规文档管理**：编辑服务条款 (TOS)、隐私协议 (Privacy Policy)。
- **用户管理**：查看/封禁用户、赠送 Credits (补单)。
- **系统监控**：OCR 队列堆积报警、Celery Worker 状态。

#### B. 核心业务逻辑
- **商业参数热更新 (Hot Reload)**：
  - 所有参数存储在 `system_settings` 表 (Key-Value/JSONB)。
  - API 读取时必须有 **TTL 缓存 (e.g., 5分钟)**，避免高频打库。
  - Admin 修改后，发布 Redis Pub/Sub 事件 `config_updated`，通知所有 API 实例清除缓存。
- **协议文档管理**：
  - 存储：TOS 和 Privacy Policy 存储在 `system_settings` 表中，Key 为 `compliance_tos_zh_cn`, `compliance_privacy_zh_cn` (多语言支持)。
  - 编译：Admin 编辑 Markdown 源码 -> 保存时同时生成 HTML 缓存 -> API 提供 `GET /api/v1/public/compliance/{type}` 供 App 端 Webview 渲染。

#### C. 管理端组件契约 (Frontend Contract)
- 组件：`ConfigEditor` (用于编辑 JSONB 参数)
  - Props: `{ configKey, schema, value, onSave }`
  - 功能：基于 JSON Schema 验证输入，防止配置错误的 JSON 导致系统崩溃。
- 组件：`MarkdownEditor` (用于编辑协议)
  - ...

### ✔ Definition of Done (DoD)
- [ ] Admin 可读写 `system_settings` 表中的商业参数
- [ ] API 侧实现配置缓存与清除机制
- [ ] Admin 界面可编辑 TOS/Privacy 并正确持久化
- [ ] 公开 API 端点 (`/public/compliance/*`) 可获取最新协议内容
- [ ] 邮箱"防输错"确认弹窗交互实现


### ✔ Definition of Done (DoD)
- [ ] 支付会话创建与 Webhook 入账联动用例
- [ ] 事务一致性：扣费与业务写入同交易测试
- [ ] RLS 与账本隔离校验
- [ ] 错误码映射与文案一致性
- [ ] 前端余额/台账组件契约对齐
- [ ] Alembic 迁移与回滚计划齐备

---

### 2.9 TTS 听书 (Text-to-Speech)

> **架构决策**：采用**纯前端离线方案**，App 内置高保真中文 TTS 模型，无需后端服务。

#### A. 技术方案
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| TTS 引擎 | **Sherpa-onnx (WASM)** | 开源、高性能、支持多语言 |
| 运行环境 | **Web Worker** | 独立线程，不阻塞 UI |
| 中文模型 | **内置** (~45MB) | App 发布时打包，首次启动可用 |
| 英文/日文模型 | **DLC 按需下载** | 用户首次选择语言时下载 |
| 存储位置 | **OPFS** (Origin Private FS) | 本地持久化，跨会话复用 |

#### B. 用户体验流程
```
入口一：书籍卡片 ⋮ 菜单 → "听书"
入口二：阅读器内 → 工具栏 → 🎧 按钮
    ↓
┌────────────────────────────────────────────────────────────┐
│  📖 TTS 播放控制器 (底部悬浮)                               │
│                                                            │
│  第 3 章 · 经济学基础                                       │
│  ▶ ══════════●══════════════════════════ 12:34 / 45:21    │
│                                                            │
│  [⏮ 上段] [⏪ -15s] [⏸ 暂停] [⏩ +15s] [⏭ 下段]           │
│  [🔊 音量] [⚡ 1.0x] [🎤 音色]                              │
└────────────────────────────────────────────────────────────┘
```

#### C. 数据库模型 (Local-Only SQLite)
```sql
-- 本地 TTS 设置 (不参与 PowerSync 同步)
CREATE TABLE local_tts_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- 单例
    voice_id TEXT DEFAULT 'zh_cn_female_01', -- 当前音色
    speed REAL DEFAULT 1.0,                  -- 播放速度 0.5-2.0
    volume REAL DEFAULT 1.0,                 -- 音量 0-1
    auto_scroll BOOLEAN DEFAULT TRUE,        -- 自动滚动文本
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 本地 TTS 模型缓存
CREATE TABLE local_tts_models (
    model_id TEXT PRIMARY KEY,               -- e.g., 'zh_cn_female_01'
    language TEXT NOT NULL,                  -- 'zh', 'en', 'ja'
    display_name TEXT NOT NULL,              -- '中文女声 (标准)'
    file_path TEXT NOT NULL,                 -- OPFS 路径
    file_size INTEGER NOT NULL,              -- 字节数
    is_bundled BOOLEAN DEFAULT FALSE,        -- 是否内置模型
    downloaded_at TEXT
);
```

#### D. 支持的音色
| 语言 | 音色 ID | 显示名称 | 大小 | 类型 |
|-----|---------|---------|------|------|
| 中文 | `zh_cn_female_01` | 中文女声 (标准) | ~45MB | 内置 |
| 中文 | `zh_cn_male_01` | 中文男声 (标准) | ~45MB | DLC |
| 英文 | `en_us_female_01` | English Female | ~30MB | DLC |
| 日文 | `ja_jp_female_01` | 日本語女性 | ~35MB | DLC |

#### E. 前端组件契约
```typescript
interface TTSController {
  // 状态
  isPlaying: boolean;
  currentPosition: { chapter: number; paragraph: number };
  progress: number; // 0-1
  duration: number; // 预估总时长 (秒)
  
  // 控制
  play(): void;
  pause(): void;
  seekTo(chapter: number, paragraph: number): void;
  setSpeed(speed: number): void;
  setVoice(voiceId: string): void;
  
  // 事件
  onParagraphChange: (para: number) => void;  // 用于高亮当前段落
  onComplete: () => void;
}
```

### ✔ Definition of Done (DoD) - TTS
- [ ] Sherpa-onnx WASM 成功加载并在 Web Worker 运行
- [ ] 中文内置模型正常发声，无明显延迟
- [ ] DLC 模型下载、存储、加载流程完整
- [ ] 阅读器内段落高亮与语音同步
- [ ] 播放控制器 UI 完整实现

---

### 2.10 权威词典 (Dictionary)

> **架构决策**：采用**内置 SQLite Sidecar 数据库**，完全离线可用，不参与 PowerSync 同步。

#### A. 技术方案
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 数据库 | **SQLite Sidecar** | `dict_master.db` (~40MB) |
| 运行模式 | **只读** | App 内置，不可编辑 |
| 词典来源 | 开源词典整合 | 现代汉语词典 + WordNet + ECDICT |
| 加载方式 | **预装打包** | Web: IndexedDB 初始化; Native: Assets |

#### B. 用户体验流程
```
阅读器内选中文字 → 弹出工具栏
    ↓
┌──────────────────────────────────────────┐
│  📖  📝  🔍  📚                           │  ← 高亮/笔记/搜索/词典
└──────────────────────────────────────────┘
    ↓ 点击 📚 词典按钮
┌──────────────────────────────────────────────────────────────┐
│  词典 · "经济"                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  【拼音】jīng jì                                             │
│  【词性】名词                                                 │
│  【释义】                                                     │
│    1. 经世济民，治理国家。                                    │
│    2. 社会物质生产、分配、交换和消费的活动和关系的总和。       │
│  【例句】市场经济是一种资源配置方式。                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  [添加到笔记]                              [关闭]             │
└──────────────────────────────────────────────────────────────┘
```

#### C. 数据库 Schema (`dict_master.db`)
```sql
-- 词条表
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,                    -- 词条
    language TEXT NOT NULL,                -- 'zh', 'en'
    phonetic TEXT,                         -- 发音/拼音
    pos TEXT,                              -- 词性 (noun, verb, adj...)
    definitions TEXT NOT NULL,             -- JSON 数组: ["释义1", "释义2"]
    examples TEXT,                         -- JSON 数组: ["例句1", "例句2"]
    etymology TEXT,                        -- 词源
    frequency INTEGER DEFAULT 0            -- 词频 (用于排序)
);

-- 索引 (预建，只读)
CREATE INDEX idx_entries_word ON entries(word);
CREATE INDEX idx_entries_language ON entries(language, word);

-- FTS 全文搜索 (用于模糊查询)
CREATE VIRTUAL TABLE entries_fts USING fts5(
    word, definitions,
    content='entries',
    content_rowid='id'
);
```

#### D. 词典内容来源
| 语言 | 词典 | 词条数 | 许可证 |
|-----|------|-------|-------|
| 中文 | CC-CEDICT + 开源汉语词典 | ~120,000 | CC BY-SA |
| 英文 | WordNet 3.1 | ~150,000 | WordNet License |
| 英汉 | ECDICT | ~770,000 | MIT |

#### E. 前端组件契约
```typescript
interface DictionaryService {
  // 查词
  lookup(word: string, language?: 'zh' | 'en'): Promise<DictEntry[]>;
  
  // 模糊搜索
  search(query: string, limit?: number): Promise<DictEntry[]>;
}

interface DictEntry {
  word: string;
  phonetic?: string;
  pos?: string;
  definitions: string[];
  examples?: string[];
}
```

### ✔ Definition of Done (DoD) - Dictionary
- [ ] `dict_master.db` 成功打包到 App 并可读取
- [ ] 中文词条查询返回正确释义
- [ ] 英文词条查询返回正确释义
- [ ] 模糊搜索功能正常
- [ ] 阅读器选词弹窗集成词典功能

---

## 3. 统一约束与实现备注
- [MUST] 禁止硬编码数值与价格；所有阈值与定价从配置与定价表读取（见 04）。
- [MUST] 前端契约统一：
  - 所有 POST 必须带 `Idempotency-Key`
  - 所有 PATCH 必须带 `If-Match`
  - 所有 GET 建议带 `If-None-Match`（弱缓存可选）
- [MUST] RLS：每次数据库操作设置会话变量实现行级隔离。
- [待确认/待实现] Reader/AI 流式细节、Shelves 完整 CRUD 与前端适配将随后续迭代补齐，并与 05 契约保持一致。



