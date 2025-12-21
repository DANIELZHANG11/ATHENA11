# 06 - 雅典娜人机交互指南 (Athena Human Interface Guidelines)

> **版本**：v3.0 (Apple HIG Edition)
> **核心原则**：像素级的精确，原生级的流畅。
> **定位**：本项目的 **视觉与交互宪法**。所有 UI 开发必须严格遵循 Apple Human Interface Guidelines (HIG)，目标是打造一款**完全复刻 Apple Books 质感**的跨平台应用。

---

## 1. 核心设计哲学 (Core Philosophy)

*   **Defer to Content (内容至上)**：UI 是内容的画框，而非主角。利用留白、字体层级和模糊材质来突出书籍本身，避免装饰性元素喧宾夺主。
*   **Clarity (清晰)**：文本必须在任何尺寸下清晰可读，图标必须精确表意，色彩必须有明确的功能指示（如蓝色代表交互）。
*   **Depth (深度)**：利用层级、阴影和转场动画构建真实的物理空间感。用户操作必须有即时的视觉反馈。

---

## 2. 布局与几何 (Layout & Geometry)

> **开发指令**：不再使用“大约”、“适中”等模糊词汇。以下是强制执行的像素级标准。

### 2.1 触达与网格 (Touch & Grid)

| 指标 | Apple 标准 (Points) | Web 实现 (Pixel/Tailwind) | 强制规则 |
| :--- | :--- | :--- | :--- |
| **最小点击热区** | **44 x 44 pt** | `min-w-[44px] min-h-[44px]` (Mobile)<br>`min-w-[32px] min-h-[32px]` (Desktop Pointer) | 任何可点击元素（图标、链接）的**实际感应区域**不得低于此值。可使用 `p-2` 或负 margin 扩大热区。 |
| **基础网格单位** | **4 pt / 8 pt** | `0.25rem` (4px) / `0.5rem` (8px) | 所有间距、尺寸必须是 4 的倍数。严禁出现 13px, 21px 等奇数（描边除外）。 |
| **侧边距 (Margins)** | **16 pt** (iPhone)<br>**20 pt** (iPad/Web) | `px-4` (Mobile)<br>`px-5` (Tablet/Desktop) | 页面内容严禁贴边。 |
| **安全区域** | **Safe Area** | `pb-[env(safe-area-inset-bottom)]` | 底部 TabBar 和顶部导航栏必须处理刘海屏和 Home Indicator。 |

### 2.2 导航栏高度体系 (Navigation Standards)

| 组件 | Mobile Height | Desktop Height | Tailwind 类名 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Nav Bar** | **44px** | **44px** / **52px** | `h-11` | 标准标题栏，包含返回按钮和操作项。 |
| **Large Title Bar** | **96px** | **N/A** (通常 Sidebar) | `h-24` | 页面顶部大标题（如“书库”），随滚动渐变收缩为 Standard。 |
| **Tab Bar (Bottom)** | **49px** | **N/A** | `h-[49px]` | 移动端底部导航，需叠加 Safe Area Bottom。 |
| **Toolbar (Bottom)** | **44px** | **N/A** | `h-11` | 阅读器内部底部工具栏。 |
| **Sidebar Item** | **N/A** | **40px** | `h-10` | 桌面端侧边栏单项高度。 |

---

## 3. 排版系统 (Typography: The SF Pro Stack)

> **字体家族**：Web 端优先使用 Apple 系统字体。
> `font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "PingFang SC", sans-serif;`

### 3.1 动态排版阶梯 (Dynamic Type Scale)

严格对齐 iOS 规范。开发时应封装为 Tailwind Utility Classes。

