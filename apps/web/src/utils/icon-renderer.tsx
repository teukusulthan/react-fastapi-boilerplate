/**
 * Unified icon renderer.
 *
 * Rule: Phosphor Web (CSS font, bundled from @phosphor-icons/web — see src/main.tsx) is the ONLY
 * icon source in application code. `svg-code` is for trusted, developer-authored brand SVGs only —
 * never user-supplied input (XSS risk).
 *
 *   renderIcon({ icon: 'house' })                  → <i class="ph ph-house">
 *   renderIcon({ icon: 'house', weight: 'fill' })  → <i class="ph-fill ph-house">
 */
import type { ReactElement } from 'react'

import type { IconType, IconWeight } from '@/types/icon'
import { cn } from '@/utils/cn'

export type { IconType, IconWeight }

export interface RenderIconOptions {
  /** Phosphor icon slug (kebab-case), e.g. "house", "chart-line-up" — or an SVG string for `svg-code`. */
  icon: string
  iconType?: IconType
  weight?: IconWeight
  size?: number
  className?: string
}

const WEIGHT_CLASS: Record<IconWeight, string> = {
  regular: 'ph',
  fill: 'ph-fill',
  bold: 'ph-bold',
  light: 'ph-light',
  duotone: 'ph-duotone',
}

export function renderIcon({ icon, iconType = 'phosphor', weight = 'regular', size, className }: RenderIconOptions): ReactElement {
  if (iconType === 'svg-code') {
    return (
      <span
        aria-hidden="true"
        className={cn('inline-flex items-center', className)}
        style={size ? { width: size, height: size } : undefined}
        dangerouslySetInnerHTML={{ __html: icon }}
      />
    )
  }

  return <i className={cn(WEIGHT_CLASS[weight] ?? 'ph', `ph-${icon}`, className)} style={size ? { fontSize: size } : undefined} aria-hidden="true" />
}
