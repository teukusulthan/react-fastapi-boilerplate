import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

import { useLoginFlow } from '../hooks/useLoginFlow'

import { LoginForm } from './LoginForm'
import { TwoFactorForm } from './TwoFactorForm'

/** Sign-in card: credentials step, then the 2FA step when the backend requires it. */
export function LoginView() {
  const { challenge, loginMutation, verifyMutation, resendMutation, restart } = useLoginFlow()

  return (
    <Card className="w-full max-w-sm gap-6 shadow-sm">
      <CardHeader className="gap-1 text-center">
        <CardTitle className="text-xl tracking-tight">
          <h1>{challenge ? 'Two-factor verification' : 'Welcome back'}</h1>
        </CardTitle>
        <CardDescription>{challenge ? 'One more step to confirm it’s you.' : 'Sign in to your account to continue.'}</CardDescription>
      </CardHeader>
      <CardContent>
        {challenge ? (
          <TwoFactorForm
            method={challenge.method}
            onSubmit={(values) => verifyMutation.mutate(values)}
            onResend={() => resendMutation.mutate()}
            onBack={restart}
            isSubmitting={verifyMutation.isPending}
            isResending={resendMutation.isPending}
            resent={resendMutation.isSuccess}
            error={verifyMutation.error ?? resendMutation.error}
          />
        ) : (
          <LoginForm
            onSubmit={(values, onError) => loginMutation.mutate(values, { onError })}
            isSubmitting={loginMutation.isPending}
            error={loginMutation.error}
          />
        )}
      </CardContent>
      {!challenge && (
        <CardFooter className="justify-center border-t pt-6">
          <p className="text-center text-xs text-muted-foreground">Trouble signing in? Contact your administrator.</p>
        </CardFooter>
      )}
    </Card>
  )
}
