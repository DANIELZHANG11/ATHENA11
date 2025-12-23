/**
 * Athena UI - 组件导出入口
 * 
 * 所有共享 UI 组件的统一导出
 */

// Tamagui 配置
export { config } from './tamagui.config'
export { TamaguiProvider } from './TamaguiProvider'

// Tamagui 核心重导出 (从 tamagui 包导入完整组件)
export {
  styled,
  View,
  Text,
  Image,
  Stack,
  XStack,
  YStack,
  ScrollView,
  Separator,
  Spinner,
  Input,
  TextArea,
  Switch,
  Checkbox,
  Label,
  Sheet,
  Dialog,
  Popover,
  Select,
  Tabs,
  Button as TamaguiButton,
  type GetProps,
} from 'tamagui'

// 排版组件
export {
  LargeTitle,
  Title1,
  Title2,
  Title3,
  Headline,
  Body,
  Callout,
  Subhead,
  Footnote,
  Caption,
} from './typography'

// 通用组件
export { Button, type ButtonProps } from './Button'
export { Card, type CardProps } from './Card'

// 业务组件
export { BookListCard, type BookListCardProps } from './BookListCard'
