# 12 - 错误码中心化参考 (Error Code Reference)

> **版本**：v1.0  
> **状态**：Active  
> **用途**：统一管理所有错误码，定义 HTTP 状态码映射、i18n 翻译 Key、前端展示规范和用户引导操作

---

## 📋 文档导航

- [§1 错误码规范](#1-错误码规范-error-code-specification)
- [§2 完整错误码表](#2-完整错误码表-complete-error-codes)
- [§3 i18n 翻译模板](#3-i18n-翻译模板-i18n-translation)
- [§4 前端处理规范](#4-前端处理规范-frontend-handling)
- [§5 后端实现规范](#5-后端实现规范-backend-implementation)

---

## §1 错误码规范 (Error Code Specification)

### 1.1 命名规则

| 规则 | 说明 | 示例 |
|------|------|------|
| **格式** | 小写 snake_case | `quota_exceeded` ✅ `QuotaExceeded` ❌ |
| **前缀** | 按模块分类 | `auth_`, `book_`, `ocr_`, `ai_`, `invite_`, `payment_` |
| **语义** | 描述问题本质 | `insufficient_credits` ✅ `error_402` ❌ |
| **长度** | 建议 20 字符以内 | `rate_limited` ✅ `too_many_requests_please_wait` ❌ |

### 1.2 错误响应格式

**后端返回格式**（FastAPI HTTPException）:
```json
{
    "detail": "quota_exceeded"
}
```

**前端封装格式**（统一错误处理后）:
```json
{
    "code": "quota_exceeded",
    "message": "存储空间已满，请升级会员或清理书籍",
    "action": "upgrade",
    "actionLabel": "升级会员"
}
```

### 1.3 HTTP 状态码映射原则

| HTTP Status | 错误类型 | 客户端处理 |
|-------------|----------|------------|
| **400** | 请求参数错误 | 提示修正输入 |
| **401** | 认证失败 | 跳转登录 |
| **402** | 需要付费 | 引导充值/订阅 |
| **403** | 权限不足/配额超限 | 引导升级或等待 |
| **404** | 资源不存在 | 刷新或返回 |
| **409** | 冲突 | 刷新/合并数据 |
| **428** | 缺少前置条件 | 重新获取版本 |
| **429** | 请求过于频繁 | 延迟重试 |
| **500** | 服务器错误 | 报告问题/稍后重试 |

---

## §2 完整错误码表 (Complete Error Codes)

### 2.1 认证模块 (auth_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `unauthorized` | 401 | `errors.unauthorized` | 请先登录 | Toast | 跳转登录页 |
| `token_expired` | 401 | `errors.token_expired` | 登录已过期，请重新登录 | Toast | 跳转登录页 |
| `token_invalid` | 401 | `errors.token_invalid` | 登录凭证无效 | Toast | 跳转登录页 |
| `auth_code_invalid` | 400 | `errors.auth_code_invalid` | 验证码错误或已过期 | Toast | 重新获取验证码 |
| `auth_code_rate_limited` | 429 | `errors.auth_code_rate_limited` | 发送验证码过于频繁，请稍后再试 | Toast | 显示倒计时 |
| `email_already_registered` | 409 | `errors.email_already_registered` | 该邮箱已注册 | Toast | 引导登录 |
| `password_too_weak` | 400 | `errors.password_too_weak` | 密码强度不足，需包含字母和数字 | Inline | 无 |
| `oauth_code_invalid` | 400 | `errors.oauth_code_invalid` | OAuth 授权码无效或已过期 | Toast | 重新登录 |
| `oauth_state_mismatch` | 400 | `errors.oauth_state_mismatch` | OAuth 状态参数不匹配 | Toast | 重新登录 |
| `oauth_provider_error` | 502 | `errors.oauth_provider_error` | 第三方服务返回错误 | Toast | 稍后重试 |
| `oauth_email_conflict` | 409 | `errors.oauth_email_conflict` | 该邮箱已绑定其他账号 | Dialog | 登录已有账号 |
| `oauth_not_linked` | 404 | `errors.oauth_not_linked` | 该 OAuth 账号未绑定 | Toast | 无 |
| `oauth_last_auth_method` | 400 | `errors.oauth_last_auth_method` | 不能解绑最后一种登录方式 | Toast | 先绑定其他方式 |
| `missing_confirm_header` | 400 | `errors.missing_confirm_header` | 缺少删除确认 Header | Toast | 无 |
| `invalid_confirm_header` | 400 | `errors.invalid_confirm_header` | 删除确认 Header 值不正确 | Toast | 无 |
| `active_subscription` | 402 | `errors.active_subscription` | 存在活跃订阅，需先取消 | Dialog | 取消订阅 |
| `account_pending_deletion` | 403 | `errors.account_pending_deletion` | 账号已在删除队列中 | Toast | 联系客服恢复 |

### 2.2 权限模块 (permission_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `forbidden` | 403 | `errors.forbidden` | 您没有权限执行此操作 | Toast | 无 |
| `readonly_mode` | 403 | `errors.readonly_mode` | 账户处于只读模式 | Dialog | 升级会员 |
| `admin_required` | 403 | `errors.admin_required` | 需要管理员权限 | Toast | 无 |

### 2.3 资源模块 (resource_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `not_found` | 404 | `errors.not_found` | 资源不存在 | Toast | 刷新页面 |
| `book_not_found` | 404 | `errors.book_not_found` | 书籍不存在或已删除 | Toast | 返回书架 |
| `file_not_found` | 404 | `errors.file_not_found` | 文件不存在 | Toast | 无 |

### 2.4 配额模块 (quota_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `quota_exceeded` | 403 | `errors.quota_exceeded` | 存储空间已满 | Dialog | 升级会员/清理书籍 |
| `upload_forbidden_quota_exceeded` | 403 | `errors.upload_forbidden` | 空间不足，无法上传 | Dialog | 升级会员/清理书籍 |
| `book_limit_reached` | 403 | `errors.book_limit_reached` | 已达书籍数量上限 | Dialog | 升级会员/删除书籍 |

### 2.5 付费模块 (payment_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `insufficient_credits` | 402 | `errors.insufficient_credits` | Credits 余额不足 | Dialog | 充值按钮 |
| `payment_failed` | 402 | `errors.payment_failed` | 支付失败，请重试 | Toast | 重试支付 |
| `subscription_expired` | 402 | `errors.subscription_expired` | 会员已过期 | Dialog | 续费按钮 |
| `receipt_invalid` | 400 | `errors.receipt_invalid` | 支付凭证无效 | Toast | 联系客服 |

### 2.6 OCR 模块 (ocr_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `ocr_quota_exceeded` | 403 | `errors.ocr_quota_exceeded` | OCR 次数已用完 | Dialog | 购买加油包 |
| `ocr_max_pages_exceeded` | 400 | `errors.ocr_max_pages_exceeded` | 书籍页数超过 2000 页限制 | Toast | 无 |
| `ocr_in_progress` | 409 | `errors.ocr_in_progress` | OCR 正在处理中 | Toast | 等待完成 |
| `already_digitalized` | 400 | `errors.already_digitalized` | 书籍已是文字版，无需 OCR | Toast | 无 |
| `ocr_failed` | 500 | `errors.ocr_failed` | OCR 处理失败 | Toast | 重试/联系客服 |

### 2.7 AI 模块 (ai_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `ai_credits_insufficient` | 402 | `errors.ai_credits_insufficient` | AI 额度不足 | Dialog | 购买加油包 |
| `ai_context_too_long` | 400 | `errors.ai_context_too_long` | 对话内容过长，请开始新对话 | Toast | 新建对话 |
| `ai_service_unavailable` | 503 | `errors.ai_service_unavailable` | AI 服务暂时不可用 | Toast | 稍后重试 |
| `ai_rate_limited` | 429 | `errors.ai_rate_limited` | AI 请求过于频繁 | Toast | 等待片刻 |
| `ai_content_filtered` | 400 | `errors.ai_content_filtered` | 请求内容不符合规范 | Toast | 修改问题 |

### 2.8 邀请模块 (invite_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `invite_code_invalid_format` | 400 | `errors.invite_code_invalid_format` | 邀请码格式不正确 | Inline | 检查输入 |
| `invite_code_not_found` | 404 | `errors.invite_code_not_found` | 邀请码不存在 | Toast | 检查邀请码 |
| `inviter_account_disabled` | 403 | `errors.inviter_account_disabled` | 邀请人账号已被禁用 | Toast | 无 |
| `already_registered` | 409 | `errors.already_registered` | 您已注册，无法使用邀请码 | Toast | 直接登录 |
| `invite_code_already_used` | 409 | `errors.invite_code_already_used` | 您已使用过邀请码 | Toast | 无 |
| `invite_rate_limited` | 429 | `errors.invite_rate_limited` | 邀请码使用过于频繁 | Toast | 稍后重试 |

### 2.9 上传模块 (upload_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `missing_filename` | 400 | `errors.missing_filename` | 缺少文件名 | Toast | 重新上传 |
| `missing_key` | 400 | `errors.missing_key` | 上传参数错误 | Toast | 重新上传 |
| `file_too_large` | 400 | `errors.file_too_large` | 文件过大，最大支持 200MB | Toast | 压缩文件 |
| `unsupported_format` | 400 | `errors.unsupported_format` | 不支持的文件格式 | Toast | 检查格式 |
| `upload_failed` | 500 | `errors.upload_failed` | 上传失败，请重试 | Toast | 重试上传 |
| `canonical_not_found` | 404 | `errors.canonical_not_found` | 秒传时原书不存在 | Toast | 重新上传 |

### 2.10 同步模块 (sync_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `device_id_required` | 400 | `errors.device_id_required` | 设备标识缺失 | Toast | 重启应用 |
| `sync_conflict` | 409 | `errors.sync_conflict` | 数据同步冲突 | Dialog | 选择版本 |
| `version_conflict` | 409 | `errors.version_conflict` | 数据已被修改，请刷新 | Toast | 刷新数据 |
| `sync_failed` | 500 | `errors.sync_failed` | 同步失败 | Toast | 重试同步 |

### 2.11 乐观锁模块 (lock_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `missing_if_match` | 428 | `errors.missing_if_match` | 请求缺少版本信息 | Silent | 自动重试 |
| `invalid_if_match` | 400 | `errors.invalid_if_match` | 版本格式错误 | Silent | 自动重试 |

### 2.12 通用模块 (general_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `validation_error` | 400 | `errors.validation_error` | 输入格式错误 | Inline | 修正输入 |
| `rate_limited` | 429 | `errors.rate_limited` | 请求过于频繁，请稍后再试 | Toast | 等待 |
| `internal_error` | 500 | `errors.internal_error` | 服务器开小差了 | Toast | 稍后重试/反馈 |
| `service_unavailable` | 503 | `errors.service_unavailable` | 服务维护中 | Dialog | 等待/查看公告 |

### 2.13 风控模块 (risk_*)

| 错误码 | HTTP | i18n Key | 中文消息 | 展示类型 | 用户引导 |
|--------|------|----------|----------|----------|----------|
| `rate_limit_ip` | 429 | `errors.rate_limit_ip` | 当前网络请求过于频繁 | Toast | 稍后重试 |
| `rate_limit_device` | 429 | `errors.rate_limit_device` | 设备操作过于频繁 | Toast | 稍后重试 |
| `account_suspended` | 403 | `errors.account_suspended` | 账号已被暂停使用 | Dialog | 联系客服 |
| `suspicious_activity` | 403 | `errors.suspicious_activity` | 检测到异常活动 | Dialog | 联系客服 |

---

## §3 i18n 翻译模板 (i18n Translation)

### 3.1 中文 (zh-CN)

```json
{
  "errors": {
    "unauthorized": "请先登录",
    "token_expired": "登录已过期，请重新登录",
    "token_invalid": "登录凭证无效",
    "auth_code_invalid": "验证码错误或已过期",
    "auth_code_rate_limited": "发送验证码过于频繁，请稍后再试",
    "email_already_registered": "该邮箱已注册",
    "password_too_weak": "密码强度不足，需包含字母和数字",
    "oauth_code_invalid": "OAuth 授权码无效或已过期",
    "oauth_state_mismatch": "OAuth 状态参数不匹配",
    "oauth_provider_error": "第三方服务返回错误，请稍后重试",
    "oauth_email_conflict": "该邮箱已绑定其他账号",
    "oauth_not_linked": "该 OAuth 账号未绑定",
    "oauth_last_auth_method": "不能解绑最后一种登录方式，请先绑定其他方式",
    "missing_confirm_header": "缺少删除确认信息",
    "invalid_confirm_header": "删除确认信息不正确",
    "active_subscription": "存在活跃订阅，请先取消后再注销账号",
    "account_pending_deletion": "账号已在删除队列中，如需恢复请联系客服",
    
    "forbidden": "您没有权限执行此操作",
    "readonly_mode": "账户处于只读模式，请升级会员解锁",
    "admin_required": "需要管理员权限",
    
    "not_found": "资源不存在",
    "book_not_found": "书籍不存在或已删除",
    "file_not_found": "文件不存在",
    
    "quota_exceeded": "存储空间已满，请升级会员或清理书籍",
    "upload_forbidden": "空间不足，无法上传新书籍",
    "book_limit_reached": "已达书籍数量上限",
    
    "insufficient_credits": "Credits 余额不足，请充值",
    "payment_failed": "支付失败，请重试",
    "subscription_expired": "会员已过期，请续费",
    "receipt_invalid": "支付凭证无效，请联系客服",
    
    "ocr_quota_exceeded": "OCR 次数已用完，请购买加油包",
    "ocr_max_pages_exceeded": "书籍页数超过 2000 页限制",
    "ocr_in_progress": "OCR 正在处理中，请等待完成",
    "already_digitalized": "书籍已是文字版，无需 OCR",
    "ocr_failed": "OCR 处理失败，请重试或联系客服",
    
    "ai_credits_insufficient": "AI 额度不足，请购买加油包",
    "ai_context_too_long": "对话内容过长，请开始新对话",
    "ai_service_unavailable": "AI 服务暂时不可用，请稍后重试",
    "ai_rate_limited": "AI 请求过于频繁，请等待片刻",
    "ai_content_filtered": "请求内容不符合规范，请修改后重试",
    
    "invite_code_invalid_format": "邀请码格式不正确",
    "invite_code_not_found": "邀请码不存在",
    "inviter_account_disabled": "邀请人账号已被禁用",
    "already_registered": "您已注册，无法使用邀请码",
    "invite_code_already_used": "您已使用过邀请码",
    "invite_rate_limited": "邀请码使用过于频繁，请稍后重试",
    
    "missing_filename": "缺少文件名",
    "missing_key": "上传参数错误",
    "file_too_large": "文件过大，最大支持 200MB",
    "unsupported_format": "不支持的文件格式",
    "upload_failed": "上传失败，请重试",
    "canonical_not_found": "秒传时原书不存在",
    
    "device_id_required": "设备标识缺失，请重启应用",
    "sync_conflict": "数据同步冲突，请选择保留版本",
    "version_conflict": "数据已被修改，请刷新后重试",
    "sync_failed": "同步失败，请检查网络后重试",
    
    "missing_if_match": "请求缺少版本信息",
    "invalid_if_match": "版本格式错误",
    
    "validation_error": "输入格式错误，请检查后重试",
    "rate_limited": "请求过于频繁，请稍后再试",
    "internal_error": "服务器开小差了，请稍后重试",
    "service_unavailable": "服务维护中，请稍后再试",
    
    "rate_limit_ip": "当前网络请求过于频繁",
    "rate_limit_device": "设备操作过于频繁",
    "account_suspended": "账号已被暂停使用，请联系客服",
    "suspicious_activity": "检测到异常活动，请联系客服"
  }
}
```

### 3.2 英文 (en)

```json
{
  "errors": {
    "unauthorized": "Please log in first",
    "token_expired": "Session expired, please log in again",
    "token_invalid": "Invalid credentials",
    "auth_code_invalid": "Verification code is incorrect or expired",
    "auth_code_rate_limited": "Too many attempts, please try again later",
    "email_already_registered": "This email is already registered",
    "password_too_weak": "Password too weak, must contain letters and numbers",
    "oauth_code_invalid": "OAuth authorization code is invalid or expired",
    "oauth_state_mismatch": "OAuth state parameter mismatch",
    "oauth_provider_error": "Third-party service error, please try again later",
    "oauth_email_conflict": "This email is already linked to another account",
    "oauth_not_linked": "This OAuth account is not linked",
    "oauth_last_auth_method": "Cannot unlink last authentication method",
    "missing_confirm_header": "Missing deletion confirmation header",
    "invalid_confirm_header": "Invalid deletion confirmation header",
    "active_subscription": "Please cancel your subscription before deleting account",
    "account_pending_deletion": "Account is pending deletion, contact support to recover",
    
    "forbidden": "You don't have permission to perform this action",
    "readonly_mode": "Account is in read-only mode, please upgrade",
    "admin_required": "Admin privileges required",
    
    "not_found": "Resource not found",
    "book_not_found": "Book not found or deleted",
    "file_not_found": "File not found",
    
    "quota_exceeded": "Storage full, please upgrade or remove books",
    "upload_forbidden": "Not enough space to upload",
    "book_limit_reached": "Book limit reached",
    
    "insufficient_credits": "Insufficient credits, please top up",
    "payment_failed": "Payment failed, please retry",
    "subscription_expired": "Subscription expired, please renew",
    "receipt_invalid": "Invalid receipt, please contact support",
    
    "ocr_quota_exceeded": "OCR quota exhausted, please purchase add-on",
    "ocr_max_pages_exceeded": "Book exceeds 2000 page limit",
    "ocr_in_progress": "OCR is processing, please wait",
    "already_digitalized": "Book already has text layer",
    "ocr_failed": "OCR failed, please retry or contact support",
    
    "ai_credits_insufficient": "AI credits insufficient, please purchase add-on",
    "ai_context_too_long": "Conversation too long, please start a new one",
    "ai_service_unavailable": "AI service temporarily unavailable",
    "ai_rate_limited": "Too many AI requests, please wait",
    "ai_content_filtered": "Content does not comply with guidelines",
    
    "invite_code_invalid_format": "Invalid invite code format",
    "invite_code_not_found": "Invite code not found",
    "inviter_account_disabled": "Inviter account is disabled",
    "already_registered": "Already registered, cannot use invite code",
    "invite_code_already_used": "You have already used an invite code",
    "invite_rate_limited": "Invite code used too frequently",
    
    "missing_filename": "Missing filename",
    "missing_key": "Upload parameter error",
    "file_too_large": "File too large, max 200MB",
    "unsupported_format": "Unsupported file format",
    "upload_failed": "Upload failed, please retry",
    "canonical_not_found": "Original book not found for instant upload",
    
    "device_id_required": "Device ID missing, please restart app",
    "sync_conflict": "Sync conflict, please choose version to keep",
    "version_conflict": "Data modified, please refresh",
    "sync_failed": "Sync failed, please check network",
    
    "missing_if_match": "Missing version header",
    "invalid_if_match": "Invalid version format",
    
    "validation_error": "Invalid input format",
    "rate_limited": "Too many requests, please try again later",
    "internal_error": "Server error, please try again later",
    "service_unavailable": "Service under maintenance",
    
    "rate_limit_ip": "Too many requests from this network",
    "rate_limit_device": "Too many requests from this device",
    "account_suspended": "Account suspended, please contact support",
    "suspicious_activity": "Suspicious activity detected, please contact support"
  }
}
```

---

## §4 前端处理规范 (Frontend Handling)

### 4.1 展示类型定义

| 类型 | 组件 | 用途 | 示例 |
|------|------|------|------|
| **Toast** | 轻量提示 | 非阻塞性通知 | "保存成功"、"操作失败" |
| **Dialog** | 模态对话框 | 需要用户确认/选择 | 配额超限、同步冲突 |
| **Inline** | 表单内联 | 字段级校验错误 | 邮箱格式错误 |
| **Silent** | 静默处理 | 自动重试/恢复 | 乐观锁冲突 |

### 4.2 统一错误处理器

```typescript
// utils/errorHandler.ts
import { t } from '@/i18n';
import { toast } from '@/components/Toast';
import { showDialog } from '@/components/Dialog';

interface ErrorAction {
  type: 'navigate' | 'dialog' | 'retry' | 'none';
  target?: string;
  label?: string;
}

const ERROR_ACTIONS: Record<string, ErrorAction> = {
  // 认证错误 → 跳转登录
  'unauthorized': { type: 'navigate', target: '/login' },
  'token_expired': { type: 'navigate', target: '/login' },
  'token_invalid': { type: 'navigate', target: '/login' },
  
  // 配额错误 → 弹窗引导
  'quota_exceeded': { type: 'dialog', target: '/upgrade', label: 'btn.upgrade' },
  'book_limit_reached': { type: 'dialog', target: '/upgrade', label: 'btn.upgrade' },
  'insufficient_credits': { type: 'dialog', target: '/topup', label: 'btn.topup' },
  'ocr_quota_exceeded': { type: 'dialog', target: '/shop/ocr', label: 'btn.buy_addon' },
  'ai_credits_insufficient': { type: 'dialog', target: '/shop/ai', label: 'btn.buy_addon' },
  
  // 冲突错误 → 弹窗选择
  'sync_conflict': { type: 'dialog' },
  'version_conflict': { type: 'retry' },
  
  // 默认
  'default': { type: 'none' },
};

export function handleApiError(error: ApiError): void {
  const code = error.detail || 'internal_error';
  const message = t(`errors.${code}`, t('errors.internal_error'));
  const action = ERROR_ACTIONS[code] || ERROR_ACTIONS['default'];
  
  switch (action.type) {
    case 'navigate':
      toast.error(message);
      router.push(action.target!);
      break;
      
    case 'dialog':
      showDialog({
        title: t('dialog.error_title'),
        message,
        primaryAction: action.target ? {
          label: t(action.label!),
          onClick: () => router.push(action.target!)
        } : undefined,
        secondaryAction: {
          label: t('btn.cancel'),
        }
      });
      break;
      
    case 'retry':
      toast.warning(message + ' ' + t('hint.will_retry'));
      // 触发自动重试逻辑
      break;
      
    default:
      toast.error(message);
  }
}
```

### 4.3 React Query 集成示例

```typescript
// hooks/useBooks.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { handleApiError } from '@/utils/errorHandler';

export function useUploadBook() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: uploadBook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      toast.success(t('book.upload_success'));
    },
    onError: (error: ApiError) => {
      handleApiError(error);
    },
  });
}
```

### 4.4 表单校验错误处理

```typescript
// 表单字段级错误
interface FieldError {
  field: string;
  code: string;
}

function handleValidationError(errors: FieldError[], form: FormInstance) {
  errors.forEach(({ field, code }) => {
    form.setError(field, {
      type: 'server',
      message: t(`errors.${code}`),
    });
  });
}
```

---

## §5 后端实现规范 (Backend Implementation)

### 5.1 自定义异常类

```python
# app/exceptions.py
from fastapi import HTTPException, status

class AthenaException(HTTPException):
    """雅典娜统一异常基类"""
    
    def __init__(self, code: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=code)
        self.code = code


# 认证异常
class UnauthorizedException(AthenaException):
    def __init__(self, code: str = "unauthorized"):
        super().__init__(code, status.HTTP_401_UNAUTHORIZED)


class TokenExpiredException(UnauthorizedException):
    def __init__(self):
        super().__init__("token_expired")


# 权限异常
class ForbiddenException(AthenaException):
    def __init__(self, code: str = "forbidden"):
        super().__init__(code, status.HTTP_403_FORBIDDEN)


class QuotaExceededException(ForbiddenException):
    def __init__(self):
        super().__init__("quota_exceeded")


class ReadonlyModeException(ForbiddenException):
    def __init__(self):
        super().__init__("readonly_mode")


# 付费异常
class PaymentRequiredException(AthenaException):
    def __init__(self, code: str = "insufficient_credits"):
        super().__init__(code, status.HTTP_402_PAYMENT_REQUIRED)


class InsufficientCreditsException(PaymentRequiredException):
    def __init__(self):
        super().__init__("insufficient_credits")


# 资源异常
class NotFoundException(AthenaException):
    def __init__(self, code: str = "not_found"):
        super().__init__(code, status.HTTP_404_NOT_FOUND)


class BookNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__("book_not_found")


# 冲突异常
class ConflictException(AthenaException):
    def __init__(self, code: str = "version_conflict"):
        super().__init__(code, status.HTTP_409_CONFLICT)


class VersionConflictException(ConflictException):
    def __init__(self):
        super().__init__("version_conflict")


class SyncConflictException(ConflictException):
    def __init__(self):
        super().__init__("sync_conflict")


# 限流异常
class RateLimitedException(AthenaException):
    def __init__(self, code: str = "rate_limited"):
        super().__init__(code, status.HTTP_429_TOO_MANY_REQUESTS)
```

### 5.2 使用示例

```python
# app/services/book_service.py
from app.exceptions import QuotaExceededException, BookNotFoundException

class BookService:
    async def upload_book(self, user_id: UUID, file_info: FileInfo) -> Book:
        # 检查配额
        stats = await self._get_user_stats(user_id)
        limit = await self._config.get_int("free_book_limit")
        
        if stats.book_count >= limit:
            raise QuotaExceededException()
        
        # 创建书籍...
    
    async def get_book(self, user_id: UUID, book_id: UUID) -> Book:
        book = await self._repo.find_by_id(book_id)
        
        if not book or book.user_id != user_id:
            raise BookNotFoundException()
        
        return book
```

### 5.3 全局异常处理器

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions import AthenaException

app = FastAPI()

@app.exception_handler(AthenaException)
async def athena_exception_handler(request: Request, exc: AthenaException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.code}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # 记录日志
    logger.exception("Unhandled exception", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "internal_error"}
    )
```

---

## 📌 快速检索

### 按 HTTP 状态码查错误

| HTTP | 错误码示例 |
|------|-----------|
| 400 | `validation_error`, `missing_filename`, `ocr_max_pages_exceeded` |
| 401 | `unauthorized`, `token_expired`, `token_invalid` |
| 402 | `insufficient_credits`, `payment_failed`, `subscription_expired` |
| 403 | `forbidden`, `quota_exceeded`, `readonly_mode`, `ocr_quota_exceeded` |
| 404 | `not_found`, `book_not_found`, `invite_code_not_found` |
| 409 | `version_conflict`, `sync_conflict`, `ocr_in_progress` |
| 429 | `rate_limited`, `ai_rate_limited`, `invite_rate_limited` |
| 500 | `internal_error`, `ocr_failed`, `sync_failed` |

### 按模块查错误

| 模块 | 前缀 | 数量 |
|------|------|------|
| 认证 | `auth_*`, `token_*` | 7 |
| 权限 | `forbidden`, `readonly_*`, `admin_*` | 3 |
| 资源 | `*_not_found` | 3 |
| 配额 | `quota_*`, `*_limit_*` | 3 |
| 付费 | `insufficient_*`, `payment_*`, `subscription_*` | 4 |
| OCR | `ocr_*`, `already_*` | 5 |
| AI | `ai_*` | 5 |
| 邀请 | `invite_*`, `inviter_*` | 6 |
| 上传 | `missing_*`, `file_*`, `upload_*`, `unsupported_*` | 6 |
| 同步 | `sync_*`, `version_*`, `device_*` | 4 |
| 通用 | `validation_*`, `rate_*`, `internal_*`, `service_*` | 4 |
| 风控 | `rate_limit_*`, `account_*`, `suspicious_*` | 4 |

---

## 📋 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-01-XX | 初始版本，整合 54 个错误码，包含 i18n 模板和前后端实现规范 |
