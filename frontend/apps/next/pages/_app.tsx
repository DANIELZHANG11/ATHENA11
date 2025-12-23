import '@tamagui/core/reset.css'

import { TamaguiProvider } from '@athena/ui'
import { PowerSyncProvider } from '@athena/app/provider/powersync'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>雅典娜 - Athena Reader</title>
        <meta name="description" content="把读过的每一本书，都变成你的知识资产" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <TamaguiProvider>
        <PowerSyncProvider>
          <Component {...pageProps} />
        </PowerSyncProvider>
      </TamaguiProvider>
    </>
  )
}
