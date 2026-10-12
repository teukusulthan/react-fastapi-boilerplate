import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'

import { toApiError } from '@/services/api-error'

/**
 * Copy backend 422 field errors (`data = [{ field, message }]`) onto react-hook-form fields.
 * Returns true when at least one field error was applied.
 */
export function applyApiFieldErrors<T extends FieldValues>(error: unknown, setError: UseFormSetError<T>, fields: readonly Path<T>[]): boolean {
  let applied = false
  for (const { field, message } of toApiError(error).fieldErrors) {
    const name = fields.find((candidate) => candidate === field)
    if (name) {
      setError(name, { type: 'server', message })
      applied = true
    }
  }
  return applied
}
