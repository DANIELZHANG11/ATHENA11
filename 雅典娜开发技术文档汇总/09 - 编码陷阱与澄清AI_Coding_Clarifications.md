# 09 - 编码陷阱与澄清 (AI Coding Clarifications)

> **版本**：v1.1
> **定位**：本文档是 "AI 开发者" 的**避坑指南**。当代码逻辑与现有文档（00-08）存在语义模糊时，**以本文档为准**。
> **核心目标**：消除布尔陷阱、明确隐式契约、填补 Schema 黑盒。

---

## 0. 字段命名统一规范 (Field Naming Standards) 🔑

> **重要**：以下是字段命名的权威定义。如果其他文档中存在旧名称，**以本节为准**。

### 0.1 核心字段重命名

| 旧名称 (Deprecated) | 新名称 (Canonical) | 说明 |
|:-------------------|:------------------|:-----|
| `is_digitalized` | `has_text_layer` | 语义更清晰：是否有可提取的文字层 |
| `reading_sessions` | `reading_time_log` | 阅读**时长**记录表，每次打开阅读器创建一条 |
| `reading_progress` | `book_position` | 阅读**位置**记录表，存储 CFI/页码/进度 |
| `total_ms` | `duration_ms` | 时长字段，单位毫秒 |

### 0.2 `has_text_layer` 语义定义

| 值 | 含义 | 前端映射 (`is_image_based`) |
|:---|:----|:---------------------------|
| `TRUE` | **文字型** (EPUB/Text-PDF)，可直接提取文本 | `FALSE` (不需要 OCR) |
| `FALSE` | **图片型** (Scan-PDF)，没有文字层 | `TRUE` (需要 OCR) |
| `NULL` | **未检测**，尚未进行文字层检测 | `TRUE` (假设需要 OCR) |

**前端计算公式**:
```typescript
const is_image_based = !book.has_text_layer || (book.has_text_layer && book.text_layer_confidence < 0.8);
```

### 0.3 阅读相关表职责划分

| 表名 (Canonical) | 职责 | 主键 | 核心字段 |
|:----------------|:----|:-----|:--------|
| `reading_time_log` | 记录每次阅读会话的**时长** | `id (UUID)` | `user_id`, `book_id`, `duration_ms`, `device_id` |
| `book_position` | 记录每本书的当前**阅读位置** | `(user_id, book_id)` | `progress`, `last_cfi`, `last_page`, `finished_at` |
| `reading_daily` | 每日阅读统计（仅服务端） | `(user_id, day)` | `total_duration_ms` |

### 0.4 软删除字段映射

| PostgreSQL | SQLite (PowerSync) | 说明 |
|:-----------|:-------------------|:-----|
| `deleted_at` (TIMESTAMPTZ, Nullable) | `is_deleted` (INTEGER, 0/1) | PowerSync Sync Rules 自动转换 |

**Sync Rules 转换公式**:
```yaml
# 从 PostgreSQL → SQLite
is_deleted: "CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END"

# 从 SQLite → PostgreSQL (在后端 trigger 中)
deleted_at: "CASE WHEN is_deleted = 1 THEN NOW() ELSE NULL END"
```

---

## 1. 语义陷阱：布尔值逻辑 (Boolean Logic Traps)

### 1.1 书籍类型：后端 vs 前端
> **高危**：后端字段与前端计算属性含义**完全相反**。
> **⚠️ 已重命名**：旧名称 `is_digitalized` 现已更名为 `has_text_layer`。

*   **后端 (PostgreSQL)**: `has_text_layer` (BOOLEAN)
    *   `TRUE`: **文字型** (EPUB/Text-PDF)。可以直接提取文本，无需 OCR。
    *   `FALSE`: **图片型** (Scan-PDF)。没有文字层，必须 OCR。
*   **前端 (SQLite/UI)**: `is_image_based` (Computed)
    *   `TRUE`: 需要显示 OCR 按钮。
    *   **计算公式**:
        ```typescript
        const is_image_based = !book.has_text_layer || (book.has_text_layer && book.text_layer_confidence < 0.8);
        ```

### 1.2 只读锁：Admin vs User
*   `is_archived`: 仅管理员/系统可操作（逻辑删除）。
*   `is_read_only_mode`: 用户账户层级的状态（欠费/超额），**不是**书籍属性。

---

## 2. 数据库 Schema 补全 (Missing Schemas)

### 2.1 `books.meta` (JSONB)
> **权威定义**：这是书籍元数据的唯一结构。

```typescript
interface BookMeta {
  // 基础元数据
  page_count?: number;      // PDF/图片书必须，用于计费。EPUB 可选。
  isbn?: string;
  publisher?: string;
  publish_date?: string;    // ISO 8601 "YYYY-MM-DD"
  language?: string;        // "zh-CN", "en-US"

  // 目录结构 (Table of Contents)
  // 注意：这是递归结构
  toc?: Array<{
    label: string;          // 章节标题 (显示的文字)
    href: string;           // 跳转链接 (如 "chapter1.html" 或 "page=10")
    children?: ToCItem[];   // 子章节
  }>;
}
```

### 2.2 `user_settings.value` (JSONB)
> **权威定义**：用户偏好设置的键值对结构。