| 样式名称 | 字号 (Size) | 行高 (Leading) | 字重 (Weight) | 用途 | Tailwind 推荐 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Large Title** | **34px** | **41px** | Regular (400) | 页面顶级标题 | `text-4xl font-normal leading-tight tracking-tight` |
| **Title 1** | **28px** | **34px** | Regular (400) | 一级版块标题 | `text-3xl font-normal leading-snug` |
| **Title 2** | **22px** | **28px** | Regular (400) | 二级标题 | `text-2xl font-normal leading-snug` |
| **Title 3** | **20px** | **25px** | Regular (400) | 弹窗/重要标题 | `text-xl font-normal leading-snug` |
| **Headline** | **17px** | **22px** | Semibold (600) | 卡片/列表标题 | `text-[17px] font-semibold leading-snug` |
| **Body (关键)** | **17px** | **22px** | Regular (400) | **正文内容** | `text-[17px] font-normal leading-snug` |
| **Callout** | **16px** | **21px** | Regular (400) | 文字按钮/次要内容 | `text-base font-normal leading-snug` |
| **Subhead** | **15px** | **20px** | Regular (400) | 副标题 | `text-[15px] font-normal leading-snug` |
| **Footnote** | **13px** | **18px** | Regular (400) | 底部说明/元数据 | `text-[13px] font-normal leading-none` |
| **Caption 1** | **12px** | **16px** | Regular (400) | 标签/微小说明 | `text-xs font-normal leading-none` |

> **关键差异**：Apple 的正文 (`Body`) 使用 **17px**，明显大于 Web 常见的 14px/16px。这是产生“高级感”和“易读性”的关键。请勿私自缩小。

---

## 4. 色彩与语义 (Colors & Semantics)

> **原则**：永远不要使用 Hex 黑色 (`#000000`) 渲染文字。使用**语义化颜色**以完美适配 Dark Mode。

### 4.1 文本与标签 (Label Colors)

| 名称 | Light Mode | Dark Mode | 用途 |
| :--- | :--- | :--- | :--- |
| **Label (Primary)** | `rgba(0,0,0, 1.0)` | `rgba(255,255,255, 1.0)` | 标题、正文、强强调 |
| **Secondary Label** | `rgba(60,60,67, 0.6)` | `rgba(235,235,245, 0.6)` | 副标题、说明文案 |
| **Tertiary Label** | `rgba(60,60,67, 0.3)` | `rgba(235,235,245, 0.3)` | 占位符、失效文字 |
| **Quaternary Label** | `rgba(60,60,67, 0.18)` | `rgba(235,235,245, 0.18)` | 分隔线、不可用状态 |

### 4.2 背景填充 (Fill Colors)

*   **System Background**:
    *   `system-background`: 纯白 (Light) / 纯黑 (Dark) —— *App 底色*。
    *   `secondary-system-background`: `#F2F2F7` (Light) / `#1C1C1E` (Dark) —— *列表/卡片/侧边栏背景*。
    *   `tertiary-system-background`: `#FFFFFF` (Light) / `#2C2C2E` (Dark) —— *二级卡片/输入框内部*。

### 4.3 关键强调色 (Tint Colors)

必须使用 iOS 标准色板：
*   **Blue (Interactive)**: `#007AFF` (Light) / `#0A84FF` (Dark) —— *所有可点击元素的默认色*。
*   **Red (Destructive)**: `#FF3B30` (Light) / `#FF453A` (Dark) —— *删除、报错*。
*   **Green (Success)**: `#34C759` (Light) / `#30D158` (Dark)。
*   **Gray (Neutral)**: `#8E8E93` (Light) / `#8E8E93` (Dark)。

---

## 5. 材质与光影 (Materials & Shadows)

这是复刻 Apple Books 质感的核心。

### 5.1 毛玻璃材质 (Materials)

使用 CSS `backdrop-filter` 实现。

| 材质名称 | 效果参数 | 适用场景 |
| :--- | :--- | :--- |
| **Thick Material** (Chrome) | `bg-white/80 dark:bg-black/80 backdrop-blur-xl` | 顶部导航栏、底部 TabBar、侧边栏 |
| **Regular Material** (Modal) | `bg-white/90 dark:bg-[#1C1C1E]/90 backdrop-blur-2xl` | 模态弹窗、Dropdown 菜单 |
| **Thin Material** (HUD) | `bg-white/70 dark:bg-black/70 backdrop-blur-lg` | 浮动工具栏、Toast 通知 |

