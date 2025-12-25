/**
 * Next.js 登录页面
 *
 * 使用共享的 LoginScreen 组件
 *
 * 根据 02号文档 §2.1 User & Auth 规范：
 * - 邮箱验证码登录（免注册机制）
 * - OAuth 登录：微信、Google、Microsoft、Apple
 * - 不需要"忘记密码"和"立即注册"链接
 *
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 * @see 雅典娜开发技术文档汇总/02 - 功能规格与垂直切片Functional_Specifications_PRD.md §2.1
 */

import { useRouter } from "next/router";
import { LoginScreen } from "@athena/app";

/** 登录成功后的 Token 类型 */
interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export default function LoginPage() {
  const router = useRouter();

  return (
    <LoginScreen
      logoUri="/athena-logo.png"
      onLoginSuccess={(tokens: AuthTokens) => {
        // TODO: 存储 token 并跳转到书库
        console.log("Login success:", tokens);
        router.push("/");
      }}
    />
  );
}
