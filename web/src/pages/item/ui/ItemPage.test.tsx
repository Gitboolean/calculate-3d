import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders, type ApiCall } from '@/shared/testing'

import { ItemPage } from './ItemPage'

const PLASTICS = [
  { id: 'petg', name: 'PETG чорний', price_per_kg_kop: 65000 },
  { id: 'pla', name: 'PLA білий', price_per_kg_kop: 40000 },
]
const BREAKDOWN = { plastic_kop: 7800, electricity_kop: 227, wear_kop: 2450, scrap_kop: 1048 }
const ITEM = {
  id: 'i1',
  name: 'Підставка',
  plastics: [{ plastic_id: 'petg', usage_cg: 12000 }],
  print_time_s: 12600,
}

type ItemBody = Omit<typeof ITEM, 'id'>

function serve({ update }: { update?: () => Response } = {}) {
  let item = { ...ITEM }
  let donation = 11525
  return mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/pricing/settings': json({ wear_per_hour_kop: 700 }),
    'GET /api/catalog/items/i1': () =>
      json({ ...item, quote: { min_donation_kop: donation, breakdown: BREAKDOWN } }),
    'POST /api/costing/quote': () => json({ min_donation_kop: 7777, breakdown: BREAKDOWN }),
    'PUT /api/catalog/items/i1': (call: ApiCall) => {
      if (update) return update()
      item = { id: 'i1', ...(call.body as ItemBody) }
      donation = 7777
      return json(item)
    },
    'DELETE /api/catalog/items/i1': json(null, 204),
  })
}

afterEach(() => vi.unstubAllGlobals())

const renderItem = (id = 'i1') =>
  renderWithProviders(<ItemPage />, { path: `/catalog/${id}`, pattern: '/catalog/:itemId' })

test('shows the parameters, donation and breakdown from current prices (AC-14)', async () => {
  serve()
  renderItem()

  expect(await screen.findByRole('heading', { level: 1, name: 'Підставка' })).toBeInTheDocument()
  expect(await screen.findByText('PETG чорний — 120,00 г')).toBeInTheDocument()
  expect(screen.getByText('Час друку: 3 год 30 хв')).toBeInTheDocument()
  const donation = screen.getByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
  expect(screen.getByText('24,50 ₴')).toBeInTheDocument()
})

test('an unknown item says so', async () => {
  mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/catalog/items/gone': problem(404, 'catalog.item_not_found'),
  })
  renderItem('gone')

  expect(await screen.findByText('Виріб не знайдено.')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'До каталогу' })).toHaveAttribute('href', '/catalog')
})

async function startEditing() {
  const user = userEvent.setup()
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })
  await user.click(screen.getByRole('button', { name: 'Змінити' }))
  return user
}

test('an edit saves new parameters and shows the new donation (AC-14b)', async () => {
  const api = serve()
  renderItem()
  const user = await startEditing()

  const name = screen.getByLabelText('Назва виробу')
  expect(name).toHaveValue('Підставка')
  expect(screen.getByLabelText('Витрата, г')).toHaveValue('120,00')
  expect(screen.getByLabelText('Години')).toHaveValue('3')
  expect(screen.getByLabelText('Хвилини')).toHaveValue('30')

  await user.clear(name)
  await user.type(name, 'Підставка XL')
  await user.selectOptions(screen.getByLabelText('Пластик'), 'PLA білий')
  await user.clear(screen.getByLabelText('Витрата, г'))
  await user.type(screen.getByLabelText('Витрата, г'), '80')
  expect(await screen.findByText('77,77 ₴')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Зберегти зміни' }))

  expect(await screen.findByRole('heading', { level: 1, name: 'Підставка XL' })).toBeInTheDocument()
  expect(await screen.findByText('PLA білий — 80,00 г')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')[0]?.body).toEqual({
    name: 'Підставка XL',
    plastics: [{ plastic_id: 'pla', usage_cg: 8000 }],
    print_time_s: 12600,
  })
})

