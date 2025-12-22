# 01 - 产品灵魂与商业模型 (Product Soul & Business Model)

> **版本**：v1.2 (Final Hardened)
> **来源**：基于《雅典娜商业模型 V9.0》与现有后端代码逻辑整合。
> **定位**：本项目的**商业宪法**。任何代码实现不得违背本文档定义的收费模式、风控策略与用户权益。
> **技术落地指南**：涉及错误码、配置读取、事务处理的具体技术规范，请严格遵循 **`00 - AI 编码宪法与规范AI_Coding_Constitution_and_Rules.md`** 中的相关条款。

---

## 1. 产品灵魂与愿景 (Product Soul & Vision)

*   **产品名称**：雅典娜 (Athena)
*   **核心 Slogan**：“把读过的每一本书，都变成你的知识资产。”
*   **核心价值主张 (UVP)**：
    为深度阅读者提供一个集“无缝云同步”、“深度 AI 知识内化”、“极致笔记体验”于一体的知识引擎。我们将碎片化的阅读行为，转化为结构化的个人智慧。

---

## 2. 核心商业模型：The Hook & The Trap

这是雅典娜区别于普通阅读器的根本。所有功能开发必须围绕这一模型闭环。

### 2.1 The Hook（诱饵）：免费同步，有限上传
*   **策略**：多端同步功能**永久免费**，降低用户准入门槛，最大化 DAU。
*   **限制点（关键）**：同步的前提是“文件在云端”。我们不限制同步，但**限制“新书上传”**。
*   **阈值配置**：
    *   免费用户配额：**50 本** 或 **1GB** 存储空间（由 Admin 动态配置 `free_book_limit` 和 `free_storage_limit`）。
*   **逻辑闭环（AI 必须遵守）**：
    *   **新设备场景**：用户在新手机登录，虽无法上传新书，但可以**完整下载并阅读**云端已有的所有书籍、笔记和 AI 记录。体验无损。
    *   **旧设备场景**：已上传的书籍可继续阅读、做笔记，但无法再添加新书。

### 2.2 The Trap（熔断）：只读锁 (Read-Only Lock)
*   **触发条件**：当用户达到存储或数量阈值（50本/1GB），且未升级 Pro 时。
*   **业务表现（Soft Lock）**：
    1.  **上传阻断**：禁止新书上传请求。
    2.  **写操作阻断**：禁止笔记、高亮、书架修改等同步请求。
    3.  **前端体验**：
        *   必须给予明确的 UI 提示（文案配置于 `msg_storage_full`）。
        *   **错误码**：前端需处理 `quota_exceeded`（使用 `t('errors.quota_exceeded')` 翻译显示）。
        *   **严禁**弹窗阻断用户的**阅读**行为。已下载的书籍必须可以继续阅读。
        *   **数据安全**：当 API 返回 403 时，前端**必须**在本地暂存用户产生的数据（笔记/高亮），标记为“待同步”，**严禁**直接丢弃或回滚。
    4.  **AI 豁免**：只要用户账户内有 Credits（信用点），**允许**继续使用 AI 对话和翻译，不受存储空间限制。

**典型场景示例：**
*   用户超额上传 → 后端返回 403 `quota_exceeded` → 前端弹出"购买加油包/升级Pro"引导。
*   免费用户尝试 OCR 1200 页书 → 后端返回 400 `ocr_max_pages_exceeded`。

---

## 3. 资源与货币体系 (Resources & Currency)

本项目实行**全配置化**的货币体系，所有数值严禁硬编码。具体读取方式请参考 `00` 号文档“配置读取铁律”。

### 3.1 核心货币：Credits（通用信用点）
*   **定义**：平台内的硬通货，用于消耗算力资源。
*   **用途**：AI 对话（RAG 问答 / 闲聊）、AI 语境翻译、OCR 额度兑换（当免费 OCR 次数用尽时）。
*   **汇率**：由 Admin 后台配置（例如：`wallet_exchange_rate`: ¥1 = 400 Credits）。
*   **精度**：所有 Credits 计算必须使用整数（避免浮点误差）。

