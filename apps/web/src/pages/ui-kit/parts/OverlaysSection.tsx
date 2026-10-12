import { useState } from 'react'
import { toast } from 'sonner'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandShortcut } from '@/components/ui/command'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { formatDate } from '@/utils/date-formatter'

import { KitDemo, KitSection } from './KitSection'

export function OverlaysSection() {
  const [date, setDate] = useState<Date | undefined>(undefined)

  return (
    <KitSection id="overlays" title="Overlays" description="Dialogs for short tasks, sheets for longer side panels, menus for row/overflow actions.">
      <KitDemo title="Dialog, sheet, confirm">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline">Open dialog</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Rename project</DialogTitle>
              <DialogDescription>The new name is visible to everyone in the workspace.</DialogDescription>
            </DialogHeader>
            <div className="grid gap-2">
              <Label htmlFor="kit-project">Name</Label>
              <Input id="kit-project" defaultValue="Acme dashboard" />
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <DialogClose asChild>
                <Button>Save changes</Button>
              </DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline">Open sheet</Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Filters</SheetTitle>
              <SheetDescription>Narrow down the list.</SheetDescription>
            </SheetHeader>
            <SheetFooter>
              <Button>Apply</Button>
            </SheetFooter>
          </SheetContent>
        </Sheet>
        <ConfirmDialog
          trigger={
            <Button variant="outline" className="text-destructive hover:text-destructive">
              Delete…
            </Button>
          }
          icon="trash"
          variant="destructive"
          title="Delete this project?"
          description="All of its data will be removed. This can't be undone."
          confirmLabel="Delete project"
          onConfirm={() => {
            toast.success('Project deleted')
          }}
        />
      </KitDemo>
      <KitDemo title="Menus, popovers, tooltips">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Options
              <i className="ph ph-caret-down" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-52">
            <DropdownMenuLabel>Project</DropdownMenuLabel>
            <DropdownMenuItem>
              <i className="ph ph-pencil-simple" aria-hidden="true" />
              Rename
              <DropdownMenuShortcut>⌘R</DropdownMenuShortcut>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <i className="ph ph-copy" aria-hidden="true" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive">
              <i className="ph ph-trash" aria-hidden="true" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">
              <i className="ph ph-calendar-blank" aria-hidden="true" />
              {date ? formatDate(date) : 'Pick a date'}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar mode="single" selected={date} onSelect={setDate} />
          </PopoverContent>
        </Popover>
        <HoverCard>
          <HoverCardTrigger asChild>
            <Button variant="link">@northwind</Button>
          </HoverCardTrigger>
          <HoverCardContent className="text-sm">
            <p className="font-medium">Northwind Traders</p>
            <p className="text-muted-foreground">Customer since 2024 · 12 projects</p>
          </HoverCardContent>
        </HoverCard>
      </KitDemo>
      <KitDemo title="Command (inline)" className="block">
        <Command className="max-w-md rounded-xl border shadow-xs">
          <CommandInput placeholder="Type a command or search…" />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            <CommandGroup heading="Suggestions">
              <CommandItem>
                <i className="ph ph-squares-four" aria-hidden="true" />
                Dashboard
                <CommandShortcut>⌘D</CommandShortcut>
              </CommandItem>
              <CommandItem>
                <i className="ph ph-users" aria-hidden="true" />
                Users
              </CommandItem>
              <CommandItem>
                <i className="ph ph-gear-six" aria-hidden="true" />
                Settings
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </KitDemo>
    </KitSection>
  )
}
