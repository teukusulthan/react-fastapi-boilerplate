import { toast } from 'sonner'

import { LoadingState } from '@/components/common/LoadingState'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Spinner } from '@/components/ui/spinner'

import { KitDemo, KitSection } from './KitSection'

export function FeedbackSection() {
  return (
    <KitSection id="feedback" title="Feedback" description="Inline alerts for page-level messages, toasts for action results, skeletons while loading.">
      <div className="grid gap-4 lg:grid-cols-2">
        <KitDemo title="Alerts" className="flex-col items-stretch">
          <Alert>
            <i className="ph ph-info" aria-hidden="true" />
            <AlertTitle>Heads up</AlertTitle>
            <AlertDescription>Maintenance is scheduled for Sunday 02:00 UTC.</AlertDescription>
          </Alert>
          <Alert variant="success">
            <i className="ph ph-check-circle" aria-hidden="true" />
            <AlertTitle>Changes saved</AlertTitle>
            <AlertDescription>Your profile is up to date.</AlertDescription>
          </Alert>
          <Alert variant="warning">
            <i className="ph ph-warning" aria-hidden="true" />
            <AlertTitle>Trial ends in 3 days</AlertTitle>
            <AlertDescription>Add a payment method to keep your workspace.</AlertDescription>
          </Alert>
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertTitle>Couldn&apos;t load data</AlertTitle>
            <AlertDescription>The server returned an error. Try again in a moment.</AlertDescription>
          </Alert>
        </KitDemo>
        <div className="grid gap-4">
          <KitDemo title="Toasts (sonner)">
            <Button variant="outline" onClick={() => toast.success('Project created', { description: 'You can invite people now.' })}>
              Success toast
            </Button>
            <Button variant="outline" onClick={() => toast.error('Could not save', { description: 'Check your connection and retry.' })}>
              Error toast
            </Button>
            <Button variant="outline" onClick={() => toast('Link copied')}>
              Plain toast
            </Button>
          </KitDemo>
          <KitDemo title="Progress & spinners" className="flex-col items-stretch">
            <Progress value={64} aria-label="Upload progress" />
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Spinner /> Inline spinner
            </div>
          </KitDemo>
          <KitDemo title="Skeleton (mirror the final layout)" className="flex-col items-stretch">
            <div className="flex items-center gap-3">
              <Skeleton className="size-10 rounded-full" />
              <div className="flex flex-1 flex-col gap-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-64 max-w-full" />
              </div>
            </div>
            <LoadingState label="Region loading state" className="min-h-24" />
          </KitDemo>
        </div>
      </div>
    </KitSection>
  )
}
