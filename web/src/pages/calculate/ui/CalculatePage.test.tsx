import { fireEvent, screen, within } from '@testing-library/react'
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
  // vtulka_A from the slicer file: 1 154 cg, 1 h 38 min (print-file-import AC-01).
  '[["pla",1154]]|5880': {
    min_donation_kop: 1882,
    breakdown: { plastic_kop: 462, electricity_kop: 106, wear_kop: 1143, scrap_kop: 171 },
  },
  // the same file after its filament is re-mapped to PETG (AC-08); only an intermediate state.
  '[["petg",1154]]|5880': {
    min_donation_kop: 2500,
    breakdown: { plastic_kop: 750, electricity_kop: 106, wear_kop: 1143, scrap_kop: 171 },
  },
  '[["pla",1154]]|6000': {
    min_donation_kop: 1900,
    breakdown: { plastic_kop: 462, electricity_kop: 108, wear_kop: 1166, scrap_kop: 173 },
  },
  '[["pla",1549],["petg",223]]|5460': {
    min_donation_kop: 2000,
    breakdown: { plastic_kop: 620, electricity_kop: 99, wear_kop: 1062, scrap_kop: 219 },
  },
  '[["pla",1549],["abs",223]]|5460': {
    min_donation_kop: 2100,
    breakdown: { plastic_kop: 700, electricity_kop: 99, wear_kop: 1062, scrap_kop: 239 },
  },
  '[["pla",8000],["petg",4000]]|7200': {
    min_donation_kop: 8063,
    breakdown: { plastic_kop: 5800, electricity_kop: 130, wear_kop: 1400, scrap_kop: 733 },
  },
}

type Body = { plastics: { plastic_id: string; usage_cg: number }[]; print_time_s: number }

function serve({
  plastics = PLASTICS as typeof PLASTICS | (() => typeof PLASTICS),
  settings = SETTINGS as typeof SETTINGS | null,
  parsed = [] as unknown[],
  save = undefined as ((call: ApiCall, n: number) => Response | Promise<Response>) | undefined,
  /** Holds the response of the second parse until this promise settles. */
  holdSecondParse = undefined as Promise<void> | undefined,
} = {}) {
  let parses = 0
  let saves = 0
  return mockApi({
    'POST /api/importing/parse': async () => {
      const n = parses++
      if (n === 1) await holdSecondParse
      return json(parsed[n] ?? parsed.at(-1))
    },
    'POST /api/catalog/items': (call: ApiCall) =>
      save ? save(call, saves++) : json({ id: 'item-1', ...(call.body as object) }, 201),
    'GET /api/pricing/plastics': () =>
      json({ items: typeof plastics === 'function' ? plastics() : plastics }),
    'GET /api/pricing/settings': json(settings),
    'POST /api/costing/quote': (call: ApiCall) => {
      const body = call.body as Body
      const key = `${JSON.stringify(body.plastics.map((p) => [p.plastic_id, p.usage_cg]))}|${body.print_time_s}`
      const quote = QUOTES[key]
      // A stray request (unexpected body) must fail loudly, not get a made-up quote.
      return quote ? json(quote) : problem(500, 'internal_error')
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
  ['1000000,01', '3', '30', 'Витрата — не більше 1 000 000 г'],
  ['120', '100000', '1', 'Час друку — не більше 100 000 год'],
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
    expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
  },
)

test('33 valid plastic rows are over the cap: no donation, no saving (AC-07)', async () => {
  const many = Array.from({ length: 33 }, (_, i) => ({
    id: `p${i}`,
    name: `Пластик ${i}`,
    price_per_kg_kop: 40000,
  }))
  const api = serve({ plastics: many })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'Пластик 32' })

  for (let row = 1; row < 33; row += 1) {
    fireEvent.click(screen.getByRole('button', { name: 'Додати пластик' }))
  }
  const selects = screen.getAllByLabelText('Пластик')
  const grams = screen.getAllByLabelText('Витрата, г')
  expect(selects).toHaveLength(33)
  selects.forEach((select, row) => {
    fireEvent.change(select, { target: { value: `p${row}` } })
    fireEvent.change(grams[row] as HTMLElement, { target: { value: '10' } })
  })
  await fillTime('1', '0')

  expect(await screen.findByText('Не більше 32 пластиків в одному розрахунку')).toBeInTheDocument()
  // every row is valid and distinct: the row count is the only thing wrong
  expect(screen.queryByText(/Цей пластик уже є/)).not.toBeInTheDocument()
  expect(screen.queryByText('Витрата має бути більшою за нуль')).not.toBeInTheDocument()
  expect(screen.queryByText('Вкажіть витрату пластику')).not.toBeInTheDocument()
  expect(
    new Set(screen.getAllByLabelText('Пластик').map((s) => (s as HTMLSelectElement).value)),
  ).toHaveProperty('size', 33)
  await new Promise((resolve) => setTimeout(resolve, 300))
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
  expect(api.callsTo('POST', '/api/costing/quote')).toHaveLength(0)
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
})

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