> **降级策略**：在不支持 `backdrop-filter` 的环境，回退到 98% 不透明度的纯色背景。

### 5.2 阴影系统 (Shadows)

Apple 风格的阴影是**弥散的、多层的、带环境光遮蔽的**。

*   **Shadow 1 (Low) - 通用卡片**:
    `box-shadow: 0 1px 2px rgba(0,0,0,0.05);`
*   **Shadow 2 (Medium) - 悬浮元素**:
    `box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);`
*   **Shadow 3 (High) - 模态窗口**:
    `box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);`

*   **Book Shadow (拟物书影 - 关键)**:
    用于书籍封面，模拟真实书本厚度和光照。
    `box-shadow: 0 4px 8px -2px rgba(0,0,0,0.12), 0 8px 16px -4px rgba(0,0,0,0.08);`

---

## 6. 组件规格字典 (Component Specifications)

### 6.1 按钮 (Buttons)

Apple 风格按钮极度克制，通常为圆角矩形或胶囊型。

*   **Fill Button (主要操作)**:
    *   高度: **44px (Mobile) / 32px (Desktop)**
    *   圆角: `rounded-full` (胶囊)
    *   背景: `bg-system-blue`
    *   文字: `text-white font-semibold text-[17px]/[15px]`
    *   **例子**: "购买", "开始阅读"
*   **Tinted Button (次要操作)**:
    *   背景: `bg-system-blue/10` (Light) / `bg-system-blue/20` (Dark)
    *   文字: `text-system-blue font-medium`
    *   **例子**: "编辑", "更多"
*   **Plain Button (导航栏按钮)**:
    *   背景: 透明
    *   文字: `text-system-blue text-[17px] font-normal`
    *   **例子**: "取消", "完成", "返回"

### 6.2 分段控制器 (Segmented Control)

用于视图切换（如：全部 / 未读）。
*   容器: `h-8 bg-[#E3E3E8] dark:bg-[#1C1C1E] rounded-lg p-0.5`
*   选中项: `bg-white dark:bg-[#636366] shadow-sm rounded-md`
*   动效: 选中滑块必须有滑动过渡动画。

### 6.3 模态视图 (Modals & Sheets)

*   **Mobile (iPhone)**: **Bottom Sheet (半屏卡片)**。
    *   从底部滑出，顶部带 Grabber (短横线)。
    *   圆角: 顶部 `rounded-t-[10px]` 或更高。
    *   背景: Regular Material。
*   **Tablet/Desktop**: **Center Dialog (中心弹窗)** 或 **Form Sheet**。
    *   居中显示。
    *   尺寸: `min-w-[320px] max-w-[640px]`。
    *   圆角: `rounded-xl` (12px-16px)。
    *   阴影: Shadow 3 (High)。

### 6.4 列表 (Lists / Table Views)

Apple 设置页风格。
*   **Inset Grouped**:
    *   容器宽度: `max-w-2xl mx-auto`.
    *   单元格圆角: 组的第一个 `rounded-t-xl`, 最后一个 `rounded-b-xl`.
    *   背景: `bg-white dark:bg-[#1C1C1E]`.
    *   分隔线: 左侧留空 16px/20px (`separator` color).
    *   高度: 单行至少 **44px**.

## 7. 资源与图标

*   **图标库**: `lucide-react` (Web 实现的最佳替代品)。
*   **线宽**: 统一使用 `stroke-width={1.5}` (Regular) 或 `2` (Medium)。严禁使用粗线条。
*   **尺寸**:
    *   Tab Bar Icon: `24px`
    *   Nav Bar Icon: `22px`
    *   List Icon: `20px`

---

## 8. 阅读器交互规格 (Reader Interaction Specifications)

> **设计原则**：沉浸式阅读体验，最小化干扰，触控操作如纸质书籍般自然。

### 8.1 手势热区定义 (Gesture Zone Map)

阅读器屏幕被划分为 9 个手势热区，支持不同的交互行为。

