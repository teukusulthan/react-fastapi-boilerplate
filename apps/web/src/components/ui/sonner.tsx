import type * as React from 'react'
import { Toaster as Sonner, type ToasterProps } from 'sonner'

import { useResolvedTheme } from '@/hooks/use-resolved-theme'

/** App toaster (mounted once in AppProviders). Use `toast.success()` / `toast.error()` from 'sonner'. */
const Toaster = (props: ToasterProps) => {
  const theme = useResolvedTheme()

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      style={
        {
          '--normal-bg': 'var(--popover)',
          '--normal-text': 'var(--popover-foreground)',
          '--normal-border': 'var(--border)',
          '--border-radius': 'calc(var(--radius) + 2px)',
        } as React.CSSProperties
      }
      icons={{
        success: <i className="ph-fill ph-check-circle text-success" aria-hidden="true" />,
        info: <i className="ph-fill ph-info text-info" aria-hidden="true" />,
        warning: <i className="ph-fill ph-warning text-warning" aria-hidden="true" />,
        error: <i className="ph-fill ph-x-circle text-destructive" aria-hidden="true" />,
        loading: <i className="ph ph-spinner animate-spin text-muted-foreground" aria-hidden="true" />,
      }}
      toastOptions={{
        classNames: {
          toast: 'font-sans shadow-lg!',
          title: 'text-sm font-medium',
          description: 'text-muted-foreground!',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
