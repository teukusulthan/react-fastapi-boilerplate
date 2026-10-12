import { cn } from '@/utils/cn'

import { CHART_SWATCHES, COLOR_SWATCHES, RADIUS_SAMPLES, TYPE_SCALE } from '../ui-kit.constants'

import { KitDemo, KitSection } from './KitSection'

export function FoundationsSection() {
  return (
    <KitSection id="foundations" title="Foundations" description="Semantic color tokens, type scale, radius and depth. Use these classes — never raw values.">
      <KitDemo title="Semantic colors" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {COLOR_SWATCHES.map((swatch) => (
          <div key={swatch.name} className="flex flex-col gap-2">
            <div className={cn('h-12 rounded-lg border', swatch.className)} />
            <div className="flex flex-col">
              <span className="text-xs font-medium">{swatch.name}</span>
              <code className="font-mono text-xs text-muted-foreground">{swatch.token}</code>
            </div>
          </div>
        ))}
      </KitDemo>
      <div className="grid gap-4 lg:grid-cols-2">
        <KitDemo title="Type scale" className="flex-col items-stretch gap-4">
          {TYPE_SCALE.map((row) => (
            <div key={row.label} className="flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">{row.label}</span>
              <span className={row.className}>{row.sample}</span>
            </div>
          ))}
        </KitDemo>
        <div className="grid gap-4">
          <KitDemo title="Chart palette (data viz only)" className="grid grid-cols-5 gap-2">
            {CHART_SWATCHES.map((swatch) => (
              <div key={swatch.name} className="flex flex-col gap-2">
                <div className={cn('h-10 rounded-md', swatch.className)} />
                <code className="font-mono text-xs text-muted-foreground">{swatch.name}</code>
              </div>
            ))}
          </KitDemo>
          <KitDemo title="Radius & depth" className="grid grid-cols-3 gap-4">
            {RADIUS_SAMPLES.map((sample) => (
              <div key={sample.label} className="flex flex-col gap-2">
                <div className={cn('h-16 border bg-background shadow-xs', sample.className)} />
                <span className="text-xs text-muted-foreground">{sample.label}</span>
              </div>
            ))}
          </KitDemo>
        </div>
      </div>
    </KitSection>
  )
}
