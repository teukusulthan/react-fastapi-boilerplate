import { PageHeader } from '@/components/common/PageHeader'

import { ActionsSection } from './parts/ActionsSection'
import { DataSection } from './parts/DataSection'
import { FeedbackSection } from './parts/FeedbackSection'
import { FormsSection } from './parts/FormsSection'
import { FoundationsSection } from './parts/FoundationsSection'
import { OverlaysSection } from './parts/OverlaysSection'
import { PatternsSection } from './parts/PatternsSection'
import { UI_KIT_SECTIONS } from './ui-kit.constants'

/**
 * Dev-only catalogue of every primitive (components/ui) and pattern (components/common, modules/data-table).
 * Hidden route: registered only when DEV_TOOLS_ENABLED (vite dev) and intentionally not in the menu.
 * Add new patterns here so the next person can see what exists.
 */
export default function UiKitPage() {
  return (
    <div className="flex flex-col gap-10">
      <div className="flex flex-col gap-4">
        <PageHeader title="UI kit" description="Every primitive and pattern in this app, themed with the active tokens. Dev builds only." />
        <nav aria-label="UI kit sections" className="flex flex-wrap gap-2">
          {UI_KIT_SECTIONS.map((section) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className="rounded-md border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground shadow-xs transition-colors hover:bg-accent hover:text-foreground"
            >
              {section.label}
            </a>
          ))}
        </nav>
      </div>
      <FoundationsSection />
      <ActionsSection />
      <FormsSection />
      <FeedbackSection />
      <OverlaysSection />
      <DataSection />
      <PatternsSection />
    </div>
  )
}
