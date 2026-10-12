import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'

import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/utils/cn'

/**
 * shadcn Field — layout primitives for forms that are not driven by react-hook-form (`form.tsx` is the
 * RHF binding). FieldSet > FieldLegend > FieldGroup > Field (FieldLabel, control, FieldDescription, FieldError).
 */
const FieldSet = React.forwardRef<HTMLFieldSetElement, React.FieldsetHTMLAttributes<HTMLFieldSetElement>>(({ className, ...props }, ref) => (
  <fieldset
    ref={ref}
    data-slot="field-set"
    className={cn('flex flex-col gap-6 has-[>[data-slot=checkbox-group]]:gap-3 has-[>[data-slot=radio-group]]:gap-3', className)}
    {...props}
  />
))
FieldSet.displayName = 'FieldSet'

const FieldLegend = React.forwardRef<HTMLLegendElement, React.HTMLAttributes<HTMLLegendElement> & { variant?: 'legend' | 'label' }>(
  ({ className, variant = 'legend', ...props }, ref) => (
    <legend
      ref={ref}
      data-slot="field-legend"
      data-variant={variant}
      className={cn('mb-3 font-medium data-[variant=label]:text-sm data-[variant=legend]:text-base', className)}
      {...props}
    />
  ),
)
FieldLegend.displayName = 'FieldLegend'

const FieldGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="field-group"
    className={cn(
      'group/field-group @container/field-group flex w-full flex-col gap-6 data-[slot=checkbox-group]:gap-3 [&>[data-slot=field-group]]:gap-4',
      className,
    )}
    {...props}
  />
))
FieldGroup.displayName = 'FieldGroup'

const fieldVariants = cva('group/field flex w-full gap-2 data-[invalid=true]:text-destructive', {
  variants: {
    orientation: {
      vertical: 'flex-col [&>*]:w-full [&>.sr-only]:w-auto',
      horizontal: [
        'flex-row items-center gap-3',
        '[&>[data-slot=field-label]]:flex-auto',
        'has-[>[data-slot=field-content]]:items-start has-[>[data-slot=field-content]]:[&>[role=checkbox],[role=radio]]:mt-px',
      ],
      responsive: [
        'flex-col @md/field-group:flex-row @md/field-group:items-center [&>*]:w-full @md/field-group:[&>*]:w-auto [&>.sr-only]:w-auto',
        '@md/field-group:[&>[data-slot=field-label]]:flex-auto',
        '@md/field-group:has-[>[data-slot=field-content]]:items-start @md/field-group:has-[>[data-slot=field-content]]:[&>[role=checkbox],[role=radio]]:mt-px',
      ],
    },
  },
  defaultVariants: {
    orientation: 'vertical',
  },
})

const Field = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof fieldVariants>>(
  ({ className, orientation = 'vertical', ...props }, ref) => (
    <div ref={ref} role="group" data-slot="field" data-orientation={orientation} className={cn(fieldVariants({ orientation }), className)} {...props} />
  ),
)
Field.displayName = 'Field'

const FieldContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="field-content" className={cn('group/field-content flex flex-1 flex-col gap-1 leading-snug', className)} {...props} />
))
FieldContent.displayName = 'FieldContent'

const FieldLabel = React.forwardRef<React.ComponentRef<typeof Label>, React.ComponentPropsWithoutRef<typeof Label>>(({ className, ...props }, ref) => (
  <Label
    ref={ref}
    data-slot="field-label"
    className={cn(
      'group/field-label peer/field-label flex w-fit gap-2 leading-snug group-data-[disabled=true]/field:opacity-50',
      'has-[>[data-slot=field]]:w-full has-[>[data-slot=field]]:flex-col has-[>[data-slot=field]]:rounded-lg has-[>[data-slot=field]]:border [&>*]:data-[slot=field]:p-4',
      'has-data-[state=checked]:border-primary has-data-[state=checked]:bg-primary/5 dark:has-data-[state=checked]:bg-primary/10',
      className,
    )}
    {...props}
  />
))
FieldLabel.displayName = 'FieldLabel'

const FieldTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="field-label"
    className={cn('flex w-fit items-center gap-2 text-sm leading-snug font-medium group-data-[disabled=true]/field:opacity-50', className)}
    {...props}
  />
))
FieldTitle.displayName = 'FieldTitle'

const FieldDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    data-slot="field-description"
    className={cn(
      'text-sm leading-normal font-normal text-muted-foreground group-has-[[data-orientation=horizontal]]/field:text-balance',
      '[&>a]:underline [&>a]:underline-offset-4 [&>a:hover]:text-primary',
      className,
    )}
    {...props}
  />
))
FieldDescription.displayName = 'FieldDescription'

const FieldSeparator = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ children, className, ...props }, ref) => (
  <div ref={ref} data-slot="field-separator" data-content={!!children} className={cn('relative -my-2 h-5 text-sm', className)} {...props}>
    <Separator className="absolute inset-0 top-1/2" />
    {children && (
      <span className="relative mx-auto block w-fit bg-background px-2 text-muted-foreground" data-slot="field-separator-content">
        {children}
      </span>
    )}
  </div>
))
FieldSeparator.displayName = 'FieldSeparator'

interface FieldErrorProps extends React.HTMLAttributes<HTMLDivElement> {
  errors?: Array<{ message?: string } | undefined>
}

const FieldError = React.forwardRef<HTMLDivElement, FieldErrorProps>(({ className, children, errors, ...props }, ref) => {
  const content = React.useMemo(() => {
    if (children) return children
    if (!errors?.length) return null
    const unique = [...new Map(errors.map((error) => [error?.message, error])).values()]
    if (unique.length === 1) return unique[0]?.message
    return <ul className="ml-4 flex list-disc flex-col gap-1">{unique.map((error, index) => error?.message && <li key={index}>{error.message}</li>)}</ul>
  }, [children, errors])

  if (!content) return null

  return (
    <div ref={ref} role="alert" data-slot="field-error" className={cn('text-sm font-normal text-destructive', className)} {...props}>
      {content}
    </div>
  )
})
FieldError.displayName = 'FieldError'

export { Field, FieldContent, FieldDescription, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSeparator, FieldSet, FieldTitle }
