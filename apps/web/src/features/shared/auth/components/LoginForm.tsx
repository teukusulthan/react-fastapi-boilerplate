import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { applyApiFieldErrors } from '@/utils/form-errors'

import { LOGIN_FIELDS } from '../constants/auth.constants'
import { loginSchema, type TLoginFormValues } from '../schemas/login.schema'
import { getLoginErrorMessage } from '../utils/login-errors'

export interface LoginFormProps {
  onSubmit: (values: TLoginFormValues, onError: (error: unknown) => void) => void
  isSubmitting: boolean
  error: unknown
}

export function LoginForm({ onSubmit, isSubmitting, error }: LoginFormProps) {
  const form = useForm<TLoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { identifier: '', password: '' },
  })

  const handleSubmit = form.handleSubmit((values) => onSubmit(values, (submitError) => applyApiFieldErrors(submitError, form.setError, LOGIN_FIELDS)))

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4" aria-label="Sign in">
        {error != null && (
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertDescription>{getLoginErrorMessage(error)}</AlertDescription>
          </Alert>
        )}

        <FormField
          control={form.control}
          name="identifier"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username or email</FormLabel>
              <FormControl>
                <Input autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder="you@example.com" {...field} />
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
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="current-password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="mt-2 w-full" loading={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
    </Form>
  )
}
