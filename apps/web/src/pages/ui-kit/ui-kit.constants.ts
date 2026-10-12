/** Static demo content for the dev-only UI kit page. */

export const UI_KIT_SECTIONS = [
  { id: 'foundations', label: 'Foundations' },
  { id: 'actions', label: 'Actions' },
  { id: 'forms', label: 'Forms' },
  { id: 'feedback', label: 'Feedback' },
  { id: 'overlays', label: 'Overlays' },
  { id: 'data', label: 'Data display' },
  { id: 'patterns', label: 'Patterns' },
] as const

export const COLOR_SWATCHES: readonly { name: string; className: string; token: string }[] = [
  { name: 'Background', className: 'bg-background', token: '--background' },
  { name: 'Card', className: 'bg-card', token: '--card' },
  { name: 'Muted', className: 'bg-muted', token: '--muted' },
  { name: 'Accent', className: 'bg-accent', token: '--accent' },
  { name: 'Primary', className: 'bg-primary', token: '--primary' },
  { name: 'Foreground', className: 'bg-foreground', token: '--foreground' },
  { name: 'Muted foreground', className: 'bg-muted-foreground', token: '--muted-foreground' },
  { name: 'Border', className: 'bg-border', token: '--border' },
  { name: 'Success', className: 'bg-success', token: '--success' },
  { name: 'Warning', className: 'bg-warning', token: '--warning' },
  { name: 'Info', className: 'bg-info', token: '--info' },
  { name: 'Destructive', className: 'bg-destructive', token: '--destructive' },
]

export const CHART_SWATCHES: readonly { name: string; className: string }[] = [
  { name: 'chart-1', className: 'bg-chart-1' },
  { name: 'chart-2', className: 'bg-chart-2' },
  { name: 'chart-3', className: 'bg-chart-3' },
  { name: 'chart-4', className: 'bg-chart-4' },
  { name: 'chart-5', className: 'bg-chart-5' },
]

export const TYPE_SCALE: readonly { label: string; className: string; sample: string }[] = [
  { label: 'Page title · text-2xl semibold', className: 'text-2xl font-semibold tracking-tight', sample: 'Projects' },
  { label: 'Section title · text-base semibold', className: 'text-base font-semibold', sample: 'Team members' },
  { label: 'Body · text-sm', className: 'text-sm', sample: 'Invite people to collaborate on this workspace.' },
  { label: 'Muted · text-sm muted', className: 'text-sm text-muted-foreground', sample: 'Last updated 3 hours ago' },
  { label: 'Caption · text-xs muted', className: 'text-xs text-muted-foreground', sample: 'Visible to admins only' },
  { label: 'Stat · text-2xl tabular-nums', className: 'text-2xl font-semibold tabular-nums', sample: '12,480' },
]

export const RADIUS_SAMPLES: readonly { label: string; className: string }[] = [
  { label: 'rounded-md · controls', className: 'rounded-md' },
  { label: 'rounded-lg · tiles', className: 'rounded-lg' },
  { label: 'rounded-xl · surfaces', className: 'rounded-xl' },
]

export interface DemoInvoice {
  id: string
  customer: string
  email: string
  amount: number
  status: 'paid' | 'pending' | 'overdue'
}

export const DEMO_INVOICES: DemoInvoice[] = [
  { id: 'INV-1042', customer: 'Northwind Traders', email: 'billing@northwind.dev', amount: 1280, status: 'paid' },
  { id: 'INV-1043', customer: 'Contoso Ltd', email: 'ap@contoso.dev', amount: 640.5, status: 'pending' },
  { id: 'INV-1044', customer: 'Fabrikam Inc', email: 'finance@fabrikam.dev', amount: 3120, status: 'overdue' },
  { id: 'INV-1045', customer: 'Tailspin Toys', email: 'accounts@tailspin.dev', amount: 89.99, status: 'paid' },
]

export const INVOICE_STATUS_TONE = { paid: 'success', pending: 'warning', overdue: 'destructive' } as const
