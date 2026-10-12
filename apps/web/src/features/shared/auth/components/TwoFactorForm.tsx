import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { getErrorMessage } from '@/services/api-error'
import type { TwoFactorMethod } from '@/types/models'

import { OTP_LENGTH, TWO_FACTOR_METHOD_HINT } from '../constants/auth.constants'
import { twoFactorSchema, type TTwoFactorFormValues } from '../schemas/login.schema'

export interface TwoFactorFormProps {
  method: TwoFactorMethod
  onSubmit: (values: TTwoFactorFormValues) => void
  onResend: () => void
  onBack: () => void
  isSubmitting: boolean
  isResending: boolean
  resent: boolean
  error: unknown
}

export function TwoFactorForm({ method, onSubmit, onResend, onBack, isSubmitting, isResending, resent, error }: TwoFactorFormProps) {
  const form = useForm<TTwoFactorFormValues>({
    resolver: zodResolver(twoFactorSchema),
    defaultValues: { otp: '' },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4" aria-label="Two-factor verification">
        {error != null && (
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertDescription>{getErrorMessage(error)}</AlertDescription>
          </Alert>
        )}
        {resent && error == null && (
          <Alert variant="success">
            <i className="ph ph-check-circle" aria-hidden="true" />
            <AlertDescription>A new code has been sent.</AlertDescription>
          </Alert>
        )}

        <FormField
          control={form.control}
          name="otp"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Verification code</FormLabel>
              <FormControl>
                <Input
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={OTP_LENGTH}
                  placeholder={'0'.repeat(OTP_LENGTH)}
                  className="h-11 text-center font-mono text-lg tracking-widest tabular-nums"
                  {...field}
                />
              </FormControl>
              <FormDescription>{TWO_FACTOR_METHOD_HINT[method]}</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="mt-2 w-full" loading={isSubmitting}>
          {isSubmitting ? 'Verifying…' : 'Verify'}
        </Button>

        <div className="flex items-center justify-between gap-2">
          <Button type="button" variant="link" className="text-muted-foreground hover:text-foreground" onClick={onBack}>
            <i className="ph ph-arrow-left" aria-hidden="true" />
            Back to sign in
          </Button>
          {method === 'email' && (
            <Button type="button" variant="link" onClick={onResend} disabled={isResending}>
              {isResending ? 'Sending…' : 'Resend code'}
            </Button>
          )}
        </div>
      </form>
    </Form>
  )
}
