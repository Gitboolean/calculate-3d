import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders, type ApiCall } from '@/shared/testing'

import { CalculatePage } from './CalculatePage'

const PLASTICS = [
  { id: 'petg', name: 'PETG чорний', price_per_kg_kop: 65000 },
  { id: 'pla', name: 'PLA білий', price_per_kg_kop: 40000 },
]
const SETTINGS = {
  tariff_per_kwh_kop: 432,
  printer_power_w: 150,
  printer_price_kop: 3000000,
  printer_lifetime_h: 5000,
  parts_per_hour_kop: 100,
  scrap_rate_permille: 100,
  wear_per_hour_kop: 700,
}
const QUOTES: Record<string, unknown> = {
  '[["petg",12000]]|12600': {
    min_donation_kop: 11525,
    breakdown: { plastic_kop: 7800, electricity_kop: 227, wear_kop: 2450, scrap_kop: 1048 },
  },
  '[["pla",8000],["petg",4000]]|7200': {
    min_donation_kop: 8063,
    breakdown: { plastic_kop: 5800, electricity_kop: 130, wear_kop: 1400, scrap_kop: 733 },
  },
}

type Body = { plastics: { plastic_id: string; usage_cg: number }[]; print_time_s: number }

function serve({ plastics = PLASTICS, settings = SETTINGS as typeof SETTINGS | null } = {}) {
  return mockApi({
    'GET /api/pricing/plastics': json({ items: plastics }),
    'GET /api/pricing/settings': json(settings),
    'POST /api/costing/quote': (call: ApiCall) => {
      const body = call.body as Body
      const key = `${JSON.stringify(body.plastics.map((p) => [p.plastic_id, p.usage_cg]))}|${body.print_time_s}`
      return json(
        QUOTES[key] ?? { min_donation_kop: 1, breakdown: QUOTES['[["petg",12000]]|12600'] },
      )
    },
  })
}

afterEach(() => vi.unstubAllGlobals())

async function fillRow(index: number, plastic: string, grams: string) {
  const user = userEvent.setup()
  await user.selectOptions(screen.getAllByLabelText('Пластик')[index] as HTMLElement, plastic)
  const input = screen.getAllByLabelText('Витрата, г')[index] as HTMLElement
  await user.clear(input)
  await user.type(input, grams)
}

async function fillTime(hours: string, minutes: string) {
  const user = userEvent.setup()
  for (const [label, value] of [
    ['Години', hours],
    ['Хвилини', minutes],
  ] as const) {
    const input = screen.getByLabelText(label)
    await user.clear(input)
    if (value) await user.type(input, value)
  }
}

test('the donation and breakdown appear without a separate action (AC-06)', async () => {
  const api = serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')

  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
  expect(screen.getByText('78,00 ₴')).toBeInTheDocument()
  expect(api.callsTo('POST', '/api/costing/quote').at(-1)?.body).toEqual({
    plastics: [{ plastic_id: 'petg', usage_cg: 12000 }],
    print_time_s: 12600,
  })
})

test('several plastics add up (AC-06b)', async () => {
  const user = userEvent.setup()
  serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await fillRow(0, 'PLA білий', '80')
  await user.click(screen.getByRole('button', { name: 'Додати пластик' }))
  await fillRow(1, 'PETG чорний', '40')
  await fillTime('2', '0')

  expect(await screen.findByText('80,63 ₴')).toBeInTheDocument()
  expect(screen.getByText('58,00 ₴')).toBeInTheDocument()
})

test.each([
  ['12,345', '3', '30', 'Витрата — з точністю до 0,01 г'],
  ['0', '3', '30', 'Витрата має бути більшою за нуль'],
  ['120', '3', '60', 'Хвилини — ціле число від 0 до 59'],
  ['120', '0', '0', 'Час друку має бути більшим за нуль'],
  ['120', '2,5', '0', 'Години — ціле невід’ємне число'],
])(
  'invalid usage %j or time %j:%j shows no donation and explains it (AC-07)',
  async (grams, hours, minutes, message) => {
    const api = serve()
    renderWithProviders(<CalculatePage />)
    await screen.findByRole('option', { name: 'PETG чорний' })

    await fillRow(0, 'PETG чорний', grams)
    await fillTime(hours, minutes)

    expect(await screen.findByText(message)).toBeInTheDocument()
    await new Promise((resolve) => setTimeout(resolve, 300))
    expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
    expect(api.callsTo('POST', '/api/costing/quote')).toHaveLength(0)
  },
)

