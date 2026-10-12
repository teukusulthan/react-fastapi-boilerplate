import { StatusBadge } from '@/components/common/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonGroup } from '@/components/ui/button-group'
import { Kbd, KbdGroup } from '@/components/ui/kbd'
import { Toggle } from '@/components/ui/toggle'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

import { KitDemo, KitSection } from './KitSection'

export function ActionsSection() {
  return (
    <KitSection id="actions" title="Actions" description="One primary button per view. Icon-only buttons get an aria-label and a tooltip.">
      <KitDemo title="Button variants">
        <Button>
          <i className="ph ph-plus" aria-hidden="true" />
          Primary
        </Button>
        <Button variant="outline">Outline</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
        <Button variant="destructive">
          <i className="ph ph-trash" aria-hidden="true" />
          Delete
        </Button>
      </KitDemo>
      <KitDemo title="Sizes & states">
        <Button size="sm">Small</Button>
        <Button>Default</Button>
        <Button size="lg">Large</Button>
        <Button loading>Saving…</Button>
        <Button disabled variant="outline">
          Disabled
        </Button>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="icon" variant="outline" aria-label="Settings">
              <i className="ph ph-gear-six" aria-hidden="true" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Settings <Kbd>S</Kbd>
          </TooltipContent>
        </Tooltip>
        <Button size="icon-sm" variant="ghost" aria-label="More">
          <i className="ph ph-dots-three" aria-hidden="true" />
        </Button>
      </KitDemo>
      <div className="grid gap-4 lg:grid-cols-2">
        <KitDemo title="Badges & status">
          <Badge>Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="outline">Outline</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="info">Info</Badge>
          <Badge variant="destructive">Destructive</Badge>
          <StatusBadge tone="success">Active</StatusBadge>
          <StatusBadge tone="warning">Pending</StatusBadge>
          <StatusBadge tone="destructive">Blocked</StatusBadge>
          <StatusBadge tone="info">Syncing</StatusBadge>
          <StatusBadge tone="neutral">Archived</StatusBadge>
        </KitDemo>
        <KitDemo title="Toggles, groups & keys">
          <ToggleGroup type="single" variant="outline" defaultValue="list" aria-label="View">
            <ToggleGroupItem value="list" aria-label="List view">
              <i className="ph ph-list" aria-hidden="true" />
            </ToggleGroupItem>
            <ToggleGroupItem value="grid" aria-label="Grid view">
              <i className="ph ph-squares-four" aria-hidden="true" />
            </ToggleGroupItem>
          </ToggleGroup>
          <Toggle aria-label="Bold" variant="outline">
            <i className="ph ph-text-b" aria-hidden="true" />
          </Toggle>
          <ButtonGroup variant="outline">
            <Button>Day</Button>
            <Button>Week</Button>
            <Button>Month</Button>
          </ButtonGroup>
          <KbdGroup>
            <Kbd>⌘</Kbd>
            <Kbd>K</Kbd>
          </KbdGroup>
        </KitDemo>
      </div>
    </KitSection>
  )
}
