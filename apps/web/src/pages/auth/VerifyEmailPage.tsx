import { useSearchParams } from 'react-router-dom'

import { VerifyEmailView } from '@/features/shared/auth'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  return <VerifyEmailView token={searchParams.get('token')} />
}
