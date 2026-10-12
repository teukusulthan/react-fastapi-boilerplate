import { useState } from 'react'
import { toast } from 'sonner'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { getUserDisplayName } from '@/features/shared/auth'
import { DataTableRowActions, type DataTableRowAction } from '@/modules/data-table'
import { getErrorMessage } from '@/services/api-error'
import { useAuthStore } from '@/stores/useAuthStore'
import type { UserDetail } from '@/types/models'

import { useDeleteUser, useUpdateUserStatus } from '../hooks/useUserMutations'

import { ResetPasswordDialog } from './ResetPasswordDialog'

type PendingDialog = 'reset-password' | 'block' | 'delete' | null

/** "…" menu of a user row: copy email, reset password, block/activate, delete (with confirmations). */
export function UserRowActions({ user }: { user: UserDetail }) {
  const currentUserId = useAuthStore((state) => state.user?.id)
  const [dialog, setDialog] = useState<PendingDialog>(null)
  const deleteUser = useDeleteUser()
  const updateStatus = useUpdateUserStatus()
  const name = getUserDisplayName(user)
  const isSelf = user.id === currentUserId

  const copyEmail = () =>
    navigator.clipboard.writeText(user.email).then(
      () => toast.success('Email copied'),
      () => toast.error('Could not copy to the clipboard'),
    )

  const activate = () =>
    updateStatus.mutate(
      { id: user.id, status: 'active' },
      {
        onSuccess: () => toast.success(`${name} is active`),
        onError: (error) => toast.error('Could not activate the user', { description: getErrorMessage(error) }),
      },
    )

  const actions: DataTableRowAction[] = [
    { label: 'Copy email', icon: 'copy', onSelect: () => void copyEmail() },
    { label: 'Reset password', icon: 'key', onSelect: () => setDialog('reset-password') },
  ]
  if (!isSelf && user.status === 'active') actions.push({ label: 'Block user', icon: 'prohibit', onSelect: () => setDialog('block') })
  if (!isSelf && (user.status === 'blocked' || user.status === 'pending')) actions.push({ label: 'Activate user', icon: 'check-circle', onSelect: activate })
  if (!isSelf) actions.push({ label: 'Delete user', icon: 'trash', variant: 'destructive', separatorBefore: true, onSelect: () => setDialog('delete') })

  return (
    <>
      <DataTableRowActions actions={actions} label={`Actions for ${name}`} />

      <ResetPasswordDialog user={user} open={dialog === 'reset-password'} onOpenChange={(open) => setDialog(open ? 'reset-password' : null)} />

      <ConfirmDialog
        open={dialog === 'block'}
        onOpenChange={(open) => setDialog(open ? 'block' : null)}
        icon="prohibit"
        variant="destructive"
        title={`Block ${name}?`}
        description="They will be signed out and can't sign in until an administrator activates the account again."
        confirmLabel="Block user"
        onConfirm={() =>
          updateStatus
            .mutateAsync({ id: user.id, status: 'blocked' })
            .then(() => toast.success(`${name} is blocked`))
            .catch((error: unknown) => {
              toast.error('Could not block the user', { description: getErrorMessage(error) })
              throw error
            })
        }
      />

      <ConfirmDialog
        open={dialog === 'delete'}
        onOpenChange={(open) => setDialog(open ? 'delete' : null)}
        icon="trash"
        variant="destructive"
        title={`Delete ${name}?`}
        description={`This permanently removes ${user.email} and signs them out. This can't be undone.`}
        confirmLabel="Delete user"
        onConfirm={() =>
          deleteUser
            .mutateAsync(user.id)
            .then(() => toast.success(`${name} was deleted`))
            .catch((error: unknown) => {
              toast.error('Could not delete the user', { description: getErrorMessage(error) })
              throw error
            })
        }
      />
    </>
  )
}
