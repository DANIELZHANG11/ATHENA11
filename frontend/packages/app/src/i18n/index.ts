/**
 * Athena i18n - 国际化翻译系统
 *
 * 遵循 00-AI编码宪法 §7.4 i18n 规范：
 * - 严禁硬编码文本
 * - 所有用户可见文本必须使用 t('key') 函数
 * - 支持插值 t('key', { count, name })
 *
 * @see 雅典娜开发技术文档汇总/00 - AI 编码宪法与规范AI_Coding_Constitution_and_Rules.md
 */

import zhCN from "./locales/zh-CN.json";
import enUS from "./locales/en-US.json";

export type Locale = "zh-CN" | "en-US";
export type TranslationKeys = keyof typeof zhCN;

const translations: Record<Locale, typeof zhCN> = {
  "zh-CN": zhCN,
  "en-US": enUS,
};

// 当前语言（默认中文）
let currentLocale: Locale = "zh-CN";

/**
 * 设置当前语言
 */
export function setLocale(locale: Locale): void {
  currentLocale = locale;
}

/**
 * 获取当前语言
 */
export function getLocale(): Locale {
  return currentLocale;
}

/**
 * 翻译函数
 *
 * @param key - 翻译键，如 'auth.login_button'
 * @param params - 插值参数，如 { count: 5, name: 'John' }
 * @returns 翻译后的文本
 *
 * @example
 * t('auth.login_button') // "登录"
 * t('books.count', { count: 5 }) // "共 5 本书"
 */
export function t(
  key: string,
  params?: Record<string, string | number>,
): string {
  const keys = key.split(".");
  let value: unknown = translations[currentLocale];

  for (const k of keys) {
    if (value && typeof value === "object" && k in value) {
      value = (value as Record<string, unknown>)[k];
    } else {
      // Key not found, return the key itself for debugging
      console.warn(`[i18n] Missing translation: ${key}`);
      return key;
    }
  }

  if (typeof value !== "string") {
    console.warn(`[i18n] Invalid translation value for: ${key}`);
    return key;
  }

  // 处理插值
  if (params) {
    return value.replace(/\{\{(\w+)\}\}/g, (_, paramKey) => {
      return params[paramKey]?.toString() ?? `{{${paramKey}}}`;
    });
  }

  return value;
}

/**
 * React Hook 版本的翻译函数
 * 用于组件内部
 */
export function useTranslation() {
  return {
    t,
    locale: currentLocale,
    setLocale,
  };
}

export default { t, setLocale, getLocale, useTranslation };
