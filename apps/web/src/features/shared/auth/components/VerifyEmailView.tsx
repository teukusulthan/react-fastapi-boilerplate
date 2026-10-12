import { Link } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LOGIN_PATH } from '@/config/constants'
import { getErrorMessage } from '@/services/api-error'

import { useVerifyEmail } from '../hooks/useVerifyEmail'

/**
 * Landing page of the verification link emailed by `POST /auth/verify-email/request`
 * (`<BE_PUBLIC_WEB_URL><BE_EMAIL_VERIFY_PATH>?token=…`, default path `/auth/verify-email`).
 */
export function VerifyEmailView({ token }: { token: string | null }) {
  const { isPending, isSuccess, error, data } = useVerifyEmail(token)

  const missingToken = !token
  const failed = missingToken || error != null

  return (
    <Card className="w-full max-w-sm gap-6 shadow-sm">
      <CardHeader className="gap-1 text-center">
        <CardTitle className="text-xl tracking-tight">
          <h1>Verify email address</h1>
        </CardTitle>
        <CardDescription>Confirming the link from your email.</CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-4" aria-live="polite">
        {!failed && (isPending || !isSuccess) && (
          <p className="flex items-center justify-center gap-2 py-2 text-sm text-muted-foreground">
            <i className="ph ph-spinner animate-spin" aria-hidden="true" />
            Verifying…
          </p>
        )}
        {isSuccess && (
          <Alert variant="success">
            <i className="ph ph-check-circle" aria-hidden="true" />
            <AlertDescription>{data?.message || 'Your email address is verified.'}</AlertDescription>
          </Alert>
        )}
        {failed && (
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertDescription>
              {missingToken ? 'This verification link is incomplete. Open the link from the email again.' : getErrorMessage(error)}
            </AlertDescription>
          </Alert>
        )}
        {(isSuccess || failed) && (
          <Button asChild className="w-full">
            <Link to={LOGIN_PATH}>Continue</Link>
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
