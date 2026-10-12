import { useState, type ReactNode } from 'react'

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { cn } from '@/utils/cn'

export interface ConfirmDialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  /** Optional trigger element (uncontrolled usage). */
  trigger?: ReactNode
  title: ReactNode
  description?: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** `destructive` for delete/block/revoke. */
  variant?: 'default' | 'destructive'
  /** Phosphor icon slug shown in a tile above the title. */
  icon?: string
  /**
   * Runs on confirm. If it returns a promise the button shows a spinner, the dialog stays open while
   * it runs and closes when it resolves (stays open on rejection so the caller can toast the error).
   */
  onConfirm: () => void | Promise<unknown>
}

/** Confirmation for consequential actions (AlertDialog). Never use `window.confirm`. */
export function ConfirmDialog({
  open: openProp,
  onOpenChange,
  trigger,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  icon,
  onConfirm,
}: ConfirmDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const [pending, setPending] = useState(false)
  const open = openProp ?? internalOpen

  const setOpen = (value: boolean) => {
    if (pending) return
    onOpenChange?.(value)
    if (openProp === undefined) setInternalOpen(value)
  }

  const handleConfirm = async () => {
    const result = onConfirm()
    if (!(result instanceof Promise)) {
      setOpen(false)
      return
    }
    setPending(true)
    try {
      await result
      setPending(false)
      onOpenChange?.(false)
      if (openProp === undefined) setInternalOpen(false)
    } catch {
      setPending(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      {trigger && <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>}
      <AlertDialogContent>
        <AlertDialogHeader>
          {icon && (
            <AlertDialogMedia className={cn(variant === 'destructive' && 'bg-destructive/10 text-destructive')}>
              <i className={cn('ph', `ph-${icon}`)} aria-hidden="true" />
            </AlertDialogMedia>
          )}
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>{cancelLabel}</AlertDialogCancel>
          <Button variant={variant} loading={pending} onClick={() => void handleConfirm()}>
            {confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
