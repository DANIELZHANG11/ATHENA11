/**
 * Athena UI - Button Component
 * 
 * Apple 风格按钮，支持 Filled / Tinted / Plain / Destructive 变体
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md §10.1
 */

import { styled, Button as TamaguiButton, GetProps } from 'tamagui'

export const Button = styled(TamaguiButton, {
  name: 'Button',
  
  // 基础样式
  alignItems: 'center',
  justifyContent: 'center',
  flexDirection: 'row',
  gap: '$2',
  
  // Apple 标准点击反馈
  pressStyle: {
    scale: 0.97,
    opacity: 0.8,
  },
  
  // 默认动画
  animation: 'fast',
  
  // 变体
  variants: {
    variant: {
      filled: {
        backgroundColor: '$systemBlue',
        color: 'white',
        borderRadius: '$full',
        paddingHorizontal: '$6',
        height: '$touchTarget', // 44px
        fontWeight: '600',
      },
      tinted: {
        backgroundColor: '$systemBlue',
        opacity: 0.1,
        color: '$systemBlue',
        borderRadius: '$sm',
        paddingHorizontal: '$4',
        height: '$touchTarget',
        fontWeight: '500',
      },
      plain: {
        backgroundColor: 'transparent',
        color: '$systemBlue',
        paddingHorizontal: '$2',
        height: '$touchTarget',
        fontWeight: '400',
      },
      destructive: {
        backgroundColor: '$systemRed',
        color: 'white',
        borderRadius: '$full',
        paddingHorizontal: '$6',
        height: '$touchTarget',
        fontWeight: '600',
      },
    },
    
    size: {
      small: {
        height: 32,
        paddingHorizontal: '$3',
        fontSize: 15,
      },
      medium: {
        height: 44,
        paddingHorizontal: '$4',
        fontSize: 17,
      },
      large: {
        height: 52,
        paddingHorizontal: '$6',
        fontSize: 17,
      },
    },
    
    disabled: {
      true: {
        opacity: 0.5,
        pointerEvents: 'none',
      },
    },
  } as const,
  
  // 默认变体
  defaultVariants: {
    variant: 'filled',
    size: 'medium',
  },
})

export type ButtonProps = GetProps<typeof Button>
