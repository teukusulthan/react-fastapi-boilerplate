import { useEffect } from 'react'

import { useResolvedTheme } from '@/hooks/use-resolved-theme'
import { applyThemeToDocument, useThemeStore } from '@/stores/useThemeStore'

/** Keep <html class="dark"> in sync with the preference and OS changes. Mount once (AppProviders). */
export function useThemeSync(): void {
  const theme = useThemeStore((state) => state.theme)
  const resolved = useResolvedTheme()

  useEffect(() => {
    applyThemeToDocument(theme)
  }, [theme, resolved])
}
