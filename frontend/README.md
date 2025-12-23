# 雅典娜阅读器 - 前端 Monorepo

> **版本**: v1.0.0  
> **技术栈**: Expo + Tamagui + Solito + Next.js  
> **包管理器**: pnpm

## 📁 项目结构

```
frontend/
├── apps/
│   ├── next/          # Next.js Web 应用
│   └── expo/          # Expo React Native 应用
├── packages/
│   ├── ui/            # 共享 UI 组件库 (Tamagui)
│   └── app/           # 共享业务逻辑 (PowerSync + SQLite)
└── turbo.json         # Turborepo 构建配置
```

## 🚀 快速开始

### 安装依赖

```bash
pnpm install
```

### 启动开发服务器

```bash
# 同时启动 Web 和 Native
pnpm dev

# 仅启动 Web (Next.js)
pnpm dev:web

# 仅启动 Native (Expo)
pnpm dev:native
```

### 构建生产版本

```bash
pnpm build
```

## 🎨 设计系统

本项目严格遵循 Apple Human Interface Guidelines (HIG)，使用 Tamagui 实现跨平台统一的设计语言。

### 字体系统

| 字体 | 用途 | 权重 |
|:---|:---|:---|
| Inter | 英文、数字 | 400, 500, 600, 700 |
| Noto Sans SC | 中文 | 400, 500, 600, 700 |

### Token 规范

- **间距**: 4px 基础网格 (`$space.1` = 4px, `$space.2` = 8px, ...)
- **圆角**: Apple Squircle (`$radius.sm` = 8px, `$radius.md` = 12px, `$radius.lg` = 20px)
- **颜色**: 语义化 (`$systemBlue`, `$systemRed`, `$systemGreen`, `$systemGray`)

### 动画参数

```typescript
// Spring 动画标准
{ stiffness: 170, damping: 26 }

// Button 点击缩放
{ scale: 0.97 }
```

## 🗄️ 离线优先架构

本项目采用 **App-First (Local-First)** 架构：

1. **UI 数据源**: 所有 UI 组件从本地 SQLite 读取数据
2. **同步机制**: PowerSync 自动处理双向同步
3. **Native 驱动**: 使用 `@op-engineering/op-sqlite` 获得原生性能

### PowerSync 表结构

| 表名 | 同步方向 | 说明 |
|:---|:---|:---|
| `books` | 双向 | 书籍元数据 |
| `book_position` | 双向 | 阅读位置 |
| `notes` | 双向 | 笔记 |
| `highlights` | 双向 | 高亮 |
| `bookmarks` | 双向 | 书签 |
| `shelves` | 双向 | 书架 |

## 📜 编码规范

请遵循 `.cursorrules` 中的强制规则：

- ❌ 禁止硬编码 Hex 颜色 (如 `#007AFF`)
- ❌ 禁止硬编码像素值 (如 `padding: 16`)
- ❌ 禁止使用非 Lucide 图标库
- ✅ 必须使用 Tamagui Token (如 `$systemBlue`, `$space.4`)
- ✅ 必须使用 useLiveQuery 读取数据

## 🔧 开发工具

### 类型检查

```bash
pnpm typecheck
```

### 代码格式化

```bash
pnpm lint
```

## 📚 相关文档

- [06 - UIUX设计系统](../雅典娜开发技术文档汇总/06%20-%20UIUX设计系统UI_UX_Design_system.md)
- [03 - 系统架构与ADR](../雅典娜开发技术文档汇总/03%20-%20系统架构与ADR%20System_Architecture_and_Decisions.md)
- [00 - AI编码宪法](../.github/copilot-instructions.md)
