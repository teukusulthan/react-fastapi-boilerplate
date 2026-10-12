import { SectionCard } from '@/components/common/SectionCard'
import type { UserProfile } from '@/types/models'
import { cn } from '@/utils/cn'

import { getAccountChecks } from '../utils/account-checks'

/** Security checklist for the signed-in account (derived from /auth/me only). */
export function SecurityCard({ user, className }: { user: UserProfile; className?: string }) {
  const checks = getAccountChecks(user)
  const passed = checks.filter((check) => check.ok).length

  return (
    <SectionCard
      title="Security"
      description={`${passed} of ${checks.length} checks passed`}
      className={className}
      actions={
        <span
          className={cn(
            'flex size-8 items-center justify-center rounded-lg',
            passed === checks.length ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning',
          )}
          aria-hidden="true"
        >
          <i className={cn('ph-fill', passed === checks.length ? 'ph-shield-check' : 'ph-shield-warning')} />
        </span>
      }
    >
      <ul className="flex flex-col gap-4">
        {checks.map((check) => (
          <li key={check.id} className="flex items-start gap-3">
            <i
              className={cn('ph-fill mt-0.5', check.ok ? 'ph-check-circle text-success' : 'ph-warning-circle text-warning')}
              aria-label={check.ok ? 'Passed' : 'Needs attention'}
            />
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="text-sm font-medium">{check.label}</span>
              <span className="truncate text-xs text-muted-foreground">{check.detail}</span>
            </div>
          </li>
        ))}
      </ul>
    </SectionCard>
  )
}