### 3.2 钱包余额 (Wallet Balance)
*   **定义**：用户充值的法币余额（CNY/USD），存储在 `credit_accounts` 表。
*   **用途**：购买加油包、支付微小额度的服务费（如单次 OCR）。

### 3.3 算力底线与风控 (The Cost)

#### OCR 额度控制（阶梯计费）
*   **数据源**：依据 `books` 表中的 `meta.page_count` 字段（必须准确）。
*   **阶梯规则（AI 必须严格实现此逻辑）**：
    | 书籍页数 (P) | 消耗策略 | 说明 |
    | :--- | :--- | :--- |
    | **P ≤ 600** | 1 个“标准单位” | 优先扣免费额度，用完扣加油包/Credits |
    | **600 < P ≤ 1000** | 2 个“标准单位” | **强制扣除**付费额度（加油包/Credits），不可用免费额度 |
    | **1000 < P ≤ 2000** | 3 个“标准单位” | **强制扣除**付费额度（加油包/Credits），不可用免费额度 |
    | **P > 2000** | **拒绝服务** | 直接报错 `OCR_MAX_PAGES_EXCEEDED` |

#### OCR 调用统一流程（Transaction Flow）
**此流程涉及资金安全，必须严格执行：**
1.  **读取页数**：检查 `meta.page_count`。
2.  **缺失探测**：若为空，触发轻量探测；若仍为空，返回 `OCR_NEEDS_MANUAL_CHECK`。
3.  **开启事务**：
    *   **扣费**：写入 `credit_transactions` 表，状态为 `Pending`。
    *   **记录任务**：写入 `ocr_jobs` 表。
4.  **调用 Worker**：提交 OCR 任务。
5.  **结果处理**：
    *   **成功**：更新 `credit_transactions` 状态为 `Confirmed`。
    *   **失败**：更新状态为 `Failed`，并**回滚扣费**（退还 Credits）。
6.  **提交事务**。

#### OCR 复用机制（假 OCR / Instant OCR）

> **设计目的**：当多个用户上传相同书籍时，只需执行一次真实 OCR，后续用户可直接复用结果。
> 这是 **ADR-008 SHA256 全局去重** 的核心商业价值之一。

**触发条件**：
1. 用户点击 OCR 按钮，触发 `POST /books/{id}/ocr`
2. 系统检测到该书籍的 `content_sha256` 与其他已完成 OCR 的书籍相同
3. 直接复用现有 OCR 结果，秒级完成

**商业逻辑（AI 必须严格执行）**：
| 场景 | 扣费 | OCR 执行 | 用户体验 |
|-----|------|---------|---------|
| 首次 OCR | ✅ 正常扣费 | ✅ 真实执行 | 等待 Worker 处理 |
| 复用 OCR | ✅ **正常扣费** | ❌ 不执行 | 秒级完成 |

> **关键约束**：
> - 用户**必须**点击 OCR 按钮才能看到 OCR 结果（商业闭环）
> - 即使是复用，也**必须**扣除配额（维护商业公平性）
> - 但不消耗 GPU 算力（降低运营成本）

**实现要点**：
```python
def trigger_book_ocr(book_id, user_id):
    # 1. 正常配额检查和扣费
    check_and_deduct_ocr_quota(user_id, page_count)
    
    # 2. 检查是否可复用（相同 SHA256 已有双层 PDF）
    existing_ocr = find_existing_ocr_by_sha256(book.content_sha256)
    
    if existing_ocr:
        # 3. 假 OCR：复制双层 PDF 到用户目录
        copy_minio_file(existing_ocr.ocr_pdf_key, new_ocr_pdf_key)
        update_book(book_id, 
            ocr_status='completed',
            ocr_pdf_key=new_ocr_pdf_key  # 双层 PDF (Dual-Layer PDF)
        )
        return {"status": "instant_completed"}  # 秒级完成
    else:
        # 4. 真 OCR：OCRmyPDF + PaddleOCR，输出双层 PDF
        celery_task.delay(book_id)
        return {"status": "processing"}
```

