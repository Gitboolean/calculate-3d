import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// Same origin: Vite proxies /api in dev, FastAPI serves both in `make run`.
// fetch is resolved per call so tests can stub globalThis.fetch.
export const api = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (request) => globalThis.fetch(request),
})

export type Schemas = components['schemas']
