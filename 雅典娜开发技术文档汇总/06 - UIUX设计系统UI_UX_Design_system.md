# 06 - 雅典娜设计系统 (Athena Design System)

> **版本**：v4.0 (Tamagui + Apple HIG Edition)
> **核心原则**：像素级对齐 Apple 标准，100% AI 驱动，零硬编码。
> **技术栈**：Expo + Tamagui + Solito + Next.js (Monorepo)
> **定位**：本项目的 **视觉宪法**。所有 UI 开发必须通过 Tamagui Token 系统实现，严禁直接书写硬编码值。

---

## 1. 核心设计哲学 (Core Philosophy)

*   **Defer to Content (内容至上)**：UI 是内容的画框，而非主角。利用留白、字体层级和模糊材质来突出书籍本身。
*   **Clarity (清晰)**：文本必须在任何尺寸下清晰可读，图标必须精确表意，色彩必须有明确的功能指示。
*   **Depth (深度)**：利用层级、阴影和 Spring 动画构建真实的物理空间感。
*   **Zero Hardcoding (零硬编码)**：**严禁**在代码中直接书写十六进制颜色、像素数值（px）、或原始 fontSize。所有样式必须通过 Tamagui Token 引用。

---

## 2. 字体系统 (The Font Stack)

> **强制规范**：必须使用以下字体堆栈，确保跨平台一致性。

### 2.1 Font Family 声明