**监控指标**：
- `athena_ocr_instant_completed_total`：OCR 复用次数
- `athena_ocr_real_processed_total`：真实 OCR 执行次数
- `athena_ocr_cost_saved_estimate`：估算节省的 GPU 成本

---

## 4. 会员权益体系 (Membership Tiers)

### 4.1 免费用户 (Free Tier)
*   **权益**：全端同步（在 50本/1GB 阈值内）、基础阅读功能。
*   **裂变奖励（邀请码）**：
    *   **机制**：邀请奖励发放必须在**事务**中完成（写入 `invites` 和 `user_stats`），防止重复领取。
    *   **奖励**：双方同时获得 `invite_bonus_storage` 和 `invite_bonus_books`。

---

### 4.1.1 邀请裂变完整流程 (Referral System)

#### 📋 邀请码生成规则

| 规则项 | 规范 |
|--------|------|
| **格式** | `[A-Z0-9]{8}` (8位大写字母+数字) |
| **生成时机** | 用户首次注册成功后自动生成 |
| **唯一性** | 全局唯一，存储于 `users.invite_code` |
| **有效期** | 永久有效 |
| **使用限制** | 每个邀请码可被无限次使用（但同一被邀请人只能用一次） |

**邀请码生成伪代码**：
```python
import secrets
import string

def generate_invite_code() -> str:
    """生成 8 位邀请码，碰撞时重试"""
    chars = string.ascii_uppercase + string.digits
    for _ in range(10):  # 最多重试 10 次
        code = ''.join(secrets.choice(chars) for _ in range(8))
        if not db.users.exists(invite_code=code):
            return code
    raise InviteCodeGenerationError("无法生成唯一邀请码")
```

#### 🔄 邀请流程时序

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   邀请人 A   │     │   被邀请人 B │     │   后端服务   │     │   数据库    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  1. 分享邀请码/链接 │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ 2. 注册时填写邀请码 │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ 3. 校验邀请码     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 4. 开启事务       │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 5. 创建用户 B     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 6. 写入 invites   │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 7. 更新 A 的      │
       │                   │                   │    user_stats     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 8. 更新 B 的      │
       │                   │                   │    user_stats     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 9. 提交事务       │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │ 10. 推送通知"获得奖励" │                   │                   │
       │<──────────────────│───────────────────│                   │
       │                   │                   │                   │
```

#### ✅ 邀请码校验流程

**校验步骤**（按顺序执行，任一失败立即返回错误）：

| 步骤 | 校验内容 | 错误码 | 用户提示 |
|------|----------|--------|----------|
| 1 | 邀请码格式是否为 8 位字母数字 | `INVITE_CODE_INVALID_FORMAT` | 邀请码格式不正确 |
| 2 | 邀请码是否存在于 `users.invite_code` | `INVITE_CODE_NOT_FOUND` | 邀请码不存在 |
| 3 | 邀请人账号是否处于正常状态 | `INVITER_ACCOUNT_DISABLED` | 邀请人账号已被禁用 |
| 4 | 被邀请人是否为新用户（首次注册） | `ALREADY_REGISTERED` | 您已注册，无法使用邀请码 |
| 5 | 被邀请人是否已使用过邀请码 | `INVITE_CODE_ALREADY_USED` | 您已使用过邀请码 |

#### 💰 奖励发放事务

**事务原子操作**（全部成功或全部回滚）：

```sql
BEGIN TRANSACTION;

