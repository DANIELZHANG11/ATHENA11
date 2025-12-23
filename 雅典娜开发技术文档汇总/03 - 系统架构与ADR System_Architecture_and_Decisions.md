# 03 - 系统架构与 ADR (System Architecture & Decisions)

> 版本：v2.1 (App-First)
> 定位：系统的物理蓝图与决策档案。任何基础设施变更必须先更新本文档。

## 1. 系统概览 (System Overview)
- Monorepo：`api`（后端）+ `web`（前端/App）+ `contracts`（OpenAPI 契约）。
- 部署：
    - **Backend**: Docker Compose (PostgreSQL, PowerSync Service, Calibre, Celery).
    - **Frontend**: **Capacitor (Android/iOS)** + Web (WASM).
- 核心理念：**App First**, **Offline First (Real)**, **Sync via PowerSync**.

## 2. 技术栈选型 (Tech Stack Matrix)

### 2.1 后端 (Backend)
- Language：Python 3.11
- Framework：FastAPI `0.115.4`
- ORM：SQLAlchemy `2.0.36`
- **Sync Engine**: **PowerSync Service (Open Edition)**
- **Object Storage**: **MinIO** (S3 Compatible)
- **Book Processing**: **Calibre CLI (ebook-polish/meta)**
- Database：PostgreSQL + **pgvector** (Vector Search)
- Task Queue：Celery `5.4.0`
- Broker/Cache：Valkey

### 2.2 前端 (Frontend/Mobile)
- Framework：React `18.3.1`
- **Mobile Runtime**: **Capacitor 6.x**
- **Local Database**: **SQLite** (Native Plugin on Mobile, WASM on Web)
- **Sync SDK**: **PowerSync SDK**
- Build Tool：Vite `5.4.10`
- Language：TypeScript `^5.6.3`
- Styling：Tailwind CSS `4.1.17` + Ionic Framework (Components)
- State：Zustand (UI State), **Live Query** (Data State)

... (Existing Content Preserved: 2.3 - 2.5 Dependency Graph, etc.) ...

## 3. 离线优先架构 (App-First Architecture)


### ADR-007: App-First Architecture (SQLite + PowerSync)
> **状态**: **ACTIVE** ✅

#### 核心决策
1.  **Native Edge Database**: 客户端使用 SQLite（通过 Capacitor/WASM）作为本地数据库，不使用 IndexedDB。
    -   **Mobile**: 使用 `capacitor-sqlite` 调用原生 SQLite，性能极高，无存储限制。
    -   **Web**: 使用 `sqlite-wasm` over `OPFS`，实现近似原生的性能。
2.  **Sync Engine**: 采用 **PowerSync**。
    -   **协议**: 基于流式复制 (Streaming Replication)，而非轮询 (Polling)。
    -   **一致性**: 最终一致性 (Eventual Consistency)。
3.  **Data Flow**:
    ```text
    UI <--> SQLite (Local) <--> PowerSync SDK <---(Sync)---> PowerSync Service <--> PostgreSQL
    ```
    -   前端代码**只读写本地 SQLite**，完全不直接调 API (Auth/Billing 除外)。
    -   同步在后台自动进行。

#### 数据与功能分层
-   **Auth/Billing**: 依然走 HTTPS API (FastAPI)。
-   **User Data (Notes, Progress, Settings)**: 走 PowerSync (SQLite)。
-   **Binary Assets (Covers, EPUBs)**: 走 Capacitor Filesystem + CDN (S3)。

### 3.1 PowerSync Service 拓扑

| 组件 | 配置 | 说明 |
| :--- | :--- | :--- |
| `powersync` 容器 | 镜像 `powersync/service:latest`，端口 `8090` | 通过 gRPC/WebSocket 为 SDK 提供流式同步 |
| PostgreSQL 连接 | 复用 `POSTGRES_HOST/USER/PASSWORD`，单独 schema `powersync` | 存储订阅 offset、上传队列、冲突日志 |
| sync_rules.yaml | 定义 10 个同步表（见下表）的列映射与过滤条件 | 与 `04_DB` 同步维护 |
| 监控 | `/metrics` 暴露 Prometheus 指标：`powersync_stream_lag`, `powersync_upload_errors_total` | 纳入 07_DevOps |

