import { useSyncExternalStore } from 'react'

import { DARK_MODE_MEDIA_QUERY, getSystemTheme, useThemeStore, type ResolvedTheme } from '@/stores/useThemeStore'

function subscribeToSystemTheme(onChange: () => void): () => void {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return () => undefined
  const mql = window.matchMedia(DARK_MODE_MEDIA_QUERY)
  mql.addEventListener('change', onChange)
  return () => mql.removeEventListener('change', onChange)
}

/** The theme actually in effect ('system' resolved against the OS preference, live-updating). */
export function useResolvedTheme(): ResolvedTheme {
  const theme = useThemeStore((state) => state.theme)
  const systemTheme = useSyncExternalStore(subscribeToSystemTheme, getSystemTheme, (): ResolvedTheme => 'light')
  return theme === 'system' ? systemTheme : theme
}
