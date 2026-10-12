import { StatusScreen } from '@/components/common/StatusScreen'
import { Button } from '@/components/ui/button'

/** Shown by AuthGuard when the session cannot be checked because the API is unreachable. */
export default function ServerUnavailable({ onRetry }: { onRetry: () => void }) {
  return (
    <StatusScreen
      fullScreen
      icon="plugs"
      title="Can't reach the server"
      description="We couldn't verify your session because the server is unavailable. Check your connection and try again."
      actions={<Button onClick={onRetry}>Try again</Button>}
    />
  )
}