**PowerSync 同步表清单（共 9 个）**：
| # | 表名 | 同步方向 | 冲突策略 |
|---|:-----|:--------|:---------|
| 1 | `books` | ↕ 双向 | LWW（仅元数据：title/author/deleted_at） |
| 2 | `reading_progress` | ↕ 双向 | LWW |
| 3 | `reading_sessions` | ↕ 双向 | LWW |
| 4 | `notes` | ↕ 双向 | Conflict Copy |
| 5 | `highlights` | ↕ 双向 | Conflict Copy |
| 6 | `bookmarks` | ↕ 双向 | 无 |
| 7 | `shelves` | ↕ 双向 | 字段合并 |
| 8 | `shelf_books` | ↕ 双向 | 无 |
| 9 | `user_settings` | ↕ 双向 | JSONB 合并 |

> **权威来源**：`docker/powersync/sync_rules.yaml` + `web/src/lib/powersync/schema.ts`  
> **详细字段映射**：见 `04_Database_Schema.md` Section 3.2
> **注意**：阅读统计通过前端聚合 `reading_sessions` + `reading_progress` 计算，不作为独立同步表。 

### 3.2 客户端 SQLite 实现

1. **Web**：`sqlite-wasm` 运行于 OPFS，提供备份/恢复脚本。
2. **Mobile (Capacitor)**：`capacitor-community/sqlite` + 原生加密插件（可选），支持增量 Schema 迁移与版本回滚。
3. **Provider 层**：`PowerSyncProvider` 包裹在 `App.tsx`，负责：
    - 初始化数据库与 schema
    - 监听网络状态并调用 SDK `connect()/disconnect()`
    - 暴露 `useLiveQuery`、`useMutation` 辅助函数
4. **数据仓储 (Repositories)**：`lib/powersync/repo/*.ts` 封装查询与写入，替代 `*Storage.ts`。

### 3.3 冲突策略

| 实体 | 策略 | 技术实现 |
| :--- | :--- | :--- |
| `reading_progress` | LWW (last_write_wins) | `updated_at` 由客户端生成，PostgreSQL 触发器比较并拒绝旧写入 |
| `notes`/`highlights` | Conflict Copy | 触发器检测同书籍+位置冲突，写入 `conflict_of` 副本，由前端提示合并 |
| `shelves`/`user_settings` | 字段级合并 (merge) | PowerSync `merge_columns` 特性 + JSONB patch |
| `books` metadata | LWW（客户端可修改） | PowerSync 允许修改 title/author/deleted_at，文件相关字段（minio_key, sha256）服务端控制 |

### 3.4 Feature Flag 设计

| 名称 | 位置 | 默认值 | 行为 |
| :--- | :--- | :--- | :--- |
| `APP_FIRST_ENABLED` | `web/src/config/featureFlags.ts` | `true` | 控制是否注入 PowerSync Provider（已启用） |
| `POWERSYNC_UPLOAD_ENABLED` | 后端环境变量 | `true` | 控制 PowerSync Service 是否允许写回 |

---

### [NEW] ADR-008: SHA256 全局去重与 OCR 复用
> **版本**: v1.1
> **状态**: **APPROVED** ✅


#### 核心决策
1. **存储去重**: 通过 `content_sha256` 字段实现文件级去重，相同文件只存储一份。
2. **OCR 双层 PDF**: OCRmyPDF + PaddleOCR 产出双层 PDF (Dual-Layer PDF)，前端 PDF.js 直接读取文字层。
3. **OCR 复用**: 相同 SHA256 的书籍可复用已有双层 PDF，实现"假 OCR"秒级完成。
4. **引用计数**: `storage_ref_count` 跟踪共享存储的引用数，支持软删除/硬删除分层策略。
5. **秒传接口**: `POST /books/dedup_reference` 允许跳过上传直接创建引用书。

> **⚠️ 废弃说明**：原 `ocr_result_key` (JSON Sidecar) 方案已废弃，改用 `ocr_pdf_key` (双层 PDF)。
> 详见 `02_Functional_Specifications_PRD.md` 中 B.2 节完整说明。

