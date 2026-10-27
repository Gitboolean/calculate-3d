import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'

import { HomePage } from './HomePage'

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

afterEach(() => vi.unstubAllGlobals())

test('shows API and database status from /api/health', async () => {
  const fetchMock = vi.fn(async (input: Request) => {
    expect(new URL(input.url).pathname).toBe('/api/health')
    return Response.json({ status: 'ok', db: 'ok' })
  })
  vi.stubGlobal('fetch', fetchMock)

  renderWithQuery(<HomePage />)

  expect(await screen.findByText('API: працює')).toBeInTheDocument()
  expect(screen.getByText('База даних: працює')).toBeInTheDocument()
  expect(fetchMock).toHaveBeenCalledOnce()
})

test('shows an error when the API is unreachable', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))),
  )

  renderWithQuery(<HomePage />)

  expect(await screen.findByText('API недоступне')).toBeInTheDocument()
})
