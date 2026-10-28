import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'

import { AppRoutes } from './AppRoutes'

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => Response.json({ status: 'ok', db: 'ok' })),
  )
})
afterEach(() => vi.unstubAllGlobals())

test('root redirects to the calculation screen', async () => {
  renderAt('/')

  expect(await screen.findByRole('heading', { level: 1, name: 'Розрахунок' })).toBeInTheDocument()
})

test('navigation links switch between the screens', async () => {
  const user = userEvent.setup()
  renderAt('/calculate')

  await user.click(screen.getByRole('link', { name: 'Налаштування цін' }))
  expect(screen.getByRole('heading', { level: 1, name: 'Налаштування цін' })).toBeInTheDocument()

  await user.click(screen.getByRole('link', { name: 'Каталог' }))
  expect(screen.getByRole('heading', { level: 1, name: 'Каталог' })).toBeInTheDocument()

  await user.click(screen.getByRole('link', { name: 'Розрахунок' }))
  expect(screen.getByRole('heading', { level: 1, name: 'Розрахунок' })).toBeInTheDocument()
})

test('marks the current screen in the navigation', () => {
  renderAt('/catalog')

  expect(screen.getByRole('link', { name: 'Каталог' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Розрахунок' })).not.toHaveAttribute('aria-current')
})

test('an item deep link opens the item screen', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (request: Request) => {
      const path = new URL(request.url).pathname
      if (path === '/api/pricing/plastics') return Response.json({ items: [] })
      if (path.startsWith('/api/catalog/items/'))
        return Response.json({
          id: 'i1',
          name: 'Підставка',
          plastics: [],
          print_time_s: 60,
          quote: {
            min_donation_kop: 1,
            breakdown: { plastic_kop: 0, electricity_kop: 0, wear_kop: 0, scrap_kop: 0 },
          },
        })
      return Response.json({ status: 'ok', db: 'ok' })
    }),
  )

  renderAt('/catalog/0190e7a4-0000-7000-8000-000000000000')

  expect(await screen.findByRole('heading', { level: 1, name: 'Підставка' })).toBeInTheDocument()
})

test('the footer shows API and database status from /api/health', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => Response.json({ status: 'ok', db: 'down' })),
  )

  renderAt('/calculate')

  expect(await screen.findByText('API: працює · База даних: не відповідає')).toBeInTheDocument()
})

test('the footer shows an error when the API is unreachable', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))),
  )

  renderAt('/calculate')

  expect(await screen.findByText('API недоступне')).toBeInTheDocument()
})
