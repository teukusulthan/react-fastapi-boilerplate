# ECharts Integration Patterns

## When to Use ECharts

Use ECharts **only** for genuine data visualization:
- Line / area charts (time series, trends)
- Bar charts (comparisons, distributions)
- Pie / donut charts (composition)
- Gauge charts (single metric with range)
- Radar charts (multi-axis comparison)
- Scatter / heatmap (correlation, density)

**Do NOT use ECharts for:** metric cards, status badges, tables, progress bars (use CSS instead).

## CDN Include

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

## Initialization Pattern

```html
<div id="chart-line" style="height: 280px;"></div>
<script>
  const chart = echarts.init(document.getElementById('chart-line'), null, {
    renderer: 'canvas'
  });
  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
</script>
```

## Theme Colors (use CSS variables)

> **Warning — CSS variable chains + oklch:** ECharts only accepts `hex`, `rgb`, `rgba`, `hsl`.  
> Design tokens are often chained (`--border-primary: var(--base-neutral-200)`) and may use `oklch(...)`.  
> `getPropertyValue` returns the raw string (e.g. `var(--base-neutral-200)`) — canvas `fillStyle` cannot resolve it.  
> Always use `resolveColor()` below, which resolves through a real DOM element.

### resolveColor helper (required — handles chained vars and oklch)

```js
/**
 * Resolves any CSS variable (including chained vars like var(--a) → var(--b) → oklch)
 * to an rgb() string that ECharts can parse, by using the browser's own CSS engine.
 */
function resolveColor(varName) {
  const el = document.createElement('div');
  el.style.color = `var(${varName})`;
  document.body.appendChild(el);
  const color = getComputedStyle(el).color;
  document.body.removeChild(el);
  return color;
}
```

### Reading tokens with resolution

Chart colors come from two token groups:

| Purpose | Token | Example |
|---------|-------|---------|
| Series colors (up to 5) | `--chart-1` … `--chart-5` | solid line, bar, pie slice |
| Gradient / shade variants | `--base-{type}-50` … `900` | area fill, hover highlight |
| UI chrome | `--font-secondary`, `--border-primary`, `--bg-secondary` | axis, tooltip, grid |

```js
// cssVar resolves CSS variable by name — always pass the var name, not the value
function cssVar(name) { return resolveColor(name); }

// Series palette — use for color[] arrays
const chart1 = cssVar('--chart-1');
const chart2 = cssVar('--chart-2');
const chart3 = cssVar('--chart-3');
const chart4 = cssVar('--chart-4');
const chart5 = cssVar('--chart-5');

// Shade scale — use for gradients, area fills, emphasis states
// Replace {type} with: primary | secondary | tertiary | quaternary | quinary
// Replace {n} with: 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900
const primary300 = cssVar('--base-primary-300');   // lighter — area fill top
const primary500 = cssVar('--base-primary-500');   // base
const primary700 = cssVar('--base-primary-700');   // darker — hover / emphasis

// Non-color tokens (no resolution needed)
const fontSecondary = style.getPropertyValue('--font-secondary').trim();
const borderPrimary = cssVar('--border-primary');
const bgSecondary   = cssVar('--bg-secondary');
const fontPrimary   = cssVar('--text-color-primary');  // use for tooltip textStyle.color — oklch-safe
```

### Alpha variant from a resolved color

`primary + '40'` (hex alpha suffix) does **not** work on `rgb(...)` strings.  
Use this helper instead:

```js
function withAlpha(rgbColor, alpha) {
  // rgbColor is already "rgb(r,g,b)" from resolveColor
  return rgbColor.replace('rgb(', 'rgba(').replace(')', `,${alpha})`);
}

// Usage in areaStyle gradient:
colorStops: [
  { offset: 0, color: withAlpha(primary, 0.33) },
  { offset: 1, color: withAlpha(primary, 0) }
]
```

## Base Option Template (theme-agnostic — colors come from CSS variables)

