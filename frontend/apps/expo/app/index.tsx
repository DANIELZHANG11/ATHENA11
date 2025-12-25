/**
 * Expo App 首页 - 开屏动画
 *
 * 应用启动时显示开屏动画，完成后跳转到登录页
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 */

import { useState } from "react";
import { useRouter } from "solito/navigation";
import { SplashScreen, LoginScreen } from "@athena/app";

/** 登录成功后的 Token 类型 */
interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export default function HomeScreen() {
  const router = useRouter();
  const [showSplash, setShowSplash] = useState(true);

  // 如果还在显示开屏动画
  if (showSplash) {
    return (
      <SplashScreen
        minDisplayTime={2500}
        showLoading={true}
        onAnimationComplete={() => {
          setShowSplash(false);
        }}
      />
    );
  }

  // 开屏动画完成后显示登录页
  return (
    <LoginScreen
      onLoginSuccess={(tokens: AuthTokens) => {
        // TODO: 存储 token 并跳转到书库
        console.log("Login success:", tokens);
        router.push("/library");
      }}
    />
  );
}
