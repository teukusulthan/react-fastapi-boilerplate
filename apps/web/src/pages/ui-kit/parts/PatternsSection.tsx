import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { StatCard } from '@/components/common/StatCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import { KitDemo, KitSection } from './KitSection'

export function PatternsSection() {
  return (
    <KitSection id="patterns" title="Patterns" description="components/common — compose pages from these before writing new layout code.">
      <KitDemo title="PageHeader" className="block">
        <PageHeader
          title="Projects"
          description="Manage the projects your team is working on."
          actions={
            <>
              <Button variant="outline">
                <i className="ph ph-download-simple" aria-hidden="true" />
                Export
              </Button>
              <Button>
                <i className="ph ph-plus" aria-hidden="true" />
                New project
              </Button>
            </>
          }
        />
      </KitDemo>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active projects" value="24" icon="folder-simple" delta={{ value: '+3', trend: 'up' }} helper="vs. last month" />
        <StatCard label="Open issues" value="128" icon="bug" delta={{ value: '-12%', trend: 'down' }} helper="vs. last week" />
        <StatCard label="Deploys today" value={null} icon="rocket-launch" helper="No data source connected yet" />
        <StatCard label="Loading" value={null} icon="spinner" loading />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard
          title="General"
          description="Basic information about the workspace."
          footer={
            <div className="flex w-full justify-end gap-2">
              <Button variant="outline">Cancel</Button>
              <Button>Save changes</Button>
            </div>
          }
        >
          <div className="grid gap-2">
            <Label htmlFor="kit-workspace">Workspace name</Label>
            <Input id="kit-workspace" defaultValue="Northwind" />
          </div>
        </SectionCard>
        <SectionCard tone="destructive" title="Danger zone" description="Irreversible actions.">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">Delete this workspace and all of its data.</p>
            <Button variant="destructive">Delete workspace</Button>
          </div>
        </SectionCard>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          variant="dashed"
          icon="folder-simple-plus"
          title="No projects yet"
          description="Create your first project to start tracking work."
          action={
            <Button>
              <i className="ph ph-plus" aria-hidden="true" />
              New project
            </Button>
          }
        />
        <EmptyState
          variant="dashed"
          icon="magnifying-glass"
          title="No matching results"
          description="Try a different search term or clear the filters."
          action={<Button variant="outline">Clear filters</Button>}
        />
      </div>
    </KitSection>
  )
}
