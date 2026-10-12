import { create } from 'zustand'

import type { UserProfile } from '@/types/models'

/**
 * - `unknown`        — session not resolved yet (GET /auth/me in flight on app start)
 * - `authenticated`  — /auth/me (or login) returned a user
 * - `anonymous`      — no valid session
 */
export type AuthStatus = 'unknown' | 'authenticated' | 'anonymous'

/** Why the session ended: `logout` (user action) or `expired` (401 / refresh failure / no session). */
export type SessionEndReason = 'logout' | 'expired'

interface AuthState {
  status: AuthStatus
  user: UserProfile | null
  endReason: SessionEndReason | null
  /** Mark the session as authenticated with the given profile. */
  setUser: (user: UserProfile) => void
  /** Forget the session client-side. Route guards react by redirecting to the login page. */
  clearSession: (reason?: SessionEndReason) => void
}

/**
 * Client-side mirror of the server session. Deliberately NOT persisted: the httpOnly cookies are
 * the source of truth, and the session is re-resolved with GET /auth/me on every app start.
 */
export const useAuthStore = create<AuthState>()((set) => ({
  status: 'unknown',
  user: null,
  endReason: null,
  setUser: (user) => set({ user, status: 'authenticated', endReason: null }),
  clearSession: (reason = 'expired') => set({ user: null, status: 'anonymous', endReason: reason }),
}))
