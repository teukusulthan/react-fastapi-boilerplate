import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { getErrorMessage } from '@/services/api-error'
import { applyApiFieldErrors } from '@/utils/form-errors'

import { USER_CREATE_FIELDS, USER_CREATE_STATUS_OPTIONS } from '../constants/user.constants'
import { useCreateUser } from '../hooks/useUserMutations'
import { createUserSchema, type TCreateUserFormValues } from '../schemas/user.schema'

const DEFAULT_VALUES: TCreateUserFormValues = { fullname: '', username: '', email: '', password: '', status: 'active' }

/** "Add user" primary action + dialog form (POST /user/add). Server 422s land on the matching field. */
export function CreateUserDialog() {
  const [open, setOpen] = useState(false)
  /** Error not attributable to a field (e.g. 403, 409 without field, network). */
  const [formError, setFormError] = useState<unknown>(null)
  const createUser = useCreateUser()
  const form = useForm<TCreateUserFormValues>({ resolver: zodResolver(createUserSchema), defaultValues: DEFAULT_VALUES })

  const handleOpenChange = (value: boolean) => {
    if (createUser.isPending) return
    if (!value) {
      form.reset(DEFAULT_VALUES)
      setFormError(null)
    }
    setOpen(value)
  }

  const onSubmit = form.handleSubmit(({ password, ...values }) => {
    setFormError(null)
    createUser.mutate(
      { ...values, ...(password ? { password } : {}) },
      {
        onSuccess: (user) => {
          toast.success('User created', { description: `${user.fullname ?? user.username} can now be managed from this list.` })
          form.reset(DEFAULT_VALUES)
          setOpen(false)
        },
        onError: (error) => {
          if (!applyApiFieldErrors(error, form.setError, USER_CREATE_FIELDS)) setFormError(error)
        },
      },
    )
  })

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <i className="ph ph-plus" aria-hidden="true" />
          Add user
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add user</DialogTitle>
          <DialogDescription>Create an account. You can assign roles and groups afterwards.</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5" aria-label="Add user">
            {formError != null && (
              <Alert variant="destructive">
                <i className="ph ph-warning-circle" aria-hidden="true" />
                <AlertDescription>{getErrorMessage(formError)}</AlertDescription>
              </Alert>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="fullname"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full name</FormLabel>
                    <FormControl>
                      <Input autoComplete="off" placeholder="Jane Cooper" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input autoComplete="off" autoCapitalize="none" spellCheck={false} placeholder="jane.cooper" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" autoComplete="off" placeholder="jane@company.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Temporary password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormDescription>At least 8 characters. Leave empty if sign-in is handled by an external identity provider.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {USER_CREATE_STATUS_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>{USER_CREATE_STATUS_OPTIONS.find((option) => option.value === field.value)?.description}</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => handleOpenChange(false)} disabled={createUser.isPending}>
                Cancel
              </Button>
              <Button type="submit" loading={createUser.isPending}>
                Create user
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