```js
const baseOption = {
  backgroundColor: 'transparent',
  grid: { left: 48, right: 16, top: 24, bottom: 32, containLabel: true },
  textStyle: { fontFamily: 'Inter, sans-serif' /* use the DESIGN.md font when a design/ theme is active */, fontSize: 12, color: fontSecondary },
  tooltip: {
    trigger: 'axis',
    backgroundColor: bgSecondary,
    borderColor: borderPrimary,
    borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 12 },
    axisPointer: { lineStyle: { color: borderPrimary } }
  },
  xAxis: {
    type: 'category',
    axisLine: { lineStyle: { color: borderPrimary } },
    axisTick: { show: false },
    axisLabel: { color: fontSecondary, fontSize: 11 },
    splitLine: { show: false }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: fontSecondary, fontSize: 11 },
    splitLine: { lineStyle: { color: borderPrimary, type: 'dashed' } }
  }
};
```

## Line Chart Example

```js
const option = {
  ...baseOption,
  color: [chart1],
  series: [{
    type: 'line',
    data: [120, 200, 150, 80, 210, 190, 330],
    smooth: true,
    lineStyle: { width: 2, color: chart1 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
      colorStops: [
        { offset: 0, color: withAlpha(chart1, 0.25) },
        { offset: 1, color: withAlpha(chart1, 0) }
      ]
    }},
    symbol: 'circle', symbolSize: 6,
    itemStyle: { color: chart1, borderColor: '#fff', borderWidth: 2 }
  }]
};
```

## Bar Chart Example

```js
const option = {
  ...baseOption,
  color: [chart1],
  series: [{
    type: 'bar',
    data: [120, 200, 150, 80, 210],
    barWidth: '40%',
    itemStyle: { color: chart1 }
  }]
};
```

## Gauge Chart Example

```js
const option = {
  backgroundColor: 'transparent',
  series: [{
    type: 'gauge',
    radius: '85%',
    startAngle: 200, endAngle: -20,
    min: 0, max: 100,
    axisLine: {
      lineStyle: { width: 12,
        color: [[0.3, success], [0.7, warning], [1, error]]
      }
    },
    pointer: { itemStyle: { color: 'auto' } },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: fontSecondary, fontSize: 10 },
    detail: { valueAnimation: true, fontSize: 28, fontWeight: 'bold',
      color: primary, formatter: '{value}%' },
    data: [{ value: 65, name: 'Utilization' }]
  }]
};
```

## Area Chart Example (standalone)

```js
const option = {
  ...baseOption,
  color: [chart1],
  series: [{
    type: 'line',
    data: [80, 140, 110, 200, 160, 240, 180],
    smooth: true,
    lineStyle: { width: 2, color: chart1 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: withAlpha(chart1, 0.33) },
          { offset: 1, color: withAlpha(chart1, 0) }
        ]
      }
    },
    symbol: 'none'
  }]
};
```

## Multi-Series Line Chart

```js
const option = {
  ...baseOption,
  color: [chart1, chart2, chart3],
  legend: {
    top: 0, right: 0,
    textStyle: { color: fontSecondary, fontSize: 11 }
  },
  series: [
    { name: 'Series A', type: 'line', data: [120, 200, 150, 80, 210, 190, 330], smooth: true },
    { name: 'Series B', type: 'line', data: [60,  100, 130, 90, 140, 160, 200], smooth: true },
    { name: 'Series C', type: 'line', data: [30,   50,  80, 40,  90, 110, 140], smooth: true }
  ]
};
```

## Pie / Donut Chart Example

```js
const option = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',   // pie/donut uses 'item', not 'axis'
    backgroundColor: bgSecondary,
    borderColor: borderPrimary,
    borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 12 }
  },
  legend: {
    bottom: 0,
    textStyle: { color: fontSecondary, fontSize: 11 }
  },
  series: [{
    type: 'pie',
    radius: ['45%', '70%'],   // remove inner radius for full pie (e.g. ['0%', '70%'])
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
    labelLine: { show: false },
    color: [chart1, chart2, chart3],
    data: [
      { value: 40, name: 'Category A' },
      { value: 30, name: 'Category B' },
      { value: 30, name: 'Category C' }
    ]
  }]
};
```

## Stacked Bar Chart Example

