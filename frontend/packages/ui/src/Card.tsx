/**
 * Athena UI - Card Component
 *
 * Apple 风格卡片，带有 Apple 超椭圆圆角和阴影
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md §10.2
 */

import { styled, View, GetProps } from "@tamagui/core";

export const Card = styled(View, {
  name: "Card",

  // 基础样式
  backgroundColor: "$backgroundTertiary",
  borderRadius: "$lg", // 20px - Apple 超椭圆风格
  padding: "$4", // 16px

  // Apple 风格阴影
  shadowColor: "$black",
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.04,
  shadowRadius: 3,

  // 变体
  variants: {
    elevated: {
      true: {
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
    },

    pressable: {
      true: {
        pressStyle: {
          scale: 0.98,
          opacity: 0.9,
        },
        animation: "fast",
      },
    },

    size: {
      small: {
        padding: "$3",
        borderRadius: "$md",
      },
      medium: {
        padding: "$4",
        borderRadius: "$lg",
      },
      large: {
        padding: "$6",
        borderRadius: "$lg",
      },
    },
  } as const,

  defaultVariants: {
    size: "medium",
  },
});

export type CardProps = GetProps<typeof Card>;
