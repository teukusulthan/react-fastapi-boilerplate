import { StatusBadge } from '@/components/common/StatusBadge'
import type { UserStatus } from '@/types/models'

import { USER_STATUS_META } from '../constants/user.constants'

export function UserStatusBadge({ status }: { status: UserStatus }) {
  const meta = USER_STATUS_META[status] ?? { label: status, tone: 'neutral' as const }
  return <StatusBadge tone={meta.tone}>{meta.label}</StatusBadge>
}
