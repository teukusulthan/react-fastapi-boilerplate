import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { getUserDisplayName } from '@/features/shared/auth'
import { getErrorMessage } from '@/services/api-error'
import type { UserDetail } from '@/types/models'
import { applyApiFieldErrors } from '@/utils/form-errors'

import { useResetUserPassword } from '../hooks/useUserMutations'
import { resetPasswordSchema, type TResetPasswordFormValues } from '../schemas/user.schema'

export interface ResetPasswordDialogProps {
  user: UserDetail
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Admin sets a new password for a user (POST /user/reset-password); their sessions are revoked. */
export function ResetPasswordDialog({ user, open, onOpenChange }: ResetPasswordDialogProps) {
  const reset = useResetUserPassword()
  const form = useForm<TResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema), defaultValues: { newPassword: '' } })

  const close = (value: boolean) => {
    if (reset.isPending) return
    if (!value) form.reset()
    onOpenChange(value)
  }

  const onSubmit = form.handleSubmit((values) =>
    reset.mutate(
      { id: user.id, newPassword: values.newPassword },
      {
        onSuccess: () => {
          toast.success('Password reset', { description: `${getUserDisplayName(user)} has been signed out of every device.` })
          close(false)
        },
        onError: (error) => {
          if (!applyApiFieldErrors(error, form.setError, ['newPassword'])) toast.error('Could not reset the password', { description: getErrorMessage(error) })
        },
      },
    ),
  )

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reset password</DialogTitle>
          <DialogDescription>Set a new password for {getUserDisplayName(user)}. They will be signed out everywhere.</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={onSubmit} noValidate className="flex flex-col gap-6">
            <FormField
              control={form.control}
              name="newPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormDescription>At least 8 characters. Share it with the user through a secure channel.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => close(false)} disabled={reset.isPending}>
                Cancel
              </Button>
              <Button type="submit" loading={reset.isPending}>
                Reset password
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
