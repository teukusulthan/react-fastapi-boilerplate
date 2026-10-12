/// <reference types="vitest/config" />
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, type Plugin } from 'vite'

const ROOT_DIR = path.dirname(fileURLToPath(import.meta.url))
const ENV_DIR = path.resolve(ROOT_DIR, 'env')

/** Public path the SPA uses to reach the backend (see src/config/env.ts). */
const API_PREFIX = '/api/v1/apps'
const DEFAULT_PROXY_TARGET = 'http://localhost:8020'

/** Defaults for `%VITE_*%` placeholders in index.html when the key is not set in env/. */
const HTML_ENV_DEFAULTS: Record<string, string> = {
  VITE_APP_NAME: 'App',
  VITE_APP_DESCRIPTION: 'Internal web application',
}

const escapeHtml = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')

/**
 * Replaces `%VITE_*%` placeholders in index.html, falling back to HTML_ENV_DEFAULTS.
 * (Vite's built-in replacement leaves unknown keys untouched, which would ship literal placeholders.)
 */
function htmlEnv(env: Record<string, string>): Plugin {
  return {
    name: 'html-env-defaults',
    transformIndexHtml: {
      order: 'pre',
      handler: (html) =>
        html.replace(/%(VITE_[A-Z0-9_]+)%/g, (match, key: string) => {
          const value = env[key] || HTML_ENV_DEFAULTS[key]
          return value === undefined ? match : escapeHtml(value)
        }),
    },
  }
}

/**
 * @phosphor-icons/web ships woff2 + woff + ttf + svg for every weight (~4 MB each).
 * Every evergreen browser uses woff2, so drop the other formats from the @font-face rules
 * to keep them out of the build output.
 */
function phosphorWoff2Only(): Plugin {
  const styleSheet = /@phosphor-icons[\\/]web[\\/]src[\\/][a-z]+[\\/]style\.css$/
  return {
    name: 'phosphor-woff2-only',
    enforce: 'pre',
    transform(code, id) {
      if (!styleSheet.test(id.split('?')[0])) return null
      return code.replace(/src:\s*([^;]+);/g, (_match, sources: string) => {
        const woff2 = sources
          .split(',')
          .map((entry) => entry.trim())
          .filter((entry) => entry.includes('.woff2'))
        return `src: ${woff2.join(', ')};`
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  // '' prefix → also read non-VITE_ keys (e.g. DEV_PROXY_TARGET) for config-time use only.
  const env = loadEnv(mode, ENV_DIR, '')
  const proxyTarget = env.DEV_PROXY_TARGET || DEFAULT_PROXY_TARGET

  return {
    envDir: ENV_DIR,
    plugins: [phosphorWoff2Only(), react(), tailwindcss(), htmlEnv(env)],
    resolve: {
      alias: {
        '@': path.resolve(ROOT_DIR, 'src'),
      },
    },
    server: {
      port: 3000,
      strictPort: true,
      proxy: {
        [API_PREFIX]: {
          target: proxyTarget,
          changeOrigin: true,
          rewrite: (requestPath) => requestPath.replace(new RegExp(`^${API_PREFIX}`), '') || '/',
        },
      },
    },
    preview: {
      port: 4173,
      strictPort: true,
      proxy: {
        [API_PREFIX]: {
          target: proxyTarget,
          changeOrigin: true,
          rewrite: (requestPath) => requestPath.replace(new RegExp(`^${API_PREFIX}`), '') || '/',
        },
      },
    },
    build: {
      outDir: 'build',
      emptyOutDir: true,
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined
            if (/node_modules[\\/](react|react-dom|scheduler|react-router|react-router-dom)[\\/]/.test(id)) return 'vendor-react'
            if (/node_modules[\\/]@tanstack[\\/]/.test(id)) return 'vendor-tanstack'
            if (/node_modules[\\/](react-hook-form|@hookform|zod)[\\/]/.test(id)) return 'vendor-form'
            if (/node_modules[\\/]@radix-ui[\\/]/.test(id)) return 'vendor-radix'
            return undefined
          },
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      css: false,
      restoreMocks: true,
      unstubEnvs: true,
    },
  }
})
