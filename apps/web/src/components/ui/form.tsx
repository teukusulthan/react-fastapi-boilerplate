import { type Label as LabelPrimitive, Slot } from 'radix-ui'
import * as React from 'react'
import { Controller, FormProvider, useFormContext, useFormState, type ControllerProps, type FieldPath, type FieldValues } from 'react-hook-form'

import { Label } from '@/components/ui/label'
import { cn } from '@/utils/cn'

const Form = FormProvider

interface FormFieldContextValue<TFieldValues extends FieldValues = FieldValues, TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>> {
  name: TName
}

const FormFieldContext = React.createContext<FormFieldContextValue | null>(null)

const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  TTransformedValues = TFieldValues,
>({
  ...props
}: ControllerProps<TFieldValues, TName, TTransformedValues>) => (
  <FormFieldContext.Provider value={{ name: props.name }}>
    <Controller {...props} />
  </FormFieldContext.Provider>
)

interface FormItemContextValue {
  id: string
}

const FormItemContext = React.createContext<FormItemContextValue | null>(null)

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext)
  const itemContext = React.useContext(FormItemContext)
  const { getFieldState } = useFormContext()
  const formState = useFormState({ name: fieldContext?.name })

  if (!fieldContext) throw new Error('useFormField should be used within <FormField>')
  if (!itemContext) throw new Error('useFormField should be used within <FormItem>')

  const fieldState = getFieldState(fieldContext.name, formState)
  const { id } = itemContext

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  }
}

const FormItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => {
  const id = React.useId()
  return (
    <FormItemContext.Provider value={{ id }}>
      <div ref={ref} data-slot="form-item" className={cn('grid gap-2', className)} {...props} />
    </FormItemContext.Provider>
  )
})
FormItem.displayName = 'FormItem'

const FormLabel = React.forwardRef<React.ComponentRef<typeof LabelPrimitive.Root>, React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root>>(
  ({ className, ...props }, ref) => {
    const { error, formItemId } = useFormField()
    return (
      <Label
        ref={ref}
        data-slot="form-label"
        data-error={!!error}
        className={cn('data-[error=true]:text-destructive', className)}
        htmlFor={formItemId}
        {...props}
      />
    )
  },
)
FormLabel.displayName = 'FormLabel'

const FormControl = React.forwardRef<React.ComponentRef<typeof Slot.Root>, React.ComponentPropsWithoutRef<typeof Slot.Root>>(({ ...props }, ref) => {
  const { error, formItemId, formDescriptionId, formMessageId } = useFormField()
  return (
    <Slot.Root
      ref={ref}
      data-slot="form-control"
      id={formItemId}
      aria-describedby={!error ? formDescriptionId : `${formDescriptionId} ${formMessageId}`}
      aria-invalid={!!error}
      {...props}
    />
  )
})
FormControl.displayName = 'FormControl'

const FormDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(({ className, ...props }, ref) => {
  const { formDescriptionId } = useFormField()
  return <p ref={ref} data-slot="form-description" id={formDescriptionId} className={cn('text-sm text-muted-foreground', className)} {...props} />
})
FormDescription.displayName = 'FormDescription'

const FormMessage = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(({ className, children, ...props }, ref) => {
  const { error, formMessageId } = useFormField()
  const body = error ? String(error.message ?? '') : children
  if (!body) return null
  return (
    <p ref={ref} data-slot="form-message" id={formMessageId} className={cn('text-sm text-destructive', className)} {...props}>
      {body}
    </p>
  )
})
FormMessage.displayName = 'FormMessage'

export { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage, useFormField }
