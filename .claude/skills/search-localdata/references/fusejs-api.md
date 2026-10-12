# Fuse.js API Reference

## Install

```bash
npm install fuse.js
```

## Constructor

```ts
const fuse = new Fuse(list, options)
```

## Key Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `keys` | `string[] \| WeightedKey[]` | — | Fields to search. Required for object lists. |
| `threshold` | `number` | `0.6` | Match quality cutoff (0=exact, 1=anything). Recommended: `0.3`–`0.4` for UX. |
| `distance` | `number` | `100` | Max distance from expected location. |
| `minMatchCharLength` | `number` | `1` | Ignore matches shorter than this. |
| `shouldSort` | `boolean` | `true` | Sort results by score. |
| `includeScore` | `boolean` | `false` | Include `score` in results. |
| `includeMatches` | `boolean` | `false` | Include match indices for highlight. |
| `useExtendedSearch` | `boolean` | `false` | Enable extended operators (see below). |
| `ignoreLocation` | `boolean` | `false` | Search entire string, not just near `location`. |
| `isCaseSensitive` | `boolean` | `false` | Case-sensitive matching. |
| `findAllMatches` | `boolean` | `false` | Continue past first match. |
| `tokenize` | `boolean` | `false` | Tokenize pattern into individual words. |
| `matchAllTokens` | `boolean` | `false` | All tokens must match. |

## Weighted Keys

```ts
const options = {
  keys: [
    { name: 'title', weight: 2 },   // higher = more important
    { name: 'description', weight: 1 }
  ]
}
```

## Nested Keys

```ts
keys: ['user.name', 'user.email', 'tags.label']
```

## Methods

```ts
fuse.search(query)           // returns FuseResult[]
fuse.search(query, { limit: 10 })  // limit results
fuse.add(item)               // add item to index
fuse.remove(item => item.id === id)  // remove by predicate
fuse.setCollection(newList)  // replace entire list
```

## Result Shape

```ts
interface FuseResult<T> {
  item: T
  refIndex: number
  score?: number      // 0=perfect match, 1=no match (if includeScore: true)
  matches?: FuseResultMatch[]  // (if includeMatches: true)
}
```

## Extended Search Operators (useExtendedSearch: true)

| Token | Description | Example |
|-------|-------------|---------|
| `jscript` | fuzzy match | `jscript` |
| `=jscript` | exact match | `=jscript` |
| `'jscript` | includes | `'jscript` |
| `!jscript` | inverse fuzzy | `!jscript` |
| `^jscript` | prefix exact | `^jscript` |
| `!^jscript` | inverse prefix | `!^jscript` |
| `.jscript$` | suffix exact | `.jscript$` |
| `!.jscript$` | inverse suffix | `!.jscript$` |

## Logical Query

```ts
fuse.search({
  $and: [
    { title: 'javascript' },
    { $or: [{ author: 'crockford' }, { tags: 'es6' }] }
  ]
})
```
