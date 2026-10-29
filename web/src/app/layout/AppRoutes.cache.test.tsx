import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'

import { json, mockApi } from '@/shared/testing'

import { AppRoutes } from './AppRoutes'

// Whole app, ONE QueryClient: a price change must never let a cached donation resurface (AC-13).

const SETTINGS = {
  tariff_per_kwh_kop: 432,
  printer_power_w: 150,
  printer_price_kop: 3000000,
  printer_lifetime_h: 5000,
  parts_per_hour_kop: 100,
  scrap_rate_permille: 100,
  wear_per_hour_kop: 700,
}
const QUOTE = (kop: number) => ({
  min_donation_kop: kop,
  breakdown: { plastic_kop: 7800, electricity_kop: 227, wear_kop: 2450, scrap_kop: 1048 },
})

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

function renderApp(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const goTo = (user: ReturnType<typeof userEvent.setup>, name: string) =>
  user.click(
    within(screen.getByRole('navigation', { name: 'Розділи' })).getByRole('link', { name }),
  )

async function changePetgPrice(user: ReturnType<typeof userEvent.setup>) {
  const row = (await screen.findByText('PETG чорний')).closest('tr') as HTMLElement
  await user.click(within(row).getByRole('button', { name: 'Змінити' }))
  const form = screen.getByRole('form', { name: 'Змінити пластик «PETG чорний»' })
  const price = within(form).getByLabelText('Ціна за кг, ₴')
  await user.clear(price)
  await user.type(price, '750')
  await user.click(within(form).getByRole('button', { name: 'Зберегти' }))
  await vi.waitFor(() => expect(screen.queryByRole('form', { name: /Змінити пластик/ })).toBeNull())
}

afterEach(() => vi.unstubAllGlobals())

test('after a plastic price change the catalog never shows the cached old donation (AC-13)', async () => {
  const user = userEvent.setup()
  let changed = false
  const fresh = deferred<Response>()
  const item = (kop: number) => ({ items: [{ id: 't1', name: 'Брелок', min_donation_kop: kop }] })
  mockApi({
    'GET /api/health': json({ status: 'ok', db: 'ok' }),
    'GET /api/pricing/plastics': () =>
      json({
        items: [{ id: 'petg', name: 'PETG чорний', price_per_kg_kop: changed ? 75000 : 65000 }],
      }),
    'GET /api/pricing/settings': json(SETTINGS),
    'PUT /api/pricing/plastics/petg': () => {
      changed = true
      return json({ id: 'petg', name: 'PETG чорний', price_per_kg_kop: 75000 })
    },
    'GET /api/catalog/items': () => (changed ? fresh.promise : json(item(11525))),
  })
  renderApp('/catalog')
  expect(await screen.findByText('115,25 ₴')).toBeInTheDocument()

  await goTo(user, 'Налаштування цін')
  await changePetgPrice(user)
  await goTo(user, 'Каталог')

  expect(screen.queryByText('115,25 ₴')).not.toBeInTheDocument()
  fresh.resolve(json(item(13505)))
  expect(await screen.findByText('135,05 ₴')).toBeInTheDocument()
  expect(screen.queryByText('115,25 ₴')).not.toBeInTheDocument()
})

test('after a plastic price change the same inputs do not show the cached old quote (AC-06)', async () => {
  const user = userEvent.setup()
  let changed = false
  const fresh = deferred<Response>()
  const api = mockApi({
    'GET /api/health': json({ status: 'ok', db: 'ok' }),
    'GET /api/pricing/plastics': () =>
      json({
        items: [{ id: 'petg', name: 'PETG чорний', price_per_kg_kop: changed ? 75000 : 65000 }],
      }),
    'GET /api/pricing/settings': json(SETTINGS),
    'PUT /api/pricing/plastics/petg': () => {
      changed = true
      return json({ id: 'petg', name: 'PETG чорний', price_per_kg_kop: 75000 })
    },
    'POST /api/costing/quote': () => (changed ? fresh.promise : json(QUOTE(11525))),
  })
  const enter = async () => {
    await screen.findByRole('option', { name: 'PETG чорний' })
    await user.selectOptions(screen.getByLabelText('Пластик'), 'PETG чорний')
    await user.type(screen.getByLabelText('Витрата, г'), '120')
    await user.type(screen.getByLabelText('Години'), '3')
    await user.type(screen.getByLabelText('Хвилини'), '30')
  }
  renderApp('/calculate')
  await enter()
  expect(await screen.findByText('115,25 ₴')).toBeInTheDocument()

  await goTo(user, 'Налаштування цін')
  await changePetgPrice(user)
  await goTo(user, 'Розрахунок')
  await enter()
  await vi.waitFor(() => expect(api.callsTo('POST', '/api/costing/quote')).toHaveLength(2))

  expect(screen.queryByText('115,25 ₴')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
  fresh.resolve(json(QUOTE(13505)))
  expect(await screen.findByText('135,05 ₴')).toBeInTheDocument()
})
