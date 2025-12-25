/**
 * Athena App - 登录页面
 *
 * 设计规范：
 * - 顶部: LOGO + Slogan (LOGO 动效: 由大变小，从下往上升起)
 * - 中部: 邮箱验证码登录 + OAuth 社交登录
 * - 底部: 服务条款
 *
 * 根据 02号文档 §2.1 User & Auth 规范：
 * - 邮箱验证码登录（免注册机制）
 * - OAuth 登录：微信、Google、Microsoft、Apple
 * - 相同邮箱自动绑定到同一账号
 *
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 * @see 雅典娜开发技术文档汇总/05 - API契约与协议API_Contracts_and_Protocols.md §5.1
 * @see 雅典娜开发技术文档汇总/02 - 功能规格与垂直切片Functional_Specifications_PRD.md §2.1
 */

import { useState, useCallback, useEffect } from "react";
import {
  YStack,
  XStack,
  View,
  Image,
  ScrollView,
  Input,
  styled,
  Separator,
  useTheme,
} from "tamagui";
import {
  LargeTitle,
  Title3,
  Body,
  Callout,
  Footnote,
  Button,
  Card,
} from "@athena/ui";
// lucide-react 图标 - 遵循 06号文档 §6 图标规范
import { Mail, CheckCircle } from "lucide-react";
import { t } from "../i18n";
// OAuth 品牌图标 - 独立 SVG 组件
import {
  WeChatIcon,
  GoogleIcon,
  MicrosoftIcon,
  AppleIcon,
} from "../components/icons";

export interface LoginScreenProps {
  /** 登录成功回调 */
  onLoginSuccess?: (tokens: {
    accessToken: string;
    refreshToken: string;
  }) => void;
  /** Logo 图片 URI */
  logoUri?: string;
}

/**
 * 动画 LOGO 容器 - CSS 动效实现
 * 从下往上升起 + 由大变小
 */
const AnimatedLogoContainer = styled(View, {
  name: "AnimatedLogoContainer",
  alignItems: "center",
  justifyContent: "center",
});

/**
 * OAuth 按钮样式容器
 */
const OAuthButton = styled(View, {
  name: "OAuthButton",
  flexDirection: "row",
  alignItems: "center",
  justifyContent: "center",
  backgroundColor: "$fill",
  borderRadius: "$sm",
  height: 48,
  gap: "$3",
  cursor: "pointer",
  pressStyle: {
    opacity: 0.7,
    scale: 0.98,
  },
});

/**
 * 生成6位随机验证码（模拟服务器发送）
 */
function generateMockVerificationCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

/**
 * 登录页面组件
 *
 * 遵循 Apple HIG 设计规范，使用 Tamagui Token 系统
 * 图标使用 lucide-react (06号文档规范)
 * 所有文本通过 i18n 翻译函数引用
 */
