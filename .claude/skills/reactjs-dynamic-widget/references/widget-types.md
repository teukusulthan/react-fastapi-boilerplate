---
name: widget-types-reference
description: TypeScript type specs for dynamic-widget — WidgetConfig, WidgetDataSource, all options interfaces.
---

# Dynamic Widget — Type Specs

## WidgetType

```ts
type WidgetType = 'chart' | 'stat' | 'list' | 'table' | 'card-grid' | 'word-cloud'
```

---

## WidgetDataSource

```ts
interface WidgetDataSource {
  type: 'api' | 'mock' | 'static'
  endpoint?: string                                         // for type: 'api'
  dataKey?: string                                          // dot-path to data: 'data.items'
  adapter?: 'default' | 'chart' | 'stat' | 'table' | ((raw: unknown) => unknown)
  params?: Record<string, unknown>                          // default params — merged with resolved filters
  mockData?: unknown                                        // for type: 'mock'
}
```

---

## WidgetShellProps

```ts
interface WidgetShellProps {
  title?: string
  subtitle?: string
  source?: string
  loading?: boolean
  error?: string
  actions?: ReactNode       // right slot of header (export, refresh buttons)
  footer?: ReactNode        // custom footer (pagination, total data row)
  children: ReactNode
}
```

---

## ChartOptions

```ts
interface ChartOptions {
  chartType: 'bar' | 'line' | 'pie' | 'gauge' | 'area'
  xKey?: string                    // key for x-axis labels
  yKey?: string                    // key for y-axis values
  seriesKey?: string               // key for series grouping (multiSeries)
  orientation?: 'vertical' | 'horizontal'   // bar chart only
  stacked?: boolean                // bar/area chart only
  multiSeries?: boolean
  smooth?: boolean                 // line/area only
  donut?: boolean                  // pie only
  showLegend?: boolean
  colors?: string[]
  // gauge only
  min?: number
  max?: number
  thresholds?: { value: number; label: string; color: string }[]
}
```

---

## StatOptions

```ts
interface StatOptions {
  layout: 'single' | 'proportion'
  value: number
  label?: string
  valueFormat?: 'number' | 'currency' | 'percent'  // default: 'number'
  breakdown?: StatBreakdownItem[]  // required when layout: 'proportion'
}

interface StatBreakdownItem {
  label: string
  value: number
  percentage: number
  color: string
}
```

---

## ListOptions

```ts
interface ListOptions {
  listType: 'progress' | 'alert' | 'checklist' | 'ranked'
  items: ListItem[]
  onCheck?: (index: number, checked: boolean) => void  // checklist only
}

// listType: 'progress'
interface ProgressListItem {
  label: string
  value: number
  max: number
  meta?: string
  color?: string
}

// listType: 'alert'
interface AlertListItem {
  severity: 'high' | 'medium' | 'low'
  text: string
  source?: string
}

// listType: 'checklist'
interface ChecklistItem {
  severity: 'high' | 'medium' | 'low'
  text: string
  checked: boolean
}

// listType: 'ranked'
interface RankedListItem {
  rank: number
  label: string
  value: number | string
  avatar?: string
}

type ListItem = ProgressListItem | AlertListItem | ChecklistItem | RankedListItem
```

---

## TableOptions

```ts
interface TableOptions {
  columns: TableColumn[]
  showFooter?: boolean
  showPagination?: boolean
  totalRows?: number
  source?: string
}

interface TableColumn {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  render?: (row: Record<string, unknown>) => ReactNode
}
```

---

## CardGridOptions

```ts
interface CardGridOptions {
  template: 'news' | 'statement'
  cols?: 2 | 3 | 4                // default: 2
  showSentiment?: boolean
}

// template: 'news'
interface NewsCardItem {
  title: string
  source: string
  sentiment?: 'positive' | 'neutral' | 'negative'
  publishedAt: string
  views?: number
  comments?: number
  imageUrl?: string
  url?: string
}

// template: 'statement'
interface StatementCardItem {
  name: string
  avatar?: string
  publishedAt: string
  text: string
  sentiment?: 'positive' | 'neutral' | 'negative'
  exposure?: number
  statements?: number
}
```

---

## WordCloudOptions

```ts
interface WordCloudOptions {
  labelKey: string             // key for the word label
  weightKey: string            // key for the word weight/size
  colorRange?: [string, string]  // [minColor, maxColor]
}
```

---

## DynamicWidgetProps (full config)

```ts
interface DynamicWidgetProps {
  id: string                           // widgetId — must match entry in widget-map
  widgetType: WidgetType
  title?: string
  subtitle?: string
  source?: string
  actions?: ReactNode
  dataSource: WidgetDataSource
  options: ChartOptions | StatOptions | ListOptions | TableOptions | CardGridOptions | WordCloudOptions
}
```

---

## Adapter Output Types

```ts
// chart.adapter output
interface ChartData {
  labels: string[]
  datasets: { label: string; data: number[]; color?: string }[]
}

// stat.adapter output
interface StatData {
  value: number
  breakdown?: StatBreakdownItem[]
}

// table.adapter output
interface TableData {
  rows: Record<string, unknown>[]
  total: number
}
```