test('the same plastic twice asks to merge the rows (AC-07)', async () => {
  const user = userEvent.setup()
  serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await fillRow(0, 'PETG чорний', '100')
  await user.click(screen.getByRole('button', { name: 'Додати пластик' }))
  await fillRow(1, 'PETG чорний', '20')
  await fillTime('1', '0')

  expect(
    await screen.findByText('Цей пластик уже є в іншому рядку — об’єднайте витрату в одному рядку'),
  ).toBeInTheDocument()
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
})

test('removing every plastic row asks for one (AC-07)', async () => {
  const user = userEvent.setup()
  serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await user.click(screen.getByRole('button', { name: 'Прибрати рядок 1' }))

  expect(screen.getByText('Додайте хоча б один пластик')).toBeInTheDocument()
})

test.each([
  [{ plastics: [] }, 'Бракує налаштувань цін: жодного пластику ще не додано.'],
  [{ settings: null }, 'Бракує налаштувань цін: тариф, потужність, знос і брак ще не збережено.'],
  [
    { plastics: [], settings: null },
    'Бракує налаштувань цін: жодного пластику ще не додано; тариф, потужність, знос і брак ще не збережено.',
  ],
])('missing settings are named with a way to them (AC-09)', async (state, message) => {
  serve(state)
  renderWithProviders(<CalculatePage />)

  expect(await screen.findByText(message)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Перейти до налаштувань цін' })).toHaveAttribute(
    'href',
    '/settings',
  )
  expect(screen.queryByLabelText('Витрата, г')).not.toBeInTheDocument()
})

test('a 409 settings_missing from the server is explained the same way (AC-09)', async () => {
  mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/pricing/settings': json(SETTINGS),
    'POST /api/costing/quote': problem(409, 'costing.settings_missing', {
      missing: ['price_settings'],
    }),
  })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await fillRow(0, 'PETG чорний', '120')
  await fillTime('1', '0')

  expect(
    await screen.findByText(
      'Бракує налаштувань цін: тариф, потужність, знос і брак ще не збережено.',
    ),
  ).toBeInTheDocument()
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
})

test('saving to the catalog becomes available once the donation is shown (AC-10)', async () => {
  serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  const save = screen.getByRole('button', { name: 'Зберегти в каталог' })
  expect(save).toBeDisabled()

  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')

  await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(save).toBeEnabled()
})

async function enterValidParams() {
  await screen.findByRole('option', { name: 'PETG чорний' })
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('1', '0')
}

test('a quote for a plastic deleted meanwhile says so, not "check the fields" (AC-07)', async () => {
  mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/pricing/settings': json(SETTINGS),
    'POST /api/costing/quote': problem(422, 'costing.plastic_not_found', { field: 'plastics.0' }),
  })
  renderWithProviders(<CalculatePage />)
  await enterValidParams()

  expect(
    await screen.findByText('Один із пластиків уже видалено з налаштувань — оберіть інший'),
  ).toBeInTheDocument()
  expect(screen.queryByText(/Перевірте поля/)).not.toBeInTheDocument()
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
})

test.each([
  ['a 500', () => problem(500, 'internal_error')],
  ['a network error', () => Promise.reject(new TypeError('Failed to fetch'))],
])('%s from the quote shows a neutral retry message (AC-07)', async (_name, reply) => {
  mockApi({
    'GET /api/pricing/plastics': json({ items: PLASTICS }),
    'GET /api/pricing/settings': json(SETTINGS),
    'POST /api/costing/quote': reply as () => Response,
  })
  renderWithProviders(<CalculatePage />)
  await enterValidParams()

  expect(await screen.findByText('Не вдалося порахувати. Спробуйте ще раз.')).toBeInTheDocument()
  expect(screen.queryByText(/Перевірте поля/)).not.toBeInTheDocument()
})
