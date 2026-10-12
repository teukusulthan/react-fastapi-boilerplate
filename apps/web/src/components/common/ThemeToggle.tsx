import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { THEME_ICON, THEME_LABEL, THEME_OPTIONS } from '@/config/theme-config'
import { useResolvedTheme } from '@/hooks/use-resolved-theme'
import { useThemeStore, type ThemePreference } from '@/stores/useThemeStore'

/** Icon button → Light / Dark / System menu. */
export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme)
  const setTheme = useThemeStore((state) => state.setTheme)
  const resolved = useResolvedTheme()

  return (
    <DropdownMenu>
      <Tooltip>
        <TooltipTrigger asChild>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" className="text-muted-foreground hover:text-foreground" aria-label={`Theme: ${THEME_LABEL[theme]}`}>
              <i className={`ph ph-${THEME_ICON[resolved]}`} aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
        </TooltipTrigger>
        <TooltipContent>Theme</TooltipContent>
      </Tooltip>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuLabel>Theme</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={theme} onValueChange={(value) => setTheme(value as ThemePreference)}>
          {THEME_OPTIONS.map((option) => (
            <DropdownMenuRadioItem key={option} value={option}>
              <i className={`ph ph-${THEME_ICON[option]}`} aria-hidden="true" />
              {THEME_LABEL[option]}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
