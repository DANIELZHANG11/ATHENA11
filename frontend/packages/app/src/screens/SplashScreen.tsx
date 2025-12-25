/**
 * Athena App - 开屏动画组件 (Splash Screen)
 *
 * 展示雅典娜 LOGO 的开屏动画
 *
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 * @see 雅典娜开发技术文档汇总/00 - AI编码宪法与规范AI_Coding_Constitution_and_Rules.md §7.4 i18n
 */

import { useEffect, useState } from "react";
import { YStack, View, Spinner } from "@athena/ui";
import { LargeTitle, Body } from "@athena/ui";
import { Image } from "tamagui";
import { t } from "../i18n";

export interface SplashScreenProps {
  /** 动画完成后的回调 */
  onAnimationComplete?: () => void;
  /** 最小显示时间（毫秒） */
  minDisplayTime?: number;
  /** 是否显示加载指示器 */
  showLoading?: boolean;
  /** 加载状态文本键 */
  loadingTextKey?: string;
  /** Logo 图片 URI - Web 默认为 /athena-logo.png */
  logoUri?: string;
}

/**
 * 开屏动画组件
 *
 * 功能：
 * 1. 展示雅典娜 LOGO (带渐入动画)
 * 2. 展示品牌 Slogan
 * 3. 可选的加载指示器
 *
 * @example
 * <SplashScreen
 *   onAnimationComplete={() => navigation.replace('Login')}
 *   minDisplayTime={2000}
 * />
 */
export function SplashScreen({
  onAnimationComplete,
  minDisplayTime = 2000,
  showLoading = true,
  loadingTextKey = "splash.loading",
  logoUri = "/athena-logo.png",
}: SplashScreenProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [opacity, setOpacity] = useState(0);

  useEffect(() => {
    // 渐入动画
    const fadeInTimer = setTimeout(() => {
      setOpacity(1);
    }, 100);

    // 完成动画
    const completeTimer = setTimeout(() => {
      if (onAnimationComplete) {
        // 渐出动画
        setOpacity(0);
        setTimeout(() => {
          setIsVisible(false);
          onAnimationComplete();
        }, 300);
      }
    }, minDisplayTime);

    return () => {
      clearTimeout(fadeInTimer);
      clearTimeout(completeTimer);
    };
  }, [minDisplayTime, onAnimationComplete]);

  if (!isVisible) return null;

  return (
    <YStack
      flex={1}
      alignItems="center"
      justifyContent="center"
      backgroundColor="$background"
      padding="$6"
      // 使用简单的 opacity 动画，避免 enterStyle 导致的插值错误
      opacity={opacity}
    >
      {/* LOGO 容器 */}
      <View marginBottom="$6">
        {/* 使用 Image 组件显示 LOGO */}
        <Image
          source={{ uri: logoUri }}
          width={150}
          height={150}
          resizeMode="contain"
          alt="Athena Logo"
        />
      </View>

      {/* 品牌名称 */}
      <LargeTitle marginBottom="$2">{t("common.app_name")}</LargeTitle>

      {/* Slogan */}
      <Body color="$labelSecondary" textAlign="center" marginBottom="$8">
        {t("common.slogan")}
      </Body>

      {/* 加载指示器 */}
      {showLoading && (
        <YStack alignItems="center" gap="$3">
          <Spinner size="small" color="$systemBlue" />
          <Body color="$labelTertiary" fontSize={13}>
            {t(loadingTextKey)}
          </Body>
        </YStack>
      )}
    </YStack>
  );
}

export default SplashScreen;