export function LoginScreen({
  onLoginSuccess,
  logoUri = "/athena-logo.png",
}: LoginScreenProps) {
  // 获取 Tamagui 主题颜色 - 用于 lucide 图标 style prop
  const theme = useTheme();

  // 表单状态
  const [email, setEmail] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [step, setStep] = useState<"email" | "verify">("email");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  // 模拟验证码（开发环境显示）
  const [mockCode, setMockCode] = useState<string | null>(null);

  // LOGO 动画状态 - 用于 CSS 动效
  const [logoAnimated, setLogoAnimated] = useState(false);

  // 邮件确认弹窗状态 (防输错机制 - 02号文档 §2.1.F)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // 页面加载后触发 LOGO 动画
  useEffect(() => {
    const timer = setTimeout(() => {
      setLogoAnimated(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // 倒计时逻辑
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // 发送验证码前的确认弹窗
  const handleSendCodeClick = useCallback(() => {
    if (!email || countdown > 0) return;
    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError(t("errors.invalid_email"));
      return;
    }
    setError(null);
    setShowConfirmDialog(true);
  }, [email, countdown]);

  // 确认发送验证码
  const handleConfirmSendCode = useCallback(async () => {
    setShowConfirmDialog(false);
    setIsLoading(true);
    setError(null);

    try {
      // TODO: 调用 POST /auth/email/send-code API
      // 遵循 05-API契约 §5.1.1
      await new Promise((resolve) => setTimeout(resolve, 800));

      // 模拟服务器生成验证码
      const code = generateMockVerificationCode();
      setMockCode(code);
      console.log(`[DEV] 模拟验证码: ${code}`);

      setStep("verify");
      setCountdown(60);
    } catch (err) {
      setError(t("errors.rate_limited"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 验证验证码
  const handleVerifyCode = useCallback(async () => {
    if (!verificationCode || verificationCode.length !== 6) return;

    setIsLoading(true);
    setError(null);

    try {
      // TODO: 调用 POST /auth/email/verify-code API
      await new Promise((resolve) => setTimeout(resolve, 800));

      // 模拟验证 - 开发环境下检查是否匹配模拟验证码
      if (mockCode && verificationCode !== mockCode) {
        setError(t("errors.invalid_code"));
        setIsLoading(false);
        return;
      }

      // 登录成功
      onLoginSuccess?.({
        accessToken: "mock_access_token",
        refreshToken: "mock_refresh_token",
      });
    } catch (err) {
      setError(t("errors.invalid_code"));
    } finally {
      setIsLoading(false);
    }
  }, [verificationCode, mockCode, onLoginSuccess]);

  // OAuth 登录处理
  const handleOAuthLogin = useCallback(
    (provider: "wechat" | "google" | "microsoft" | "apple") => {
      // TODO: 调用 GET /auth/oauth/{provider}/authorize API
      // 根据 02号文档 §2.1 B.2 OAuth 登录流程
      console.log(`[DEV] OAuth 登录: ${provider}`);
      alert(
        `${provider.toUpperCase()} 登录功能开发中...\n\n根据 02号文档，相同邮箱会自动绑定到同一账号。`,
      );
    },
    [],
  );

  return (
    <ScrollView
      flex={1}
      backgroundColor="$background"
      contentContainerStyle={{
        flexGrow: 1,
      }}
    >
      <YStack
        flex={1}
        padding="$6"
        justifyContent="space-between"
        minHeight="100%"
      >
        {/* ========== 顶部区域 - LOGO + Slogan ========== */}
        <YStack
          alignItems="center"
          justifyContent="center"
          paddingTop="$8"
          paddingBottom="$4"
        >
          {/* LOGO 动效容器 - CSS 过渡实现由大变小、从下往上升起 */}
          <AnimatedLogoContainer
            marginBottom="$4"
            style={{
              transform: logoAnimated
                ? "translateY(0) scale(1)"
                : "translateY(60px) scale(1.3)",
              opacity: logoAnimated ? 1 : 0,
              transition: "all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)",
            }}
          >
            <Image
              source={{ uri: logoUri }}
              width={100}
              height={100}
              resizeMode="contain"
              alt="Athena Logo"
            />
          </AnimatedLogoContainer>

          {/* 品牌名称 */}
          <LargeTitle marginBottom="$2">{t("common.app_name")}</LargeTitle>

          {/* Slogan */}
          <Callout color="$labelSecondary" textAlign="center">
            {t("common.slogan")}
          </Callout>
        </YStack>

        {/* ========== 中部区域 - 登录表单 ========== */}
        <YStack flex={1} justifyContent="center" gap="$4">
          <Card padding="$5" gap="$4">
            {step === "email" ? (
              <>
                {/* 邮箱输入 */}
                <YStack gap="$2">
                  <Footnote color="$labelSecondary" paddingLeft="$1">
                    {t("auth.email")}
                  </Footnote>
                  <XStack
                    alignItems="center"
                    backgroundColor="$fill"
                    borderRadius="$sm"
                    paddingHorizontal="$3"
                    height={48}
                    gap="$3"
                  >
                    <Mail
                      size={20}
                      strokeWidth={1.5}
                      color={theme.systemGray?.val}
                    />
                    <Input
                      flex={1}
                      backgroundColor="transparent"
                      borderWidth={0}
                      paddingHorizontal={0}
                      height="100%"
                      placeholder={t("auth.email_placeholder")}
                      value={email}
                      onChangeText={setEmail}
                      keyboardType="email-address"
                      autoCapitalize="none"
                      autoComplete="email"
                    />
                  </XStack>
                </YStack>

                {/* 错误提示 */}
                {error && (
                  <Body color="$systemRed" textAlign="center">
                    {error}
                  </Body>
                )}

                {/* 获取验证码按钮 */}
                <Button
                  variant="filled"
                  size="large"
                  onPress={handleSendCodeClick}
                  disabled={!email || isLoading}
                  marginTop="$2"
                >
                  {isLoading ? t("common.loading") : t("auth.get_code")}
                </Button>
              </>
            ) : (
              <>
                {/* 验证码输入 */}
                <YStack gap="$2">
                  <Footnote color="$labelSecondary" paddingLeft="$1">
                    {t("auth.verification_code")}
                  </Footnote>
                  <Body color="$labelSecondary" marginBottom="$2">
                    {t("auth.code_sent_to")} {email}
                  </Body>
                  <Input
                    backgroundColor="$fill"
                    borderRadius="$sm"
                    paddingHorizontal="$4"
                    height={48}
                    placeholder="000000"
                    value={verificationCode}
                    onChangeText={setVerificationCode}
                    keyboardType="number-pad"
                    maxLength={6}
                    textAlign="center"
                    fontSize="$8"
                  />
                  {/* 开发环境显示模拟验证码 */}
                  {mockCode && (
                    <Footnote
                      color="$systemOrange"
                      textAlign="center"
                      marginTop="$2"
                    >
                      [DEV] 模拟验证码: {mockCode}
                    </Footnote>
                  )}
                </YStack>

                {/* 重新发送 */}
                <XStack justifyContent="center">
                  <Body
                    color={countdown > 0 ? "$labelTertiary" : "$systemBlue"}
                    onPress={countdown > 0 ? undefined : handleConfirmSendCode}
                    cursor={countdown > 0 ? "default" : "pointer"}
                  >
                    {countdown > 0
                      ? t("auth.resend_code_countdown", { seconds: countdown })
                      : t("auth.resend_code_text")}
                  </Body>
                </XStack>

                {/* 错误提示 */}
                {error && (
                  <Body color="$systemRed" textAlign="center">
                    {error}
                  </Body>
                )}

                {/* 登录/注册按钮 */}
                <Button
                  variant="filled"
                  size="large"
                  onPress={handleVerifyCode}
                  disabled={verificationCode.length !== 6 || isLoading}
                  marginTop="$2"
                >
                  {isLoading ? t("common.loading") : t("auth.login_register")}
                </Button>

                {/* 返回修改邮箱 */}
                <Body
                  color="$systemBlue"
                  textAlign="center"
                  onPress={() => {
                    setStep("email");
                    setVerificationCode("");
                    setMockCode(null);
                    setError(null);
                  }}
                  cursor="pointer"
                >
                  {t("auth.change_email")}
                </Body>
              </>
            )}
          </Card>

          {/* ========== OAuth 社交登录区域 ========== */}
          <YStack gap="$4" marginTop="$2">
            {/* 分隔线 */}
            <XStack alignItems="center" gap="$3">
              <Separator flex={1} />
              <Footnote color="$labelTertiary">
                {t("auth.or_continue_with")}
              </Footnote>
              <Separator flex={1} />
            </XStack>

            {/* OAuth 按钮组 - 根据 02号文档 §2.1 B.2 支持四种 OAuth */}
            <YStack gap="$3">
              {/* 微信登录 */}
              <OAuthButton onPress={() => handleOAuthLogin("wechat")}>
                <WeChatIcon size={24} />
                <Body fontWeight="500">{t("auth.login_with_wechat")}</Body>
              </OAuthButton>

              {/* Google 登录 */}
              <OAuthButton onPress={() => handleOAuthLogin("google")}>
                <GoogleIcon size={24} />
                <Body fontWeight="500">{t("auth.login_with_google")}</Body>
              </OAuthButton>

              {/* Microsoft 登录 */}
              <OAuthButton onPress={() => handleOAuthLogin("microsoft")}>
                <MicrosoftIcon size={24} />
                <Body fontWeight="500">{t("auth.login_with_microsoft")}</Body>
              </OAuthButton>

              {/* Apple 登录 */}
              <OAuthButton onPress={() => handleOAuthLogin("apple")}>
                <AppleIcon size={24} color={theme.label?.val} />
                <Body fontWeight="500">{t("auth.login_with_apple")}</Body>
              </OAuthButton>
            </YStack>
          </YStack>
        </YStack>

        {/* ========== 底部区域 - 服务条款 ========== */}
        <YStack
          alignItems="center"
          justifyContent="flex-end"
          paddingBottom="$6"
          paddingTop="$4"
        >
          {/* 服务条款 - 02号文档 §2.1.D 免注册机制风险提示 */}
          <Footnote color="$labelTertiary" textAlign="center" maxWidth={320}>
            {t("auth.agree_terms")}{" "}
            <Footnote color="$systemBlue" cursor="pointer">
              {t("auth.terms_of_service")}
            </Footnote>{" "}
            {t("auth.and")}{" "}
            <Footnote color="$systemBlue" cursor="pointer">
              {t("auth.privacy_policy")}
            </Footnote>
          </Footnote>
        </YStack>
      </YStack>

      {/* ========== 邮箱确认弹窗 - 防输错机制 (02号文档 §2.1.F) ========== */}
      {showConfirmDialog && (
        <View
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          backgroundColor="rgba(0,0,0,0.5)"
          alignItems="center"
          justifyContent="center"
          padding="$6"
        >
          <Card padding="$6" maxWidth={400} width="100%">
            <YStack alignItems="center" gap="$4">
              <CheckCircle
                size={48}
                strokeWidth={1.5}
                color={theme.systemBlue?.val}
              />
              <Title3 textAlign="center">
                {t("auth.confirm_email_title")}
              </Title3>
              <LargeTitle textAlign="center" color="$systemBlue">
                {email}
              </LargeTitle>
              <Body color="$labelSecondary" textAlign="center">
                {t("auth.confirm_email_message")}
              </Body>
              <XStack gap="$3" marginTop="$2" width="100%">
                <Button
                  variant="plain"
                  flex={1}
                  onPress={() => setShowConfirmDialog(false)}
                >
                  {t("auth.go_back_edit")}
                </Button>
                <Button
                  variant="filled"
                  flex={1}
                  onPress={handleConfirmSendCode}
                >
                  {t("auth.confirm_send")}
                </Button>
              </XStack>
            </YStack>
          </Card>
        </View>
      )}
    </ScrollView>
  );
}

export default LoginScreen;
