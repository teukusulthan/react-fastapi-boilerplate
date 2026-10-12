import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { userService } from '@/services/user.service'
import type { FindDTO } from '@/types/api'

import { USER_QUERY_KEYS } from '../constants/user.constants'

/** POST /user/get-all (admin only). Keeps the previous page visible while the next one loads. */
export function useUserList(query: FindDTO) {
  return useQuery({
    queryKey: USER_QUERY_KEYS.list(query),
    queryFn: () => userService.getAll(query),
    placeholderData: keepPreviousData,
  })
}
