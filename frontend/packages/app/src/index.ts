/**
 * Athena App - 共享业务逻辑导出入口
 */

// Provider
export {
  PowerSyncProvider,
  usePowerSync,
  useLiveQuery,
  useMutation,
} from "./provider/powersync";
export { AppSchema, type Database } from "./provider/powersync/schema";

// i18n 国际化
export {
  t,
  setLocale,
  getLocale,
  useTranslation,
  type Locale,
  type TranslationKeys,
} from "./i18n";

// Screens 屏幕组件
export {
  SplashScreen,
  LoginScreen,
  type SplashScreenProps,
  type LoginScreenProps,
} from "./screens";