test.each([
  ['hours', '2,5', '0', 'Години', 'Години — ціле невід’ємне число'],
  ['minutes', '3', '60', 'Хвилини', 'Хвилини — ціле число від 0 до 59'],
])(
  'the %s error is announced on its input via aria-describedby (a11y)',
  async (_field, hours, minutes, label, message) => {
    serve()
    renderWithProviders(<CalculatePage />)
    await screen.findByRole('option', { name: 'PETG чорний' })

    await fillRow(0, 'PETG чорний', '120')
    await fillTime(hours, minutes)

    await screen.findByText(message)
    expect(screen.getByLabelText(label)).toHaveAccessibleDescription(message)
  },
)

test('the combined time error describes both time inputs (a11y)', async () => {
  serve()
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await fillRow(0, 'PETG чорний', '120')
  await fillTime('0', '0')

  const message = 'Час друку має бути більшим за нуль'
  await screen.findByText(message)
  expect(screen.getByLabelText('Години')).toHaveAccessibleDescription(message)
  expect(screen.getByLabelText('Хвилини')).toHaveAccessibleDescription(message)
})

// ── print-file-import: the slicer file fills the calculation (T15) ──
const PLA = 'Bambu PLA Basic @BBL A1M'
const VTULKA = {
  plate: { index: 1, name: '' },
  print_time_s: 5880,
  filaments: [
    {
      filament_name: PLA,
      filament_type: 'PLA',
      filament_color: '#FFFFFF',
      usage_mg: 11540,
      plastic_id: 'pla',
    },
  ],
}
const TWO_COLORS = {
  plate: { index: 1, name: 'mini christmas tree' },
  print_time_s: 5460,
  filaments: [
    { ...VTULKA.filaments[0], filament_color: '#3F8E43', usage_mg: 15490, plastic_id: 'pla' },
    { ...VTULKA.filaments[0], filament_color: '#000000', usage_mg: 2230, plastic_id: null },
  ],
}

async function importFile(name = 'vtulka_A.gcode.3mf') {
  await userEvent.upload(
    screen.getByLabelText('Файл слайсера'),
    new File([new Uint8Array([0x50, 0x4b])], name),
  )
}

test('an imported file replaces every manual row and the time, then prices it (AC-01)', async () => {
  serve({ parsed: [VTULKA] })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  await screen.findByText('115,25 ₴')

  await importFile()

  await vi.waitFor(() => expect(screen.getAllByLabelText('Витрата, г')).toHaveLength(1))
  expect(screen.getByLabelText('Витрата, г')).toHaveValue('11,54')
  expect(screen.getAllByLabelText('Пластик')[0]).toHaveValue('pla')
  expect(screen.getByLabelText('Години')).toHaveValue('1')
  expect(screen.getByLabelText('Хвилини')).toHaveValue('38')
  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('18,82 ₴')).toBeInTheDocument()
})

test('the author can still edit by hand after an import', async () => {
  serve({ parsed: [VTULKA] })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')

  await fillTime('1', '40')

  expect(await screen.findByText('19,00 ₴')).toBeInTheDocument()
})

test('a second import replaces the first, and no donation shows until all are mapped', async () => {
  const user = userEvent.setup()
  serve({ parsed: [VTULKA, TWO_COLORS] })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')

  await importFile('LITTLE_TREES.gcode.3mf')

  expect(await screen.findByText('Пластина 1 · mini christmas tree')).toBeInTheDocument()
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()

  await user.selectOptions(screen.getByLabelText(`Пластик для ${PLA} #000000`), 'petg')

  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('20,00 ₴')).toBeInTheDocument()
  expect(screen.getAllByLabelText('Витрата, г').map((i) => (i as HTMLInputElement).value)).toEqual([
    '15,49',
    '2,23',
  ])
})