```js
const option = {
  ...baseOption,
  color: [chart1, chart2, chart3],
  legend: {
    top: 0, right: 0,
    textStyle: { color: fontSecondary, fontSize: 11 }
  },
  series: [
    {
      name: 'Series A', type: 'bar', stack: 'total',
      data: [120, 200, 150, 80, 210],
      barWidth: '40%',
      itemStyle: { color: chart1 }
    },
    {
      name: 'Series B', type: 'bar', stack: 'total',
      data: [60, 100, 80, 50, 90],
      itemStyle: { color: chart2 }
    }
  ]
};
```

## Horizontal Bar Chart Example

```js
const option = {
  backgroundColor: 'transparent',
  grid: { left: 100, right: 24, top: 12, bottom: 12, containLabel: true },
  textStyle: { fontFamily: 'Inter, sans-serif' /* use the DESIGN.md font when a design/ theme is active */, fontSize: 12, color: fontSecondary },
  tooltip: {
    trigger: 'axis',
    backgroundColor: bgSecondary, borderColor: borderPrimary, borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 12 }
  },
  xAxis: {
    type: 'value',
    axisLine: { show: false }, axisTick: { show: false },
    axisLabel: { color: fontSecondary, fontSize: 11 },
    splitLine: { lineStyle: { color: borderPrimary, type: 'dashed' } }
  },
  yAxis: {
    type: 'category',
    data: ['Label A', 'Label B', 'Label C', 'Label D', 'Label E'],
    axisLine: { lineStyle: { color: borderPrimary } },
    axisTick: { show: false },
    axisLabel: { color: fontSecondary, fontSize: 11 }
  },
  series: [{
    type: 'bar',
    data: [210, 180, 150, 120, 80],
    barWidth: '50%',
    itemStyle: { color: primary }
  }]
};
```

## Radar Chart Example

```js
const option = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    backgroundColor: bgSecondary, borderColor: borderPrimary, borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 12 }
  },
  radar: {
    indicator: [
      { name: 'Metric A', max: 100 },
      { name: 'Metric B', max: 100 },
      { name: 'Metric C', max: 100 },
      { name: 'Metric D', max: 100 },
      { name: 'Metric E', max: 100 }
    ],
    axisLine: { lineStyle: { color: borderPrimary } },
    splitLine: { lineStyle: { color: borderPrimary } },
    splitArea: { show: false },
    axisName: { color: fontSecondary, fontSize: 11 }
  },
  series: [{
    type: 'radar',
    data: [{
      value: [80, 60, 75, 90, 55],
      name: 'Score',
      lineStyle: { color: primary, width: 2 },
      areaStyle: { color: primary + '33' },
      itemStyle: { color: primary }
    }]
  }]
};
```

## Multi-Chart Page Pattern

Wrap all chart initialization in a function so it can be called again on theme switch.  
This is required because CSS variable values are resolved once at call time — they don't update reactively.

```js
// Chart element IDs — used for dispose on reinit
const CHART_IDS = ['chart-line', 'chart-pie' /* add all ids */];

function initCharts() {
  // Dispose existing instances before reinit (required for theme switch)
  CHART_IDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) { const inst = echarts.getInstanceByDom(el); if (inst) inst.dispose(); }
  });

  function cssVar(name) { return resolveColor(name); }

  const c1 = cssVar('--chart-1');
  const c2 = cssVar('--chart-2');
  const c3 = cssVar('--chart-3');
  const c4 = cssVar('--chart-4');
  const c5 = cssVar('--chart-5');
  const fontSecondary = cssVar('--font-secondary');
  const fontPrimary   = cssVar('--text-color-primary');
  const borderPrimary = cssVar('--border-primary');
  const bgSecondary   = cssVar('--bg-secondary');

  const lineChart = echarts.init(document.getElementById('chart-line'));
  lineChart.setOption({ /* line option */ });

  const pieChart = echarts.init(document.getElementById('chart-pie'));
  pieChart.setOption({ /* pie option */ });

  window.__charts = [lineChart, pieChart /* add all instances */];
}

document.addEventListener('DOMContentLoaded', () => {
  initCharts();

  // Re-resolve colors and reinit charts when theme class toggles
  window.__reinitCharts = initCharts;

  window.addEventListener('resize', () => {
    (window.__charts || []).forEach(c => c.resize());
  });
});
```

In the theme toggle handler, call reinit after toggling the class:

