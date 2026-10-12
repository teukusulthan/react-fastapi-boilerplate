---
name: search-localdata
description: "Implement client-side fuzzy search on local/mock data in React apps using fuse.js. Use when asked to add search functionality, filter lists, implement fuzzy search, search across local arrays or mock data, or wire a search input to a data list. Covers useSearch hook, SearchInput component, multi-field/weighted search, highlight matches, debounced search."
---

# Search Localdata (fuse.js)

## Install

```bash
npm install fuse.js
```

## Quickstart

1. Create `src/hooks/use-search.ts` (Pattern 1 or 2 from references/patterns.md)
2. Create `src/components/common/SearchInput.tsx` (Pattern 5 — a shadcn `Input` with a `ph-magnifying-glass` icon; `components/ui/` is reserved for shadcn primitives). For lists rendered with `DataTable` (`src/modules/data-table/`), use the search slot of `DataTableToolbar` instead.
3. Wire hook + component in the feature

```tsx
// Feature component
const { query, setQuery, results } = useSearch(DATA_LIST, {
  keys: ['name', 'description'],
  threshold: 0.3,
  ignoreLocation: true,
})

return (
  <>
    <SearchInput value={query} onChange={setQuery} placeholder="Cari..." />
    {results.map(item => <ItemCard key={item.id} item={item} />)}
  </>
)
```

## Decision Tree

| Need | Use |
|------|-----|
| Simple list filter | Pattern 1 — `useSearch` |
| Show match highlights | Pattern 2 + Pattern 4 |
| Search fields have different importance | Pattern 3 (weighted keys) |
| List > 500 items or real-time typing lag | Pattern 6 (debounced) |

## Placement

- Hook → `src/hooks/use-search.ts` (generic) or `src/features/{domain}/hooks/use-{entity}-search.ts` (domain-specific)
- `SearchInput` → `src/components/common/SearchInput.tsx` (generic pattern composed from the shadcn `Input`; visual rules: [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md))
- Domain-specific search wrapper → `src/features/{domain}/{feature}/components/`

## References

- **[fusejs-api.md](references/fusejs-api.md)** — Full options, methods, result shape, extended operators, logical query
- **[patterns.md](references/patterns.md)** — All 6 patterns: basic hook, with highlights, weighted, highlight renderer, SearchInput component, debounced

Read `references/fusejs-api.md` when you need option details or logical query syntax.
Read `references/patterns.md` when implementing any pattern — copy and adapt directly.

## Key Rules

- Always use `ignoreLocation: true` for searching across full strings (not just near position 0)
- Default `threshold: 0.3` — tighten to `0.2` for precise, loosen to `0.4–0.5` for forgiving
- Return `list` unchanged when `query` is empty — never show empty results on blank input
- Memoize `new Fuse(...)` with `useMemo` — never construct in render
- `minMatchCharLength: 2` prevents noise from single-character matches
