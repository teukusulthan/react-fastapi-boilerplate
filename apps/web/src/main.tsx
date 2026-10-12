// Inter (variable, self-hosted — no third-party font request).
import '@fontsource-variable/inter'
// Phosphor icon fonts, bundled locally (weights supported by utils/icon-renderer.tsx).
import '@phosphor-icons/web/regular'
import '@phosphor-icons/web/fill'
import '@phosphor-icons/web/bold'
import '@phosphor-icons/web/light'
import '@phosphor-icons/web/duotone'
import './index.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { AppProviders } from '@/components/wrappers/AppProviders'
import RouteIndex from '@/routes'

const container = document.getElementById('root')
if (!container) throw new Error('Root element #root not found in index.html')

createRoot(container).render(
  <StrictMode>
    <AppProviders>
      <RouteIndex />
    </AppProviders>
  </StrictMode>,
)
