import { differenceInCalendarDays, differenceInSeconds, format, formatDistanceStrict, isValid, parseISO } from 'date-fns'

export const DATE_FORMAT = 'dd MMM yyyy'
export const DATE_TIME_FORMAT = 'dd MMM yyyy, HH:mm'

function toDate(value: string | number | Date): Date {
  return typeof value === 'string' ? parseISO(value) : new Date(value)
}

/** Format an ISO string / epoch / Date in the user's local timezone. Returns `fallback` for empty or invalid input. */
export function formatDateTime(value: string | number | Date | null | undefined, pattern = DATE_TIME_FORMAT, fallback = '—'): string {
  if (value === null || value === undefined || value === '') return fallback
  const date = toDate(value)
  return isValid(date) ? format(date, pattern) : fallback
}

export function formatDate(value: string | number | Date | null | undefined, fallback = '—'): string {
  return formatDateTime(value, DATE_FORMAT, fallback)
}

/** Within this many days dates read as "3 days ago"; older ones as an absolute date. */
export const RELATIVE_TIME_MAX_DAYS = 30

/**
 * Human relative time: "Just now", "5 minutes ago", "3 days ago"; falls back to `dd MMM yyyy` after
 * RELATIVE_TIME_MAX_DAYS and to `fallback` for empty/invalid input. Pair with a tooltip showing the full date
 * (`components/common/RelativeTime`).
 */
export function formatRelativeTime(value: string | number | Date | null | undefined, fallback = '—', now: Date = new Date()): string {
  if (value === null || value === undefined || value === '') return fallback
  const date = toDate(value)
  if (!isValid(date)) return fallback
  const seconds = differenceInSeconds(now, date)
  if (seconds >= 0 && seconds < 60) return 'Just now'
  if (Math.abs(differenceInCalendarDays(now, date)) > RELATIVE_TIME_MAX_DAYS) return format(date, DATE_FORMAT)
  return formatDistanceStrict(date, now, { addSuffix: true })
}