\`\`\`css
/* 全局 Font Stack - 写入 tamagui.config.ts */
font-family: Inter, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif;
\`\`\`

| 语言 | 主字体 | 回退字体 | 说明 |
| :--- | :--- | :--- | :--- |
| **英文/数字** | **Inter** | SF Pro Text, -apple-system | Google 开源，Web 可变字体 |
| **中文** | **Noto Sans SC** | PingFang SC, "Microsoft YaHei" | 思源黑体简体中文版 |

### 2.2 字体权重映射 (Font Weight Tokens)

| Token 名称 | 数值 | Inter 权重 | Noto Sans SC 权重 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| \`$fontWeight.regular\` | 400 | Regular | Regular | 正文 |
| \`$fontWeight.medium\` | 500 | Medium | Medium | 次要强调 |
| \`$fontWeight.semibold\` | 600 | SemiBold | Bold | 标题、按钮 |
| \`$fontWeight.bold\` | 700 | Bold | Bold | 强强调 |

### 2.3 字体加载策略

\`\`\`typescript
// apps/expo/app/_layout.tsx
import { useFonts } from 'expo-font'
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold } from '@expo-google-fonts/inter'

// apps/next/pages/_app.tsx
import '@fontsource/inter/variable.css'
import '@fontsource/noto-sans-sc/400.css'
import '@fontsource/noto-sans-sc/500.css'
import '@fontsource/noto-sans-sc/700.css'
\`\`\`

---

## 3. Token 系统 (Design Tokens)

> **铁律**：所有数值必须通过 Token 引用。违反此规则的代码将被 CI 拒绝。

### 3.1 间距系统 (Spacing Tokens)

基于 **4px 网格** 步进，严禁出现非 4 倍数的间距值（描边除外）。

| Token | 像素值 | rem 值 | 用途示例 |
| :--- | :--- | :--- | :--- |
| \`$space.0\` | 0px | 0 | 无间距 |
| \`$space.1\` | 4px | 0.25rem | 极小间隙、图标内边距 |
| \`$space.2\` | 8px | 0.5rem | 紧凑元素间距 |
| \`$space.3\` | 12px | 0.75rem | 列表项内边距 |
| \`$space.4\` | 16px | 1rem | **标准间距 (Mobile Margin)** |
| \`$space.5\` | 20px | 1.25rem | **标准间距 (Desktop Margin)** |
| \`$space.6\` | 24px | 1.5rem | 区块间距 |
| \`$space.8\` | 32px | 2rem | 大区块分隔 |
| \`$space.10\` | 40px | 2.5rem | 页面顶部/底部留白 |
| \`$space.12\` | 48px | 3rem | 特大间距 |
| \`$space.16\` | 64px | 4rem | 页面级分隔 |

### 3.2 圆角系统 (Border Radius Tokens)

采用 **Apple 超椭圆 (Squircle)** 风格，通过 CSS \`border-radius\` 配合 \`smooth\` 属性实现。

| Token | 像素值 | 用途 | 说明 |
| :--- | :--- | :--- | :--- |
| \`$radius.none\` | 0px | 无圆角 | 分割线、全出血图片 |
| \`$radius.xs\` | 4px | 小型标签 | Tag, Badge |
| \`$radius.sm\` | 8px | 按钮、输入框 | **Apple 标准小圆角** |
| \`$radius.md\` | 12px | 卡片、弹窗 | **Apple 标准中圆角** |
| \`$radius.lg\` | 20px | 大型卡片、模态框 | **Apple 超椭圆风格** |
| \`$radius.xl\` | 28px | 底部 Sheet | 底部弹出面板 |
| \`$radius.full\` | 9999px | 胶囊按钮、头像 | 完全圆形 |

> **Squircle 模式**：在 Tamagui 中启用 \`smoothCorners: true\` 以获得 Apple 超椭圆效果。

### 3.3 阴影系统 (Shadow Tokens)

Apple 风格阴影特点：**扩散半径大、透明度极低、多层叠加**。

| Token | CSS 值 | 用途 |
| :--- | :--- | :--- |
| \`$shadow.sm\` | \`0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)\` | 通用卡片、列表项 |
| \`$shadow.md\` | \`0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05)\` | 悬浮元素、Dropdown |
| \`$shadow.lg\` | \`0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05)\` | 模态窗口、重要卡片 |
| \`$shadow.xl\` | \`0 20px 25px -5px rgba(0,0,0,0.10), 0 8px 10px -6px rgba(0,0,0,0.05)\` | 全屏弹窗、Drawer |
| \`$shadow.book\` | \`0 4px 8px -2px rgba(0,0,0,0.12), 0 8px 16px -4px rgba(0,0,0,0.08)\` | **书籍封面专用** |

---

## 4. 色彩语义系统 (Semantic Color Tokens)

> **原则**：必须使用 Apple 语义色，支持 Light/Dark 模式自动映射。严禁使用 Hex 硬编码。

### 4.1 系统强调色 (System Tint Colors)

| Token | Light Mode | Dark Mode | 用途 |
| :--- | :--- | :--- | :--- |
| \`$color.systemBlue\` | \`#007AFF\` | \`#0A84FF\` | **所有可交互元素** |
| \`$color.systemRed\` | \`#FF3B30\` | \`#FF453A\` | 删除、错误、警告 |
| \`$color.systemGreen\` | \`#34C759\` | \`#30D158\` | 成功、完成、在线 |
| \`$color.systemOrange\` | \`#FF9500\` | \`#FF9F0A\` | 警告、提醒 |
| \`$color.systemYellow\` | \`#FFCC00\` | \`#FFD60A\` | 高亮、星标 |
| \`$color.systemGray\` | \`#8E8E93\` | \`#8E8E93\` | 中性、禁用 |

### 4.2 文本色彩 (Label Colors)

| Token | Light Mode | Dark Mode | 用途 |
| :--- | :--- | :--- | :--- |
| \`$color.label\` | \`rgba(0,0,0,1.0)\` | \`rgba(255,255,255,1.0)\` | 标题、正文 |
| \`$color.labelSecondary\` | \`rgba(60,60,67,0.6)\` | \`rgba(235,235,245,0.6)\` | 副标题、说明 |
| \`$color.labelTertiary\` | \`rgba(60,60,67,0.3)\` | \`rgba(235,235,245,0.3)\` | 占位符、禁用文字 |
| \`$color.labelQuaternary\` | \`rgba(60,60,67,0.18)\` | \`rgba(235,235,245,0.16)\` | 分隔线 |

### 4.3 背景填充 (Background Colors)

| Token | Light Mode | Dark Mode | 用途 |
| :--- | :--- | :--- | :--- |
| \`$color.background\` | \`#FFFFFF\` | \`#000000\` | App 主背景 |
| \`$color.backgroundSecondary\` | \`#F2F2F7\` | \`#1C1C1E\` | 列表背景、侧边栏 |
| \`$color.backgroundTertiary\` | \`#FFFFFF\` | \`#2C2C2E\` | 卡片内部、输入框 |
| \`$color.backgroundElevated\` | \`#FFFFFF\` | \`#1C1C1E\` | 弹窗、模态框 |

### 4.4 分隔与填充 (Separator & Fill)

| Token | Light Mode | Dark Mode | 用途 |
| :--- | :--- | :--- | :--- |
| \`$color.separator\` | \`rgba(60,60,67,0.29)\` | \`rgba(84,84,88,0.65)\` | 分隔线 |
| \`$color.fill\` | \`rgba(120,120,128,0.2)\` | \`rgba(120,120,128,0.36)\` | 输入框背景 |
| \`$color.fillSecondary\` | \`rgba(120,120,128,0.16)\` | \`rgba(120,120,128,0.32)\` | 次要填充 |

---

## 5. 排版阶梯 (Typography Scale)

> **关键**：Apple 的正文 Body 使用 **17px**，这是产生"高级感"和"易读性"的关键。严禁私自缩小。

### 5.1 排版 Token 定义

| Token | 字号 | 行高 | 字重 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| \`$fontSize.largeTitle\` | **34px** | **41px** | Regular (400) | 页面大标题 |
| \`$fontSize.title1\` | **28px** | **34px** | Regular (400) | 一级标题 |
| \`$fontSize.title2\` | **22px** | **28px** | Regular (400) | 二级标题 |
| \`$fontSize.title3\` | **20px** | **25px** | Regular (400) | 三级标题 |
| \`$fontSize.headline\` | **17px** | **22px** | Semibold (600) | 卡片标题 |
| \`$fontSize.body\` | **17px** | **24px** | Regular (400) | **正文内容** |
| \`$fontSize.callout\` | **16px** | **21px** | Regular (400) | 次要内容 |
| \`$fontSize.subhead\` | **15px** | **20px** | Regular (400) | 副标题 |
| \`$fontSize.footnote\` | **13px** | **18px** | Regular (400) | 脚注说明 |
| \`$fontSize.caption\` | **12px** | **16px** | Regular (400) | 标签、微小说明 |

### 5.2 Tamagui 排版组件

\`\`\`typescript
// packages/ui/src/typography.ts
export const LargeTitle = styled(Text, { fontSize: '$largeTitle', lineHeight: 41, fontWeight: '$regular' })
export const Title1 = styled(Text, { fontSize: '$title1', lineHeight: 34, fontWeight: '$regular' })
export const Title2 = styled(Text, { fontSize: '$title2', lineHeight: 28, fontWeight: '$regular' })
export const Title3 = styled(Text, { fontSize: '$title3', lineHeight: 25, fontWeight: '$regular' })
export const Headline = styled(Text, { fontSize: '$headline', lineHeight: 22, fontWeight: '$semibold' })
export const Body = styled(Text, { fontSize: '$body', lineHeight: 24, fontWeight: '$regular' })
export const Callout = styled(Text, { fontSize: '$callout', lineHeight: 21, fontWeight: '$regular' })
export const Subhead = styled(Text, { fontSize: '$subhead', lineHeight: 20, fontWeight: '$regular' })
export const Footnote = styled(Text, { fontSize: '$footnote', lineHeight: 18, fontWeight: '$regular' })
export const Caption = styled(Text, { fontSize: '$caption', lineHeight: 16, fontWeight: '$regular' })
\`\`\`

---

## 6. 图标规范 (Icon System)

> **强制规范**：全平台锁定使用 **Lucide** 图标库，严禁引入其他图标库。

### 6.1 图标库声明

\`\`\`typescript
// 仅允许的引入方式
import { BookOpen, Search, Settings } from 'lucide-react'        // Web
import { BookOpen, Search, Settings } from 'lucide-react-native' // Native
\`\`\`

### 6.2 图标尺寸规范

| 场景 | 尺寸 | Lucide size 属性 | 说明 |
| :--- | :--- | :--- | :--- |
| **Tab Bar** | 24px | \`size={24}\` | 底部导航图标 |
| **Nav Bar** | 22px | \`size={22}\` | 顶部导航按钮 |
| **List Item** | 20px | \`size={20}\` | **标准列表图标** |
| **Button Icon** | 18px | \`size={18}\` | 按钮内图标 |
| **Inline** | 16px | \`size={16}\` | 文本内联图标 |

### 6.3 图标样式

| 属性 | 值 | 说明 |
| :--- | :--- | :--- |
| \`strokeWidth\` | **1.5** (Regular) / **2** (Medium) | 标准线宽，严禁使用粗线条 |
| \`color\` | \`$color.systemBlue\` / \`$color.label\` | 语义化颜色 |

---

## 7. 布局与几何 (Layout & Geometry)

### 7.1 触控热区 (Touch Targets)

| 平台 | 最小热区 | Token | 说明 |
| :--- | :--- | :--- | :--- |
| **Mobile** | **44 × 44 px** | \`$size.touchTarget\` | Apple HIG 强制标准 |
| **Desktop** | **32 × 32 px** | \`$size.touchTargetDesktop\` | 指针设备可适当缩小 |

### 7.2 导航栏高度

| 组件 | 高度 | Token | 说明 |
| :--- | :--- | :--- | :--- |
| **Standard Nav Bar** | 44px | \`$size.navBar\` | 顶部标准导航栏 |
| **Large Title Bar** | 96px | \`$size.navBarLarge\` | 大标题导航栏 |
| **Tab Bar** | 49px | \`$size.tabBar\` | 底部 Tab 栏 |
| **Toolbar** | 44px | \`$size.toolbar\` | 阅读器底部工具栏 |

### 7.3 安全区域

\`\`\`typescript
// 必须处理安全区域
import { useSafeAreaInsets } from 'react-native-safe-area-context'

const insets = useSafeAreaInsets()
// paddingBottom: insets.bottom + 49 (TabBar 高度)
\`\`\`

---

## 8. 动画与交互 (Animation & Interaction)

### 8.1 全局 Spring 动画配置

\`\`\`typescript
// packages/ui/src/tamagui.config.ts
export const animations = createAnimations({
  fast: {
    type: 'spring',
    stiffness: 250,
    damping: 25,
  },
  medium: {
    type: 'spring',
    stiffness: 170,  // Apple 标准
    damping: 26,     // Apple 标准
  },
  slow: {
    type: 'spring',
    stiffness: 120,
    damping: 20,
  },
})
\`\`\`

### 8.2 按钮点击反馈

\`\`\`typescript
// 所有 Button 组件的默认点击缩放
export const Button = styled(TamaguiButton, {
  pressStyle: {
    scale: 0.97,  // Apple 标准点击缩放
    opacity: 0.8,
  },
  animation: 'fast',
})
\`\`\`

### 8.3 页面过渡动画

| 过渡类型 | 配置 | 用途 |
| :--- | :--- | :--- |
| **Push** | \`duration: 350ms, easing: cubic-bezier(0.2, 0.8, 0.2, 1)\` | 页面入栈 |
| **Modal** | \`spring: { stiffness: 170, damping: 26 }\` | 模态弹出 |
| **Fade** | \`duration: 200ms\` | 淡入淡出 |

---

## 9. 材质与毛玻璃 (Materials)

### 9.1 毛玻璃效果 (Blur Materials)

| Token | 配置 | 用途 |
| :--- | :--- | :--- |
| \`$material.thick\` | \`bg-white/80 dark:bg-black/80 backdrop-blur-xl\` | 导航栏、TabBar |
| \`$material.regular\` | \`bg-white/90 dark:bg-[#1C1C1E]/90 backdrop-blur-2xl\` | 模态弹窗 |
| \`$material.thin\` | \`bg-white/70 dark:bg-black/70 backdrop-blur-lg\` | Toast、HUD |

### 9.2 React Native 实现

\`\`\`typescript
import { BlurView } from 'expo-blur'

<BlurView intensity={80} tint="light" style={styles.navbar} />
\`\`\`

---

## 10. 组件规格 (Component Specifications)

### 10.1 按钮 (Buttons)

| 类型 | 高度 (Mobile/Desktop) | 圆角 | 背景 | 文字 |
| :--- | :--- | :--- | :--- | :--- |
| **Filled** | 44px / 32px | \`$radius.full\` | \`$color.systemBlue\` | white, semibold |
| **Tinted** | 44px / 32px | \`$radius.sm\` | \`$color.systemBlue\` 10% | \`$color.systemBlue\` |
| **Plain** | 44px / 32px | none | transparent | \`$color.systemBlue\` |
| **Destructive** | 44px / 32px | \`$radius.full\` | \`$color.systemRed\` | white, semibold |

### 10.2 卡片 (Cards)

\`\`\`typescript
export const Card = styled(View, {
  backgroundColor: '$backgroundTertiary',
  borderRadius: '$lg',        // 20px
  padding: '$4',              // 16px
  shadowColor: '$shadow.sm',
})
\`\`\`

### 10.3 列表项 (List Items)

| 属性 | 值 | 说明 |
| :--- | :--- | :--- |
| 最小高度 | 44px | 符合触控热区 |
| 左侧内边距 | 16px (Mobile) / 20px (Desktop) | 统一侧边距 |
| 分隔线 | 左侧缩进 16px | Apple 风格 |

---

## 11. 阅读器交互规格 (Reader Interaction)

### 11.1 手势热区定义

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                    TOP ZONE (15%)                            │
│              [点击] → 显示/隐藏导航栏                         │
├──────────┬────────────────────────────────┬─────────────────┤
│  LEFT    │         CENTER ZONE            │    RIGHT        │
│  ZONE    │            (60%)               │    ZONE         │
│  (15%)   │  [点击] → 显示/隐藏工具栏        │    (15%)        │
│  [点击]  │  [长按] → 文本选择              │   [点击]        │
│    ↓     │  [双击] → 标记书签              │     ↓           │
│  上一页  │  [捏合] → 字号缩放              │   下一页        │
├──────────┴────────────────────────────────┴─────────────────┤
│                   BOTTOM ZONE (10%)                          │
│              [上滑] → 显示进度条                              │
└─────────────────────────────────────────────────────────────┘
\`\`\`

### 11.2 翻页动画

\`\`\`typescript
const pageAnimation = {
  type: 'spring',
  stiffness: 170,
  damping: 26,
  displacement: '100%',
}
\`\`\`

### 11.3 高亮颜色

| 颜色 | Light Mode | Dark Mode | Token |
| :--- | :--- | :--- | :--- |
| 黄色（默认） | \`#FFEB3B\` | \`#FDD835\` | \`$color.highlightYellow\` |
| 绿色 | \`#4CAF50\` | \`#66BB6A\` | \`$color.highlightGreen\` |
| 蓝色 | \`#2196F3\` | \`#42A5F5\` | \`$color.highlightBlue\` |
| 紫色 | \`#9C27B0\` | \`#AB47BC\` | \`$color.highlightPurple\` |
| 红色 | \`#F44336\` | \`#EF5350\` | \`$color.highlightRed\` |

---

## 12. 质量验收清单 (QA Checklist)

在提交任何 UI 代码前，必须检查：

- [ ] **零硬编码**: 代码中是否存在直接书写的 Hex 颜色或 px 数值？
- [ ] **Token 引用**: 所有样式是否通过 \`$space\`, \`$color\`, \`$radius\`, \`$fontSize\` 引用？
- [ ] **图标来源**: 所有图标是否来自 \`lucide-react\` / \`lucide-react-native\`？
- [ ] **热区达标**: 可点击元素热区是否 >= 44px (Mobile)？
- [ ] **字体正确**: 英文是否使用 Inter，中文是否使用 Noto Sans SC？
- [ ] **深色模式**: Dark Mode 下是否正常显示？
- [ ] **动画流畅**: 交互动画是否达到 60fps？
- [ ] **Spring 参数**: 动画是否使用 \`stiffness: 170, damping: 26\`？
