/**
 * Athena UI - TamaguiProvider
 * 
 * 跨平台统一的 Tamagui Provider 封装
 */

import { TamaguiProvider as TamaguiProviderOG, type TamaguiProviderProps } from '@tamagui/core'
import { useColorScheme } from 'react-native'
import { config } from './tamagui.config'

export function TamaguiProvider({ children, ...rest }: Omit<TamaguiProviderProps, 'config'>) {
  const colorScheme = useColorScheme()

  return (
    <TamaguiProviderOG
      config={config}
      defaultTheme={colorScheme === 'dark' ? 'dark' : 'light'}
      {...rest}
    >
      {children}
    </TamaguiProviderOG>
  )
}
