import "@tamagui/core/reset.css";
// 字体加载 - 遵循 06-UIUX设计系统 §2.3 字体加载策略
// Inter (英文/数字) + Noto Sans SC (中文)
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-sans-sc/500.css";
import "@fontsource/noto-sans-sc/700.css";

import { TamaguiProvider } from "@athena/ui";
import { PowerSyncProvider } from "@athena/app/provider/powersync";
import type { AppProps } from "next/app";
import Head from "next/head";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>雅典娜 - Athena Reader</title>
        <meta
          name="description"
          content="把读过的每一本书，都变成你的知识资产"
        />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, maximum-scale=1"
        />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <TamaguiProvider>
        <PowerSyncProvider>
          <Component {...pageProps} />
        </PowerSyncProvider>
      </TamaguiProvider>
    </>
  );
}
