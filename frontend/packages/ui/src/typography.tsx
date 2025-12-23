/**
 * Athena UI - Typography Components
 * 
 * 基于 Apple HIG 排版阶梯
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md §5
 */

import { styled, Text } from '@tamagui/core'

// Large Title - 34px / 41px
export const LargeTitle = styled(Text, {
  name: 'LargeTitle',
  fontSize: 34,
  lineHeight: 41,
  fontWeight: '400',
  color: '$label',
})

// Title 1 - 28px / 34px
export const Title1 = styled(Text, {
  name: 'Title1',
  fontSize: 28,
  lineHeight: 34,
  fontWeight: '400',
  color: '$label',
})

// Title 2 - 22px / 28px
export const Title2 = styled(Text, {
  name: 'Title2',
  fontSize: 22,
  lineHeight: 28,
  fontWeight: '400',
  color: '$label',
})

// Title 3 - 20px / 25px
export const Title3 = styled(Text, {
  name: 'Title3',
  fontSize: 20,
  lineHeight: 25,
  fontWeight: '400',
  color: '$label',
})

// Headline - 17px / 22px / Semibold
export const Headline = styled(Text, {
  name: 'Headline',
  fontSize: 17,
  lineHeight: 22,
  fontWeight: '600',
  color: '$label',
})

// Body - 17px / 24px (Apple 标准正文)
export const Body = styled(Text, {
  name: 'Body',
  fontSize: 17,
  lineHeight: 24,
  fontWeight: '400',
  color: '$label',
})

// Callout - 16px / 21px
export const Callout = styled(Text, {
  name: 'Callout',
  fontSize: 16,
  lineHeight: 21,
  fontWeight: '400',
  color: '$label',
})

// Subhead - 15px / 20px
export const Subhead = styled(Text, {
  name: 'Subhead',
  fontSize: 15,
  lineHeight: 20,
  fontWeight: '400',
  color: '$label',
})

// Footnote - 13px / 18px
export const Footnote = styled(Text, {
  name: 'Footnote',
  fontSize: 13,
  lineHeight: 18,
  fontWeight: '400',
  color: '$labelSecondary',
})

// Caption - 12px / 16px
export const Caption = styled(Text, {
  name: 'Caption',
  fontSize: 12,
  lineHeight: 16,
  fontWeight: '400',
  color: '$labelSecondary',
})
