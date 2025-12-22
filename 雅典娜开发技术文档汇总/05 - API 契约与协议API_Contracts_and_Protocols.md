# 05 - API 契约与协议 (API Contracts & Protocols)

> **版本**: v1.1

> **SSOT (Single Source of Truth)**: 具体的 Request/Response Schema 以 `contracts/api/v1/*.yaml` (OpenAPI) 文件为唯一事实来源。本文档仅作为核心协议与交互逻辑的开发者手册。

## 1. 接口设计规范 (Interface Design Specifications)

### 1.1 版本控制与路径
所有 API 均遵循 RESTful 风格，URI 必须包含版本号：
*   **Base URL**: `https://api.athena.app/api/v1`
*   **Format**: `/api/v1/{resource}/{id}/{action}`

### 1.2 认证与鉴权 (Authentication)
*   **Header**: `Authorization: Bearer <access_token>`
*   **Token Type**: JWT (JSON Web Token)
*   **Token Source**: 通过 `/api/v1/auth/email/verify_code` 获取。
*   **无状态性**: 服务端不存储 Session，完全依赖 JWT 签名验证。

### 1.3 跨域资源共享 (CORS)
*   **Policy**: 严格限制 Origin，仅允许白名单域名（Web/Mobile App）。
*   **Headers**: 允许标准 Headers 及自定义 Headers (`Idempotency-Key`, `If-Match`)。

---

## 2. 标准错误码表 (Global Error Codes)

以下错误码对应 `HTTPException(status_code=..., detail="...")` 中的 `detail` 字段。

| Code (detail) | HTTP Status | Description |
| :--- | :--- | :--- |
| `unauthorized` | 401 | 认证失败或 Token 过期 |
| `forbidden` | 403 | 权限不足 |
| `not_found` | 404 | 资源不存在 |
| `missing_if_match` | 428 | 缺少 `If-Match` 头（针对乐观锁资源） |
| `invalid_if_match` | 400 | `If-Match` 格式错误（需为 `W/"<version>"`） |
| `version_conflict` | 409 | 资源版本冲突（乐观锁检查失败） |
| `quota_exceeded` | 403 | 存储或书籍配额超限，账户进入只读模式 |
| `upload_forbidden_quota_exceeded` | 403 | 上传动作因配额超限被拒绝 |
| `ocr_quota_exceeded` | 403 | OCR 配额不足 |
| `ocr_max_pages_exceeded` | 400 | 书籍页数超过 2000 页限制 |
| `ocr_in_progress` | 409 | OCR 任务正在处理中 |
| `already_digitalized` | 400 | 书籍已是文字型，无需 OCR |
| `missing_filename` | 400 | 上传初始化时缺少文件名 |
| `missing_key` | 400 | 上传完成时缺少 S3 Object Key |
| `canonical_not_found` | 404 | 秒传时原书不存在 |
| `device_id_required` | 400 | 同步操作缺少设备 ID |
| `rate_limited` | 429 | 请求频率过高 |
| `internal_error` | 500 | 服务器内部错误 |

---

## 3. App-First 数据同步协议 (App-First Data Sync Protocol)

> **核心架构决策**: 雅典娜采用 **App-First 架构**，PowerSync 负责数据同步，REST API 负责文件操作和复杂业务逻辑。


### 3.1 PowerSync 访问协议

- **Endpoint**: `wss://sync.athena.app/stream`（生产） / `ws://localhost:8090/stream`（本地）。
- **Auth**: 与 REST 相同的 `Authorization: Bearer <JWT>`，PowerSync Service 会验证并在连接上下文中注入 `user_id`、`device_id`。
- **Metadata**: 客户端在 `connect()` 时需传入：
  ```json
  {
    "client": "web|ios|android",
    "sdk_version": "1.2.0",
    "device_id": "uuid",
    "schema_version": 3
  }
  ```
- **Backpressure**: SDK 自动处理；Service 端暴露 `stream_lag_ms` 指标供监控。
- **错误映射**: PowerSync 错误码映射至 REST 错误：`permission_denied -> 403`, `validation_failed -> 400`, `conflict -> 409`。

### 3.2 API 与 PowerSync 职责分离 (Responsibility Separation)

> **重要性**: 🔴 核心架构决策 - 所有开发者必读


雅典娜采用 **App-First 架构**，PowerSync 负责数据同步，REST API 负责文件操作和复杂业务逻辑。**两者使用统一的 JWT 认证**，避免 token 分裂。

#### 3.B.1 职责划分表

| 功能类别 | 负责方 | 说明 |
| :--- | :--- | :--- |
| **用户认证** | REST API | 登录、发送验证码、token 签发与刷新 |
| **元数据同步** | PowerSync | 书籍列表、笔记、高亮、阅读进度、书架 |
| **文件上传** | REST API | 书籍文件通过 S3 Presigned URL 上传，PowerSync 无法传输二进制文件 |
| **文件下载** | REST API + S3 | 获取 Presigned Download URL |
| **OCR 任务** | REST API | 触发 OCR、查询进度（计算密集型任务） |
| **AI 功能** | REST API | 流式响应、向量检索、对话历史 |
| **账单支付** | REST API | Stripe 集成、配额管理 |
| **离线读写** | PowerSync (SQLite) | 本地优先，后台自动同步 |
| **实时通知** | PowerSync | 通过同步流推送状态变更 |

#### 3.B.2 JWT 统一规范

**单一 Token 源**: 所有 JWT 由 REST API 的 `/auth/*` 端点签发，PowerSync 和 API 使用相同的 secret 验证。

```
┌─────────────────┐                    ┌─────────────────┐
│   REST API      │ ──── 签发 JWT ──→  │     客户端      │
│  (auth.py)      │                    │                 │
└─────────────────┘                    └────────┬────────┘
        ↑                                       │
        │ 相同 secret                           │ 同一个 JWT
        ↓                                       ↓
┌─────────────────┐                    ┌─────────────────┐
│   PowerSync     │ ←── 验证 JWT ────  │     客户端      │
│  (验证器)       │                    │  (sync 请求)    │
└─────────────────┘                    └─────────────────┘
```

**必须包含的 JWT Claims**:
```json
{
  "sub": "<user_id>",           // 必须: 用户 ID
  "aud": "authenticated",       // 必须: PowerSync Supabase 模式要求
  "iat": 1718600000,
  "exp": 1718686400
}
```

**关键配置（docker-compose.yml）**:
```yaml
# REST API
api:
  environment:
    AUTH_SECRET: ${AUTH_SECRET:-dev_powersync_secret_change_in_production}

# PowerSync
powersync:
  environment:
    PS_SUPABASE_JWT_SECRET: ${AUTH_SECRET:-dev_powersync_secret_change_in_production}
```

> ⚠️ **警告**: API 和 PowerSync 的 JWT secret 必须完全一致，否则客户端无法同时访问两个服务。

#### 3.B.3 典型工作流示例

**上传书籍**（需要 API + PowerSync 协作）:
```
1. [客户端] 调用 POST /api/v1/books/upload_init → 获取 S3 Presigned URL
2. [客户端] PUT 文件到 S3
3. [客户端] 调用 POST /api/v1/books/upload_complete → 创建 books 记录
4. [PowerSync] 自动同步 books 表变更到所有设备
5. [客户端其他设备] 通过 PowerSync 接收到新书，显示在书架
```

**创建笔记**（纯 PowerSync）:
```
1. [客户端] 写入本地 SQLite (notes 表)
2. [PowerSync SDK] 后台自动推送到服务器
3. [服务器] 写入 PostgreSQL
4. [PowerSync] 同步到其他设备
```

**AI 对话**（纯 REST API）:
```
1. [客户端] POST /api/v1/ai/chat (SSE)
2. [API] 流式返回 AI 响应
3. [客户端] 实时显示
```

#### 3.B.4 故障排查检查清单

