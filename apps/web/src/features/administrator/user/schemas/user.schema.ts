import { z } from 'zod'

import { PASSWORD_MIN_LENGTH } from '../constants/user.constants'

export const createUserSchema = z.object({
  fullname: z.string().trim().min(1, 'Full name is required').max(100, 'Full name is too long'),
  username: z
    .string()
    .trim()
    .min(3, 'Use at least 3 characters')
    .max(50, 'Username is too long')
    .regex(/^[A-Za-z0-9._-]+$/, 'Letters, numbers, dots, dashes and underscores only'),
  email: z.string().trim().min(1, 'Email is required').pipe(z.email('Enter a valid email address')),
  /** Optional: omitted when accounts are managed by an external identity provider. */
  password: z.union([z.literal(''), z.string().min(PASSWORD_MIN_LENGTH, `Use at least ${PASSWORD_MIN_LENGTH} characters`).max(72, 'Password is too long')]),
  status: z.enum(['active', 'pending']),
})

export type TCreateUserFormValues = z.infer<typeof createUserSchema>

export const resetPasswordSchema = z.object({
  newPassword: z.string().min(PASSWORD_MIN_LENGTH, `Use at least ${PASSWORD_MIN_LENGTH} characters`).max(72, 'Password is too long'),
})

export type TResetPasswordFormValues = z.infer<typeof resetPasswordSchema>