```
┌─────────────────────────────────────────────────────────────┐
│                    TOP ZONE (15%)                            │
│              [点击] → 显示/隐藏导航栏                         │
├──────────┬────────────────────────────────┬─────────────────┤
│          │                                │                 │
│  LEFT    │         CENTER ZONE            │    RIGHT        │
│  ZONE    │            (60%)               │    ZONE         │
│  (15%)   │                                │    (15%)        │
│          │  [点击] → 显示/隐藏工具栏        │                 │
│  [点击]  │  [长按] → 文本选择              │   [点击]        │
│    ↓     │  [双击] → 标记/取消书签         │     ↓           │
│  上一页  │  [捏合] → 字号缩放 (PDF)        │   下一页        │
│          │                                │                 │
├──────────┴────────────────────────────────┴─────────────────┤
│                   BOTTOM ZONE (10%)                          │
│              [点击] → 显示/隐藏工具栏                         │
│              [上滑] → 显示进度条                              │
└─────────────────────────────────────────────────────────────┘
```

**热区参数**:
| 区域 | 位置 | 尺寸 | 主要手势 |
|-----|------|------|---------|
| TOP | y: 0 - 15% | 全宽 | 单击切换 UI |
| LEFT | x: 0 - 15%, y: 15% - 90% | 15% × 75% | 单击翻上一页 |
| CENTER | x: 15% - 85%, y: 15% - 90% | 70% × 75% | 多功能区 |
| RIGHT | x: 85% - 100%, y: 15% - 90% | 15% × 75% | 单击翻下一页 |
| BOTTOM | y: 90% - 100% | 全宽 | 上滑显示进度 |

### 8.2 翻页动画参数 (Page Turn Animation)

**EPUB 流式翻页**:
```typescript
const scrollPageAnimation = {
  type: "slide",
  direction: "horizontal" | "vertical",  // 基于用户设置
  duration: 300,                          // 毫秒
  easing: "cubic-bezier(0.25, 0.1, 0.25, 1.0)",  // Apple 标准缓动
  displacement: "100vw",                  // 水平滑动距离
}
```

**PDF 固定翻页**:
```typescript
const pdfPageAnimation = {
  // 仿真翻页 (Curl) - 可选高级模式
  curlEffect: {
    enabled: true,
    shadowOpacity: 0.3,
    curlRadius: "15%",
    duration: 400,
  },
  // 淡入淡出 (默认)
  fadeEffect: {
    duration: 200,
    easing: "ease-in-out",
  },
  // 无动画 (省电模式)
  noneEffect: {
    duration: 0,
  }
}
```

### 8.3 阅读器工具栏规格 (Reader Toolbar)

**顶部导航栏** (高度 44px):
```
┌──────────────────────────────────────────────────────────────┐
│  [←]     《思考，快与慢》- 第3章               [🔍] [⋮]      │
└──────────────────────────────────────────────────────────────┘
```
- 返回按钮：`← chevron-left`，44×44px 热区
- 标题：居中，最多显示 20 字符，超出省略
- 右侧操作：搜索、更多菜单

**底部工具栏** (高度 44px + Safe Area):
```
┌──────────────────────────────────────────────────────────────┐
│  [📑]    [Aa]    [☀️]    [🔖]    [💬]                        │
│  目录     字体    亮度    书签    笔记                        │
└──────────────────────────────────────────────────────────────┘
```

**进度滑块** (从底部上滑激活):
```
┌──────────────────────────────────────────────────────────────┐
│  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●     │
│  第 125 页                                     共 320 页    │
│  39%                              预计剩余 2 小时 15 分钟    │
└──────────────────────────────────────────────────────────────┘
```

### 8.4 文本选择与操作 (Text Selection)

**触发方式**：长按 500ms

**选择手柄样式**:
```typescript
const selectionHandle = {
  color: "#007AFF",           // System Blue
  size: 20,                   // px
  shape: "teardrop",          // 水滴形
  hitArea: 44,                // 触控热区
}
```