```typescript
// 针对不同 key 的 value 结构定义
type UserSettingsValue = 
  | { theme: 'light' | 'dark' | 'system' }          // key: "appearance"
  | { fontSize: number; fontFamily: string }        // key: "reader_preference"
  | { autoSync: boolean; cellularSync: boolean }    // key: "sync_config"
```

---

## 3. 向量存储：唯一事实来源 (Vector Storage)

> **消除幻觉**：项目已完全移除 OpenSearch/Elasticsearch，不存在该组件。

*   **存储位置**: **PostgreSQL `vectors` 表** (pgvector)。
*   **索引类型**: **HNSW** (`index_vectors_on_content_vector_hnsw`).
*   **操作方式**:
    *   **Python**: 使用 SQLAlchemy + `pgvector` 库。
    *   **SQL**: `ORDER BY embedding <=> :query_embedding LIMIT 5`.
*   **中文支持**:
    *   **向量搜索**: 依赖 Embedding 模型（语言无关）。
    *   **混合搜索**: 如需关键词过滤，使用 PostgreSQL 内置 TSVECTOR，**禁止**引入 Elasticsearch/OpenSearch。


---

## 4. PowerSync 权限黑盒 (Permission Boundaries)

> **消除幻觉**：本地数据库并非全字段可写。前端修改某些字段只会被后端静默丢弃。

### 4.1 严禁前端修改的字段 (Read-Only Fields)
以下字段在 `sync_rules.yaml` 中标记为 **No-Upload** 或被后端触发器拦截：
1.  `ocr_status`: **严禁前端修改**。OCR 状态流转仅由 Celery Worker 更新。前端只能读取以显示进度。
2.  `storage_ref_count`: **严禁前端修改**。这是后端维护的引用计数。
3.  `has_text_layer`: 仅由导入/OCR 任务更新。

### 4.2 前端可写字段 (Writable Fields)
1.  `last_read_position` (reading_time_log)
2.  `progress` (book_position)
3.  `content`, `color` (notes/highlights)
4.  `title`, `author` (books - 允许用户手动修正元数据)

---

## 5. 交互契约：只读锁与逃生舱 (UI Contracts)

### 5.1 只读锁 (Soft Lock) 表现
当 API 返回 `403 quota_exceeded` 时，前端交互规范：
1.  **新建笔记**：
    *   **允许**用户输入和点击保存。
    *   **写入**本地 SQLite (Success)。
    *   **上传** PowerSync (Fail -> Error Handler)。
    *   **UI 反馈**：笔记卡片显式 `CloudOff` 图标（带斜杠的云），Tooltip: "空间已满，暂存本地"。
2.  **严禁**：
    *   严禁 Disable 输入框。
    *   严禁在本地回滚（删除）这条笔记。

### 5.2 阅读器事件 (Reader Events)
Reader 组件的对外 Props 契约：
```typescript
interface ReaderProps {
  // 输入：当前位置
  location: string; // CFI 标准字符串，如 "epubcfi(/6/4!/4/2:0)"

  // 输出：位置变更
  // 注意：必须通过 Debounce (e.g. 500ms) 触发，不要每滚动一像素就触发
  onLocationChange: (cfi: string, percentage: number) => void;
}
```

---

## 6. 统计逻辑：时长与心跳 (Stats Logic)

> **📝 命名变更**：
> - 原 `total_ms` → `duration_ms`（更清晰）
> - 原 `reading_sessions` → `reading_time_log`（更准确）

### 6.1 `duration_ms` 的定义
*   **定义**：指 **本次阅读会话** 的持续时长，**不是** 历史累计总时长。
*   **重置时机**：每次打开书籍进入阅读器，开启一个新的会话记录，`duration_ms` 从 0 开始计时。


### 6.2 心跳包逻辑
*   **前端行为**：
    *   每 60 秒发送一次心跳。
    *   Payload: `{ session_id: "uuid", duration_ms: 60000 }` (1分钟), `{ duration_ms: 120000 }` (2分钟)...
    *   **注意**：发送的是**当前会话的累计值**，**不是增量**。
*   **后端行为**：
    *   PostgreSQL: `UPDATE reading_time_log SET duration_ms = GREATEST(duration_ms, new_val)`.
    *   **防止回滚**：如果网络乱序导致 "1分钟" 的包晚于 "2分钟" 的包到达，后端必须忽略较小的值。

---

## 7. 架构陷阱：HTTP 的诱惑 (The Siren Call of REST)

### 7.1 "为什么不能直接调 API？"
> **场景**：你发现 PowerSync 的配置有点麻烦，或者一时没想到怎么写本地 SQLite 的 SQL。
> **诱惑**：你看到 `05` 号文档里有 `POST /api/v1/notes` 接口。
> **陷阱**："我就直接调 API 存一下笔记吧，反正后端也能存进去。"

**绝对禁止**。
不是因为我们没有定义冲突处理（我们定义了），而是因为**App-First 架构的核心信任链会断裂**：
1.  **断网即死**：直接调 API 导致你的功能在飞机上、地铁里直接报错。
2.  **UI 假死**：API 请求有延迟，UI 需要 Spinner，破坏了"本地优先"的 0ms 响应体验。
3.  **状态分裂**：API 写入成功了，但本地 SQLite 还没同步回来。用户刷新页面，笔记"消失"了（直到 PowerSync 下一次拉取）。

**开发者铁律**：除文件上传/Auth/AI外，**忘掉 REST API 的存在**。只与本地 SQLite 说话。