test('saving the item sends the filament mappings; only saving sends them (AC-07)', async () => {
  const user = userEvent.setup()
  const api = serve({ parsed: [TWO_COLORS] })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await user.selectOptions(await screen.findByLabelText(`Пластик для ${PLA} #000000`), 'petg')
  await screen.findByText('20,00 ₴')
  expect(api.callsTo('POST', '/api/catalog/items')).toHaveLength(0)

  await user.type(screen.getByLabelText('Назва виробу'), 'Ялинка')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))

  await screen.findByText('Інша сторінка')
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).toEqual({
    name: 'Ялинка',
    plastics: [
      { plastic_id: 'pla', usage_cg: 1549 },
      { plastic_id: 'petg', usage_cg: 223 },
    ],
    print_time_s: 5460,
    filament_mappings: [
      { filament_name: PLA, filament_color: '#3F8E43', plastic_id: 'pla' },
      { filament_name: PLA, filament_color: '#000000', plastic_id: 'petg' },
    ],
  })
})

test('a manual calculation is saved without filament mappings', async () => {
  const user = userEvent.setup()
  const api = serve()
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  await screen.findByText('115,25 ₴')

  await user.type(screen.getByLabelText('Назва виробу'), 'Брелок')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))

  await screen.findByText('Інша сторінка')
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).not.toHaveProperty('filament_mappings')
})

const GONE = 'Пластик, обраний для філамента з файлу, уже видалено — оберіть інший.'

test('cancelling an import drops the mapping panel and its mappings from a later save (F4)', async () => {
  const user = userEvent.setup()
  const api = serve({ parsed: [TWO_COLORS] })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByRole('region', { name: 'Філаменти з файлу' })
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))

  expect(screen.queryByRole('region', { name: 'Філаменти з файлу' })).not.toBeInTheDocument()
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeEnabled()

  await user.type(screen.getByLabelText('Назва виробу'), 'Брелок')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await screen.findByText('Інша сторінка')
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).not.toHaveProperty('filament_mappings')
})

test('a save rejected for a deleted mapped plastic says so and asks for the plastic again (F5)', async () => {
  const user = userEvent.setup()
  serve({
    parsed: [VTULKA],
    save: () =>
      problem(422, 'importing.plastic_not_found', { field: 'filament_mappings.0.plastic_id' }),
  })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')
  await user.type(screen.getByLabelText('Назва виробу'), 'Втулка')

  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))

  expect(await screen.findByText(GONE)).toBeInTheDocument()
  expect(screen.queryByText(/Спробуйте ще раз/)).not.toBeInTheDocument()
  expect(screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`)).toHaveValue('')
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
})

test('a deleted mapped plastic disappears from the plastic choices after the rejected save (R4)', async () => {
  const user = userEvent.setup()
  let deleted = false
  serve({
    parsed: [VTULKA],
    plastics: () => (deleted ? PLASTICS.filter((p) => p.id !== 'pla') : PLASTICS),
    save: () => {
      deleted = true
      return problem(422, 'importing.plastic_not_found', {
        field: 'filament_mappings.0.plastic_id',
      })
    },
  })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')
  await user.type(screen.getByLabelText('Назва виробу'), 'Втулка')
  expect(screen.getAllByRole('option', { name: 'PLA білий' }).length).toBeGreaterThan(0)

  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))

  expect(await screen.findByText(GONE)).toBeInTheDocument()
  await vi.waitFor(() =>
    expect(screen.queryAllByRole('option', { name: 'PLA білий' })).toHaveLength(0),
  )
})

test('a re-chosen plastic survives manual row edits and is what gets saved (AC-08)', async () => {
  const user = userEvent.setup()
  const api = serve({ parsed: [VTULKA] })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')
  await user.selectOptions(screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`), 'petg')
  await vi.waitFor(() => expect(screen.getAllByLabelText('Пластик')[0]).toHaveValue('petg'))

  await user.click(screen.getByRole('button', { name: 'Прибрати рядок 1' }))
  await user.click(screen.getByRole('button', { name: 'Додати пластик' }))
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  await screen.findByText('115,25 ₴')
  await user.type(screen.getByLabelText('Назва виробу'), 'Втулка')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))

  await screen.findByText('Інша сторінка')
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).toMatchObject({
    plastics: [{ plastic_id: 'petg', usage_cg: 12000 }],
    filament_mappings: [{ filament_name: PLA, filament_color: '#FFFFFF', plastic_id: 'petg' }],
  })
  expect(
    (api.callsTo('POST', '/api/catalog/items')[0]?.body as { filament_mappings: unknown[] })
      .filament_mappings,
  ).toHaveLength(1)
})

