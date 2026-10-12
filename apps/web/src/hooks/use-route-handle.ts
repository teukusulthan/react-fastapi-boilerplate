import { useMatches } from 'react-router-dom'

import type { IRouteHandle } from '@/types/menu'

/** The deepest matched route `handle` (crumb/title for routes that are not in the menu). Data routers only. */
export function useRouteHandle(): IRouteHandle | undefined {
  const matches = useMatches()
  for (let index = matches.length - 1; index >= 0; index -= 1) {
    const handle = matches[index].handle as IRouteHandle | undefined
    if (handle && (handle.crumb || handle.title)) return handle
  }
  return undefined
}
