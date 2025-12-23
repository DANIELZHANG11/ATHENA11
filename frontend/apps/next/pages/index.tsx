import { YStack, LargeTitle, Body, Button } from '@athena/ui'
import { useRouter } from 'solito/navigation'

export default function HomePage() {
  const router = useRouter()

  return (
    <YStack flex={1} alignItems="center" justifyContent="center" padding="$6" space="$4">
      <LargeTitle>雅典娜</LargeTitle>
      <Body color="$labelSecondary">
        把读过的每一本书，都变成你的知识资产
      </Body>
      <Button
        onPress={() => router.push('/library')}
        backgroundColor="$systemBlue"
        color="white"
      >
        进入书库
      </Button>
    </YStack>
  )
}
