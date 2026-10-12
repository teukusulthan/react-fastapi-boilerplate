/**
 * shadcn/ui Sidebar (new-york) — behavior kept from upstream (collapse state, mobile sheet, ⌘/Ctrl+B,
 * tooltips when collapsed), ported to React 18 (`forwardRef`) and Phosphor icons.
 *
 * Shell contract: the app has a full-width h-12 header, so pass a top offset on <Sidebar>
 * (`className="top-12 h-[calc(100svh-3rem)]"`) — the fixed panel never covers the header, and the
 * in-flow gap element reserves its width so main content never sits underneath it.
 * `variant="inset"` drops the border so the main area can render as an inset panel (see AppLayout).
 */
import { cva, type VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'
import * as React from 'react'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useIsMobile } from '@/hooks/use-mobile'
import { cn } from '@/utils/cn'

const SIDEBAR_STORAGE_KEY = 'sidebar-state'
const SIDEBAR_WIDTH = '15rem'
const SIDEBAR_WIDTH_MOBILE = '18rem'
const SIDEBAR_WIDTH_ICON = '3.25rem'
const SIDEBAR_KEYBOARD_SHORTCUT = 'b'

type SidebarState = 'expanded' | 'collapsed'

interface SidebarContextValue {
  state: SidebarState
  open: boolean
  setOpen: (open: boolean) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  isMobile: boolean
  toggleSidebar: () => void
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

function useSidebar(): SidebarContextValue {
  const context = React.useContext(SidebarContext)
  if (!context) throw new Error('useSidebar must be used within a SidebarProvider.')
  return context
}

function readStoredOpen(fallback: boolean): boolean {
  try {
    const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
    return stored === null ? fallback : stored === 'true'
  } catch {
    return fallback
  }
}

interface SidebarProviderProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

const SidebarProvider = React.forwardRef<HTMLDivElement, SidebarProviderProps>(
  ({ defaultOpen = true, open: openProp, onOpenChange: setOpenProp, className, style, children, ...props }, ref) => {
    const isMobile = useIsMobile()
    const [openMobile, setOpenMobile] = React.useState(false)
    const [internalOpen, setInternalOpen] = React.useState(() => readStoredOpen(defaultOpen))
    const open = openProp ?? internalOpen

    const setOpen = React.useCallback(
      (value: boolean) => {
        if (setOpenProp) setOpenProp(value)
        else setInternalOpen(value)
        try {
          window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(value))
        } catch {
          // storage unavailable (private mode) — state still works in memory
        }
      },
      [setOpenProp],
    )

    const toggleSidebar = React.useCallback(() => {
      if (isMobile) setOpenMobile((value) => !value)
      else setOpen(!open)
    }, [isMobile, open, setOpen])

    React.useEffect(() => {
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
          event.preventDefault()
          toggleSidebar()
        }
      }
      window.addEventListener('keydown', handleKeyDown)
      return () => window.removeEventListener('keydown', handleKeyDown)
    }, [toggleSidebar])

    const state: SidebarState = open ? 'expanded' : 'collapsed'

    const contextValue = React.useMemo<SidebarContextValue>(
      () => ({ state, open, setOpen, isMobile, openMobile, setOpenMobile, toggleSidebar }),
      [state, open, setOpen, isMobile, openMobile, toggleSidebar],
    )

    return (
      <SidebarContext.Provider value={contextValue}>
        <div
          ref={ref}
          data-slot="sidebar-wrapper"
          data-state={state}
          style={{ '--sidebar-width': SIDEBAR_WIDTH, '--sidebar-width-icon': SIDEBAR_WIDTH_ICON, ...style } as React.CSSProperties}
          className={cn('group/sidebar-wrapper flex w-full has-data-[variant=inset]:bg-sidebar', className)}
          {...props}
        >
          {children}
        </div>
      </SidebarContext.Provider>
    )
  },
)
SidebarProvider.displayName = 'SidebarProvider'

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  side?: 'left' | 'right'
  variant?: 'sidebar' | 'inset'
  collapsible?: 'offcanvas' | 'icon' | 'none'
}

