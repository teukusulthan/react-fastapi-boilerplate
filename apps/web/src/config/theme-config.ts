import type { ThemePreference } from '@/stores/useThemeStore'

export const THEME_OPTIONS: readonly ThemePreference[] = ['light', 'dark', 'system']

export const THEME_LABEL: Record<ThemePreference, string> = {
  light: 'Light',
  dark: 'Dark',
  system: 'System',
}

export const THEME_ICON: Record<ThemePreference, string> = {
  light: 'sun',
  dark: 'moon',
  system: 'desktop',
}

export const NEXT_THEME: Record<ThemePreference, ThemePreference> = {
  light: 'dark',
  dark: 'system',
  system: 'light',
}
