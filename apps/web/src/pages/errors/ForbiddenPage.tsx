import { Link } from 'react-router-dom'

import { StatusScreen } from '@/components/common/StatusScreen'
import { Button } from '@/components/ui/button'

export default function ForbiddenPage() {
  return (
    <StatusScreen
      code="403"
      icon="lock-key"
      title="Access denied"
      description="Your account does not have permission to view this page. Contact an administrator if you need access."
      actions={
        <Button asChild variant="outline">
          <Link to="/">Go to dashboard</Link>
        </Button>
      }
    />
  )
}
