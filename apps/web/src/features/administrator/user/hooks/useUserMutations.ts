import { useMutation, useQueryClient } from '@tanstack/react-query'

import { userService, type IUserCreatePayload, type IUserResetPasswordPayload } from '@/services/user.service'
import type { UserStatus } from '@/types/models'

import { USER_QUERY_KEYS } from '../constants/user.constants'

/** Invalidate every user list after a successful write. */
function useInvalidateUsers() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: USER_QUERY_KEYS.all })
}

/** POST /user/add */
export function useCreateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({ mutationFn: (payload: IUserCreatePayload) => userService.add(payload), onSuccess: invalidate })
}

/** DELETE /user/delete?id= (the backend refuses to delete the caller's own account). */
export function useDeleteUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({ mutationFn: (id: string) => userService.delete({ id }), onSuccess: invalidate })
}

/** PUT /user/update with only `status` (PATCH semantics). */
export function useUpdateUserStatus() {
  const invalidate = useInvalidateUsers()
  return useMutation({ mutationFn: ({ id, status }: { id: string; status: UserStatus }) => userService.update({ id, status }), onSuccess: invalidate })
}

/** POST /user/reset-password — also revokes the user's sessions. */
export function useResetUserPassword() {
  return useMutation({ mutationFn: (payload: IUserResetPasswordPayload) => userService.resetPassword(payload) })
}
