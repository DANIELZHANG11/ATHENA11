/**
 * OAuth 品牌图标组件
 *
 * 由于 lucide-react 不提供品牌 logo，此文件定义了 OAuth 登录所需的品牌 SVG 图标。
 * 所有图标遵循以下规范：
 * - 尺寸：可配置，默认 24x24
 * - 颜色：使用官方品牌色（单色 SVG）
 *
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md §6
 * @see 雅典娜开发技术文档汇总/02 - 功能规格与垂直切片Functional_Specifications_PRD.md §2.1 B.2
 */

import React from "react";

interface IconProps {
  /** 图标尺寸 (正方形) */
  size?: number;
  /** 图标颜色 (可选，默认使用品牌色) */
  color?: string;
}

/**
 * 微信图标 (WeChat)
 * 品牌色: #07C160 (微信绿)
 */
export function WeChatIcon({ size = 24, color = "#07C160" }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8.691 2.188C4.294 2.188.5 5.39.5 9.39c0 2.116 1.088 4.012 2.79 5.309l-.696 2.156 2.463-1.27c.823.232 1.69.354 2.587.354.282 0 .56-.012.834-.035-.175-.598-.268-1.22-.268-1.86 0-4.013 3.886-7.266 8.667-7.266.254 0 .505.013.753.038C16.66 3.878 13.008 2.188 8.69 2.188zm-3.24 4.037c.568 0 1.028.461 1.028 1.028 0 .568-.46 1.027-1.027 1.027-.567 0-1.028-.46-1.028-1.027 0-.567.46-1.028 1.028-1.028zm6.463 0c.567 0 1.027.461 1.027 1.028 0 .568-.46 1.027-1.027 1.027-.568 0-1.028-.46-1.028-1.027 0-.567.46-1.028 1.028-1.028z"
        fill={color}
      />
      <path
        d="M23.5 14.044c0-3.44-3.36-6.235-7.5-6.235-4.141 0-7.5 2.795-7.5 6.235 0 3.44 3.359 6.234 7.5 6.234.844 0 1.66-.113 2.422-.32l2.104 1.104-.595-1.845c1.522-1.105 2.569-2.721 2.569-4.573zm-9.643-1.028c-.483 0-.875-.392-.875-.876 0-.483.392-.875.875-.875.484 0 .876.392.876.875 0 .484-.392.876-.876.876zm4.286 0c-.484 0-.876-.392-.876-.876 0-.483.392-.875.876-.875.483 0 .875.392.875.875 0 .484-.392.876-.875.876z"
        fill={color}
      />
    </svg>
  );
}

/**
 * Google 图标
 * 使用多色版本以保持品牌识别度
 */
export function GoogleIcon({ size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

/**
 * Microsoft 图标
 * 使用官方四色田字格
 */
export function MicrosoftIcon({ size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="1" y="1" width="10" height="10" fill="#F25022" />
      <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
      <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
      <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
    </svg>
  );
}

/**
 * Apple 图标
 * 品牌色: 根据主题动态切换
 * - Light Mode: #000000 (黑色)
 * - Dark Mode: #FFFFFF (白色)
 *
 * @param color - 可选，手动指定颜色。不传时默认使用 currentColor
 */
export function AppleIcon({ size = 24, color = "currentColor" }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"
        fill={color}
      />
    </svg>
  );
}

/**
 * 导出所有 OAuth 图标
 */
export const OAuthIcons = {
  WeChat: WeChatIcon,
  Google: GoogleIcon,
  Microsoft: MicrosoftIcon,
  Apple: AppleIcon,
};

export default OAuthIcons;