const Sidebar = React.forwardRef<HTMLDivElement, SidebarProps>(
  ({ side = 'left', variant = 'sidebar', collapsible = 'offcanvas', className, children, ...props }, ref) => {
    const { isMobile, state, openMobile, setOpenMobile } = useSidebar()

    if (collapsible === 'none') {
      return (
        <div ref={ref} data-slot="sidebar" className={cn('flex h-full w-(--sidebar-width) flex-col bg-sidebar text-sidebar-foreground', className)} {...props}>
          {children}
        </div>
      )
    }

    if (isMobile) {
      return (
        <Sheet open={openMobile} onOpenChange={setOpenMobile}>
          <SheetContent
            data-sidebar="sidebar"
            data-slot="sidebar"
            data-mobile="true"
            side={side}
            showCloseButton={false}
            className="w-(--sidebar-width) bg-sidebar p-0 text-sidebar-foreground"
            style={{ '--sidebar-width': SIDEBAR_WIDTH_MOBILE } as React.CSSProperties}
          >
            <SheetHeader className="sr-only">
              <SheetTitle>Navigation</SheetTitle>
              <SheetDescription>Main navigation</SheetDescription>
            </SheetHeader>
            <div className="flex h-full w-full flex-col">{children}</div>
          </SheetContent>
        </Sheet>
      )
    }

    return (
      <div
        ref={ref}
        className="group peer hidden text-sidebar-foreground md:block"
        data-state={state}
        data-collapsible={state === 'collapsed' ? collapsible : ''}
        data-variant={variant}
        data-side={side}
        data-slot="sidebar"
      >
        {/* In-flow spacer: reserves the sidebar width so content never sits under the fixed panel. */}
        <div
          data-slot="sidebar-gap"
          className={cn(
            'relative w-(--sidebar-width) bg-transparent transition-[width] duration-200 ease-linear',
            'group-data-[collapsible=offcanvas]:w-0 group-data-[collapsible=icon]:w-(--sidebar-width-icon)',
          )}
        />
        <div
          data-slot="sidebar-container"
          className={cn(
            'fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear md:flex',
            side === 'left'
              ? 'left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]'
              : 'right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]',
            variant === 'sidebar' && (side === 'left' ? 'border-r border-sidebar-border' : 'border-l border-sidebar-border'),
            'group-data-[collapsible=icon]:w-(--sidebar-width-icon)',
            className,
          )}
          {...props}
        >
          <div data-sidebar="sidebar" data-slot="sidebar-inner" className="flex h-full w-full flex-col bg-sidebar">
            {children}
          </div>
        </div>
      </div>
    )
  },
)
Sidebar.displayName = 'Sidebar'

const SidebarTrigger = React.forwardRef<React.ComponentRef<typeof Button>, React.ComponentProps<typeof Button>>(({ className, onClick, ...props }, ref) => {
  const { toggleSidebar } = useSidebar()
  return (
    <Button
      ref={ref}
      data-sidebar="trigger"
      data-slot="sidebar-trigger"
      variant="ghost"
      size="icon-sm"
      className={cn('text-muted-foreground hover:text-foreground', className)}
      onClick={(event) => {
        onClick?.(event)
        toggleSidebar()
      }}
      {...props}
    >
      <i className="ph ph-sidebar-simple" aria-hidden="true" />
      <span className="sr-only">Toggle sidebar</span>
    </Button>
  )
})
SidebarTrigger.displayName = 'SidebarTrigger'

/** Main content region next to the sidebar. With `variant="inset"` it renders as a rounded panel. */
const SidebarInset = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement>>(({ className, ...props }, ref) => (
  <main
    ref={ref}
    data-slot="sidebar-inset"
    className={cn(
      'relative flex min-w-0 flex-1 flex-col bg-background',
      'md:peer-data-[variant=inset]:mr-2 md:peer-data-[variant=inset]:mb-2 md:peer-data-[variant=inset]:overflow-hidden md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:border md:peer-data-[variant=inset]:shadow-xs',
      className,
    )}
    {...props}
  />
))
SidebarInset.displayName = 'SidebarInset'

const SidebarHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sidebar-header" data-sidebar="header" className={cn('flex flex-col gap-2 p-2', className)} {...props} />
))
SidebarHeader.displayName = 'SidebarHeader'

const SidebarFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sidebar-footer" data-sidebar="footer" className={cn('flex flex-col gap-2 p-2', className)} {...props} />
))
SidebarFooter.displayName = 'SidebarFooter'

const SidebarSeparator = React.forwardRef<React.ComponentRef<typeof Separator>, React.ComponentProps<typeof Separator>>(({ className, ...props }, ref) => (
  <Separator ref={ref} data-slot="sidebar-separator" data-sidebar="separator" className={cn('mx-2 w-auto bg-sidebar-border', className)} {...props} />
))
SidebarSeparator.displayName = 'SidebarSeparator'

/** Scroll container of the sidebar body. Wrap long content in `PerfectScrollArea` (see AppSidebar). */
const SidebarContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="sidebar-content"
    data-sidebar="content"
    className={cn('flex min-h-0 flex-1 flex-col gap-2 overflow-hidden', className)}
    {...props}
  />
))
SidebarContent.displayName = 'SidebarContent'

const SidebarGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sidebar-group" data-sidebar="group" className={cn('relative flex w-full min-w-0 flex-col p-2', className)} {...props} />
))
SidebarGroup.displayName = 'SidebarGroup'

const SidebarGroupLabel = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { asChild?: boolean }>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : 'div'
    return (
      <Comp
        ref={ref}
        data-slot="sidebar-group-label"
        data-sidebar="group-label"
        className={cn(
          'flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium text-muted-foreground transition-[margin,opacity] duration-200 ease-linear outline-none',
          'focus-visible:ring-[3px] focus-visible:ring-sidebar-ring/50',
          'group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0',
          className,
        )}
        {...props}
      />
    )
  },
)
SidebarGroupLabel.displayName = 'SidebarGroupLabel'

const SidebarGroupContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sidebar-group-content" data-sidebar="group-content" className={cn('w-full text-sm', className)} {...props} />
))
SidebarGroupContent.displayName = 'SidebarGroupContent'

const SidebarMenu = React.forwardRef<HTMLUListElement, React.HTMLAttributes<HTMLUListElement>>(({ className, ...props }, ref) => (
  <ul ref={ref} data-slot="sidebar-menu" data-sidebar="menu" className={cn('flex w-full min-w-0 flex-col gap-0.5', className)} {...props} />
))
SidebarMenu.displayName = 'SidebarMenu'

const SidebarMenuItem = React.forwardRef<HTMLLIElement, React.HTMLAttributes<HTMLLIElement>>(({ className, ...props }, ref) => (
  <li ref={ref} data-slot="sidebar-menu-item" data-sidebar="menu-item" className={cn('group/menu-item relative', className)} {...props} />
))
SidebarMenuItem.displayName = 'SidebarMenuItem'

const sidebarMenuButtonVariants = cva(
  [
    'peer/menu-button flex w-full items-center gap-2.5 overflow-hidden rounded-md px-2 text-left text-sm text-sidebar-foreground outline-none transition-[width,height,padding,background-color,color]',
    'hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground focus-visible:ring-[3px] focus-visible:ring-sidebar-ring/50',
    'disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50',
    'data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground',
    '[&>i]:text-muted-foreground hover:[&>i]:text-sidebar-accent-foreground data-[active=true]:[&>i]:text-sidebar-accent-foreground',
    'group-data-[collapsible=icon]:size-9! group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0! group-data-[collapsible=icon]:[&>span:last-child]:hidden',
    '[&>span:last-child]:truncate',
  ],
  {
    variants: {
      size: {
        default: 'h-8',
        sm: 'h-7 text-xs',
        lg: 'h-12 group-data-[collapsible=icon]:p-0!',
      },
    },
    defaultVariants: {
      size: 'default',
    },
  },
)

interface SidebarMenuButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof sidebarMenuButtonVariants> {
  asChild?: boolean
  isActive?: boolean
  tooltip?: string | React.ComponentProps<typeof TooltipContent>
}