### [NEW] ADR-008.1: OCR 双层 PDF (Dual-Layer PDF)
> **版本**: v1.0
> **状态**: **APPROVED** ✅

#### 问题背景
原设计使用 JSON Sidecar 存储 OCR 结果，存在以下问题：
1. 前端需额外请求 JSON 文件并解析
2. 文字与渲染坐标分离，实现复杂
3. JSON 文件增加存储和传输成本

#### 核心决策
采用 **双层 PDF (Dual-Layer PDF)** 替代 JSON Sidecar：

| 方面 | JSON Sidecar (废弃) | 双层 PDF (采用) |
|------|--------------------|--------------------|
| OCR 引擎 | PaddleOCR → JSON | OCRmyPDF + PaddleOCR → PDF |
| 存储产物 | `ocr-result-xxx.json` | `ocr.pdf` (含隐藏文字层) |
| 前端读取 | `fetch()` + JSON 解析 | PDF.js `page.getTextContent()` |
| 文字定位 | 需手动映射坐标 | PDF 内置，自动对齐 |
| 复用方式 | 复制 JSON Key | 复制 PDF 文件 |

#### 技术实现
```python
# OCRmyPDF CLI 示例
ocrmypdf --output-type pdf --deskew --optimize 1 \\
    --pdf-renderer hocr \\
    --tesseract-timeout 180 \\
    --jobs 4 \\
    --plugin paddleocr_plugin \\
    input.pdf output.pdf
```

#### 前端使用
```typescript
// PDF.js 读取文字层
const page = await pdfDoc.getPage(pageNum);
const textContent = await page.getTextContent();
// textContent.items 包含 { str, transform, width, ... }
```

#### 数据库字段变更
- 废弃: `ocr_result_key` (TEXT) - JSON 文件 MinIO Key
- 新增: `ocr_pdf_key` (TEXT) - 双层 PDF MinIO Key


### ADR-009: Local Asset Cache (S3 Protection)
> **状态**: **PROPOSED** ⚠️
*   **问题**: S3 Presigned URL 有效期短，且每次加载消耗流量/CDN 费用。
*   **决策**: 前端必须实现只读缓存层。
    1.  从 S3 下载图片 -> 保存到 OPFS (Origin Private File System) 或 Capacitor Filesystem -> 获取 `file://` 或 `blob:` URL。
    2.  SQLite `local_book_files` 表映射 `s3_key` -> `local_path`。
    3.  `Image` 组件优先读取本地，失败才请求网络并触发下载。

### ADR-010: Client-side Segmentation (Chinese Search)
> **状态**: **PROPOSED** ⚠️
*   **问题**: SQLite FTS5 默认分词器 (unicode61) 不支持中文语义分词，搜索体验差。
*   **决策**: **前端预分词** (Pre-segmentation)。
    1.  在写入 SQLite 前，使用浏览器/系统原生 `Intl.Segmenter` (zh-CN) 对文本进行分词。
    2.  分词结果（如 "经济 经济学"）存入隐藏的 FTS 索引列。
    3.  搜索时，同样对用户 Query 进行分词后再查询。

### ADR-011: Sync Debounce (Battery & Net)
> **状态**: **PROPOSED** ⚠️
*   **问题**: 阅读进度更新极快 (每页)，实时上传导致电量/流量浪费。
*   **决策**: **Throttled Upload**。
    1.  写入 SQLite: **Immediate** (保证 UI 响应和本地一致性)。
    2.  Trigger PowerSync Upload: **Debounced** (e.g., 30s delay or onPause).

## 4. 移动端兼容性 (Mobile Compatibility)
*   **强制升级**: 在 API Gateway 层检查 `X-Client-Version` Header。低于最小兼容版本 (MinSupportedVersion) 的请求直接返回 `426 Upgrade Required`。
*   **Schema 迁移**: 移动端 SQLite Schema 变更遵循 **Additive Only** (只增不减) 原则。不允许删除列或修改列类型，只能新增 Nullable 列。

