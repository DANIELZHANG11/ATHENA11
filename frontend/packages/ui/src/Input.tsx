/**
 * Athena UI - Input Component
 *
 * Apple 风格输入框，带图标支持
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md §10.3
 */

import { styled, GetProps, Stack, View } from "@tamagui/core";
import { Input as TamaguiInput, XStack } from "tamagui";
import type { ReactNode } from "react";

export const InputBase = styled(TamaguiInput, {
  name: "Input",

  // 基础样式
  backgroundColor: "$fill",
  borderRadius: "$sm", // 8px - Apple 标准
  paddingHorizontal: "$4", // 16px
  height: 44, // 标准触控热区
  fontSize: 17, // body size
  color: "$label",
  borderWidth: 0,

  // 焦点样式
  focusStyle: {
    borderWidth: 2,
    borderColor: "$systemBlue",
    backgroundColor: "$backgroundTertiary",
  },

  // 占位符
  placeholderTextColor: "$labelTertiary",

  // 变体
  variants: {
    size: {
      small: {
        height: 36,
        fontSize: 15,
        paddingHorizontal: "$3",
      },
      medium: {
        height: 44,
        fontSize: 17,
        paddingHorizontal: "$4",
      },
      large: {
        height: 52,
        fontSize: 17,
        paddingHorizontal: "$5",
      },
    },

    error: {
      true: {
        borderWidth: 2,
        borderColor: "$systemRed",
      },
    },

    disabled: {
      true: {
        opacity: 0.5,
        pointerEvents: "none",
      },
    },
  } as const,

  defaultVariants: {
    size: "medium",
  },
});

export interface InputWithIconProps extends GetProps<typeof InputBase> {
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

/**
 * 带图标的输入框包装组件
 */
export function InputWithIcon({
  leftIcon,
  rightIcon,
  ...props
}: InputWithIconProps) {
  return (
    <XStack
      alignItems="center"
      backgroundColor="$fill"
      borderRadius="$sm"
      paddingHorizontal="$3"
      height={44}
      gap="$2"
      focusStyle={{
        borderWidth: 2,
        borderColor: "$systemBlue",
      }}
    >
      {leftIcon && (
        <View
          width={24}
          height={24}
          alignItems="center"
          justifyContent="center"
        >
          {leftIcon}
        </View>
      )}
      <InputBase
        {...props}
        flex={1}
        backgroundColor="transparent"
        paddingHorizontal={0}
        height="100%"
      />
      {rightIcon && (
        <View
          width={24}
          height={24}
          alignItems="center"
          justifyContent="center"
        >
          {rightIcon}
        </View>
      )}
    </XStack>
  );
}

export const Input = InputBase;
export type InputProps = GetProps<typeof Input>;
