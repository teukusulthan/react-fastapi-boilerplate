# Search Localdata — Patterns

## Pattern 1: useSearch Hook (standard)

```ts
// src/hooks/use-search.ts
import Fuse, { IFuseOptions } from 'fuse.js'
import { useMemo, useState } from 'react'

export function useSearch<T>(list: T[], options: IFuseOptions<T>) {
  const [query, setQuery] = useState('')

  const fuse = useMemo(() => new Fuse(list, options), [list, options])

  const results = useMemo(() => {
    if (!query.trim()) return list
    return fuse.search(query).map(r => r.item)
  }, [fuse, query, list])

  return { query, setQuery, results }
}
```

**Usage:**

```tsx
const { query, setQuery, results } = useSearch(PRODUCTS, {
  keys: ['name', 'description'],
  threshold: 0.3,
  ignoreLocation: true,
})
```

---

## Pattern 2: useSearch with Score + Highlight Support

```ts
import Fuse, { IFuseOptions, FuseResult } from 'fuse.js'
import { useMemo, useState } from 'react'

export function useSearch<T>(list: T[], options: IFuseOptions<T>) {
  const [query, setQuery] = useState('')

  const fuse = useMemo(
    () => new Fuse(list, { includeScore: true, includeMatches: true, ...options }),
    [list, options]
  )

  const results: FuseResult<T>[] = useMemo(() => {
    if (!query.trim()) return list.map((item, i) => ({ item, refIndex: i }))
    return fuse.search(query)
  }, [fuse, query, list])

  return { query, setQuery, results }
}
```

---

## Pattern 3: Multi-field Weighted Search

```ts
const options: IFuseOptions<Product> = {
  keys: [
    { name: 'name', weight: 3 },
    { name: 'category', weight: 2 },
    { name: 'description', weight: 1 },
  ],
  threshold: 0.3,
  ignoreLocation: true,
  minMatchCharLength: 2,
}
```

---

## Pattern 4: Highlight Match Characters

```tsx
function highlightMatch(text: string, indices: readonly [number, number][]): string {
  let result = ''
  let lastIndex = 0
  for (const [start, end] of indices) {
    result += text.slice(lastIndex, start)
    result += `<mark>${text.slice(start, end + 1)}</mark>`
    lastIndex = end + 1
  }
  result += text.slice(lastIndex)
  return result
}

// In component:
const match = result.matches?.find(m => m.key === 'name')
if (match?.indices) {
  const highlighted = highlightMatch(item.name, match.indices)
  return <span dangerouslySetInnerHTML={{ __html: highlighted }} />
}
```

---

## Pattern 5: SearchInput Component

> Visual rules: `reactjs-ui-design`. For table lists, `DataTableToolbar` (`@/modules/data-table`) already
> renders the search input — use this only for standalone local-search UI. Domain-agnostic, so it lives
> in `src/components/common/` (not `components/ui/`, which is reserved for shadcn primitives).

```tsx
// src/components/common/SearchInput.tsx
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/utils/cn'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchInput({ value, onChange, placeholder = 'Search…', className }: SearchInputProps) {
  return (
    <div className={cn('relative w-full max-w-sm', className)}>
      <i className="ph ph-magnifying-glass pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-base leading-none text-muted-foreground" aria-hidden="true" />
      <Input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="pr-9 pl-9"
      />
      {value && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Clear search"
          onClick={() => onChange('')}
          className="absolute top-1/2 right-1 size-7 -translate-y-1/2 text-muted-foreground"
        >
          <i className="ph ph-x" aria-hidden="true" />
        </Button>
      )}
    </div>
  )
}
```

Icons are Phosphor (`lucide-react` is not allowed in this app — see `reactjs-icon`).

---

## Pattern 6: Debounced Search (for large lists)

```ts
import { useEffect, useState, useRef } from 'react'

export function useDebouncedSearch<T>(list: T[], options: IFuseOptions<T>, delay = 200) {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), delay)
    return () => clearTimeout(timer)
  }, [query, delay])

  const fuse = useMemo(() => new Fuse(list, options), [list, options])

  const results = useMemo(() => {
    if (!debouncedQuery.trim()) return list
    return fuse.search(debouncedQuery).map(r => r.item)
  }, [fuse, debouncedQuery, list])

  return { query, setQuery, results, isDebouncing: query !== debouncedQuery }
}
```

---

## Recommended Options by Use Case

| Use Case | `threshold` | `ignoreLocation` | `keys` |
|----------|-------------|-----------------|--------|
| Short labels / names | `0.3` | `true` | `['name']` |
| Long descriptions | `0.4` | `true` | weighted |
| Exact-ish search | `0.2` | `false` | — |
| Broad/forgiving | `0.5` | `true` | — |