test('an imported usage over 1 000 000 g is explained: no donation, no saving (AC-14)', async () => {
  const api = serve({
    parsed: [{ ...VTULKA, filaments: [{ ...VTULKA.filaments[0], usage_mg: 1_000_000_010 }] }],
  })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await importFile()

  expect(await screen.findByText('Витрата — не більше 1 000 000 г')).toBeInTheDocument()
  await new Promise((resolve) => setTimeout(resolve, 300))
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
  expect(api.callsTo('POST', '/api/costing/quote')).toHaveLength(0)
  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
})

test('an imported 11 543 mg shows as 11,55 g, rounded up (AC-03)', async () => {
  serve({
    parsed: [{ ...VTULKA, filaments: [{ ...VTULKA.filaments[0], usage_mg: 11_543 }] }],
  })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })

  await importFile()

  await vi.waitFor(() => expect(screen.getByLabelText('Витрата, г')).toHaveValue('11,55'))
})

const CONFLICT = {
  plate: { index: 1, name: 'two whites' },
  print_time_s: 7200,
  filaments: [
    { ...VTULKA.filaments[0], filament_color: '#FFFFFF', usage_mg: 80000, plastic_id: 'pla' },
    { ...VTULKA.filaments[0], filament_color: '#EEEEEE', usage_mg: 40000, plastic_id: 'pla' },
  ],
}

test('importing the same conflicting file again asks about the merge again (AC-10)', async () => {
  const user = userEvent.setup()
  serve({ parsed: [CONFLICT] })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile('two_whites.gcode.3mf')
  const first = await screen.findByRole('alertdialog')
  await user.click(within(first).getByRole('button', { name: 'Обрати інший пластик' }))
  await vi.waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())

  await importFile('two_whites.gcode.3mf')

  const again = await screen.findByRole('alertdialog')
  expect(within(again).getByText('Це справді той самий пластик?')).toBeInTheDocument()
})

test('cancelling a ready import restores the manual rows, time and donation (AC-07)', async () => {
  const user = userEvent.setup()
  const api = serve({ parsed: [VTULKA] })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  await screen.findByText('115,25 ₴')
  await importFile()
  await screen.findByText('18,82 ₴')

  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))

  expect(screen.queryByRole('region', { name: 'Філаменти з файлу' })).not.toBeInTheDocument()
  expect(screen.getAllByLabelText('Пластик')[0]).toHaveValue('petg')
  expect(screen.getByLabelText('Витрата, г')).toHaveValue('120')
  expect(screen.getByLabelText('Години')).toHaveValue('3')
  expect(screen.getByLabelText('Хвилини')).toHaveValue('30')
  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
  expect(screen.queryByText('18,82 ₴')).not.toBeInTheDocument()

  await user.type(screen.getByLabelText('Назва виробу'), 'Брелок')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await screen.findByText('Інша сторінка')
  const body = api.callsTo('POST', '/api/catalog/items')[0]?.body
  expect(body).not.toHaveProperty('filament_mappings')
  expect(body).toMatchObject({
    plastics: [{ plastic_id: 'petg', usage_cg: 12000 }],
    print_time_s: 12600,
  })
})

test('cancelling a ready import over an empty form leaves it empty, no donation (AC-07)', async () => {
  const user = userEvent.setup()
  serve({ parsed: [VTULKA] })
  renderWithProviders(<CalculatePage />)
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('18,82 ₴')

  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))

  expect(screen.getByLabelText('Витрата, г')).toHaveValue('')
  expect(screen.getAllByLabelText('Пластик')[0]).toHaveValue('')
  expect(screen.getByLabelText('Години')).toHaveValue('')
  expect(screen.queryByRole('status', { name: 'Мінімальний донат' })).not.toBeInTheDocument()
  expect(screen.queryByText('18,82 ₴')).not.toBeInTheDocument()
})

// The same file with another print time: a second ready import with its own quote.
const VTULKA_B = { ...VTULKA, print_time_s: 6000 }

async function manual120() {
  await screen.findByRole('option', { name: 'PETG чорний' })
  await fillRow(0, 'PETG чорний', '120')
  await fillTime('3', '30')
  await screen.findByText('115,25 ₴')
}

async function expectManualForm() {
  expect(screen.queryByRole('region', { name: 'Філаменти з файлу' })).not.toBeInTheDocument()
  expect(screen.getAllByLabelText('Пластик')[0]).toHaveValue('petg')
  expect(screen.getByLabelText('Витрата, г')).toHaveValue('120')
  expect(screen.getByLabelText('Години')).toHaveValue('3')
  expect(screen.getByLabelText('Хвилини')).toHaveValue('30')
  const donation = await screen.findByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
}

