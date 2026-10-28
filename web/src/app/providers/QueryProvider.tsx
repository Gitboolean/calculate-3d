import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { ApiError } from '@/shared/api'

// A 4xx (not found, settings missing, invalid input) will not change on retry — show it at once.
const retry = (failureCount: number, error: Error) =>
  !(error instanceof ApiError && error.status < 500) && failureCount < 3

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry } } }))
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