### ADR-012: 移动端 Schema 优雅演进 (Elegant Schema Migration)
> **状态**: **PROPOSED** ⚠️
> **背景**: 移动端 App 更新滞后，无法像 Web 一样强制用户刷新。一旦后端删除了某个同步字段，旧版 App 的 PowerSync 可能会崩溃或报错。
> **决策**: 采用 **"Expand & Contract" (扩展-收缩)** 四阶段策略。

1.  **Phase 1: Expand (扩展)**
    *   后端 DB 新增字段 `new_column`。
    *   后端 API/Sync 兼容层同时写入 `old_column` 和 `new_column`。
    *   发布新版 App (v2)，读取 `new_column`，但仍能处理 `old_column`。
2.  **Phase 2: Migrate (迁移)**
    *   运行后台脚本，将存量数据的 `old_column` 刷入 `new_column`。
    *   此时旧版 App (v1) 读写 `old_column`，新版 App (v2) 读写 `new_column`。
3.  **Phase 3: Deprecate (废弃)**
    *   等待绝大多数用户升级到 v2+。
    *   发布新版 App (v3)，代码中完全移除对 `old_column` 的引用。
    *   **警告**：此时 v1 用户可能无法正常同步该字段，但 App 不会崩溃（PowerSync 容错）。
4.  **Phase 4: Contract (收缩)**
    *   后端 DB 正式删除 `old_column`。
    *   此操作必须在 Phase 3 实施数月后进行。

**在 CI/CD 中的强制措施**：
*   **Lint Check**: 在 CI 中检查 `alembic` 迁移脚本，严禁检测到 `DROP COLUMN` 或 `ALTER COLUMN TYPE` 操作，除非带有特权 Tag `#FORCE_DROP`。

---

## 5. 前端技术栈 (Frontend Tech Stack)

### ADR-013: Expo + Tamagui + Solito + Next.js Monorepo
> **版本**: v1.0
> **状态**: **APPROVED** ✅
> **日期**: 2024-12

#### 问题背景

雅典娜需要同时覆盖 iOS、Android、Web 三端，并保持以下核心需求：
1. **100% AI 驱动开发**：代码生成需要 AI 能够理解的统一语法（Tailwind 语境）
2. **离线优先 (Local-First)**：深度集成 SQLite + PowerSync
3. **跨平台共享**：组件和业务逻辑在三端高度复用
4. **原生级性能**：特别是阅读器场景的文本渲染性能
5. **Apple 像素级对齐**：设计系统需要严格遵循 Apple HIG

原有技术栈 (Capacitor + React + Tailwind) 存在以下问题：
- 移动端非原生渲染，性能瓶颈
- Web 和 Native 组件无法真正共享
- Tailwind 在 React Native 生态兼容性差

#### 核心决策

采用 **Expo + Tamagui + Solito + Next.js** 全栈跨平台架构：

