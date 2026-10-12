import { z } from 'zod'

/**
 * Typed, validated access to Vite env variables (env/.env*).
 * Never read `import.meta.env` anywhere else — import `env` from here.
 */

/** Treat empty / whitespace-only values as "not set" so defaults apply (`VITE_X=` in .env files). */
const optionalString = <T extends z.ZodType>(schema: T) =>
  z.preprocess((value) => (typeof value === 'string' && value.trim() === '' ? undefined : value), schema)

const apiBaseUrl = z
  .string()
  .trim()
  .refine((value) => value.startsWith('/') || /^https?:\/\/[^\s/]+/i.test(value), {
    message: 'must be a relative path starting with "/" or an absolute http(s) URL',
  })
  .transform((value) => (value.length > 1 ? value.replace(/\/+$/, '') : value))

const envSchema = z.object({
  VITE_API_BASE_URL: optionalString(apiBaseUrl.default('/api/v1/apps')),
  VITE_APP_NAME: optionalString(z.string().trim().default('App')),
  VITE_APP_DESCRIPTION: optionalString(z.string().trim().default('')),
  VITE_MAPBOX_TOKEN: optionalString(z.string().trim().default('')),
  MODE: z.string().default('development'),
  DEV: z.boolean().default(false),
  PROD: z.boolean().default(false),
})

export interface AppEnv {
  api: { baseUrl: string }
  app: { name: string; description: string; mode: string; isDev: boolean; isProd: boolean }
  map: { mapboxToken: string }
}

/** Parse a raw env record (normally `import.meta.env`). Throws a readable error listing invalid keys. */
export function parseEnv(raw: Record<string, unknown>): AppEnv {
  const result = envSchema.safeParse(raw)
  if (!result.success) {
    const issues = result.error.issues.map((issue) => `  - ${issue.path.join('.') || '(root)'}: ${issue.message}`).join('\n')
    throw new Error(`Invalid environment configuration (check env/.env*):\n${issues}`)
  }
  const values = result.data
  return {
    api: { baseUrl: values.VITE_API_BASE_URL },
    app: {
      name: values.VITE_APP_NAME,
      description: values.VITE_APP_DESCRIPTION,
      mode: values.MODE,
      isDev: values.DEV,
      isProd: values.PROD,
    },
    map: { mapboxToken: values.VITE_MAPBOX_TOKEN },
  }
}

const env: AppEnv = parseEnv(import.meta.env)

/**
 * True only in `vite` dev builds. A literal (`import.meta.env.DEV` is replaced at build time), so code
 * guarded by it — e.g. the /ui-kit route — is tree-shaken out of production bundles.
 */
export const DEV_TOOLS_ENABLED: boolean = import.meta.env.DEV

export default env
