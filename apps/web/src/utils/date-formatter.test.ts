import { describe, expect, it } from 'vitest'

import { formatDateTime, formatRelativeTime } from './date-formatter'

const NOW = new Date('2026-10-12T09:30:00Z')

describe('formatRelativeTime', () => {
  it('returns the fallback for empty or invalid input', () => {
    expect(formatRelativeTime(null, '—', NOW)).toBe('—')
    expect(formatRelativeTime('', 'Never', NOW)).toBe('Never')
    expect(formatRelativeTime('not-a-date', '—', NOW)).toBe('—')
  })

  it('reads recent dates relatively', () => {
    expect(formatRelativeTime('2026-10-12T09:29:30Z', '—', NOW)).toBe('Just now')
    expect(formatRelativeTime('2026-10-12T07:30:00Z', '—', NOW)).toBe('2 hours ago')
    expect(formatRelativeTime('2026-10-09T09:30:00Z', '—', NOW)).toBe('3 days ago')
  })

  it('switches to an absolute date for old values', () => {
    expect(formatRelativeTime('2026-06-14T10:10:00Z', '—', NOW)).toBe(formatDateTime('2026-06-14T10:10:00Z', 'dd MMM yyyy'))
  })
})
