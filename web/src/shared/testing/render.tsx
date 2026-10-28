import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router'

/**
 * Renders `ui` at `path` (matched by `pattern`) with a fresh QueryClient and no retries.
 * Providers live in `wrapper`, so `rerender(<Other />)` keeps the same client and router.
 */
export function renderWithProviders(
  ui: ReactElement,
  { path = '/', pattern = '*' }: { path?: string; pattern?: string } = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  function Providers({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path={pattern} element={children} />
            <Route path="*" element={<p>Інша сторінка</p>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
  return { client, ...render(ui, { wrapper: Providers }) }
}
