/**
 * Athena UI - BookListCard Component
 * 
 * 书籍列表卡片，用于书架视图
 * 样式遵循 Apple HIG，使用 $radius.lg 和 $shadow.sm
 * 支持 PowerSync useLiveQuery 实时更新
 * 
 * @see 雅典娜开发技术文档汇总/06 - UIUX设计系统UI_UX_Design_system.md
 */

import { styled, View, Image, GetProps } from 'tamagui'
import { Headline, Subhead, Caption } from './typography'

// 书籍封面容器
const CoverContainer = styled(View, {
  name: 'BookCoverContainer',
  width: 80,
  height: 120,
  borderRadius: '$sm',
  overflow: 'hidden',
  backgroundColor: '$backgroundSecondary',
  
  // 书籍封面阴影
  shadowColor: '$black',
  shadowOffset: { width: 0, height: 4 },
  shadowOpacity: 0.12,
  shadowRadius: 8,
})

// 书籍封面图片
const CoverImage = styled(Image, {
  name: 'BookCoverImage',
  width: '100%',
  height: '100%',
  resizeMode: 'cover',
})

// 书籍信息容器
const InfoContainer = styled(View, {
  name: 'BookInfoContainer',
  flex: 1,
  marginLeft: '$4',
  justifyContent: 'center',
  gap: '$1',
})

// 进度条容器
const ProgressContainer = styled(View, {
  name: 'ProgressContainer',
  height: 4,
  backgroundColor: '$fill',
  borderRadius: '$full',
  overflow: 'hidden',
  marginTop: '$2',
})

// 进度条填充
const ProgressFill = styled(View, {
  name: 'ProgressFill',
  height: '100%',
  backgroundColor: '$systemBlue',
  borderRadius: '$full',
})

// 主卡片容器
const CardContainer = styled(View, {
  name: 'BookListCard',
  flexDirection: 'row',
  padding: '$4',
  backgroundColor: '$backgroundTertiary',
  borderRadius: '$lg', // 20px - Apple 超椭圆
  
  // Apple 风格阴影 ($shadow.sm)
  shadowColor: '$black',
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.04,
  shadowRadius: 3,
  
  // 点击反馈
  pressStyle: {
    scale: 0.98,
    opacity: 0.9,
  },
  animation: 'fast',
})

// BookListCard Props
export interface BookListCardProps {
  id: string
  title: string
  author: string
  coverUrl?: string
  progress?: number // 0-1
  lastReadAt?: string
  onPress?: () => void
}

/**
 * BookListCard 组件
 * 
 * 使用示例:
 * ```tsx
 * import { useLiveQuery } from '@athena/app/hooks/useLiveQuery'
 * 
 * function BookList() {
 *   const books = useLiveQuery('SELECT * FROM books WHERE is_deleted = 0')
 *   
 *   return books.map(book => (
 *     <BookListCard
 *       key={book.id}
 *       id={book.id}
 *       title={book.title}
 *       author={book.author}
 *       coverUrl={book.cover_url}
 *       progress={book.progress}
 *       onPress={() => router.push(`/reader/${book.id}`)}
 *     />
 *   ))
 * }
 * ```
 */
export function BookListCard({
  id,
  title,
  author,
  coverUrl,
  progress = 0,
  lastReadAt,
  onPress,
}: BookListCardProps) {
  // 格式化进度百分比
  const progressPercent = Math.round(progress * 100)
  
  // 格式化最后阅读时间
  const formatLastRead = (dateString?: string) => {
    if (!dateString) return null
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays}天前`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
    return `${Math.floor(diffDays / 30)}个月前`
  }

  return (
    <CardContainer onPress={onPress}>
      {/* 封面 */}
      <CoverContainer>
        {coverUrl ? (
          <CoverImage source={{ uri: coverUrl }} />
        ) : (
          // 默认封面占位符
          <View
            flex={1}
            alignItems="center"
            justifyContent="center"
            backgroundColor="$backgroundSecondary"
          >
            <Caption color="$labelTertiary">无封面</Caption>
          </View>
        )}
      </CoverContainer>
      
      {/* 书籍信息 */}
      <InfoContainer>
        <Headline numberOfLines={2}>{title}</Headline>
        <Subhead color="$labelSecondary" numberOfLines={1}>
          {author}
        </Subhead>
        
        {/* 进度条 */}
        {progress > 0 && (
          <>
            <ProgressContainer>
              <ProgressFill width={`${progressPercent}%`} />
            </ProgressContainer>
            <Caption color="$labelTertiary">
              已读 {progressPercent}%
              {lastReadAt && ` · ${formatLastRead(lastReadAt)}`}
            </Caption>
          </>
        )}
      </InfoContainer>
    </CardContainer>
  )
}

export type { BookListCardProps as BookCardProps }