-- Step 1: 创建邀请记录
INSERT INTO invites (
    id, inviter_id, invitee_id, code_used, 
    reward_storage_mb, reward_books, created_at
) VALUES (
    gen_random_uuid(), 
    :inviter_id, 
    :invitee_id, 
    :invite_code,
    (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_storage'),
    (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_books'),
    NOW()
);

-- Step 2: 更新邀请人的统计（bonus_storage_mb, bonus_book_limit）
UPDATE user_stats 
SET 
    bonus_storage_mb = bonus_storage_mb + (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_storage'),
    bonus_book_limit = bonus_book_limit + (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_books'),
    updated_at = NOW()
WHERE user_id = :inviter_id;

-- Step 3: 更新被邀请人的统计（同样获得奖励）
UPDATE user_stats 
SET 
    bonus_storage_mb = bonus_storage_mb + (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_storage'),
    bonus_book_limit = bonus_book_limit + (SELECT value::int FROM system_settings WHERE key = 'invite_bonus_books'),
    updated_at = NOW()
WHERE user_id = :invitee_id;

COMMIT;
```

**关键字段说明**：

| 表名 | 字段 | 说明 |
|------|------|------|
| `user_stats` | `bonus_storage_mb` | 邀请获得的额外存储空间（MB） |
| `user_stats` | `bonus_book_limit` | 邀请获得的额外书籍数量 |
| `invites` | `inviter_id` | 邀请人用户 ID |
| `invites` | `invitee_id` | 被邀请人用户 ID |
| `invites` | `code_used` | 使用的邀请码 |
| `invites` | `reward_storage_mb` | 本次奖励的存储空间 |
| `invites` | `reward_books` | 本次奖励的书籍数量 |

#### 🛡️ 防刷策略

| 风控维度 | 规则 | 触发动作 |
|----------|------|----------|
| **IP 限制** | 同一 IP 24小时内最多注册 5 个账号 | 拒绝注册，返回 `RATE_LIMIT_IP` |
| **设备限制** | 同一设备指纹 24小时内最多注册 3 个账号 | 拒绝注册，返回 `RATE_LIMIT_DEVICE` |
| **邀请频率** | 同一邀请码 1小时内最多被使用 10 次 | 拒绝使用，返回 `INVITE_RATE_LIMITED` |
| **异常检测** | 同一邀请人 24小时内邀请超过 50 人 | 标记账号人工审核，暂停奖励发放 |
| **账号关联** | 邀请人与被邀请人不能有相同的设备指纹/IP | 拒绝奖励，记录日志 |

**设备指纹采集**（前端）：
- 浏览器 UA + 屏幕分辨率 + 时区 + Canvas 指纹 + WebGL 指纹
- 移动端：设备 ID (IDFV/Android ID) + 型号 + 系统版本

**风控日志表** `invite_risk_logs`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `event_type` | VARCHAR(50) | 事件类型：`REGISTER_BLOCKED`, `REWARD_BLOCKED`, `MANUAL_REVIEW` |
| `ip_address` | INET | 请求 IP |
| `device_fingerprint` | VARCHAR(64) | 设备指纹哈希 |
| `inviter_id` | UUID | 邀请人 ID（如有） |
| `invitee_id` | UUID | 被邀请人 ID（如有） |
| `reason` | TEXT | 触发原因 |
| `created_at` | TIMESTAMPTZ | 记录时间 |

#### 📊 邀请相关 API 端点

| 方法 | 端点 | 功能 | 认证 |
|------|------|------|------|
| GET | `/api/v1/user/invite-code` | 获取当前用户的邀请码 | 需要 |
| POST | `/api/v1/auth/register` | 注册时可携带 `invite_code` 参数 | 不需要 |
| GET | `/api/v1/user/invite-stats` | 获取邀请统计（邀请人数、获得奖励） | 需要 |
| GET | `/api/v1/user/invites` | 获取邀请历史列表 | 需要 |

**请求/响应示例**：

```json
// GET /api/v1/user/invite-stats
{
    "data": {
        "invite_code": "A1B2C3D4",
        "total_invites": 12,
        "total_bonus_storage_mb": 6000,
        "total_bonus_books": 120,
        "share_url": "https://athena.app/i/A1B2C3D4"
    }
}

// POST /api/v1/auth/register (带邀请码)
{
    "email": "newuser@example.com",
    "password": "securepassword123",
    "invite_code": "A1B2C3D4"  // 可选
}
```

---

### 4.2 Pro 会员 (Pro Membership)
*   **定价**：`price_membership_yearly_first` / `price_membership_yearly_renew`。
*   **权益核心**：
    1.  **解除只读锁**。
    2.  **月度赠礼 (Monthly Gift)**：赠送 Credits 和 OCR 额度，**月底清零，不可累计**。
    3.  **优先队列**：享受 P0/P1 级调度优先级。

### 4.3 加油包 (Add-ons)
AI 加油包：购买额外的 Credits（如 ¥9.9 买 4000 点）。
OCR 加油包：购买额外的 OCR 次数（如 ¥8.8 买 10 次）。
特性：加油包额度永久有效，不会随月度清零。

---

## 5. 运营配置化要求 (Admin Requirements)

为了保证商业灵活性，**以下所有参数必须对接 `system_settings` 表**。代码实现时需遵循 `00 - AI 编码宪法与规范AI_Coding_Constitution_and_Rules.md` 号文档的“配置读取铁律”。

配置项 Key	说明	默认值示例	适用范围	DB 映射
free_book_limit	免费书籍数量上限	50	全局	system_settings
free_storage_limit	免费存储空间上限 (MB)	1024	全局	system_settings
ocr_page_thresholds	OCR 页数阶梯定义	JSON	OCR 服务	system_settings
ocr_concurrency_limit	OCR 全局并发数	1	任务调度	system_settings
wallet_exchange_rate	钱包余额兑换 Credits 汇率	400	计费	system_settings
pricing_rules	多平台定价策略	JSON	收银台	pricing_rules 表
invite_bonus_storage	邀请奖励空间	500	裂变	system_settings
invite_bonus_books	邀请奖励书籍	10	裂变	system_settings



---

## 6. 多平台支付策略 (Multi-Platform Payment)
Web 端：直接对接 Stripe/WeChat Pay，使用标准价格。
移动端 (iOS/Android)：
必须使用 IAP (In-App Purchase)。
“苹果税”处理：在 Admin 后台为 iOS 平台配置独立的价格（如 ¥78），以覆盖 30% 的佣金成本。
合规红线：App 内严禁出现任何引导用户去 Web 端充值的链接或文案。
*   **IAP 关键流程 (P2)**：
    *   **凭证校验**：后端必须校验 Apple/Google Receipt，防止伪造。
    *   **Webhook**：处理 `DID_RENEW`, `REFUND` 等订阅状态变更通知。
    *   **掉单处理**：前端必须在本地存储 pending transaction，直到后端确认入账。

---

## 7. 度量与监控 KPI (Metrics & Monitoring)

运营与技术团队需共同关注以下核心指标：
*   **athena_user_dau**：日活跃用户数。
*   **athena_users_in_readonly**：处于只读锁状态的用户数。
*   **ocr_deduction_failures_total**：OCR 扣费失败次数。
*   **credit_transactions_failed_total**：通用交易失败次数。

---

**[AI 指令总结]**
1.  **数值来源**：本文档中提到的所有数字仅为示例。在编写代码时，**严禁硬编码**，必须使用配置项 Key。
2.  **逻辑实现**：OCR、上传、邀请功能必须严格对照本文档的逻辑流程。
3.  **技术底线**：实现上述逻辑时，必须严格遵守 `00 - AI 编码宪法与规范AI_Coding_Constitution_and_Rules.md` 文档中的事务、错误码和安全规范。