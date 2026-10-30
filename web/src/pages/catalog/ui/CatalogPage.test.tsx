import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders } from '@/shared/testing'

import { CatalogPage } from './CatalogPage'

const ITEMS = [
  { id: 'b1', name: 'Benchy тризуб', min_donation_kop: 9000 },
  { id: 't1', name: 'Брелок-тризуб', min_donation_kop: 11525 },
]

afterEach(() => vi.unstubAllGlobals())

const renderAt = (path: string) =>
  renderWithProviders(<CatalogPage />, { path, pattern: '/catalog' })

test('the search in ?q= filters on the server and the list keeps its order (AC-12)', async () => {
  const api = mockApi({ 'GET /api/catalog/items': json({ items: ITEMS }) })
  renderAt('/catalog?q=тризуб')

  const table = await screen.findByRole('table')
  const rows = within(table).getAllByRole('row').slice(1)
  expect(
    rows.map((r) =>
      within(r)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ),
  ).toEqual([
    ['Benchy тризуб', '90,00 ₴'],
    ['Брелок-тризуб', '115,25 ₴'],
  ])
  expect(screen.getByLabelText('Пошук за назвою')).toHaveValue('тризуб')
  expect(new URLSearchParams(api.calls[0]?.search).get('q')).toBe('тризуб')
})

test('typing a search asks the server with it', async () => {
  const user = userEvent.setup()
  const api = mockApi({ 'GET /api/catalog/items': json({ items: [] }) })
  renderAt('/catalog')
  await screen.findByText('Каталог порожній. Збережіть розрахунок на сторінці «Розрахунок».')

  await user.type(screen.getByLabelText('Пошук за назвою'), 'зуб')

  await screen.findByText('Нічого не знайдено за запитом «зуб».')
  expect(new URLSearchParams(api.calls.at(-1)?.search).get('q')).toBe('зуб')
})

test('each item links to its page', async () => {
  mockApi({ 'GET /api/catalog/items': json({ items: ITEMS }) })
  renderAt('/catalog')

  expect(await screen.findByRole('link', { name: 'Брелок-тризуб' })).toHaveAttribute(
    'href',
    '/catalog/t1',
  )
})

test('opening the catalog again asks the server again and shows the new price (AC-13)', async () => {
  let price = 11525
  const api = mockApi({
    'GET /api/catalog/items': () =>
      json({ items: [{ id: 't1', name: 'Брелок-тризуб', min_donation_kop: price }] }),
  })
  const view = renderAt('/catalog')
  expect(await screen.findByText('115,25 ₴')).toBeInTheDocument()

  price = 13505
  view.rerender(<p>Налаштування</p>)
  view.rerender(<CatalogPage />)

  expect(await screen.findByText('135,05 ₴')).toBeInTheDocument()
  expect(api.callsTo('GET', '/api/catalog/items')).toHaveLength(2)
})

test('missing price settings are explained (409 costing.settings_missing)', async () => {
  mockApi({
    'GET /api/catalog/items': problem(409, 'costing.settings_missing', {
      missing: ['price_settings'],
    }),
  })
  renderAt('/catalog')

  expect(
    await screen.findByText(
      'Бракує налаштувань цін: тариф, потужність, знос і брак ще не збережено.',
    ),
  ).toBeInTheDocument()
})

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

test('the table stays on screen while a filtered list is loading (no loading flash)', async () => {
  const user = userEvent.setup()
  const pending = deferred<Response>()
  const api = mockApi({
    'GET /api/catalog/items': (call) =>
      new URLSearchParams(call.search).has('q') ? pending.promise : json({ items: ITEMS }),
  })
  renderAt('/catalog')
  await screen.findByRole('table')

  await user.type(screen.getByLabelText('Пошук за назвою'), 'б')

  await vi.waitFor(() =>
    expect(api.callsTo('GET', '/api/catalog/items').some((c) => c.search.includes('q='))).toBe(
      true,
    ),
  )
  expect(screen.getByRole('table')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Benchy тризуб' })).toBeInTheDocument()
  expect(screen.queryByText('Завантажую каталог…')).not.toBeInTheDocument()
  pending.resolve(json({ items: [ITEMS[0]] }))
})

test('typing "pe" quickly asks the server once, for the final query only (debounce)', async () => {
  const user = userEvent.setup()
  const api = mockApi({
    'GET /api/catalog/items': (call) =>
      json({ items: new URLSearchParams(call.search).has('q') ? [ITEMS[0]] : ITEMS }),
  })
  renderAt('/catalog')
  await screen.findByRole('table')

  await user.type(screen.getByLabelText('Пошук за назвою'), 'pe')
  await vi.waitFor(() => expect(screen.getAllByRole('row')).toHaveLength(2))
  await new Promise((r) => setTimeout(r, 600))

  const qs = api
    .callsTo('GET', '/api/catalog/items')
    .map((c) => new URLSearchParams(c.search).get('q'))
    .filter((q) => q !== null)
  expect(qs).toEqual(['pe'])
})

test('clearing a search that found nothing never flashes an empty-state while the list reloads', async () => {
  const user = userEvent.setup()
  const pending = deferred<Response>()
  const api = mockApi({
    'GET /api/catalog/items': (call) => {
      const q = new URLSearchParams(call.search).get('q')
      if (q === 'xyz') return json({ items: [] })
      return q ? json({ items: [] }) : pending.promise
    },
  })
  renderAt('/catalog?q=xyz')
  await screen.findByText('Нічого не знайдено за запитом «xyz».')

  await user.clear(screen.getByLabelText('Пошук за назвою'))
  await vi.waitFor(() =>
    expect(
      api
        .callsTo('GET', '/api/catalog/items')
        .filter((c) => !new URLSearchParams(c.search).has('q')),
    ).toHaveLength(1),
  )

  expect(screen.queryByText(/Каталог порожній/)).not.toBeInTheDocument()
  expect(screen.queryByText(/Нічого не знайдено/)).not.toBeInTheDocument()
  pending.resolve(json({ items: ITEMS }))
  expect(await screen.findByRole('link', { name: 'Benchy тризуб' })).toBeInTheDocument()
})
