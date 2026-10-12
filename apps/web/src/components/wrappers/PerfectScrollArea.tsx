import { useEffect, useRef, type ReactNode } from 'react'
import PerfectScrollbar, { type ScrollBarProps } from 'react-perfect-scrollbar'

import { cn } from '@/utils/cn'

export interface PerfectScrollAreaProps extends Omit<ScrollBarProps, 'children'> {
  children?: ReactNode
  /** Classes for the inner content wrapper (e.g. padding / flex layout). */
  contentClassName?: string
}

/**
 * Mandatory wrapper for bounded scroll regions (main column, sidebar body, panels, drawers…).
 * Scrollbar look is themed globally in styles/components.css (`.ps__*`).
 * Content/viewport size changes are observed so the scrollbar stays accurate.
 */
export function PerfectScrollArea({ className, contentClassName, options, children, ...props }: PerfectScrollAreaProps) {
  const scrollbarRef = useRef<PerfectScrollbar>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const content = contentRef.current
    if (!content || typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(() => scrollbarRef.current?.updateScroll())
    observer.observe(content)
    if (content.parentElement) observer.observe(content.parentElement)
    return () => observer.disconnect()
  }, [])

  return (
    <PerfectScrollbar ref={scrollbarRef} className={cn('perfect-scroll-area', className)} options={{ wheelPropagation: false, ...options }} {...props}>
      <div ref={contentRef} className={contentClassName}>
        {children}
      </div>
    </PerfectScrollbar>
  )
}