| 症状 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| API 认证成功，PowerSync 401 | JWT secret 不一致 | 检查 `AUTH_SECRET` 和 `PS_SUPABASE_JWT_SECRET` 是否相同 |
| PowerSync "Known keys: " 空 | 缺少 `supabase: true` 配置 | 在 powersync.yaml 中启用 Supabase 模式 |
| Token 刷新后仍然 401 | 浏览器缓存旧 token | 强制刷新页面或清除 localStorage |
| 上传成功但书架不显示 | PowerSync 未连接 | 检查 WebSocket 连接状态 |
| 书籍元数据同步但封面不显示 | 封面 URL 过期 | 检查 S3 Presigned URL 有效期 |

---

### 3.3 PowerSync 数据操作规范 (Data Operation Specification)

> **重要性**: 🔴 **核心架构规范 - 必须严格遵守**
> **原则**: PowerSync 是主要同步通道，REST API 仅用于 PowerSync 无法处理的场景

### 3.C.1 核心原则

```
┌─────────────────────────────────────────────────────────────────────┐
│                    数据同步架构                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐        PowerSync         ┌─────────────┐          │
│   │   前端       │ ◄═══════════════════════► │  PostgreSQL │          │
│   │  (SQLite)   │    双向实时同步            │   (后端)    │          │
│   └──────┬──────┘                          └──────┬──────┘          │
│          │                                        │                 │
│          │ REST API (仅特殊场景)                   │                 │
│          └────────────────────────────────────────┘                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**核心原则**：
1. **PowerSync 优先**：所有 CRUD 操作优先使用 PowerSync 本地写入
2. **API 辅助**：仅文件操作、计算密集型任务使用 REST API
3. **离线优先**：用户操作应立即响应，后台自动同步

### 3.C.2 数据表操作规范

#### 表 1: books（书籍元数据）

| 操作 | 负责方 | 前端实现 | 说明 |
|:-----|:------|:--------|:-----|
| **创建** | REST API | `POST /api/v1/books/upload_complete` | 上传流程创建，PowerSync 自动同步到客户端 |
| **读取** | PowerSync | `SELECT * FROM books` | 实时响应式查询 |
| **更新标题/作者** | PowerSync | `UPDATE books SET title=?, author=? WHERE id=?` | 本地写入，自动同步到服务器 |
| **软删除** | PowerSync | `UPDATE books SET deleted_at=? WHERE id=?` | 本地写入，自动同步到服务器 |
| **硬删除(含文件)** | REST API | `DELETE /api/v1/books/{id}` | 需要删除 MinIO 文件 |
| **恢复删除** | PowerSync | `UPDATE books SET deleted_at=NULL WHERE id=?` | 本地写入，自动同步 |

> **⚠️ 关键配置**: 后端 `powersync.py` 的 `ALLOWED_TABLES` 必须包含 `books`！

#### 表 2: book_position（阅读位置）

| 操作 | 负责方 | 前端实现 | 说明 |
|:-----|:------|:--------|:-----|
| **创建/更新** | PowerSync | `INSERT OR REPLACE INTO book_position` | 实时保存，跨设备同步 |
| **读取** | PowerSync | `SELECT * FROM book_position WHERE book_id=?` | 响应式查询 |

#### 表 3: notes / highlights / bookmarks（笔记/高亮/书签）

| 操作 | 负责方 | 前端实现 | 说明 |
|:-----|:------|:--------|:-----|
| **创建** | PowerSync | `INSERT INTO notes (...)` | 离线创建，自动同步 |
| **更新** | PowerSync | `UPDATE notes SET ... WHERE id=?` | 离线更新 |
| **软删除** | PowerSync | `UPDATE notes SET is_deleted=1, deleted_at=?` | 离线删除 |
| **读取** | PowerSync | `SELECT * FROM notes WHERE book_id=? AND is_deleted=0` | 响应式 |

#### 表 4: shelves / shelf_books（书架）

| 操作 | 负责方 | 前端实现 | 说明 |
|:-----|:------|:--------|:-----|
| **创建书架** | PowerSync | `INSERT INTO shelves (...)` | 离线创建 |
| **更新书架** | PowerSync | `UPDATE shelves SET ... WHERE id=?` | 离线更新 |
| **删除书架** | PowerSync | `UPDATE shelves SET is_deleted=1` | 软删除 |
| **添加书籍到书架** | PowerSync | `INSERT INTO shelf_books (...)` | 离线操作 |
| **从书架移除书籍** | PowerSync | `DELETE FROM shelf_books WHERE ...` | 离线操作 |

### 3.3.3 REST API 专属场景

以下场景 **必须** 使用 REST API，因为 PowerSync 无法处理：

| 场景 | API 端点 | 原因 |
|:-----|:---------|:-----|
| **上传书籍文件** | `POST /books/upload_init` + S3 + `POST /books/upload_complete` | 二进制文件传输 |
| **下载书籍文件** | `GET /books/{id}/content` | 获取 S3 Presigned URL |
| **获取封面图片** | `GET /books/{id}/cover` | 图片二进制流 |
| **触发 OCR** | `POST /books/{id}/ocr/trigger` | 计算密集型异步任务 |
| **AI 对话** | `POST /ai/chat` (SSE) | 流式响应 |
| **AI 向量搜索** | `POST /ai/search` | 使用 PostgreSQL pgvector |
| **认证登录** | `POST /auth/*` | JWT 签发 |
| **账单支付** | `POST /billing/*` | Stripe 集成 |
| **永久删除书籍** | `DELETE /books/{id}/permanent` | 需要删除私人数据和更新引用计数 |
| **批量永久删除** | `DELETE /books/permanent` | 批量删除私人数据 |

> **⚠️ 注意**：软删除（设置 `deleted_at`）应使用 PowerSync；  
> 恢复删除（清除 `deleted_at`）也应使用 PowerSync（与软删除对称）；  
> 永久删除（清理私人数据）**必须**使用 REST API，因为需要：
> 1. 删除 notes, highlights, bookmarks, book_position 等关联数据
> 2. 更新引用书的 `storage_ref_count`
> 3. 检查是否需要清理孤立的原书

### 3.3.4 后端 ALLOWED_TABLES 配置

**位置**: `api/app/powersync.py`

```python
ALLOWED_TABLES = {
    "books",              # ✅ 必须添加！允许元数据修改和软删除
    "book_position",      # 阅读位置（原 reading_progress）
    "reading_time_log",   # 阅读时长记录（原 reading_sessions）
    "notes",
    "highlights",
    "bookmarks",
    "shelves",
    "shelf_books",
    "user_settings",
}
```

> **🔴 重要**: 如果 `books` 不在白名单中，前端对书籍的所有修改都不会同步到服务器！

### 3.3.5 前端代码实现规范

**✅ 正确示例 - 使用 PowerSync：**
```typescript
// 修改书籍元数据
const db = usePowerSync()
await db.execute(
  'UPDATE books SET title = ?, author = ?, updated_at = ? WHERE id = ?',
  [newTitle, newAuthor, new Date().toISOString(), bookId]
)
// PowerSync 自动同步到服务器，无需额外处理
```

**✅ 正确示例 - 软删除书籍：**
```typescript
await db.execute(
  'UPDATE books SET deleted_at = ?, updated_at = ? WHERE id = ?',
  [new Date().toISOString(), new Date().toISOString(), bookId]
)
// 30天后由后台任务硬删除
```

**❌ 错误示例 - 不应该这样做：**
```typescript
// 错误：不应该用 API 修改元数据（除非必须删除文件）
await fetch(`/api/v1/books/${bookId}/metadata`, {
  method: 'PATCH',
  body: JSON.stringify({ title: newTitle })
})
// 这绕过了 PowerSync，导致数据不一致
```

### 3.3.6 同步流程图

```
用户操作 (书籍元数据修改)
     │
     ▼
┌─────────────────┐
│  前端 SQLite    │  ← 1. 立即写入本地数据库
│  (PowerSync)    │
└────────┬────────┘
         │
         ▼  2. PowerSync SDK 后台推送
┌─────────────────┐
│  PowerSync      │  ← 3. 调用 /api/v1/sync/upload
│  Connector      │
└────────┬────────┘
         │
         ▼  4. 写入 PostgreSQL
┌─────────────────┐
│   PostgreSQL    │
│   (后端数据库)   │
└────────┬────────┘
         │
         ▼  5. PowerSync sync_rules 检测变更
┌─────────────────┐
│  其他设备       │  ← 6. 实时同步到所有设备
│  (PowerSync)    │
└─────────────────┘
```

---


---

## 4. 特殊交互协议 (Special Protocols)

### 4.1 幂等性设计 (Idempotency)
防止网络重试导致的数据重复创建。

*   **Header**: `Idempotency-Key: <UUID>`
*   **适用范围**: 所有非安全方法 (`POST`, `PATCH`, `DELETE`)，特别是 `POST /api/v1/books` 和 `POST /api/v1/notes`。
*   **后端机制**:
    1.  Redis 缓存 Key: `idem:{resource}:{action}:{user_id}:{key}`。
    2.  TTL: 24 小时。
    3.  **Hit**: 直接返回缓存的 Response Body (HTTP 200)。
    4.  **Miss**: 执行业务逻辑 -> 缓存结果 -> 返回。

### 4.2 乐观并发控制 (Optimistic Concurrency)
解决多端同时修改同一资源（如笔记、标签）的冲突问题。

*   **Header**: `If-Match: W/"<version>"` (Weak ETag format)
*   **适用范围**: `PATCH /api/v1/notes/{id}`, `PATCH /api/v1/tags/{id}`, `PATCH /api/v1/books/{id}`。
*   **交互流程**:
    1.  **Read**: Client 获取资源，获得 `etag: W/"1"` (对应 DB `version=1`)。
    2.  **Update**: Client 发送 `PATCH` 请求，带上 `If-Match: W/"1"`。
    3.  **Verify**:
        *   若 DB `version == 1`: 更新成功，DB `version` -> 2，返回 200。
        *   若 DB `version > 1`: 更新失败，抛出 `409 Conflict (version_conflict)`。
    4.  **Resolve**: Client 收到 409 后，应重新拉取最新数据，合并冲突后重试。

### 4.3 文件上传协议 (Direct Upload)
采用 S3 Presigned URL 模式，文件流不经过 API Server。支持 **SHA256 全局去重**（ADR-008）。

*   **流程**:
    1.  **Init**: `POST /api/v1/books/upload_init`
        *   Body: `{ "filename": "book.pdf", "content_type": "application/pdf", "content_sha256": "6f4c24abd60a55d3..." }`
        *   Resp (正常上传): `{ "upload_url": "https://s3...", "key": "raw/...", "dedup_available": false }`
        *   Resp (全局去重命中): `{ "dedup_available": true, "canonical_id": "uuid", "has_ocr": true }`
    2.  **Upload** (仅当 `dedup_available=false`):
        *   Client `PUT` 文件流至 `upload_url`
    3.  **Complete** (正常上传): `POST /api/v1/books/upload_complete`
        *   Body: `{ "key": "raw/...", "title": "..." }`
        *   Resp: `{ "id": "book_uuid", "status": "processing" }`
    4.  **Dedup Reference** (秒传): `POST /api/v1/books/dedup_reference`
        *   Body: `{ "filename": "book.pdf", "content_sha256": "6f4c24abd60a55d3...", "size": 12345678 }`
        *   Resp: `{ "id": "new_book_uuid", "dedup_type": "global", "canonical_book_id": "original_uuid", "has_ocr": true }`
*   **SHA256 全局去重**: 相同文件只存储一份，通过 `content_sha256` 实现全局去重和秒传。
*   **服务端备用计算**: 若客户端未提供 `content_sha256`（移动端可能失败），服务端在 `upload_complete` 时从 S3 读取文件计算。

### 4.4 AI 流式响应 (SSE)
基于 Server-Sent Events 标准。

*   **Endpoint**: `GET /api/v1/ai/stream`
*   **Content-Type**: `text/event-stream`
*   **Message Format**: `data: <content>\n\n`
*   **Event Protocol**:
    1.  **Start**: `data: BEGIN\n\n` (连接建立)
    2.  **Delta**: `data: <token_chunk>\n\n` (持续推送)
    3.  **End**: 连接关闭 (Client 收到 EOF 或后端关闭)
*   **Cache**: 支持 Redis 缓存（基于 Prompt Hash），缓存命中时会以极快速度重放 SSE 流。

### 4.5 实时同步 (WebSocket)
用于笔记与文档的协同编辑。

*   **Endpoint**: `ws://api.athena.app/ws/notes/{note_id}`
*   **Sub-Protocol**: 无（Raw WebSocket）。
*   **Payload Protocol**: **Custom JSON Protocol** (Lite Yjs-like).
    *   **Handshake**: Server 发送 `{"type": "ready", "version": <int>}`。
    *   **Update**: Client 发送 `{"type": "update", "client_version": <int>, "update": "<base64>"}`。
    *   **Conflict**: Server 返回 `{"type": "conflict", "version": <int>}`，Client 需重置。
*   **Auth**: 通过 URL Query Parameter (`?token=...`) 或 Header 传递 Token。

---

## 5. 核心接口索引 (Key Endpoints Index)

> 完整 Schema 请查阅 `contracts/api/v1/` 下的 YAML 文件。

### 5.1 Auth & User (`auth.yaml`)

#### 5.1.1 邮箱验证码登录
*   `POST /api/v1/auth/email/send_code`: 发送验证码
*   `POST /api/v1/auth/email/verify_code`: 登录/注册 (获取 Token)
*   `POST /api/v1/auth/refresh`: 刷新 Token
*   `POST /api/v1/auth/logout`: 登出当前会话
*   `GET /api/v1/auth/me`: 获取当前用户信息
*   `GET /api/v1/auth/sessions`: 获取所有登录会话
*   `DELETE /api/v1/auth/sessions/{id}`: 踢出指定设备

#### 5.1.2 第三方 OAuth 登录 🆕

> **支持的 Provider**: `wechat` | `google` | `microsoft` | `apple`

*   `GET /api/v1/auth/oauth/{provider}/authorize`: 获取 OAuth 授权 URL
*   `GET /api/v1/auth/oauth/{provider}/callback`: OAuth 回调处理
*   `POST /api/v1/auth/oauth/{provider}/token`: 移动端 Token 交换

##### `GET /api/v1/auth/oauth/{provider}/authorize`

获取第三方 OAuth 授权 URL，用于 Web 端重定向登录。

**Path Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `provider` | string | OAuth 提供商：`wechat` / `google` / `microsoft` / `apple` |

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `redirect_uri` | string | 授权成功后的回调 URI |
| `state` | string? | 可选，防 CSRF 状态参数（建议传入） |

**Response 200**:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=email+profile&state=..."
}
```

##### `GET /api/v1/auth/oauth/{provider}/callback`

处理 OAuth 回调，验证授权码并签发 JWT。

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `code` | string | OAuth 授权码 |
| `state` | string? | 状态参数（需与请求时一致） |

**Response 302** (成功时重定向):
```
Location: {redirect_uri}?access_token=...&refresh_token=...&is_new_user=true
```

**Error Responses**:
| 错误码 | HTTP | 说明 |
|--------|------|------|
| `oauth_code_invalid` | 400 | 授权码无效或已过期 |
| `oauth_state_mismatch` | 400 | State 参数不匹配（可能是 CSRF 攻击） |
| `oauth_provider_error` | 502 | 第三方服务返回错误 |
| `oauth_email_conflict` | 409 | OAuth 邮箱已被其他账号绑定 |

##### `POST /api/v1/auth/oauth/{provider}/token`

移动端 Native SDK 直接交换 Token（适用于 Google Sign-In、Apple Sign In 等）。

**Request Body**:
```json
{
  "id_token": "<Google/Apple ID Token>",
  "access_token": "<WeChat access_token>",
  "openid": "<WeChat openid>",
  "device_id": "uuid"
}
```
> 注：不同 provider 需要不同字段。Google/Apple 使用 `id_token`，微信使用 `access_token` + `openid`。

**Response 200**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "John Doe",
    "avatar_url": "https://...",
    "is_new_user": true
  }
}
```

#### 5.1.3 OAuth 账号管理

*   `GET /api/v1/auth/oauth/accounts`: 获取已绑定的 OAuth 账号列表
*   `POST /api/v1/auth/oauth/{provider}/link`: 绑定新的 OAuth 账号（需登录态）
*   `DELETE /api/v1/auth/oauth/{provider}/unlink`: 解绑 OAuth 账号

##### `DELETE /api/v1/auth/oauth/{provider}/unlink`

解绑指定的 OAuth 账号。

**Response 200**:
```json
{ "success": true }
```

**Error Responses**:
| 错误码 | HTTP | 说明 |
|--------|------|------|
| `oauth_not_linked` | 404 | 该 OAuth 账号未绑定 |
| `oauth_last_auth_method` | 400 | 不能解绑最后一种登录方式 |

#### 5.1.4 账号注销 🆕

*   `DELETE /api/v1/users/me`: 注销账号（GDPR 合规）

##### `DELETE /api/v1/users/me`

永久删除用户账号及所有关联数据。此操作不可逆。

**Request Headers**:
| Header | 说明 |
|--------|------|
| `Authorization` | Bearer Token（必须） |
| `X-Confirm-Delete` | 确认删除（必须为 `"CONFIRM_DELETE_MY_ACCOUNT"`） |

**Request Body** (可选):
```json
{
  "reason": "不再使用",
  "feedback": "可选的反馈信息"
}
```

**Response 200**:
```json
{
  "success": true,
  "message": "账号已删除，所有数据将在 30 天内完全清除",
  "deletion_scheduled_at": "2024-02-15T00:00:00Z"
}
```

**删除流程（GDPR 合规）**:
```
DELETE /users/me
    ↓
1. 验证 X-Confirm-Delete Header
    ↓
2. 立即注销所有登录会话 (revoke all tokens)
    ↓
3. 标记账号为 pending_deletion
    ↓
4. 发送确认邮件（含 7 天内取消链接）
    ↓
5. 30 天后：后台任务永久删除
   - 删除所有 books（触发引用计数减少）
   - 删除所有 notes/highlights
   - 删除所有 book_position/reading_time_log
   - 删除 user_oauth_accounts
   - 删除 user_sessions
   - 删除 credit_accounts/credit_ledger
   - 删除 ai_conversations/ai_messages
   - 匿名化 invites 记录
   - 最后删除 users 记录
```

**Error Responses**:
| 错误码 | HTTP | 说明 |
|--------|------|------|
| `missing_confirm_header` | 400 | 缺少 X-Confirm-Delete Header |
| `invalid_confirm_header` | 400 | 确认 Header 值不正确 |
| `active_subscription` | 402 | 存在活跃订阅，需先取消 |

### 5.2 Books (`books.yaml`)
*   `GET /api/v1/books`: 书籍列表 (Cursor Pagination)
*   `POST /api/v1/books/upload_init`: 上传初始化 (支持 SHA256 去重检查)
*   `POST /api/v1/books/upload_complete`: 上传完成 (服务端备用 SHA256 计算)
*   `POST /api/v1/books/dedup_reference`: **秒传接口** (SHA256 全局去重)
*   `GET /api/v1/books/{id}`: 书籍详情
*   `PATCH /api/v1/books/{id}`: 更新书籍元数据 (支持 `If-Match`)
*   `DELETE /api/v1/books/{id}`: 删除书籍 (软删除/硬删除分层策略)

### 5.3 Notes & Highlights (`notes.yaml`, `highlights.yaml`, `tags.yaml`)
*   `GET /api/v1/notes`: 笔记列表
*   `POST /api/v1/notes`: 创建笔记 (支持 `Idempotency-Key`)
*   `PATCH /api/v1/notes/{id}`: 更新笔记 (支持 `If-Match`)
*   `GET /api/v1/highlights`: 高亮列表
*   `GET /api/v1/tags`: 标签列表
*   `POST /api/v1/tags`: 创建标签

#### 5.3.1 数据导出 API

##### `GET /api/v1/export/notes`

导出用户笔记和高亮数据。

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `format` | string | 导出格式：`markdown` / `json` / `html`，默认 `markdown` |
| `bookId` | UUID? | 可选，筛选指定书籍的笔记 |
| `includeHighlights` | boolean | 是否包含高亮，默认 `true` |
| `dateFrom` | ISO8601? | 可选，筛选起始日期 |
| `dateTo` | ISO8601? | 可选，筛选结束日期 |

**Response 200** (Markdown 格式):
```markdown
# 我的阅读笔记

> 导出时间：2024-01-15T10:30:00Z
> 笔记总数：42 条
> 高亮总数：128 条

---

## 📖 Thinking, Fast and Slow
*作者：Daniel Kahneman*

### 第一章 系统1与系统2

#### 💡 高亮
> "Nothing in life is as important as you think it is, while you are thinking about it."
> — 位置: 第 45 页

> "A reliable way to make people believe in falsehoods is frequent repetition."
> — 位置: 第 62 页

#### 📝 笔记
**关于双系统理论** (2024-01-10)
系统1是快速、自动、无意识的；系统2是慢速、需要努力、有意识的。日常决策大多由系统1主导，这解释了很多认知偏差的来源。

---

## 📖 The Lean Startup
*作者：Eric Ries*

...
```

**Response 200** (JSON 格式):
```typescript
{
  "exportedAt": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "summary": {
    "totalNotes": 42,
    "totalHighlights": 128,
    "totalBooks": 5
  },
  "books": [
    {
      "id": "book-uuid-1",
      "title": "Thinking, Fast and Slow",
      "author": "Daniel Kahneman",
      "highlights": [
        {
          "id": "highlight-uuid-1",
          "content": "Nothing in life is as important as you think it is...",
          "location": {
            "cfi": "epubcfi(/6/4!/4/2/1:0)",
            "chapter": "Chapter 1",
            "page": 45
          },
          "color": "#FFEB3B",
          "createdAt": "2024-01-08T14:20:00Z",
          "tags": ["psychology", "decision-making"]
        }
      ],
      "notes": [
        {
          "id": "note-uuid-1",
          "title": "关于双系统理论",
          "content": "系统1是快速、自动、无意识的...",
          "location": {
            "cfi": "epubcfi(/6/4!/4/2/1:0)",
            "chapter": "Chapter 1",
            "page": 45
          },
          "linkedHighlightId": "highlight-uuid-1",
          "createdAt": "2024-01-10T09:15:00Z",
          "updatedAt": "2024-01-12T16:30:00Z",
          "tags": ["psychology"]
        }
      ]
    }
  ]
}
```

**JSON Schema** (导出格式定义):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AthenaExportV1",
  "type": "object",
  "required": ["exportedAt", "version", "summary", "books"],
  "properties": {
    "exportedAt": { "type": "string", "format": "date-time" },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+$" },
    "summary": {
      "type": "object",
      "properties": {
        "totalNotes": { "type": "integer", "minimum": 0 },
        "totalHighlights": { "type": "integer", "minimum": 0 },
        "totalBooks": { "type": "integer", "minimum": 0 }
      }
    },
    "books": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "title": { "type": "string" },
          "author": { "type": "string" },
          "highlights": { "type": "array" },
          "notes": { "type": "array" }
        }
      }
    }
  }
}
```

### 5.4 AI (`ai.yaml`)
*   `GET /api/v1/ai/conversations`: 对话历史列表 (Cursor Pagination)
*   `POST /api/v1/ai/conversations`: 创建会话 + 首条消息
*   `GET /api/v1/ai/conversations/{id}`: 获取会话详情 (返回 ETag)
*   `PATCH /api/v1/ai/conversations/{id}`: 修改标题/元数据 (需 If-Match)
*   `DELETE /api/v1/ai/conversations/{id}`: 软删除会话
*   `POST /api/v1/ai/conversations/{id}/messages`: 追加消息 (SSE 流式响应)
*   `POST /api/v1/ai/chat`: **聊天模式** (纯 LLM，无 RAG，无书库上下文，SSE 流式)
*   `POST /api/v1/ai/translate`: **翻译模式** (纯 LLM，无 RAG，SSE 流式)

> **技术栈**：FastAPI + LlamaIndex + IBM Docling + Vercel AI SDK (前端)
> **Token 计费**：SSE 结束时通过 `onFinish` 回调获取 Token 数，扣除 Credits
> **三种模式**：聊天模式 (通用对话) / 翻译模式 (选中文本翻译) / 问答模式 (书籍 RAG)

### 5.5 Realtime Docs (`realtime.py`)
*   `WS /ws/notes/{note_id}`: 笔记/文档实时同步通道

### 5.6 Billing (`billing.yaml`)

#### 5.6.1 基础端点
*   `GET /api/v1/billing/plans`: 获取订阅方案
*   `POST /api/v1/billing/checkout`: 创建支付会话（Web 端 Stripe）
*   `GET /api/v1/billing/history`: 获取支付历史
*   `GET /api/v1/billing/subscription`: 获取当前订阅状态

#### 5.6.2 IAP 凭证校验端点

##### `POST /api/v1/billing/iap/apple/verify`

Apple App Store 内购凭证服务端校验。

**Request Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```typescript
{
  "transactionId": string,           // StoreKit 2 原始交易 ID
  "originalTransactionId": string,   // 原始交易 ID（订阅续费时不变）
  "signedPayload": string,           // JWS 格式的签名凭证
  "productId": string,               // 产品 ID (如 "athena_pro_monthly")
  "environment": "Production" | "Sandbox"
}
```

**后端校验流程**:
```
1. 解析 JWS signedPayload
   ├─ 验证签名（Apple Root CA → Intermediate → Leaf）
   ├─ 校验 bundleId 匹配 APP_BUNDLE_ID
   └─ 校验 environment 匹配当前环境
2. 调用 App Store Server API
   ├─ GET /inApps/v1/transactions/{transactionId}
   └─ 验证交易状态为 purchased/subscribed
3. 防重放检查
   └─ Redis: SETNX transaction:{transactionId} 1 EX 86400
4. 更新用户权益
   ├─ membership_expire_at = expiresDate
   └─ 写入 payment_records 表
```

**Response 200** (校验成功):
```typescript
{
  "valid": true,
  "productId": "athena_pro_monthly",
  "expiresAt": "2025-01-20T00:00:00Z",
  "isTrialPeriod": false,
  "membershipUpdated": true
}
```

**Response 400** (凭证无效):
```typescript
{
  "error": "invalid_receipt",
  "message": "IAP 凭证签名验证失败或已过期"
}
```

##### `POST /api/v1/billing/iap/google/verify`

Google Play Billing 内购凭证服务端校验。

**Request Body**:
```typescript
{
  "purchaseToken": string,           // Google Play 购买令牌
  "productId": string,               // 产品 ID
  "packageName": string,             // 应用包名
  "isSubscription": boolean          // true=订阅, false=一次性购买
}
```

**后端校验流程**:
```
1. 使用 Google Play Developer API
   ├─ 订阅: GET /androidpublisher/v3/.../subscriptions/{productId}/tokens/{token}
   └─ 一次性: GET /androidpublisher/v3/.../products/{productId}/purchases/{token}
2. 验证响应
   ├─ purchaseState == 0 (已购买)
   ├─ acknowledgementState == 1 (已确认)
   └─ 订阅: expiryTimeMillis > now
3. 服务端确认购买（如未确认）
   └─ POST .../subscriptions/{productId}/tokens/{token}:acknowledge
4. 更新用户权益
```

**Response 200** (校验成功):
```typescript
{
  "valid": true,
  "productId": "athena_pro_monthly",
  "expiresAt": "2025-01-20T00:00:00Z",
  "autoRenewing": true,
  "membershipUpdated": true
}
```

#### 5.6.3 Webhook 端点与签名验证

##### `POST /api/v1/billing/webhooks/stripe`

Stripe 事件 Webhook 接收端点。

**Webhook 事件类型**:
| 事件 | 处理逻辑 |
|-----|---------|
| `checkout.session.completed` | 创建/更新订阅，延长 `membership_expire_at` |
| `invoice.paid` | 订阅续费成功，延长会员期限 |
| `invoice.payment_failed` | 发送支付失败通知，标记风险用户 |
| `customer.subscription.deleted` | 订阅取消，设置到期时间 |

**签名验证** (必须在处理前验证):
```python
import stripe

@app.post("/api/v1/billing/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 处理事件...
```

**环境变量**:
```env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx  # Stripe Dashboard 获取
```

##### `POST /api/v1/billing/webhooks/apple`

Apple App Store Server Notifications V2 接收端点。

**Webhook 签名验证**:
```python
from authlib.jose import jwt
from cryptography.x509 import load_pem_x509_certificate

async def verify_apple_notification(signed_payload: str) -> dict:
    """
    验证 Apple Server-to-Server Notification V2 签名
    """
    # 1. 解码 JWS 头部获取证书链
    header = jwt.decode_header(signed_payload)
    x5c = header.get("x5c", [])
    
    # 2. 验证证书链 (Leaf → Intermediate → Apple Root CA)
    leaf_cert = load_pem_x509_certificate(base64.b64decode(x5c[0]))
    # ... 验证证书链完整性
    
    # 3. 使用 Leaf 证书公钥验证签名
    payload = jwt.decode(signed_payload, leaf_cert.public_key())
    
    # 4. 验证 bundleId 和 environment
    assert payload["data"]["bundleId"] == settings.APP_BUNDLE_ID
    
    return payload
```

**通知类型处理**:
| notificationType | 处理逻辑 |
|-----------------|---------|
| `SUBSCRIBED` | 新订阅，延长会员期限 |
| `DID_RENEW` | 续订成功，延长会员期限 |
| `EXPIRED` | 订阅过期，更新状态 |
| `DID_FAIL_TO_RENEW` | 续订失败，发送提醒 |
| `REFUND` | 退款，撤销权益 |

##### `POST /api/v1/billing/webhooks/wechat`

微信支付 V3 版 Webhook 接收端点。

**签名验证算法**:
```python
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives import hashes
import base64

async def verify_wechat_signature(request: Request) -> dict:
    """
    微信支付 V3 签名验证
    """
    timestamp = request.headers["Wechatpay-Timestamp"]
    nonce = request.headers["Wechatpay-Nonce"]
    signature = request.headers["Wechatpay-Signature"]
    serial = request.headers["Wechatpay-Serial"]
    body = await request.body()
    
    # 1. 构造验签串
    sign_str = f"{timestamp}\n{nonce}\n{body.decode()}\n"
    
    # 2. 获取微信支付平台证书（按 serial 匹配）
    wechat_cert = await get_wechat_certificate(serial)
    
    # 3. SHA256withRSA 验签
    try:
        wechat_cert.public_key().verify(
            base64.b64decode(signature),
            sign_str.encode(),
            PKCS1v15(),
            hashes.SHA256()
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid WeChatPay signature")
    
    # 4. 解密通知内容 (AES-256-GCM)
    resource = json.loads(body)["resource"]
    plaintext = aes_gcm_decrypt(
        key=settings.WECHAT_API_V3_KEY,
        nonce=resource["nonce"],
        ciphertext=resource["ciphertext"],
        associated_data=resource["associated_data"]
    )
    return json.loads(plaintext)
```

**环境变量**:
```env
WECHAT_MCH_ID=1234567890              # 商户号
WECHAT_API_V3_KEY=xxxxxxxxxxxxxxxx    # API v3 密钥（32字节）
WECHAT_MCH_PRIVATE_KEY_PATH=./certs/apiclient_key.pem
WECHAT_MCH_CERT_SERIAL=xxxxxx         # 商户证书序列号
```

### 5.7 Books Metadata (`books.yaml`)
*   `PATCH /api/v1/books/{id}/metadata`: 更新书籍元数据（书名、作者）
*   `GET /api/v1/books/{id}`: 书籍详情（包含 `metadata_confirmed` 状态）

### 5.8 Push Notifications (`notifications.yaml`)

#### 5.8.1 设备注册与管理

##### `POST /api/v1/devices`

注册设备以接收推送通知。

**Request Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```typescript
{
  "platform": "ios" | "android" | "web",
  "token": string,              // APNs Device Token / FCM Registration Token
  "deviceId": string,           // 设备唯一标识 (UUID)
  "deviceName": string,         // 设备名称 (如 "iPhone 15 Pro")
  "appVersion": string,         // 应用版本号
  "osVersion": string           // 操作系统版本
}
```

**Response 201** (注册成功):
```typescript
{
  "id": string,                 // 设备记录 ID
  "platform": "ios" | "android" | "web",
  "registeredAt": string,
  "notificationsEnabled": true
}
```

##### `DELETE /api/v1/devices/{device_id}`

注销设备推送。

**Response 204** (删除成功)

##### `GET /api/v1/devices`

获取当前用户所有注册设备列表。

**Response 200**:
```typescript
{
  "devices": [
    {
      "id": string,
      "platform": "ios" | "android" | "web",
      "deviceName": string,
      "lastActiveAt": string,
      "notificationsEnabled": boolean
    }
  ]
}
```

#### 5.8.2 推送通知类型定义

**NotificationType 枚举**:
```typescript
enum NotificationType {
  // 系统通知
  OCR_COMPLETED = "ocr_completed",           // OCR 处理完成
  OCR_FAILED = "ocr_failed",                 // OCR 处理失败
  BOOK_READY = "book_ready",                 // 书籍处理完成可阅读
  
  // 订阅通知
  SUBSCRIPTION_EXPIRING = "sub_expiring",    // 订阅即将到期（提前3天）
  SUBSCRIPTION_EXPIRED = "sub_expired",      // 订阅已过期
  PAYMENT_FAILED = "payment_failed",         // 支付失败
  PAYMENT_SUCCESS = "payment_success",       // 支付成功
  
  // 阅读提醒
  READING_REMINDER = "reading_reminder",     // 阅读提醒
  STREAK_WARNING = "streak_warning",         // 阅读连续天数警告
  
  // 社交功能（预留）
  SHARE_RECEIVED = "share_received",         // 收到分享
  COMMENT_REPLY = "comment_reply"            // 评论回复
}
```

**推送消息结构**:
```typescript
interface PushPayload {
  notificationType: NotificationType;
  title: string;
  body: string;
  data?: {
    bookId?: string;
    noteId?: string;
    deepLink?: string;           // 如 "athena://books/{id}"
    [key: string]: any;
  };
  badge?: number;                // iOS 角标数
  sound?: string;                // 通知音效
  priority?: "high" | "normal";  // 消息优先级
}
```

#### 5.8.3 后端推送服务架构

**APNs 集成** (iOS):
```python
# 使用 PyAPNs2 库
from apns2.client import APNsClient
from apns2.payload import Payload

async def send_ios_notification(
    device_token: str, 
    notification: PushPayload
):
    client = APNsClient(
        credentials=settings.APNS_AUTH_KEY_PATH,
        use_sandbox=settings.APNS_USE_SANDBOX
    )
    payload = Payload(
        alert={"title": notification.title, "body": notification.body},
        badge=notification.badge,
        sound=notification.sound or "default",
        custom=notification.data
    )
    client.send_notification(device_token, payload, settings.APP_BUNDLE_ID)
```

**FCM 集成** (Android/Web):
```python
# 使用 Firebase Admin SDK
import firebase_admin
from firebase_admin import messaging

async def send_fcm_notification(
    registration_token: str,
    notification: PushPayload
):
    message = messaging.Message(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.body
        ),
        data=notification.data,
        token=registration_token,
        android=messaging.AndroidConfig(
            priority="high" if notification.priority == "high" else "normal"
        ),
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon="/icons/notification-icon.png"
            )
        )
    )
    messaging.send(message)
```

**环境变量**:
```env
# APNs (iOS)
APNS_AUTH_KEY_PATH=./certs/AuthKey_XXXXX.p8
APNS_KEY_ID=XXXXXXXXXX
APNS_TEAM_ID=XXXXXXXXXX
APNS_USE_SANDBOX=false
APP_BUNDLE_ID=com.athena.reader

# FCM (Android/Web)
GOOGLE_APPLICATION_CREDENTIALS=./certs/firebase-service-account.json
```

#### 5.8.4 用户通知偏好设置

##### `PATCH /api/v1/users/me/notification-settings`

更新用户通知偏好。

**Request Body**:
```typescript
{
  "ocrNotifications": boolean,       // OCR 完成通知
  "subscriptionAlerts": boolean,     // 订阅相关提醒
  "readingReminders": boolean,       // 阅读提醒
  "reminderTime": string,            // 提醒时间 (HH:mm, 如 "20:00")
  "marketingNotifications": boolean  // 营销推广（默认 false）
}
```

**Response 200** (更新成功):
```typescript
{
  "updated": true,
  "settings": { /* 同上 */ }
}
```

---


---

## 7. OCR 服务触发接口

> **设计原则**：OCR 是收费/限额服务，由用户主动触发，而非上传后自动执行。

### 7.1 触发 OCR 处理

#### `POST /api/v1/books/{book_id}/ocr`

用户主动请求对图片型 PDF 进行 OCR 处理。支持 **OCR 复用（假 OCR）**（ADR-008）。

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `book_id` | UUID | 书籍 ID |

**处理逻辑**:
1. 正常配额检查和扣费（阶梯计费）
2. 检查是否可复用（相同 SHA256 已有 OCR 结果）
   - 可复用 → 假 OCR，秒级完成
   - 不可复用 → 真实 OCR，提交 Celery 任务

**Response 200** (OCR 复用 - 假 OCR):
```typescript
{
  "status": "instant_completed",
  "ocrResultKey": "ocr-result-xxx.json",
  "message": "OCR 结果已复用，处理完成。"
}
```

**Response 200** (成功加入队列 - 真实 OCR):
```typescript
{
  "status": "queued",
  "queuePosition": number,        // 队列位置
  "estimatedMinutes": number,     // 预计处理时间（分钟）
  "message": "OCR 任务已进入排队，预计 15 分钟后完成。您现在可以继续阅读该书，但暂时无法使用笔记和 AI 服务。"
}
```

**Response 400** (书籍已是文字型):
```typescript
{
  "error": "already_digitalized",
  "message": "该书籍已经是文字型，无需进行 OCR 处理。"
}
```

**Response 400** (超过页数限制):
```typescript
{
  "error": "ocr_max_pages_exceeded",
  "message": "该书籍页数超过 2000 页，暂不支持 OCR 处理。"
}
```

**Response 403** (OCR 配额不足):
```typescript
{
  "error": "ocr_quota_exceeded",
  "message": "您的 OCR 配额已用尽。免费用户每月可处理 3 本书籍，升级会员可获得更多配额。",
  "quota": {
    "used": 3,
    "limit": 3,
    "resetAt": "2025-01-01T00:00:00Z"
  }
}
```

**Response 409** (OCR 已在处理中):
```typescript
{
  "error": "ocr_in_progress",
  "message": "该书籍的 OCR 任务正在处理中，请稍候。",
  "queuePosition": 2,
  "estimatedMinutes": 10
}
```

> **商业逻辑（⚠️ 重要）**:
> - 用户**必须**点击 OCR 按钮才能看到 OCR 结果（商业闭环）
> - 即使是复用（假 OCR），也**必须**扣除配额（维护商业公平性）
> - 但不消耗 GPU 算力（降低运营成本）

### 6.2 查询 OCR 状态

#### `GET /api/v1/books/{book_id}/ocr/status`

查询书籍的 OCR 处理状态。

**Response 200**:
```typescript
{
  "bookId": string,
  "isDigitalized": boolean,       // 是否已是文字型
  "ocrStatus": "pending" | "processing" | "completed" | "failed" | null,
  "queuePosition"?: number,       // 仅当 status=pending 时返回
  "estimatedMinutes"?: number,
  "completedAt"?: string,         // 仅当 status=completed 时返回
  "errorMessage"?: string         // 仅当 status=failed 时返回
}
```

### 6.3 前端集成示例

```typescript
// 检测到图片型 PDF 后显示的对话框
function OcrPromptDialog({ book, onClose }: { book: Book; onClose: () => void }) {
  const [loading, setLoading] = useState(false);
  
  const handleOcrNow = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/books/${book.id}/ocr`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`OCR 已进入排队，预计 ${data.estimatedMinutes} 分钟后完成`);
        onClose();
      } else if (res.status === 403) {
        const data = await res.json();
        toast.error(data.message);
        // 显示升级会员弹窗
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>📖 书籍初检完成</DialogTitle>
      <DialogContent>
        <p>
          您上传的《{book.title}》经过雅典娜初步检查，此书为图片形式的 PDF 电子书。
          为了获得更好的阅读、笔记以及 AI 提问体验，我们建议您对此书进行图片转文本（OCR）服务。
        </p>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>稍后再处理</Button>
        <Button variant="primary" onClick={handleOcrNow} loading={loading}>
          🚀 马上转换
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## 8. 笔记/高亮冲突处理接口

### 7.1 获取冲突副本列表

#### `GET /api/v1/notes/conflicts`

获取当前用户所有存在冲突的笔记。

**Response 200**:
```typescript
{
  "conflicts": Array<{
    "originalId": string,         // 原始笔记 ID
    "originalContent": string,
    "originalUpdatedAt": string,
    "originalDeviceId": string,
    "conflictCopyId": string,     // 冲突副本 ID
    "conflictContent": string,
    "conflictUpdatedAt": string,
    "conflictDeviceId": string,
    "bookId": string,
    "bookTitle": string
  }>
}
```

### 7.2 解决冲突

#### `POST /api/v1/notes/{note_id}/resolve-conflict`

用户选择保留哪个版本或手动合并。

**Request Body**:
```typescript
{
  "resolution": "keep_original" | "keep_conflict" | "merge",
  "mergedContent"?: string  // 仅当 resolution=merge 时需要
}
```

**Response 200**:
```typescript
{
  "noteId": string,
  "content": string,
  "message": "冲突已解决"
}
```

---

## 9. 书籍元数据管理接口

### 8.1 更新书籍元数据

#### `PATCH /api/v1/books/{book_id}/metadata`

用户确认或修改书籍的元数据（书名、作者）。

**Request Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
If-Match: W/"<version>"  // 乐观锁（可选）
```

**Request Body**:
```typescript
{
  "title"?: string,           // 书籍名称
  "author"?: string,          // 作者
  "confirmed": boolean        // 是否标记为已确认（即使不修改也可确认）
}
```

**Response 200**:
```typescript
{
  "id": string,
  "title": string,
  "author": string | null,
  "metadataConfirmed": boolean,
  "metadataConfirmedAt": string | null,
  "metadataVersion": string,  // 版本指纹，用于心跳同步
  "version": number           // 乐观锁版本号
}
```

**Response 409** (版本冲突):
```typescript
{
  "error": "version_conflict",
  "message": "书籍信息已被其他设备修改，请刷新后重试",
  "currentVersion": number
}
```

### 8.2 元数据版本与 PowerSync 同步

元数据 (`title`, `author`) 的变更通过 PowerSync 自动同步。

**客户端写入逻辑**:
```typescript
// 使用 PowerSync 修改书籍元数据
const db = usePowerSyncDatabase();
await db.execute(
  'UPDATE books SET title = ?, author = ?, updated_at = ? WHERE id = ?',
  [newTitle, newAuthor, new Date().toISOString(), bookId]
);
// PowerSync 自动将变更同步到服务器
```

**冲突处理**:
- 元数据采用 LWW (Last-Write-Wins) 策略
- 冲突由 PowerSync Service 自动解决，无需客户端干预

### 8.3 元数据确认状态事件

当后台完成元数据提取后，通过 PowerSync 自动同步到客户端：

**事件类型**: `metadata_extracted` (通过 PowerSync 推送)

```typescript
// 前端监听 books 表变更
const books = useLiveQuery(
  'SELECT * FROM books WHERE id = ?',
  [bookId]
);

// 当 metadata_confirmed 变为 true 时，UI 自动更新
useEffect(() => {
  if (books?.[0]?.metadata_confirmed) {
    // 元数据已确认，可显示"已验证"标记
  }
}, [books]);
    "extracted": true,          // 是否成功提取到任何元数据
    "needsConfirmation": true   // 是否需要用户确认
  }
}
```

**前端响应**：
- 收到事件后弹出元数据确认对话框
- 用户确认后调用 `PATCH /api/v1/books/{id}/metadata`
- 如果用户选择「跳过」，可调用 `PATCH` 仅设置 `confirmed: true`

### 8.4 AI 对话中的元数据使用

> **⚠️ 重要设计决策**

书籍的 `title` 和 `author` 字段会作为上下文信息发送给上游 AI 模型，以提高回答的精准度。

**系统提示词模板** (参见 `api/app/ai.py`):
```python
BOOK_CONTEXT_PROMPT = """
用户正在阅读的文档信息：
- 书籍/文档名称：{title}
- 作者：{author if author else "未知"}

请基于以上背景信息，结合文档内容回答用户的问题。
"""
```

**影响说明**：
| 元数据状态 | AI 对话表现 |
|-----------|------------|
| 有书名+作者 | AI 能准确理解上下文，引用时使用正确书名 |
| 仅有书名 | AI 能识别文档，但可能无法关联作者信息 |
| 均为空/文件名 | AI 仅基于内容回答，可能缺乏背景理解 |

**私人资料场景**：
- 用户上传的可能不是书籍，而是个人文档、笔记、资料等
- 此时用户可跳过元数据确认
- AI 对话仍可正常使用，仅基于文档内容本身回答

---

## 10. SHA256 全局去重接口 (ADR-008)

### 9.1 秒传接口

#### `POST /api/v1/books/dedup_reference`

当 `upload_init` 返回 `dedup_available: true` 时，客户端调用此接口创建引用书籍，无需实际上传文件。

**Request Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```typescript
{
  "filename": string,           // 文件名
  "content_sha256": string,     // SHA256 哈希
  "size": number                // 文件大小 (bytes)
}
```

**Response 201** (成功创建引用书籍):
```typescript
{
  "id": string,                 // 新书籍 UUID
  "title": string,              // 继承自原书
  "author": string | null,
  "dedupType": "global",        // 去重类型
  "canonicalBookId": string,    // 原始书籍 ID
  "hasOcr": boolean,            // 原书是否已完成 OCR
  "coverImageKey": string | null,
  "downloadUrl": string         // 预签名下载 URL
}
```

**Response 404** (原书不存在):
```typescript
{
  "error": "canonical_not_found",
  "message": "去重引用的原始书籍不存在或已被删除"
}
```

**Response 403** (配额不足):
```typescript
{
  "error": "quota_exceeded",
  "message": "书籍配额已满，请升级会员或删除部分书籍"
}
```

### 9.2 书籍删除接口

#### `DELETE /api/v1/books/{book_id}`

删除书籍，采用**软删除/硬删除分层策略**（ADR-008）。

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `book_id` | UUID | 书籍 ID |

**处理逻辑**:
1. **私人数据**：始终立即删除（笔记、高亮、阅读进度、书架关联）
2. **引用书**（`canonical_book_id IS NOT NULL`）：
   - 物理删除书籍记录
   - 减少原书 `storage_ref_count`
   - 检查原书是否需要清理
3. **原书**（`canonical_book_id IS NULL`）：
   - 有引用（`ref_count > 1`）→ 软删除（设置 `deleted_at`）
   - 无引用（`ref_count <= 1`）→ 硬删除（清理所有公共数据）

**Response 200** (删除成功):
```typescript
{
  "message": "书籍已删除",
  "deleteType": "soft" | "hard",  // 删除类型
  "cleanedResources"?: {          // 仅硬删除时返回
    "file": boolean,
    "cover": boolean,
    "ocrResult": boolean,
    "vectorIndex": boolean
  }
}
```

**Response 404** (书籍不存在):
```typescript
{
  "error": "book_not_found",
  "message": "书籍不存在或已被删除"
}
```

### 9.3 公共数据 vs 私人数据

| 数据类型 | 所有者 | 软删除时 | 硬删除时 |
|---------|-------|---------|----------|
| S3 文件 (PDF/EPUB) | 共享 | ✅ 保留 | ❌ 删除 |
| 封面图片 | 共享 | ✅ 保留 | ❌ 删除 |
| OCR 双层 PDF | 共享 | ✅ 保留 | ❌ 删除 |
| 向量索引 (pgvector) | 共享 | ✅ 保留 | ❌ 删除 |
| 笔记/高亮 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |
| 阅读进度 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |
| 书架关联 | 用户私有 | ❌ 立即删除 | ❌ 立即删除 |

> **设计原理**：
> - 当多个用户共享同一文件时，删除不应影响其他用户
> - 只有最后一个用户删除时，才物理清理公共数据
> - 私人数据始终立即删除，保护用户隐私

---

## 10. 管理后台 API (`admin.yaml`)

> **访问控制**：Admin API 仅限具有 `admin` 角色的用户访问。所有请求需通过 `X-Admin-Token` 或具有 admin 权限的 JWT 认证。

### 10.1 系统设置管理

#### `GET /api/v1/admin/settings`

获取所有系统设置。

**Request Headers**:
```
Authorization: Bearer <admin_access_token>
```

**Response 200**:
```typescript
{
  "settings": [
    {
      "key": "ocr_free_quota",
      "value": "3",
      "type": "integer",
      "description": "免费用户每月 OCR 配额",
      "updatedAt": "2024-01-15T10:30:00Z",
      "updatedBy": "admin@athena.app"
    },
    {
      "key": "max_upload_size_mb",
      "value": "100",
      "type": "integer",
      "description": "单文件最大上传大小 (MB)"
    },
    {
      "key": "maintenance_mode",
      "value": "false",
      "type": "boolean",
      "description": "维护模式开关"
    }
  ]
}
```

#### `PATCH /api/v1/admin/settings/{key}`

更新单个系统设置。

**Request Body**:
```typescript
{
  "value": string,
  "reason": string              // 修改原因（审计日志）
}
```

**Response 200**:
```typescript
{
  "key": "ocr_free_quota",
  "oldValue": "3",
  "newValue": "5",
  "updatedAt": "2024-01-15T11:00:00Z",
  "updatedBy": "admin@athena.app"
}
```

#### `POST /api/v1/admin/settings`

创建新的系统设置。

**Request Body**:
```typescript
{
  "key": string,
  "value": string,
  "type": "string" | "integer" | "boolean" | "json",
  "description": string
}
```

### 10.2 用户管理

#### `GET /api/v1/admin/users`

获取用户列表（分页）。

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `page` | integer | 页码，默认 1 |
| `limit` | integer | 每页数量，默认 20，最大 100 |
| `search` | string? | 邮箱或昵称搜索 |
| `membership` | string? | 筛选会员类型：`free` / `pro` / `expired` |
| `sort` | string | 排序字段：`created_at` / `last_active_at` |

**Response 200**:
```typescript
{
  "users": [
    {
      "id": "user-uuid",
      "email": "user@example.com",
      "displayName": "张三",
      "membership": "pro",
      "membershipExpireAt": "2025-06-01T00:00:00Z",
      "booksCount": 42,
      "notesCount": 156,
      "createdAt": "2023-01-15T10:30:00Z",
      "lastActiveAt": "2024-01-14T18:20:00Z",
      "isActive": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1250,
    "totalPages": 63
  }
}
```

#### `PATCH /api/v1/admin/users/{user_id}`

更新用户信息（管理员操作）。

**Request Body**:
```typescript
{
  "isActive"?: boolean,                   // 启用/禁用账户
  "membershipExpireAt"?: string,          // 手动调整会员到期时间
  "freeOcrUsage"?: integer,               // 重置 OCR 配额
  "reason": string                        // 操作原因（必填）
}
```

### 10.3 统计报表

#### `GET /api/v1/admin/stats/overview`

获取系统概览统计。

**Response 200**:
```typescript
{
  "users": {
    "total": 12500,
    "activeToday": 850,
    "activeThisWeek": 3200,
    "newThisMonth": 420,
    "proMembers": 2100
  },
  "books": {
    "total": 85000,
    "uploadedToday": 320,
    "totalStorageGB": 1250.5
  },
  "ocr": {
    "processedToday": 45,
    "queueLength": 12,
    "avgProcessingMinutes": 8.5
  },
  "ai": {
    "conversationsToday": 1200,
    "tokensUsedToday": 2500000,
    "avgTokensPerConversation": 2083
  }
}
```

#### `GET /api/v1/admin/stats/revenue`

获取收入统计。

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `period` | string | 统计周期：`day` / `week` / `month` |
| `from` | ISO8601 | 起始日期 |
| `to` | ISO8601 | 结束日期 |

**Response 200**:
```typescript
{
  "period": "month",
  "from": "2024-01-01",
  "to": "2024-01-31",
  "revenue": {
    "total": 52800.00,
    "currency": "CNY",
    "breakdown": {
      "apple_iap": 28500.00,
      "google_play": 12300.00,
      "stripe": 8500.00,
      "wechat": 3500.00
    }
  },
  "subscriptions": {
    "new": 180,
    "renewed": 420,
    "cancelled": 35,
    "churnRate": 0.054
  }
}
```

### 10.4 审计日志

#### `GET /api/v1/admin/audit-logs`

获取管理员操作审计日志。

**Query Parameters**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| `adminId` | UUID? | 筛选特定管理员 |
| `action` | string? | 筛选操作类型 |
| `from` | ISO8601 | 起始时间 |
| `to` | ISO8601 | 结束时间 |

**Response 200**:
```typescript
{
  "logs": [
    {
      "id": "log-uuid",
      "adminEmail": "admin@athena.app",
      "action": "update_user_membership",
      "targetType": "user",
      "targetId": "user-uuid",
      "changes": {
        "membershipExpireAt": {
          "from": "2024-01-15T00:00:00Z",
          "to": "2025-01-15T00:00:00Z"
        }
      },
      "reason": "用户投诉支付问题，延长一年会员",
      "timestamp": "2024-01-14T16:30:00Z",
      "ipAddress": "192.168.1.100"
    }
  ]
}
```

---

> **文档结束** - 数据同步协议请参见 Section 3 (App-First 数据同步协议)。
