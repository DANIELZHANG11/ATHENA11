/**
 * Next.js 首页 - 开屏动画
 *
 * 应用启动时显示开屏动画，完成后跳转到登录页
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { SplashScreen } from "@athena/app";

export default function HomePage() {
  const router = useRouter();
  const [showSplash, setShowSplash] = useState(true);

  // Web 端可以直接跳转，不需要显示 Splash
  // 但为了演示效果，保留开屏动画
  useEffect(() => {
    // 检查是否已登录（从 localStorage 获取 token）
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;

    if (token) {
      // 已登录，跳转到书库
      router.replace("/library");
    }
  }, [router]);

  if (showSplash) {
    return (
      <SplashScreen
        minDisplayTime={2000}
        showLoading={true}
        onAnimationComplete={() => {
          setShowSplash(false);
          // 跳转到登录页
          router.push("/login");
        }}
      />
    );
  }

  return null;
}
