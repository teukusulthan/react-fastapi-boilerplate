import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { formatDateTime, formatRelativeTime } from '@/utils/date-formatter'
import { cn } from '@/utils/cn'

export interface RelativeTimeProps {
  value: string | number | Date | null | undefined
  /** Shown when there is no date. */
  fallback?: string
  className?: string
}

/** "3h ago" with the absolute date in a tooltip (and in `<time dateTime>` for assistive tech). */
export function RelativeTime({ value, fallback = 'Never', className }: RelativeTimeProps) {
  const relative = formatRelativeTime(value, '')
  if (!relative || value === null || value === undefined) return <span className={cn('text-muted-foreground', className)}>{fallback}</span>

  const iso = new Date(value).toISOString()
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <time dateTime={iso} className={cn('cursor-default tabular-nums', className)}>
          {relative}
        </time>
      </TooltipTrigger>
      <TooltipContent>{formatDateTime(value)}</TooltipContent>
    </Tooltip>
  )
}
