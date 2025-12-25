/**
 * Athena UI - Logo 组件
 *
 * 雅典娜 LOGO 组件，支持不同尺寸
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 */

import { GetProps } from "@tamagui/core";
import { Image } from "tamagui";

// LOGO 资源路径（需要在不同平台适配）
// Expo: require('@athena/app/assets/athena-logo.png')
// Next.js: /athena-logo.png (放在 public 目录)

export interface LogoProps {
  /** Logo 尺寸预设 */
  size?: "small" | "medium" | "large" | "hero";
  /** 自定义宽度 */
  width?: number;
  /** 自定义高度 */
  height?: number;
}

const LOGO_SIZES = {
  small: { width: 40, height: 40 },
  medium: { width: 64, height: 64 },
  large: { width: 100, height: 100 },
  hero: { width: 150, height: 150 },
} as const;

/**
 * Logo 组件
 *
 * @example
 * // 使用预设尺寸
 * <Logo size="hero" />
 *
 * // 使用自定义尺寸
 * <Logo width={120} height={120} />
 */
export function Logo({ size = "medium", width, height }: LogoProps) {
  const dimensions = {
    width: width ?? LOGO_SIZES[size].width,
    height: height ?? LOGO_SIZES[size].height,
  };

  return (
    <Image
      // 使用 require 需要在 metro/webpack 中配置
      // 这里使用占位符，实际需要在各平台配置
      source={{
        uri: "/athena-logo.png", // Next.js public 目录
        width: dimensions.width,
        height: dimensions.height,
      }}
      width={dimensions.width}
      height={dimensions.height}
      resizeMode="contain"
      alt="Athena Logo"
    />
  );
}

export type { GetProps };
