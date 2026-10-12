---
name: reactjs-chart
description: The only approved chart stack for apps/web — ECharts 6 (already a dependency) rendered through a single EChartWrapper + useChartTheme in src/components/wrappers/. The wrapper is NOT present in the boilerplate yet; this skill contains the recipe to create it, theme it from the CSS design tokens (light/dark via useResolvedTheme), and the rules/forbidden patterns for chart code. Map use cases are handled by reactjs-map.
---

# Charts (ECharts)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the chart stack (ECharts wrapper, theme hook, option builders).

> **Not present in the boilerplate yet.** `echarts@^6` is installed, but there is no
> wrapper and no chart in the app. Before the first chart, create
> `src/components/wrappers/EChartWrapper.tsx` and `src/components/wrappers/useChartTheme.ts`
> from the recipe below (both are 3rd-party adapters → `components/wrappers/`).

Samples: [references/echarts-samples.md](references/echarts-samples.md) · Maps:
`.claude/skills/reactjs-map/SKILL.md`

## Rules

- MUST render every chart through `EChartWrapper`; feature code never imports runtime `echarts`
  (type-only `import type { EChartsOption } from 'echarts'` is fine).
- MUST NOT add Recharts, Chart.js, ApexCharts, Nivo, Victory or hand-rolled SVG/canvas charts.
- MUST register chart types/components only inside `EChartWrapper.tsx` (`echarts.use([...])`).
- MUST derive the chart mode from `useResolvedTheme()` (`src/hooks/use-resolved-theme.ts`,
  already resolves `'system'`) — never hardcode `mode="light"`.
