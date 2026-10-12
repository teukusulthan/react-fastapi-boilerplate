import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const DARK_QUERY = '(prefers-color-scheme: dark)'

export function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return 'light'
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light'
}

export function resolveTheme(theme: ThemePreference): ResolvedTheme {
  return theme === 'system' ? getSystemTheme() : theme
}

/** Apply the `.dark` class on <html> (Tailwind `dark:` variant + `.dark` tokens in variable.css). */
export function applyThemeToDocument(theme: ThemePreference): void {
  if (typeof document === 'undefined') return
  const resolved = resolveTheme(theme)
  const root = document.documentElement
  root.classList.toggle('dark', resolved === 'dark')
  root.style.colorScheme = resolved
}

interface ThemeState {
  theme: ThemePreference
  setTheme: (theme: ThemePreference) => void
}

/** The single theme mechanism of the app (persisted preference). */
export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'system',
      setTheme: (theme) => {
        set({ theme })
        applyThemeToDocument(theme)
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => applyThemeToDocument(state?.theme ?? 'system'),
    },
  ),
)

export const DARK_MODE_MEDIA_QUERY = DARK_QUERY
