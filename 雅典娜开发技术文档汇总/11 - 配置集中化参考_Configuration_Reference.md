# 11 - 配置集中化参考 (Configuration Reference)

> **版本**：v1.0  
> **状态**：Active  
> **用途**：集中管理所有端口、超时、环境变量、system_settings 配置项，防止硬编码和配置分散

---

## 📋 文档导航

- [§1 端口分配表](#1-端口分配表-port-allocation)
- [§2 超时配置表](#2-超时配置表-timeout-configuration)
- [§3 环境变量清单](#3-环境变量清单-environment-variables)
- [§4 system_settings 键值表](#4-system_settings-键值表-system-settings)
- [§5 容器网络配置](#5-容器网络配置-container-network)

---

## §1 端口分配表 (Port Allocation)

> **约定**：Athena 项目使用 **4XXXX** 端口段，避免与系统服务和其他项目冲突。

### 1.1 外部访问端口

| 端口 | 服务 | 协议 | 环境 | 说明 |
|------|------|------|------|------|
| **48080** | Nginx / Traefik | HTTP | 生产/开发 | Web 入口（HTTP 反向代理） |
| **48443** | Nginx | HTTPS | 生产 | Web 入口（TLS 终结） |
| **48173** | Vite Dev Server | HTTP | 开发 | 前端开发服务器 |
| **48000** | API Server (FastAPI) | HTTP | 开发/生产 | 后端 API 服务 |
| **48090** | PowerSync | WS/HTTP | 开发/生产 | 同步服务（客户端连接） |

### 1.2 内部服务端口

| 端口 | 服务 | 协议 | 说明 |
|------|------|------|------|
| **45432** | PostgreSQL | TCP | 主数据库（仅内网访问） |
| **46379** | Valkey (Redis) | TCP | 缓存 + Celery Broker |
| **48333** | MinIO S3 API | HTTP | 对象存储 S3 兼容接口 |
| **48888** | MinIO Console | HTTP | 对象存储管理控制台 |
| **48085** | Tolgee | HTTP | 多语言管理平台 |
| **48081** | Calibre UI | HTTP | Calibre 转换服务 |
| **48082** | Calibre Web | HTTP | Calibre Web 界面 |
| **49091** | PowerSync Metrics | HTTP | Prometheus 指标导出 |

### 1.3 监控与日志端口

| 端口 | 服务 | 协议 | 说明 |
|------|------|------|------|
| **49090** | Prometheus | HTTP | 指标收集（预留） |
| **43100** | Grafana | HTTP | 监控面板（预留） |
| **43000** | Loki | HTTP | 日志聚合（预留） |

### 1.4 端口分配规则

| 范围 | 用途 | 示例 |
|------|------|------|
| **480XX** | 用户访问服务 | 48000(API), 48080(Web), 48090(Sync) |
| **481XX** | 工具服务 | 48081(Calibre), 48085(Tolgee) |
| **483XX** | 存储服务 | 48333(MinIO S3), 48888(MinIO Console) |
| **454XX** | 数据库 | 45432(PostgreSQL) |
| **463XX** | 缓存 | 46379(Valkey) |
| **490XX** | 监控 | 49090(Prometheus), 49091(PowerSync Metrics) |
| **431XX** | 可视化 | 43100(Grafana), 43000(Loki) |

---

## §2 超时配置表 (Timeout Configuration)

### 2.1 HTTP 请求超时

| 场景 | 超时时间 | 配置位置 | 说明 |
|------|----------|----------|------|
| **API 常规请求** | 30s | Nginx `proxy_read_timeout` | 普通 REST API 调用 |
| **文件上传** | 300s (5min) | Nginx `client_body_timeout` | 大文件上传 |
| **AI 流式响应** | 180s (3min) | Nginx `proxy_read_timeout` | SSE 流式传输 |
| **健康检查** | 5s | Docker Compose `healthcheck` | 容器健康检查 |

### 2.2 Celery 任务超时

| 任务类型 | soft_timeout | hard_timeout | 超时处理 |
|----------|--------------|--------------|----------|
| **Calibre 转换** | 4min | 5min | 标记 `failed` + `processing_error='timeout'` |
| **OCR 处理** | 25min | 30min | 标记 `failed` + `processing_error='timeout'` |
| **向量索引** | 8min | 10min | 标记 `failed` + 允许重试 |
| **封面提取** | 1min | 2min | 标记 `failed` + 允许重试 |

### 2.3 数据库连接超时

| 配置项 | 超时时间 | 配置位置 | 说明 |
|--------|----------|----------|------|
| `connect_timeout` | 10s | SQLAlchemy | 建立连接超时 |
| `statement_timeout` | 60s | PostgreSQL | 单条 SQL 执行超时 |
| `idle_in_transaction_session_timeout` | 300s | PostgreSQL | 事务空闲超时 |
| `server_idle_timeout` | 600s | PgBouncer | 空闲连接回收 |

### 2.4 同步超时

| 配置项 | 超时时间 | 说明 |
|--------|----------|------|
| PowerSync 心跳 | 30s | 客户端 ping 间隔 |
| PowerSync 断开重连 | 5s | 首次重连等待 |
| PowerSync 最大重连 | 60s | 指数退避最大值 |

### 2.5 WebSocket 关闭码

| 关闭码 | 含义 | 客户端处理 |
|--------|------|------------|
| `4000` | 通用错误 | 提示用户重试 |
| `4001` | 未授权 | 跳转登录页 |
| `4009` | 超时 | 自动重连 |
| `4429` | 限流 | 延迟后重连 |

---

## §3 环境变量清单 (Environment Variables)

### 3.1 数据库配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://user:pass@host:5432/athena` | ✅ |
| `DATABASE_POOL_SIZE` | 连接池大小 | `20` | ❌ |
| `DATABASE_MAX_OVERFLOW` | 连接池溢出 | `10` | ❌ |
| `DATABASE_ECHO` | 打印 SQL（开发） | `false` | ❌ |

### 3.2 缓存配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `REDIS_URL` | Valkey/Redis 连接串 | `redis://localhost:46379/0` | ✅ |
| `CELERY_BROKER_URL` | Celery Broker | `redis://localhost:46379/1` | ✅ |
| `CELERY_RESULT_BACKEND` | Celery Result | `redis://localhost:46379/2` | ✅ |

### 3.3 对象存储配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `MINIO_ENDPOINT` | MinIO 地址 | `localhost:48333` | ✅ |
| `MINIO_ACCESS_KEY` | 访问密钥 | `athena_access_key` | ✅ |
| `MINIO_SECRET_KEY` | 私密密钥 | `athena_secret_key` | ✅ |
| `MINIO_BUCKET_BOOKS` | 书籍存储桶 | `athena-books` | ❌ |
| `MINIO_BUCKET_COVERS` | 封面存储桶 | `athena-covers` | ❌ |
| `MINIO_SECURE` | 使用 HTTPS | `false` | ❌ |

### 3.4 PowerSync 配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `POWERSYNC_PORT` | 服务端口 | `48090` | ❌ |
| `POWERSYNC_DATABASE_URL` | 直连 PostgreSQL | `postgresql://...` | ✅ |
| `POWERSYNC_JWT_SECRET` | JWT 验证密钥 | `your-256-bit-secret` | ✅ |
| `POWERSYNC_UPLOAD_ENABLED` | 允许客户端写入 | `true` | ❌ |
| `POWERSYNC_LOG_LEVEL` | 日志级别 | `info` | ❌ |

### 3.5 认证与安全

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | `your-super-secret-key` | ✅ |
| `JWT_ALGORITHM` | JWT 算法 | `HS256` | ❌ |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌有效期 | `30` | ❌ |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌有效期 | `7` | ❌ |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:48173` | ✅ |

### 3.6 AI 服务配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `AI_PROXY_URL` | AI API 代理地址 | `https://api.openai-proxy.com` | ✅ |
| `AI_API_KEY` | AI 服务 API Key | `sk-...` | ✅ |
| `AI_DEFAULT_MODEL` | 默认模型 | `gpt-4o-mini` | ❌ |
| `AI_MAX_TOKENS` | 最大 Token 数 | `4096` | ❌ |
| `EMBEDDING_MODEL` | 向量模型 | `text-embedding-3-small` | ❌ |

### 3.7 前端环境变量

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `http://localhost:48000` | ✅ |
| `VITE_POWERSYNC_URL` | PowerSync 地址 | `http://localhost:48090` | ✅ |
| `VITE_TOLGEE_API_URL` | Tolgee API 地址 | `http://localhost:48085` | ✅ |
| `VITE_TOLGEE_API_KEY` | Tolgee API Key | `tgpak_...` | ✅ |

### 3.8 生产环境专用

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `SENTRY_DSN` | Sentry 错误追踪 | `https://xxx@sentry.io/xxx` | ❌ |
| `LOG_LEVEL` | 日志级别 | `INFO` | ❌ |
| `ENVIRONMENT` | 运行环境 | `production` | ✅ |
| `WORKERS` | Uvicorn Worker 数 | `4` | ❌ |

---

## §4 system_settings 键值表 (System Settings)

> **铁律**：所有业务参数必须从 `system_settings` 表读取，禁止硬编码。

### 4.1 用户限额配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `free_book_limit` | 免费用户书籍上限 | `50` | INT | 全局 |
| `free_storage_limit` | 免费用户存储上限 (MB) | `1024` | INT | 全局 |
| `pro_book_limit` | Pro 用户书籍上限 | `500` | INT | 全局 |
| `pro_storage_limit` | Pro 用户存储上限 (MB) | `10240` | INT | 全局 |

### 4.2 邀请裂变配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `invite_bonus_storage` | 邀请奖励存储 (MB) | `500` | INT | 裂变 |
| `invite_bonus_books` | 邀请奖励书籍数 | `10` | INT | 裂变 |
| `invite_max_per_hour` | 邀请码每小时最大使用次数 | `10` | INT | 风控 |
| `invite_max_per_day` | 邀请人每日最大邀请数 | `50` | INT | 风控 |

### 4.3 OCR 服务配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `ocr_page_thresholds` | OCR 页数阶梯定义 | `{"thresholds":[100,300,500],"costs":[1,2,3,5]}` | JSON | OCR 服务 |
| `ocr_concurrency_limit` | OCR 全局并发数 | `1` | INT | 任务调度 |
| `ocr_free_monthly_limit` | 免费用户月度 OCR 次数 | `3` | INT | 全局 |
| `ocr_pro_monthly_limit` | Pro 用户月度 OCR 次数 | `30` | INT | 全局 |

### 4.4 AI 服务配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `ai_proxy_url` | AI API 代理地址 | `https://api.openai-proxy.com` | TEXT | AI 服务 |
| `usd_to_credit_rate` | 美元转 Credit 汇率 | `400` | INT | 计费 |
| `ai_service_fee_percentage` | AI 服务费百分比 | `20` | INT | 计费 |
| `ai_free_monthly_credits` | 免费用户月度 Credits | `1000` | INT | 全局 |
| `ai_pro_monthly_credits` | Pro 用户月度 Credits | `10000` | INT | 全局 |
| `ai_llm_model_default` | 默认 LLM 模型 | `gpt-4o-mini` | TEXT | AI 服务 |
| `ai_embedding_model` | 向量嵌入模型 | `text-embedding-3-small` | TEXT | AI 服务 |
| `ai_translate_cost_credits` | 翻译模式每次费用 | `50` | INT | 计费 |
| `ai_rag_cost_per_1k_tokens` | RAG 模式每 1K Token 费用 | `10` | INT | 计费 |

### 4.5 TTS 服务配置 (前端本地)

> **说明**：TTS 为纯前端功能，配置存储在本地 SQLite `local_tts_settings` 表。

| 本地配置项 | 说明 | 默认值 | 数据类型 |
|------------|------|--------|----------|
| `voice_id` | 当前音色 ID | `zh_cn_female_01` | TEXT |
| `speed` | 播放速度 | `1.0` | REAL |
| `volume` | 音量 | `1.0` | REAL |
| `auto_scroll` | 自动滚动 | `true` | BOOL |

**TTS 模型资源**：
| 模型 ID | 语言 | 大小 | 类型 |
|---------|------|------|------|
| `zh_cn_female_01` | 中文 | ~45MB | 内置 |
| `zh_cn_male_01` | 中文 | ~45MB | DLC |
| `en_us_female_01` | 英文 | ~30MB | DLC |
| `ja_jp_female_01` | 日文 | ~35MB | DLC |

### 4.6 词典服务配置 (前端本地)

> **说明**：词典为只读 Sidecar SQLite 数据库，App 内置打包。

| 资源 | 文件名 | 大小 | 说明 |
|------|--------|------|------|
| 权威词典 | `dict_master.db` | ~40MB | CC-CEDICT + WordNet + ECDICT |

### 4.7 定价配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `price_membership_yearly_first` | 首年会员价格 (分) | `6800` | INT | 支付 |
| `price_membership_yearly_renew` | 续费会员价格 (分) | `9800` | INT | 支付 |
| `price_ai_addon_credits` | AI 加油包价格 (分) | `990` | INT | 支付 |
| `price_ai_addon_amount` | AI 加油包 Credits 数 | `4000` | INT | 支付 |
| `price_ocr_addon_price` | OCR 加油包价格 (分) | `880` | INT | 支付 |
| `price_ocr_addon_amount` | OCR 加油包次数 | `10` | INT | 支付 |
| `wallet_exchange_rate` | 钱包余额兑换 Credits 汇率 | `400` | INT | 计费 |

### 4.8 文件处理配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `original_file_retention_days` | 原始文件保留天数 | `30` | INT | 存储 |
| `max_upload_size_mb` | 最大上传文件大小 (MB) | `200` | INT | 上传 |
| `allowed_formats` | 允许的文件格式 | `["epub","pdf","mobi","azw3"]` | JSON | 上传 |

### 4.9 合规配置

| Key | 说明 | 默认值 | 数据类型 | 适用范围 |
|-----|------|--------|----------|----------|
| `compliance_tos_zh_cn` | 服务条款(中文) | Markdown 内容 | TEXT | 法务 |
| `compliance_privacy_zh_cn` | 隐私政策(中文) | Markdown 内容 | TEXT | 法务 |
| `compliance_tos_en` | 服务条款(英文) | Markdown 内容 | TEXT | 法务 |
| `compliance_privacy_en` | 隐私政策(英文) | Markdown 内容 | TEXT | 法务 |

### 4.10 配置读取示例

**后端 Python 代码**：
```python
from app.services.config_service import ConfigService

class BookService:
    def __init__(self, config: ConfigService):
        self._config = config
    
    async def check_upload_limit(self, user_id: UUID, file_size: int) -> bool:
        """检查用户上传限额"""
        max_size = await self._config.get_int("max_upload_size_mb", default=200)
        return file_size <= max_size * 1024 * 1024
    
    async def get_user_book_limit(self, is_pro: bool) -> int:
        """获取用户书籍限额"""
        key = "pro_book_limit" if is_pro else "free_book_limit"
        return await self._config.get_int(key)
```

**ConfigService 接口**：
```python
class ConfigService:
    async def get(self, key: str, default: str = None) -> str:
        """获取字符串配置"""
        
    async def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        
    async def get_json(self, key: str, default: dict = None) -> dict:
        """获取 JSON 配置"""
        
    async def set(self, key: str, value: str) -> None:
        """设置配置（Admin 专用）"""
        
    def invalidate_cache(self, key: str = None) -> None:
        """清除配置缓存"""
```

---

## §5 容器网络配置 (Container Network)

### 5.1 Docker 网络

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 网络名称 | `athena-network` | Docker Bridge 网络 |
| 子网 | `172.20.0.0/16` | 固定 IP 段 |
| 网关 | `172.20.0.1` | 默认网关 |

### 5.2 服务固定 IP（可选）

| 服务 | IP | 说明 |
|------|-----|------|
| postgres | `172.20.0.10` | 主数据库 |
| valkey | `172.20.0.11` | 缓存服务 |
| minio | `172.20.0.12` | 对象存储 |
| api | `172.20.0.20` | 后端服务 |
| powersync | `172.20.0.21` | 同步服务 |

### 5.3 服务发现

容器内部通过服务名进行通信，无需 IP：
```yaml
# docker-compose.yml 示例
services:
  api:
    environment:
      - DATABASE_URL=postgresql://athena:password@postgres:5432/athena
      - REDIS_URL=redis://valkey:6379/0
      - MINIO_ENDPOINT=minio:9000
```

---

## 📌 快速检索

### 按服务查端口

| 服务 | 端口 | 用途 |
|------|------|------|
| API Server | 48000 | REST API |
| PowerSync | 48090/49091 | 同步/指标 |
| PostgreSQL | 45432 | 数据库 |
| MinIO | 48333/48888 | S3 API/Console |
| Valkey | 46379 | 缓存 |
| Nginx | 48080/48443 | HTTP/HTTPS 入口 |

### 按用途查配置

| 用途 | 配置 Key / 环境变量 |
|------|---------------------|
| 书籍限额 | `free_book_limit`, `pro_book_limit` |
| 存储限额 | `free_storage_limit`, `pro_storage_limit` |
| 邀请奖励 | `invite_bonus_storage`, `invite_bonus_books` |
| OCR 计费 | `ocr_page_thresholds` |
| AI 计费 | `usd_to_credit_rate`, `ai_service_fee_percentage` |
| JWT 配置 | `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` |

---

## 📋 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-01-XX | 初始版本，整合端口、超时、环境变量、system_settings |
