# ECharts — Sample Code

> Rules: [../SKILL.md](../SKILL.md). `EChartWrapper` / `useChartTheme` are not present in the
> boilerplate yet — create them at `src/components/wrappers/EChartWrapper.tsx` and
> `src/components/wrappers/useChartTheme.ts` from the SKILL recipe before using these samples.

## Mode + theme (canonical)

```tsx
// create the wrapper files first (see SKILL recipe)
import { useChartTheme } from '@/components/wrappers/useChartTheme'
import { useResolvedTheme } from '@/hooks/use-resolved-theme'

const mode = useResolvedTheme()   // 'light' | 'dark' ('system' already resolved, live)
const theme = useChartTheme(mode) // colors read from src/styles/variable.css tokens
```

## Label formatter (canonical)

```ts
label: {
  formatter: (p: unknown) => {
    const v = (p as { value?: unknown }).value
    return typeof v === 'number' && v !== 0 ? String(v) : ''
  },
},
```

## Basic bar / line

```tsx
import type { EChartsOption } from 'echarts'

// recipe import — create the wrapper first
import { EChartWrapper } from '@/components/wrappers/EChartWrapper'

const option: EChartsOption = {
  xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed'] },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [120, 200, 150] }],
}

<EChartWrapper option={option} mode={mode} height={320} ariaLabel="Weekly volume" />
```

## With a TanStack Query hook

```tsx
const { data, isPending } = useWeeklyVolume(query)   // feature hook → service → backend
const option = useMemo(() => buildWeeklyOption(data ?? [], theme), [data, theme])

<EChartWrapper option={option} mode={mode} loading={isPending} height={320} />
```

## Pie with token palette

```ts
const option: EChartsOption = {
  tooltip: { trigger: 'item' },
  series: [
    {
      type: 'pie',
      radius: ['45%', '70%'],
      data: [
        { name: 'Active', value: 42 },
        { name: 'Pending', value: 7 },
      ],
      // colors come from the wrapper's `color: theme.palette` default
    },
  ],
}
```

## Accessing the instance

```tsx
import type { ECharts } from 'echarts/core'

const chartRef = useRef<ECharts | null>(null)

<EChartWrapper option={option} mode={mode} onChartReady={(chart) => { chartRef.current = chart }} />

chartRef.current?.dispatchAction({ type: 'highlight', seriesIndex: 0 })
```

## New chart type (e.g. heatmap)

1. In `EChartWrapper.tsx`: `import { HeatmapChart } from 'echarts/charts'` and add it (plus
   `VisualMapComponent` from `echarts/components`) to the `echarts.use([...])` list.
2. Use `series: [{ type: 'heatmap', … }]` in the option builder.

## Responsive sizes

```tsx
<EChartWrapper option={option} mode={mode} height={400} width="100%" />
<EChartWrapper option={option} mode={mode} height="50vh" />
```

The container must have a real width (parents in a flex chain need `min-w-0`).