const SidebarMenuButton = React.forwardRef<HTMLButtonElement, SidebarMenuButtonProps>(
  ({ asChild = false, isActive = false, size = 'default', tooltip, className, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : 'button'
    const { isMobile, state } = useSidebar()

    const button = (
      <Comp
        ref={ref}
        data-slot="sidebar-menu-button"
        data-sidebar="menu-button"
        data-size={size}
        data-active={isActive}
        className={cn(sidebarMenuButtonVariants({ size }), className)}
        {...props}
      />
    )

    if (!tooltip) return button

    const tooltipProps = typeof tooltip === 'string' ? { children: tooltip } : tooltip

    return (
      <Tooltip>
        <TooltipTrigger asChild>{button}</TooltipTrigger>
        <TooltipContent side="right" align="center" hidden={state !== 'collapsed' || isMobile} {...tooltipProps} />
      </Tooltip>
    )
  },
)
SidebarMenuButton.displayName = 'SidebarMenuButton'

/** Small count/label at the right edge of a menu item. */
const SidebarMenuBadge = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="sidebar-menu-badge"
    data-sidebar="menu-badge"
    className={cn(
      'pointer-events-none absolute top-1.5 right-1.5 flex h-5 min-w-5 items-center justify-center rounded-md px-1 text-xs font-medium text-muted-foreground tabular-nums select-none',
      'group-data-[collapsible=icon]:hidden',
      className,
    )}
    {...props}
  />
))
SidebarMenuBadge.displayName = 'SidebarMenuBadge'

const SidebarMenuSkeleton = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { showIcon?: boolean }>(
  ({ className, showIcon = false, ...props }, ref) => (
    <div
      ref={ref}
      data-slot="sidebar-menu-skeleton"
      data-sidebar="menu-skeleton"
      className={cn('flex h-8 items-center gap-2 rounded-md px-2', className)}
      {...props}
    >
      {showIcon && <Skeleton className="size-4 rounded-md" data-sidebar="menu-skeleton-icon" />}
      <Skeleton className="h-4 max-w-3/4 flex-1" data-sidebar="menu-skeleton-text" />
    </div>
  ),
)
SidebarMenuSkeleton.displayName = 'SidebarMenuSkeleton'

const SidebarMenuSub = React.forwardRef<HTMLUListElement, React.HTMLAttributes<HTMLUListElement>>(({ className, ...props }, ref) => (
  <ul
    ref={ref}
    data-slot="sidebar-menu-sub"
    data-sidebar="menu-sub"
    className={cn(
      'mx-3.5 flex min-w-0 translate-x-px flex-col gap-0.5 border-l border-sidebar-border px-2.5 py-0.5 group-data-[collapsible=icon]:hidden',
      className,
    )}
    {...props}
  />
))
SidebarMenuSub.displayName = 'SidebarMenuSub'

const SidebarMenuSubItem = React.forwardRef<HTMLLIElement, React.HTMLAttributes<HTMLLIElement>>(({ className, ...props }, ref) => (
  <li ref={ref} data-slot="sidebar-menu-sub-item" data-sidebar="menu-sub-item" className={cn('group/menu-sub-item relative', className)} {...props} />
))
SidebarMenuSubItem.displayName = 'SidebarMenuSubItem'

const SidebarMenuSubButton = React.forwardRef<HTMLAnchorElement, React.AnchorHTMLAttributes<HTMLAnchorElement> & { asChild?: boolean; isActive?: boolean }>(
  ({ asChild = false, isActive = false, className, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : 'a'
    return (
      <Comp
        ref={ref}
        data-slot="sidebar-menu-sub-button"
        data-sidebar="menu-sub-button"
        data-active={isActive}
        className={cn(
          'flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-md px-2 text-sm text-sidebar-foreground outline-none',
          'hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground focus-visible:ring-[3px] focus-visible:ring-sidebar-ring/50',
          'data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground',
          className,
        )}
        {...props}
      />
    )
  },
)
SidebarMenuSubButton.displayName = 'SidebarMenuSubButton'

export {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarSeparator,
  SidebarTrigger,
  useSidebar,
}