test('cancelling while a re-import is parsing still brings back the manual form (AC-07)', async () => {
  const user = userEvent.setup()
  let release = () => {}
  const held = new Promise<void>((resolve) => (release = resolve))
  const api = serve({ parsed: [VTULKA, VTULKA_B], holdSecondParse: held })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await manual120()
  await importFile()
  await screen.findByText('18,82 ₴')
  await importFile('vtulka_B.gcode.3mf')
  await screen.findByRole('button', { name: 'Імпортую…' })

  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))
  release()
  await screen.findByRole('button', { name: 'Імпортувати файл' })
  // The late file is shown as a fresh import (B); cancelling it ends on the manual form.
  const late = await screen.findByRole('region', { name: 'Філаменти з файлу' })
  expect(within(late).getByText(PLA)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))

  await expectManualForm()
  await user.type(screen.getByLabelText('Назва виробу'), 'Брелок')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await screen.findByText('Інша сторінка')
  const body = api.callsTo('POST', '/api/catalog/items')[0]?.body
  expect(body).not.toHaveProperty('filament_mappings')
  expect(body).toMatchObject({
    plastics: [{ plastic_id: 'petg', usage_cg: 12000 }],
    print_time_s: 12600,
  })
})

test('cancelling after two imports restores the form from before the first one (AC-07)', async () => {
  const user = userEvent.setup()
  const api = serve({ parsed: [VTULKA, VTULKA_B] })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await manual120()
  await importFile()
  await screen.findByText('18,82 ₴')
  await importFile('vtulka_B.gcode.3mf')
  await screen.findByText('19,00 ₴')

  await user.click(screen.getByRole('button', { name: 'Скасувати імпорт' }))

  await expectManualForm()
  expect(screen.queryByText('19,00 ₴')).not.toBeInTheDocument()
  await user.type(screen.getByLabelText('Назва виробу'), 'Брелок')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await screen.findByText('Інша сторінка')
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).not.toHaveProperty('filament_mappings')
})

test('a rejected save clears only the rejected choice, not one made while it was saving (AC-07, AC-08)', async () => {
  const user = userEvent.setup()
  let release = () => {}
  const held = new Promise<void>((resolve) => (release = resolve))
  const two = {
    ...TWO_COLORS,
    filaments: [TWO_COLORS.filaments[0], { ...TWO_COLORS.filaments[1], plastic_id: 'petg' }],
  }
  const api = serve({
    parsed: [two],
    plastics: [...PLASTICS, { id: 'abs', name: 'ABS сірий', price_per_kg_kop: 50000 }],
    save: async () => {
      await held
      return problem(422, 'importing.plastic_not_found', {
        field: 'filament_mappings.0.plastic_id',
      })
    },
  })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await screen.findByRole('option', { name: 'PETG чорний' })
  await importFile()
  await screen.findByText('20,00 ₴')
  await user.type(screen.getByLabelText('Назва виробу'), 'Ялинка')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await vi.waitFor(() => expect(api.callsTo('POST', '/api/catalog/items')).toHaveLength(1))

  await user.selectOptions(screen.getByLabelText(`Пластик для ${PLA} #000000`), 'abs')
  release()

  await screen.findByText('Пластик, обраний для філамента з файлу, уже видалено — оберіть інший.')
  expect(screen.getByLabelText(`Пластик для ${PLA} #3F8E43`)).toHaveValue('')
  expect(screen.getByLabelText(`Пластик для ${PLA} #000000`)).toHaveValue('abs')
})

test('«Скасувати імпорт» is disabled while the save is in flight (AC-07, R5)', async () => {
  const user = userEvent.setup()
  let release = () => {}
  const held = new Promise<void>((resolve) => (release = resolve))
  const api = serve({
    parsed: [VTULKA],
    save: async (call) => {
      await held
      return json({ id: 'item-1', ...(call.body as object) }, 201)
    },
  })
  renderWithProviders(<CalculatePage />, { path: '/calculate', pattern: '/calculate' })
  await manual120()
  await importFile()
  await screen.findByText('18,82 ₴')
  await user.type(screen.getByLabelText('Назва виробу'), 'Втулка')
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
  await vi.waitFor(() => expect(api.callsTo('POST', '/api/catalog/items')).toHaveLength(1))

  expect(screen.getByRole('button', { name: 'Скасувати імпорт' })).toBeDisabled()
  release()
  await screen.findByText('Інша сторінка')
})
