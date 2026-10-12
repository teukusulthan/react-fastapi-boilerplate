# data-ui Mapping — shadcn Migration Layer

## Rule

Every structural element MUST carry a `data-ui` attribute alongside its Tailwind utility classes. Never replace utility classes — always ADD `data-ui` as a co-existing attribute.

```html
<!-- ✅ CORRECT — utility classes + data-ui, semantic tokens, rounded-xl surface -->
<div class="bg-card text-card-foreground border border-border rounded-xl shadow-xs flex flex-col" data-ui="card">
  <div class="flex items-start justify-between gap-4 p-6 pb-0" data-ui="card-header">...</div>
  <div class="p-6" data-ui="card-content">...</div>
  <div class="flex items-center justify-end gap-2 border-t border-border px-6 py-4" data-ui="card-footer">...</div>
</div>

<!-- ❌ WRONG — utility classes removed -->
<div data-ui="card">

<!-- ❌ WRONG — canvas token on a card, square corners, no border -->
<div class="bg-background p-4" data-ui="card">
```

Use the shadcn semantic classes so the React conversion maps 1:1 (see `coding-rules.md` → Visual Direction).

## Mapping Table

| `data-ui` value | shadcn Component |
|---|---|
| `card` | `<Card>` |
| `card-header` | `<CardHeader>` |
| `card-content` | `<CardContent>` |
| `card-footer` | `<CardFooter>` |
| `card-title` | `<CardTitle>` |
| `card-description` | `<CardDescription>` |
| `btn-primary` | `<Button variant="default">` |
| `btn-secondary` | `<Button variant="secondary">` |
| `btn-outline` | `<Button variant="outline">` |
| `btn-ghost` | `<Button variant="ghost">` |
| `btn-destructive` | `<Button variant="destructive">` |
| `btn-icon` | `<Button size="icon">` |
| `input-field` | `<Input>` |
| `textarea-field` | `<Textarea>` |
| `select-field` | `<Select>` |
| `checkbox-field` | `<Checkbox>` |
| `switch-field` | `<Switch>` |
| `label-field` | `<Label>` |
| `form-item` | `<FormItem>` |
| `form-message` | `<FormMessage>` |
| `badge` | `<Badge>` |
| `badge-secondary` | `<Badge variant="secondary">` |
| `alert` | `<Alert>` |
| `alert-destructive` | `<Alert variant="destructive">` |
| `progress-bar` | `<Progress>` |
| `skeleton` | `<Skeleton>` |
| `separator` | `<Separator>` |
| `avatar` | `<Avatar>` |
| `tabs-root` | `<Tabs>` |
| `tab-trigger` | `<TabsTrigger>` |
| `tab-content` | `<TabsContent>` |
| `dialog` | `<Dialog>` |
| `dialog-content` | `<DialogContent>` |
| `dialog-header` | `<DialogHeader>` |
| `dialog-footer` | `<DialogFooter>` |
| `sheet` | `<Sheet>` |
| `popover` | `<Popover>` |
| `tooltip` | `<Tooltip>` |
| `dropdown-menu` | `<DropdownMenu>` |
| `nav-menu` | `<NavigationMenu>` |
| `breadcrumb` | `<Breadcrumb>` |
| `pagination` | `<Pagination>` |
| `accordion` | `<Accordion>` |
| `data-table` | `<Table>` |
| `table-head` | `<TableHead>` |
| `table-row` | `<TableRow>` |
| `table-cell` | `<TableCell>` |
| `sidebar` | `<Sidebar>` |

## Extra `data-*` for Props Mapping

Add these alongside `data-ui` to pre-declare shadcn props:

```html
<!-- variant & size hints -->
<button data-ui="btn-primary" data-variant="default" data-size="sm" class="...">Save</button>

<!-- state hints -->
<input data-ui="input-field" data-state="error" class="..." />
<div data-ui="alert-destructive" data-variant="destructive" class="...">

<!-- layout hints for complex components -->
<div data-ui="tabs-root" data-default-value="overview" class="...">
  <button data-ui="tab-trigger" data-value="overview" class="...">Overview</button>
  <div data-ui="tab-content" data-value="overview" class="...">...</div>
</div>
```

These attributes are stripped by the browser (no visual effect) but give the React converter exact props without guesswork.
