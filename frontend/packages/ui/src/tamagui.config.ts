/**
 * Athena Design System - Tamagui Configuration
 * 
 * 基于 06 - UIUX设计系统文档 v4.0 实现
 * 遵循 Apple HIG 标准，零硬编码
 * 
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 */

import { createTamagui, createTokens, createFont } from '@tamagui/core'
import { createAnimations } from '@tamagui/animations-react-native'

// ============================================================================
// 1. 字体系统 (Font Stack)
// Font Family: Inter, "Noto Sans SC", -apple-system, sans-serif
// ============================================================================

const interFont = createFont({
  family: 'Inter, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif',
  size: {
    1: 12,   // caption
    2: 13,   // footnote
    3: 15,   // subhead
    4: 16,   // callout
    5: 17,   // body / headline
    6: 20,   // title3
    7: 22,   // title2
    8: 28,   // title1
    9: 34,   // largeTitle
  },
  lineHeight: {
    1: 16,   // caption
    2: 18,   // footnote
    3: 20,   // subhead
    4: 21,   // callout
    5: 24,   // body
    6: 25,   // title3
    7: 28,   // title2
    8: 34,   // title1
    9: 41,   // largeTitle
  },
  weight: {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  letterSpacing: {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 0,
    8: 0,
    9: -0.5,
  },
  face: {
    400: { normal: 'Inter_400Regular' },
    500: { normal: 'Inter_500Medium' },
    600: { normal: 'Inter_600SemiBold' },
    700: { normal: 'Inter_700Bold' },
  },
})

// ============================================================================
// 2. Design Tokens
// ============================================================================

const tokens = createTokens({
  // ---------------------------------------------------------------------------
  // 2.1 间距系统 (Spacing) - 基于 4px 网格
  // ---------------------------------------------------------------------------
  space: {
    0: 0,
    1: 4,    // $1 = 4px
    2: 8,    // $2 = 8px
    3: 12,   // $3 = 12px
    4: 16,   // $4 = 16px (Mobile Margin)
    5: 20,   // $5 = 20px (Desktop Margin)
    6: 24,   // $6 = 24px
    8: 32,   // $8 = 32px
    10: 40,  // $10 = 40px
    12: 48,  // $12 = 48px
    16: 64,  // $16 = 64px
    true: 16, // default
  },

  // ---------------------------------------------------------------------------
  // 2.2 尺寸系统 (Size)
  // ---------------------------------------------------------------------------
  size: {
    0: 0,
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    5: 20,
    6: 24,
    8: 32,
    10: 40,
    12: 48,
    16: 64,
    // 触控热区
    touchTarget: 44,
    touchTargetDesktop: 32,
    // 导航栏
    navBar: 44,
    navBarLarge: 96,
    tabBar: 49,
    toolbar: 44,
    true: 16,
  },

  // ---------------------------------------------------------------------------
  // 2.3 圆角系统 (Border Radius) - Apple 超椭圆风格
  // ---------------------------------------------------------------------------
  radius: {
    none: 0,
    xs: 4,
    sm: 8,    // Apple 标准小圆角
    md: 12,   // Apple 标准中圆角
    lg: 20,   // Apple 超椭圆风格
    xl: 28,   // 底部 Sheet
    full: 9999,
    true: 12,
  },

  // ---------------------------------------------------------------------------
  // 2.4 层级系统 (Z-Index)
  // ---------------------------------------------------------------------------
  zIndex: {
    0: 0,
    1: 100,
    2: 200,
    3: 300,
    4: 400,
    5: 500,
  },

  // ---------------------------------------------------------------------------
  // 2.5 颜色系统 (Colors) - Apple 语义色 + Light/Dark 支持
  // ---------------------------------------------------------------------------
  color: {
    // 透明
    transparent: 'transparent',
    
    // ========== 系统强调色 (Light Mode) ==========
    systemBlue: '#007AFF',
    systemRed: '#FF3B30',
    systemGreen: '#34C759',
    systemOrange: '#FF9500',
    systemYellow: '#FFCC00',
    systemGray: '#8E8E93',
    
    // ========== 文本色彩 (Light Mode) ==========
    label: 'rgba(0,0,0,1.0)',
    labelSecondary: 'rgba(60,60,67,0.6)',
    labelTertiary: 'rgba(60,60,67,0.3)',
    labelQuaternary: 'rgba(60,60,67,0.18)',
    
    // ========== 背景填充 (Light Mode) ==========
    background: '#FFFFFF',
    backgroundSecondary: '#F2F2F7',
    backgroundTertiary: '#FFFFFF',
    backgroundElevated: '#FFFFFF',
    
    // ========== 分隔与填充 (Light Mode) ==========
    separator: 'rgba(60,60,67,0.29)',
    fill: 'rgba(120,120,128,0.2)',
    fillSecondary: 'rgba(120,120,128,0.16)',
    
    // ========== 高亮颜色 (Light Mode) ==========
    highlightYellow: '#FFEB3B',
    highlightGreen: '#4CAF50',
    highlightBlue: '#2196F3',
    highlightPurple: '#9C27B0',
    highlightRed: '#F44336',
    
    // ========== 常用色 ==========
    white: '#FFFFFF',
    black: '#000000',
  },
})

// ============================================================================
// 3. 暗色主题 (Dark Theme Colors)
// ============================================================================

const darkColors = {
  // 系统强调色 (Dark Mode)
  systemBlue: '#0A84FF',
  systemRed: '#FF453A',
  systemGreen: '#30D158',
  systemOrange: '#FF9F0A',
  systemYellow: '#FFD60A',
  systemGray: '#8E8E93',
  
  // 文本色彩 (Dark Mode)
  label: 'rgba(255,255,255,1.0)',
  labelSecondary: 'rgba(235,235,245,0.6)',
  labelTertiary: 'rgba(235,235,245,0.3)',
  labelQuaternary: 'rgba(235,235,245,0.16)',
  
  // 背景填充 (Dark Mode)
  background: '#000000',
  backgroundSecondary: '#1C1C1E',
  backgroundTertiary: '#2C2C2E',
  backgroundElevated: '#1C1C1E',
  
  // 分隔与填充 (Dark Mode)
  separator: 'rgba(84,84,88,0.65)',
  fill: 'rgba(120,120,128,0.36)',
  fillSecondary: 'rgba(120,120,128,0.32)',
  
  // 高亮颜色 (Dark Mode)
  highlightYellow: '#FDD835',
  highlightGreen: '#66BB6A',
  highlightBlue: '#42A5F5',
  highlightPurple: '#AB47BC',
  highlightRed: '#EF5350',
}

// ============================================================================
// 4. 动画系统 (Animations) - Apple 标准 Spring 参数
// ============================================================================

const animations = createAnimations({
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
  // 按钮点击反馈
  bouncy: {
    type: 'spring',
    stiffness: 300,
    damping: 20,
  },
  // 懒加载动画
  lazy: {
    type: 'spring',
    stiffness: 60,
    damping: 15,
  },
})

// ============================================================================
// 5. 主题配置 (Themes)
// ============================================================================

const lightTheme = {
  // 语义色 (放在前面，后面的属性会覆盖)
  ...tokens.color,
  // 主题特定覆盖
  background: tokens.color.background,
  backgroundHover: tokens.color.backgroundSecondary,
  backgroundPress: tokens.color.backgroundTertiary,
  backgroundFocus: tokens.color.backgroundSecondary,
  color: tokens.color.label,
  colorHover: tokens.color.label,
  colorPress: tokens.color.labelSecondary,
  colorFocus: tokens.color.label,
  borderColor: tokens.color.separator,
  borderColorHover: tokens.color.separator,
  borderColorPress: tokens.color.labelTertiary,
  borderColorFocus: tokens.color.systemBlue,
  placeholderColor: tokens.color.labelTertiary,
}

const darkTheme = {
  // 语义色 (放在前面，后面的属性会覆盖)
  ...darkColors,
  // 主题特定覆盖
  background: darkColors.background,
  backgroundHover: darkColors.backgroundSecondary,
  backgroundPress: darkColors.backgroundTertiary,
  backgroundFocus: darkColors.backgroundSecondary,
  color: darkColors.label,
  colorHover: darkColors.label,
  colorPress: darkColors.labelSecondary,
  colorFocus: darkColors.label,
  borderColor: darkColors.separator,
  borderColorHover: darkColors.separator,
  borderColorPress: darkColors.labelTertiary,
  borderColorFocus: darkColors.systemBlue,
  placeholderColor: darkColors.labelTertiary,
}

// ============================================================================
// 6. 创建 Tamagui 配置
// ============================================================================

export const config = createTamagui({
  tokens,
  themes: {
    light: lightTheme,
    dark: darkTheme,
  },
  fonts: {
    body: interFont,
    heading: interFont,
  },
  animations,
  
  // 媒体查询断点
  media: {
    xs: { maxWidth: 660 },
    sm: { maxWidth: 800 },
    md: { maxWidth: 1020 },
    lg: { maxWidth: 1280 },
    xl: { maxWidth: 1420 },
    xxl: { maxWidth: 1600 },
    gtXs: { minWidth: 660 + 1 },
    gtSm: { minWidth: 800 + 1 },
    gtMd: { minWidth: 1020 + 1 },
    gtLg: { minWidth: 1280 + 1 },
    short: { maxHeight: 820 },
    tall: { minHeight: 820 },
    hoverNone: { hover: 'none' },
    pointerCoarse: { pointer: 'coarse' },
  },

  // 默认属性
  defaultProps: {
    // 默认 Spring 动画
    animateOnly: ['transform', 'opacity'],
  },

  // Shorthands (简写)
  shorthands: {
    px: 'paddingHorizontal',
    py: 'paddingVertical',
    mx: 'marginHorizontal',
    my: 'marginVertical',
    bg: 'backgroundColor',
    br: 'borderRadius',
    w: 'width',
    h: 'height',
    f: 'flex',
  } as const,

  // 设置
  settings: {
    allowedStyleValues: 'somewhat-strict-web',
    autocompleteSpecificTokens: 'except-special',
  },
})

export default config

// 类型导出
export type AppConfig = typeof config
declare module '@tamagui/core' {
  interface TamaguiCustomConfig extends AppConfig {}
}