```
┌────────────────────────────────────────────────────────────┐
│                     Monorepo 结构                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  apps/                                                     │
│  ├── next/           # Next.js Web 应用                    │
│  │   └── pages/      # Web 路由 (文件系统路由)              │
│  └── expo/           # Expo Native 应用 (iOS/Android)      │
│      └── app/        # Expo Router (文件系统路由)          │
│                                                            │
│  packages/                                                 │
│  ├── ui/             # Tamagui 共享组件库                  │
│  │   ├── tamagui.config.ts    # Design Tokens              │
│  │   └── src/                 # 组件源码                   │
│  └── app/            # 共享业务逻辑                        │
│      ├── provider/   # PowerSync Provider                  │
│      ├── hooks/      # 共享 Hooks                          │
│      └── features/   # 功能模块                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 技术栈详解

| 层级 | 技术选型 | 版本 | 职责 |
|:-----|:---------|:-----|:-----|
| **Build** | Turborepo | ^2.0 | Monorepo 构建编排 |
| **Web Runtime** | Next.js | ^14.0 | SSR/SSG、Web 路由、API Routes |
| **Native Runtime** | Expo | ^51.0 | iOS/Android 原生容器、Expo Router |
| **跨平台路由** | Solito | ^4.0 | 统一导航 API (`useRouter`) |
| **UI 框架** | Tamagui | ^1.100 | 跨平台组件库、Design Tokens |
| **状态管理** | Zustand | ^4.5 | 轻量 UI 状态 |
| **数据层** | PowerSync + op-sqlite | latest | 本地优先同步 |
| **图标** | Lucide | ^0.400 | 统一图标库 |

#### 选型理由

| 需求 | Tamagui 优势 | 对比 React Native Paper / NativeBase |
|:-----|:------------|:-------------------------------------|
| **AI 驱动** | 类 Tailwind 语法 (`$space.4`, `$color.blue`) | AI 可直接生成符合规范的代码 |
| **性能** | 编译时样式提取，零运行时开销 | 其他方案有运行时 CSS-in-JS 开销 |
| **跨平台** | 同一组件渲染为 Web DOM + Native View | 真正的代码共享，非"适配" |
| **Apple HIG** | 内置 Spring 动画、Squircle 圆角 | 原生支持 Apple 设计语言 |
| **Design Tokens** | 原生支持 Token 系统 | 其他方案需要额外封装 |

| 需求 | Solito 优势 | 对比手动封装 |
|:-----|:-----------|:------------|
| **路由统一** | `useRouter().push('/book/123')` 跨平台通用 | 无需分别调用 `next/router` 和 `expo-router` |
| **链接组件** | `<SolitoLink href="/settings">` 自动适配 | 自动渲染为 `<a>` (Web) 或 `TouchableOpacity` (Native) |

| 需求 | op-sqlite 优势 | 对比 expo-sqlite |
|:-----|:--------------|:-----------------|
| **性能** | C++ 实现，批量操作快 10x | expo-sqlite 使用 JS bridge |
| **PowerSync 集成** | PowerSync 官方推荐 | 更好的同步性能 |

#### 目录规范

```
athena/
├── apps/
│   ├── next/                    # Next.js Web App
│   │   ├── pages/               # 页面路由
│   │   ├── public/              # 静态资源
│   │   └── next.config.js       # Next.js 配置
│   └── expo/                    # Expo Native App
│       ├── app/                 # Expo Router 路由
│       ├── assets/              # Native 资源
│       └── app.json             # Expo 配置
├── packages/
│   ├── ui/                      # 共享 UI 组件
│   │   ├── src/
│   │   │   ├── tamagui.config.ts   # Design Tokens
│   │   │   ├── Button.tsx          # 按钮组件
│   │   │   ├── Card.tsx            # 卡片组件
│   │   │   ├── BookListCard.tsx    # 书籍卡片
│   │   │   └── typography.ts       # 排版组件
│   │   └── package.json
│   └── app/                     # 共享业务逻辑
│       ├── provider/
│       │   └── powersync/       # PowerSync 初始化
│       ├── hooks/               # 共享 Hooks
│       ├── features/            # 功能模块
│       └── package.json
├── .cursorrules                 # AI 编码规则
├── turbo.json                   # Turborepo 配置
└── package.json                 # 根 package.json
```

#### 关键约束

1. **零硬编码**：所有样式必须通过 Tamagui Token (`$space.4`, `$color.systemBlue`) 引用
2. **图标唯一来源**：仅允许从 `lucide-react` / `lucide-react-native` 引入
3. **组件位置**：可复用组件必须放在 `packages/ui`，业务逻辑放在 `packages/app`
4. **路由统一**：使用 Solito 的 `useRouter()`，禁止直接使用 `next/router` 或 `expo-router`
5. **数据层**：UI 只能读取 PowerSync 暴露的 SQLite 数据，禁止直接调用 REST API

#### 迁移策略

从现有 Capacitor 架构迁移采用**渐进式策略**：

1. **Phase 1**：建立 Monorepo 骨架，配置 Tamagui Design Tokens
2. **Phase 2**：迁移共享组件到 `packages/ui`
3. **Phase 3**：实现 PowerSync Provider 在新架构下的初始化
4. **Phase 4**：逐页面迁移，优先迁移阅读器核心功能
5. **Phase 5**：废弃旧 Capacitor 项目
