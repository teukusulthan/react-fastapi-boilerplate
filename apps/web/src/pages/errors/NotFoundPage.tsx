import { Link } from 'react-router-dom'

import { StatusScreen } from '@/components/common/StatusScreen'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  return (
    <StatusScreen
      fullScreen
      code="404"
      icon="compass"
      title="Page not found"
      description="The page you are looking for does not exist or has been moved."
      actions={
        <Button asChild>
          <Link to="/">Go to dashboard</Link>
        </Button>
      }
    />
  )
}