- MUST take colors from `useChartTheme(mode)` (reads the shadcn semantic CSS tokens in
  `src/styles/variable.css`: `--chart-1…5`, `--foreground`, `--muted-foreground`, `--border`) — no
  unexplained hex in `option`. Series use `chart-1…5` (extended brand palettes only for data-viz
  when 5 series aren't enough); status colors only when the series *is* a status.
- MUST place every chart in a card surface (`Card`/`SectionCard`, `rounded-xl`, `bg-card`,
  `border-border`, `shadow-xs` at most) with a `text-base font-semibold` title, a one-line
  `text-sm text-muted-foreground` description and optional actions in the header — never a bare
  canvas on the page. Keep axes/grid quiet (muted labels, thin split lines, no chart borders/3D/
  gradients/shadows) and legends small. Dashboard placement: `reactjs-ui-design` §5.2.
- MUST show designed states: `Skeleton` (same height as the chart, `rounded-lg`) while loading,
  `EmptyState` (e.g. `ph-chart-bar`) when there is no data, `Alert variant="destructive"` + Retry on
  error — never an empty axis grid.
- MUST size charts responsively: `width="100%"` + explicit `height`; the wrapper resizes with
  a `ResizeObserver`.
- MUST type label/tooltip formatters as `(p: unknown) => string` and narrow at runtime.
- Option builders are pure functions in `features/{domain}/{feature}/config/` or `utils/`,
  not inside components; data comes from TanStack Query hooks.
- Provide `ariaLabel` describing the chart.

## Recipe — `src/components/wrappers/useChartTheme.ts` (create it)

```ts
import { useMemo } from 'react'

export type ChartMode = 'light' | 'dark'

export interface ChartTheme {
  palette: string[]
  text: string
  textMuted: string
  axisLine: string
  splitLine: string
  background: string
  fontFamily: string
}

const read = (style: CSSStyleDeclaration, name: string, fallback: string) => style.getPropertyValue(name).trim() || fallback

/** Chart colors from the active CSS tokens; recomputed when the resolved theme changes. */
export function useChartTheme(mode: ChartMode): ChartTheme {
  return useMemo(() => {
    const style = getComputedStyle(document.documentElement)
    return {
      palette: ['--chart-1', '--chart-2', '--chart-3', '--chart-4', '--chart-5'].map((token) => read(style, token, 'currentColor')),
      text: read(style, '--foreground', 'currentColor'),
      textMuted: read(style, '--muted-foreground', 'currentColor'),
      axisLine: read(style, '--border', 'currentColor'),
      splitLine: read(style, '--border', 'currentColor'),
      background: 'transparent',
      fontFamily: read(style, '--font-sans', 'sans-serif'),
    }
    // mode is the cache key: tokens differ per theme class on <html>
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])
}
```

## Recipe — `src/components/wrappers/EChartWrapper.tsx` (create it)

```tsx
import type { EChartsOption } from 'echarts'
import { BarChart, GaugeChart, LineChart, PieChart, ScatterChart } from 'echarts/charts'
import { DatasetComponent, GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useRef } from 'react'

import { cn } from '@/utils/cn'

import { useChartTheme, type ChartMode } from './useChartTheme'

// Register once. Add chart types here — never in feature code.
echarts.use([BarChart, LineChart, PieChart, ScatterChart, GaugeChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, DatasetComponent, CanvasRenderer])

export interface EChartWrapperProps {
  option: EChartsOption
  mode: ChartMode
  height?: number | string
  width?: number | string
  loading?: boolean
  ariaLabel?: string
  className?: string
  onChartReady?: (chart: echarts.ECharts) => void
}

export function EChartWrapper({ option, mode, height = 320, width = '100%', loading = false, ariaLabel = 'Chart', className, onChartReady }: EChartWrapperProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)
  const theme = useChartTheme(mode)

  // init / dispose + resize
  useEffect(() => {
    const el = containerRef.current
    if (!el) return undefined
    const chart = echarts.init(el, undefined, { renderer: 'canvas' })
    chartRef.current = chart
    onChartReady?.(chart)
    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(el)
    return () => {
      observer.disconnect()
      chart.dispose()
      chartRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- init once per mount
  }, [])

  // option + theme defaults (caller option spread last = wins)
  useEffect(() => {
    chartRef.current?.setOption(
      {
        backgroundColor: theme.background,
        color: theme.palette,
        textStyle: { color: theme.text, fontFamily: theme.fontFamily },
        tooltip: { trigger: 'item' },
        legend: { textStyle: { color: theme.textMuted } },
        ...option,
      },
      { notMerge: true },
    )
  }, [option, theme])

  useEffect(() => {
    if (loading) chartRef.current?.showLoading()
    else chartRef.current?.hideLoading()
  }, [loading])

  return <div ref={containerRef} role="img" aria-label={ariaLabel} className={cn('min-h-0', className)} style={{ width, height }} />
}
```

Axis/grid styling that depends on the theme (axis line, split line colors) belongs in the
option builder, fed by `useChartTheme(mode)`:

```ts
// src/features/{domain}/{feature}/config/{name}.chart.ts — example option builder
import type { EChartsOption } from 'echarts'

import type { ChartTheme } from '@/components/wrappers/useChartTheme'

export function buildDailyBarOption(labels: string[], values: number[], theme: ChartTheme): EChartsOption {
  return {
    grid: { left: 40, right: 16, top: 24, bottom: 32 },
    xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: theme.axisLine } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: theme.splitLine } } },
    series: [{ type: 'bar', data: values }],
  }
}
```

Usage in a feature component (chart inside a card, with states):

```tsx
const mode = useResolvedTheme()                       // from '@/hooks/use-resolved-theme'
const theme = useChartTheme(mode)
const { data, isPending, error, refetch } = useDailyStats(query)      // TanStack Query hook in the feature
const option = useMemo(() => buildDailyBarOption(data?.labels ?? [], data?.values ?? [], theme), [data, theme])

return (
  <SectionCard title="Daily sign-ins" description="Last 30 days" className="xl:col-span-2">
    {isPending ? (
      <Skeleton className="h-80 w-full rounded-lg" />
    ) : error ? (
      <Alert variant="destructive">…{getErrorMessage(error)} + Retry…</Alert>
    ) : !data?.values.length ? (
      <EmptyState icon="chart-bar" title="No sign-ins yet" description="Data appears after the first login." />
    ) : (
      <EChartWrapper option={option} mode={mode} height={320} ariaLabel="Daily sign-ins" />
    )}
  </SectionCard>
)
```

`SectionCard`, `EmptyState` live in `src/components/common/` (check their props there); a plain
shadcn `Card` + `CardHeader`/`CardTitle`/`CardDescription`/`CardContent` is equally fine.

## Forbidden

| Violation | Use instead |
|---|---|
| `import * as echarts from 'echarts'` in features/pages | `EChartWrapper` |
| `echarts.use()` outside the wrapper | register in `EChartWrapper.tsx` |
| `recharts` / `chart.js` / `apexcharts` / `nivo` | ECharts via `EChartWrapper` |
| hex colors in `option` | `useChartTheme(mode)` tokens (add new tokens to `variable.css` light + dark) |
| `mode="light"` or passing `'system'` | `useResolvedTheme()` |
| `formatter: (p: { value: number }) => …` | `(p: unknown) => …` + narrowing |
| option objects built inline in JSX | pure builder in `config/`/`utils/` + `useMemo` |

## Extending the wrapper

Add new props with defaults (one `useEffect` per concern), keep existing props
backward-compatible, register new chart types in the `echarts.use([...])` list, and add a
sample to `references/echarts-samples.md`.

## Checklist

- [ ] Wrapper + theme hook exist in `src/components/wrappers/` (created from this recipe)
- [ ] Chart data from a TanStack Query hook; option from a pure builder
- [ ] Mode from `useResolvedTheme()`; colors from `useChartTheme()`
- [ ] Explicit height, `width="100%"`, `ariaLabel`
- [ ] Chart sits in a `rounded-xl` card with title/description; loading/empty/error states designed
- [ ] Works in light and dark theme; no console errors on unmount (dispose)
- [ ] Looked at it: `npm run ui:snapshot -- --route <path>` (`reactjs-ui-design` §8)
- [ ] `npm run typecheck && npm run lint && npm run build` (apps/web) pass