```js
btn.addEventListener('click', function () {
  document.documentElement.classList.toggle('dark');
  // ... other toggle logic ...
  if (window.__reinitCharts) window.__reinitCharts();
});
```

## Resize on Window Change

Always add resize listener for responsive behavior:

```js
window.addEventListener('resize', () => chart.resize());
```

---

## Mini Charts (Analytics Dashboard)

Mini charts live inside metric cards. Use a small fixed container (height 48–80px), no axes, no tooltip, no legend — pure visual indicator.

### Common mini chart types in analytics dashboards

| Type | Use case |
|------|----------|
| Sparkline (line) | Trend over time inside a KPI card |
| Mini area | Revenue / traffic trend with fill |
| Mini bar | Daily/weekly distribution in a card |
| Mini donut | Completion ratio, usage share |
| Progress ring (gauge) | Single percentage, circular fill |
| Bullet bar (horizontal bar) | Target vs actual in a narrow row |

---

### Sparkline (Trend Line, no axes)

```html
<div id="mini-sparkline" style="height:48px; width:120px;"></div>
```

```js
const sparkline = echarts.init(document.getElementById('mini-sparkline'), null, { renderer: 'canvas' });
sparkline.setOption({
  backgroundColor: 'transparent',
  grid: { left: 0, right: 0, top: 4, bottom: 4 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: bgSecondary, borderColor: borderPrimary, borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 11 },
    axisPointer: { lineStyle: { color: borderPrimary } }
  },
  xAxis: { type: 'category', show: false, data: ['M','T','W','T','F','S','S'] },
  yAxis: { type: 'value', show: false },
  series: [{
    type: 'line',
    data: [30, 55, 42, 70, 60, 85, 78],
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2, color: chart1 }
  }]
});
```

---

### Mini Area Chart (trend with fill)

```html
<div id="mini-area" style="height:60px; width:160px;"></div>
```

```js
const miniArea = echarts.init(document.getElementById('mini-area'), null, { renderer: 'canvas' });
miniArea.setOption({
  backgroundColor: 'transparent',
  grid: { left: 0, right: 0, top: 4, bottom: 4 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: bgSecondary, borderColor: borderPrimary, borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 11 },
    axisPointer: { lineStyle: { color: borderPrimary } }
  },
  xAxis: { type: 'category', show: false, data: ['1','2','3','4','5','6','7'] },
  yAxis: { type: 'value', show: false },
  series: [{
    type: 'line',
    data: [120, 200, 150, 240, 180, 280, 210],
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2, color: chart1 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: withAlpha(chart1, 0.33) },
          { offset: 1, color: withAlpha(chart1, 0) }
        ]
      }
    }
  }]
});
```

---

### Mini Bar Chart (distribution inside card)

```html
<div id="mini-bar" style="height:60px; width:120px;"></div>
```

```js
const miniBar = echarts.init(document.getElementById('mini-bar'), null, { renderer: 'canvas' });
miniBar.setOption({
  backgroundColor: 'transparent',
  grid: { left: 0, right: 0, top: 4, bottom: 4 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: bgSecondary, borderColor: borderPrimary, borderWidth: 1,
    textStyle: { color: fontPrimary, fontSize: 11 },
    axisPointer: { lineStyle: { color: borderPrimary } }
  },
  xAxis: { type: 'category', show: false, data: ['M','T','W','T','F','S','S'] },
  yAxis: { type: 'value', show: false },
  series: [{
    type: 'bar',
    data: [
      { value: 40, itemStyle: { color: chart1 } },
      { value: 65, itemStyle: { color: chart1 } },
      { value: 55, itemStyle: { color: chart1 } },
      { value: 80, itemStyle: { color: cssVar('--base-primary-400') } }, // highlight peak — lighter shade
      { value: 70, itemStyle: { color: chart1 } },
      { value: 45, itemStyle: { color: chart1 } },
      { value: 60, itemStyle: { color: chart1 } }
    ],
    barWidth: '55%',
    barCategoryGap: '20%',
    itemStyle: { borderRadius: [2, 2, 0, 0] }
  }]
});
```

---

### Mini Donut (completion / share ratio)

```html
<div id="mini-donut" style="height:80px; width:80px;"></div>
```