test('an invalid edit is explained and not sent (AC-14c)', async () => {
  const api = serve()
  renderItem()
  const user = await startEditing()

  await user.clear(screen.getByLabelText('Витрата, г'))
  await user.clear(screen.getByLabelText('Назва виробу'))
  await user.click(screen.getByRole('button', { name: 'Зберегти зміни' }))

  expect(screen.getByText('Вкажіть витрату пластику')).toBeInTheDocument()
  expect(screen.getByText('Назва виробу обов’язкова')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(0)
})

test('a rejected edit keeps the form and the item unchanged (AC-14c)', async () => {
  const api = serve({ update: () => problem(409, 'catalog.name_taken', { field: 'name' }) })
  renderItem()
  const user = await startEditing()

  await user.clear(screen.getByLabelText('Назва виробу'))
  await user.type(screen.getByLabelText('Назва виробу'), 'Органайзер')
  await user.click(screen.getByRole('button', { name: 'Зберегти зміни' }))

  expect(await screen.findByText('Виріб з такою назвою вже є в каталозі')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Скасувати' }))
  expect(screen.getByRole('heading', { level: 1, name: 'Підставка' })).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(1)
})

test('deleting after confirmation removes the item and returns to the catalog (AC-15)', async () => {
  const user = userEvent.setup()
  const api = serve()
  renderItem()
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })

  await user.click(screen.getByRole('button', { name: 'Видалити' }))
  await user.click(
    within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Видалити' }),
  )

  expect(await screen.findByText('Інша сторінка')).toBeInTheDocument()
  expect(api.callsTo('DELETE', '/api/catalog/items/i1')).toHaveLength(1)
})

test('cancelling the deletion keeps the item (AC-15)', async () => {
  const user = userEvent.setup()
  const api = serve()
  renderItem()
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })

  await user.click(screen.getByRole('button', { name: 'Видалити' }))
  await user.click(
    within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Скасувати' }),
  )

  expect(screen.getByRole('heading', { level: 1, name: 'Підставка' })).toBeInTheDocument()
  expect(api.callsTo('DELETE', '/api/catalog/items/i1')).toHaveLength(0)
})

function serveWithQuote(quote: () => Response) {
  return mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/pricing/settings': json({ wear_per_hour_kop: 700 }),
    'GET /api/catalog/items/i1': () =>
      json({ ...ITEM, quote: { min_donation_kop: 11525, breakdown: BREAKDOWN } }),
    'POST /api/costing/quote': quote,
  })
}

test.each([
  [
    '409 settings_missing',
    () => problem(409, 'costing.settings_missing', { missing: ['price_settings'] }),
    'Бракує налаштувань цін: тариф, потужність, знос і брак ще не збережено.',
  ],
  [
    '422 plastic_not_found',
    () => problem(422, 'costing.plastic_not_found', { field: 'plastics.0' }),
    'Один із пластиків уже видалено з налаштувань — оберіть інший',
  ],
])('editing: a quote %s is shown and blocks saving (AC-07, AC-09)', async (_n, reply, message) => {
  serveWithQuote(reply)
  renderItem()
  await startEditing()

  expect(await screen.findByText(message)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Зберегти зміни' })).toBeDisabled()
})

test('failing to load plastics shows an error, not an endless loading text', async () => {
  mockApi({
    'GET /api/pricing/plastics': problem(500, 'internal_error'),
    'GET /api/catalog/items/i1': () =>
      json({ ...ITEM, quote: { min_donation_kop: 11525, breakdown: BREAKDOWN } }),
  })
  renderItem()

  expect(await screen.findByText('Не вдалося завантажити пластики.')).toBeInTheDocument()
  expect(screen.queryByText('Завантажую виріб…')).not.toBeInTheDocument()
})

test('missing settings on the item page render inside the page section with a heading (AC-09)', async () => {
  mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/catalog/items/i1': problem(409, 'costing.settings_missing', {
      missing: ['plastics'],
    }),
  })
  renderItem()

  expect(
    await screen.findByText('Бракує налаштувань цін: жодного пластику ще не додано.'),
  ).toBeInTheDocument()
  expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  expect(
    screen.getByText('Бракує налаштувань цін: жодного пластику ще не додано.').closest('section'),
  ).toContainElement(screen.getByRole('heading', { level: 1 }))
})