**弹出菜单** (Selection Menu):
```
┌─────────────────────────────────────────────────┐
│  高亮  │  笔记  │  复制  │  翻译  │  朗读  │  ⋯  │
└─────────────────────────────────────────────────┘
```
- 位置：选中文本上方/下方，自动避开屏幕边缘
- 动画：fade-in + scale (0.95 → 1.0)，duration 150ms
- 最小宽度：280px
- 高度：40px

**高亮颜色选择器**:
| 颜色 | Hex (Light) | Hex (Dark) | 名称 |
|-----|-------------|------------|------|
| 🟡 | `#FFEB3B` | `#FDD835` | 黄色（默认） |
| 🟢 | `#4CAF50` | `#66BB6A` | 绿色 |
| 🔵 | `#2196F3` | `#42A5F5` | 蓝色 |
| 🟣 | `#9C27B0` | `#AB47BC` | 紫色 |
| 🔴 | `#F44336` | `#EF5350` | 红色 |

### 8.5 字体与排版设置面板 (Typography Panel)

**面板高度**：50% 屏幕高度 (Bottom Sheet)

**可调参数**:
| 设置项 | 范围 | 默认值 | 增量 |
|-------|------|--------|------|
| 字号 | 12px - 32px | 17px | 1px |
| 行高 | 1.2 - 2.5 | 1.6 | 0.1 |
| 字间距 | -2% - 10% | 0% | 1% |
| 段落间距 | 0 - 32px | 16px | 4px |
| 页边距 | 8px - 48px | 24px | 4px |

**字体选择** (系统预设):
- 思源宋体 (Noto Serif SC) - 中文默认
- 思源黑体 (Noto Sans SC) - 无衬线
- 霞鹜文楷 (LXGW WenKai) - 手写风格
- SF Pro Text - 英文默认
- Georgia - 英文衬线
- OpenDyslexic - 阅读障碍辅助

### 8.6 亮度与主题 (Brightness & Theme)

**主题模式**:
| 模式 | 背景色 | 文字色 | 使用场景 |
|------|--------|--------|---------|
| 明亮 | `#FFFFFF` | `#1C1C1E` | 日间阅读 |
| 暗色 | `#1C1C1E` | `#EBEBF5` | 夜间阅读 |
| 护眼 | `#F5F1E6` | `#333333` | 长时间阅读 |
| 深黑 | `#000000` | `#EEEEEE` | OLED 省电 |

**亮度滑块**:
- 范围：5% - 100%
- 步进：连续滑动
- 可覆盖系统亮度（需用户授权）

### 8.7 过渡动画时序 (Animation Timing)

| 动画类型 | 持续时间 | 缓动函数 | 说明 |
|---------|---------|---------|------|
| 工具栏显隐 | 250ms | ease-in-out | 淡入淡出 + 上下滑动 |
| 翻页滑动 | 300ms | cubic-bezier(0.25, 0.1, 0.25, 1.0) | Apple 标准 |
| 菜单弹出 | 150ms | ease-out | 缩放 + 淡入 |
| 高亮渲染 | 100ms | linear | 即时反馈 |
| 进度条滑动 | 0ms | - | 实时跟随手指 |

---

## 9. 质量验收清单 (QA Checklist)

在提交任何 UI 代码前，必须检查：

1.  [ ] **热区达标**: 在手机上，按钮是否容易点击（>= 44px）？
2.  [ ] **字体层级**: 是否使用了 SF Pro 标准字号（Body 17px）？
3.  [ ] **深色模式**: 切换到 Dark Mode，文字是否清晰？背景是否不刺眼（不是纯黑，而是深灰）？
4.  [ ] **对齐**: 侧边距是否严格统一（Mobile 16px / Desktop 20px）？
5.  [ ] **反馈**: 点击任何按钮，是否有透明度降低 (`opacity-70`) 或背景色加深的高亮态？
6.  [ ] **翻页流畅**: 翻页动画是否达到 60fps？无明显卡顿？
7.  [ ] **手势识别**: 左右区域翻页是否灵敏？中央区域长按是否准确触发选择？