```js
const miniDonut = echarts.init(document.getElementById('mini-donut'), null, { renderer: 'canvas' });
miniDonut.setOption({
  backgroundColor: 'transparent',
  series: [{
    type: 'pie',
    radius: ['60%', '85%'],
    center: ['50%', '50%'],
    silent: true,         // disable hover interaction
    label: { show: false },
    labelLine: { show: false },
    data: [
      { value: 72, itemStyle: { color: chart1 } },
      { value: 28, itemStyle: { color: withAlpha(chart1, 0.13) } }
    ]
  }]
});
```

Pair with a centered text overlay using absolute positioning:

```html
<div style="position:relative; width:80px; height:80px;">
  <div id="mini-donut" style="width:80px; height:80px;"></div>
  <span style="position:absolute; inset:0; display:flex; align-items:center;
               justify-content:center; font-size:13px; font-weight:700;
               color:var(--font-primary);">72%</span>
</div>
```

---

### Progress Ring (single gauge, circular)

```html
<div id="mini-ring" style="height:80px; width:80px;"></div>
```

```js
const miniRing = echarts.init(document.getElementById('mini-ring'), null, { renderer: 'canvas' });
miniRing.setOption({
  backgroundColor: 'transparent',
  series: [{
    type: 'gauge',
    radius: '90%',
    startAngle: 90, endAngle: -270,   // full-circle progress
    min: 0, max: 100,
    progress: { show: true, width: 8, itemStyle: { color: chart1 } },
    axisLine: { lineStyle: { width: 8, color: [[1, withAlpha(chart1, 0.13)]] } },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { show: false },
    pointer: { show: false },
    detail: {
      valueAnimation: true,
      offsetCenter: [0, 0],
      fontSize: 14, fontWeight: 'bold',
      color: 'var(--font-primary)',
      formatter: '{value}%'
    },
    data: [{ value: 68 }]
  }]
});
```

---

### Bullet Bar (target vs actual, horizontal)

```html
<div id="mini-bullet" style="height:40px; width:200px;"></div>
```

```js
const miniBullet = echarts.init(document.getElementById('mini-bullet'), null, { renderer: 'canvas' });
miniBullet.setOption({
  backgroundColor: 'transparent',
  grid: { left: 0, right: 0, top: 8, bottom: 8 },
  xAxis: { type: 'value', show: false, max: 100 },
  yAxis: { type: 'category', show: false, data: [''] },
  series: [
    {
      // background track
      type: 'bar', data: [100], barWidth: 8,
      itemStyle: { color: withAlpha(chart1, 0.13), borderRadius: 4 },
      silent: true, z: 1
    },
    {
      // actual value
      type: 'bar', data: [73], barWidth: 8,
      itemStyle: { color: chart1, borderRadius: 4 },
      z: 2
    },
    {
      // target marker (markLine alternative — use scatter)
      type: 'scatter', data: [[85, 0]],
      symbol: 'rect', symbolSize: [3, 16],
      itemStyle: { color: cssVar('--base-warning-500') },
      z: 3
    }
  ]
});
```

---

### Mini Chart Layout in a Metric Card

Typical card structure pairing a stat with a sparkline:

```html
<div class="card" style="display:flex; justify-content:space-between; align-items:flex-end;
     padding:16px; background:var(--bg-secondary); border:1px solid var(--border-primary);
     border-radius:8px;">
  <div>
    <p style="margin:0; font-size:12px; color:var(--font-secondary);">Total Revenue</p>
    <p style="margin:4px 0 0; font-size:24px; font-weight:700; color:var(--font-primary);">$48,250</p>
    <p style="margin:4px 0 0; font-size:11px; color:var(--base-success-500);">↑ 12.4% vs last month</p>
  </div>
  <div id="card-sparkline" style="height:48px; width:120px; flex-shrink:0;"></div>
</div>
```

---

### Mini Chart Sizing Reference

| Container width | Container height | Recommended type |
|----------------|-----------------|-----------------|
| 80–120px | 48px | Sparkline, mini area |
| 80px × 80px | square | Mini donut, progress ring |
| 120–160px | 56–72px | Mini bar |
| 180–240px | 40px | Bullet bar |
