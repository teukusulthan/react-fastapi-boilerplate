import { z } from 'zod'

import { OTP_LENGTH } from '../constants/auth.constants'

export const loginSchema = z.object({
  identifier: z.string().trim().min(1, 'Username or email is required').max(254, 'Username or email is too long'),
  password: z.string().min(1, 'Password is required').max(256, 'Password is too long'),
})

export type TLoginFormValues = z.infer<typeof loginSchema>

export const twoFactorSchema = z.object({
  otp: z
    .string()
    .trim()
    .regex(new RegExp(`^\\d{${OTP_LENGTH}}$`), `Enter the ${OTP_LENGTH}-digit code`),
})

export type TTwoFactorFormValues = z.infer<typeof twoFactorSchema>
