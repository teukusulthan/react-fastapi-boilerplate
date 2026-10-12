import { SectionCard } from '@/components/common/SectionCard'

import { GETTING_STARTED_STEPS } from '../constants/overview.constants'

/** Builder guidance for the boilerplate dashboard — replace with the product's real content. */
export function NextStepsCard() {
  return (
    <SectionCard title="Build from here" description="This dashboard is a starting point. Replace it with the first real screen of your product.">
      <ol className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {GETTING_STARTED_STEPS.map((step, index) => (
          <li key={step.title} className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-4">
            <div className="flex items-center justify-between">
              <span className="flex size-8 items-center justify-center rounded-lg border bg-background text-muted-foreground shadow-xs" aria-hidden="true">
                <i className={`ph ph-${step.icon}`} />
              </span>
              <span className="text-xs font-medium text-muted-foreground tabular-nums">Step {index + 1}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm font-medium">{step.title}</span>
              <span className="text-sm text-muted-foreground">{step.detail}</span>
            </div>
            <code className="mt-auto truncate rounded-md bg-background px-2 py-1 font-mono text-xs text-muted-foreground ring-1 ring-border">{step.path}</code>
          </li>
        ))}
      </ol>
    </SectionCard>
  )
}
