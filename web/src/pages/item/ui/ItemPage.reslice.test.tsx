import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders, type ApiCall } from '@/shared/testing'

import { ItemPage } from './ItemPage'

const PLASTICS = [
  { id: 'petg', name: 'PETG чорний', price_per_kg_kop: 65000 },
  { id: 'pla', name: 'PLA білий', price_per_kg_kop: 40000 },
]
const BREAKDOWN = { plastic_kop: 1, electricity_kop: 1, wear_kop: 1, scrap_kop: 1 }
const PLA = 'Bambu PLA Basic @BBL A1M'
// AC-05: «Підставка» PLA 80 g + PETG 40 g, 2 h 0 min, 80,63 ₴.
const SAVED = {
  id: 'i1',
  name: 'Підставка',
  plastics: [
    { plastic_id: 'pla', usage_cg: 8000 },
    { plastic_id: 'petg', usage_cg: 4000 },
  ],
  print_time_s: 7200,
}
const RESLICED = {
  plate: { index: 1, name: '' },
  print_time_s: 8100,
  filaments: [
    {
      filament_name: PLA,
      filament_type: 'PLA',
      filament_color: '#FFFFFF',
      usage_mg: 95000,
      plastic_id: 'pla',
    },
  ],
}
const QUOTES: Record<string, number> = {
  '[["pla",8000],["petg",4000]]|7200': 8063,
  '[["pla",9500]]|8100': 6073,
  '[["pla",9600]]|8100': 6150,
  '[["pla",9500],["petg",2000]]|8100': 7000,
  '[["pla",9500],["abs",2000]]|8100': 7100,
}

type Body = { plastics: { plastic_id: string; usage_cg: number }[]; print_time_s: number }
const keyOf = (b: Body) =>
  `${JSON.stringify(b.plastics.map((p) => [p.plastic_id, p.usage_cg]))}|${b.print_time_s}`

function serve({
  parse = () => json(RESLICED),
  items = [SAVED] as (typeof SAVED)[],
  update = undefined as ((call: ApiCall) => Response | Promise<Response>) | undefined,
  plastics = (() => PLASTICS) as () => typeof PLASTICS,
} = {}) {
  let reads = 0
  return mockApi({
    'GET /api/pricing/plastics': () => json({ items: plastics() }),
    'GET /api/catalog/items/i1': () => {
      const item = items[Math.min(reads++, items.length - 1)] ?? SAVED
      const kop = QUOTES[keyOf(item)] ?? 1
      return json({ ...item, quote: { min_donation_kop: kop, breakdown: BREAKDOWN } })
    },
    'POST /api/costing/quote': (call: ApiCall) => {
      const kop = QUOTES[keyOf(call.body as Body)]
      return kop ? json({ min_donation_kop: kop, breakdown: BREAKDOWN }) : problem(500, 'x')
    },
    'POST /api/importing/parse': parse,
    'PUT /api/catalog/items/i1': (call: ApiCall) =>
      update ? update(call) : json({ id: 'i1', ...(call.body as object) }),
  })
}

afterEach(() => vi.unstubAllGlobals())

const renderItem = () =>
  renderWithProviders(<ItemPage />, { path: '/catalog/i1', pattern: '/catalog/:itemId' })

async function importResliced() {
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })
  await userEvent.upload(
    screen.getByLabelText('Файл слайсера'),
    new File([new Uint8Array([0x50, 0x4b])], 'pidstavka.gcode.3mf'),
  )
  return screen.findByRole('region', { name: 'Було → стало' })
}

test('a re-sliced file shows «було → стало» before anything is saved (AC-05)', async () => {
  const api = serve()
  renderItem()

  const panel = await importResliced()

  expect(within(panel).getByText('PLA білий: 80 г → 95 г')).toBeInTheDocument()
  expect(within(panel).getByText('PETG чорний: 40 г → прибрано')).toBeInTheDocument()
  expect(within(panel).getByText('Час друку: 2 год 0 хв → 2 год 15 хв')).toBeInTheDocument()
  expect(await within(panel).findByText('Мінімальний донат: 80,63 ₴ → 60,73 ₴')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(0)
})

test('confirming saves exactly the new parameters and mappings, name unchanged (AC-05)', async () => {
  const user = userEvent.setup()
  const api = serve()
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/60,73 ₴/)

  await user.click(within(panel).getByRole('button', { name: 'Підтвердити' }))

  await vi.waitFor(() => expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(1))
  expect(api.callsTo('PUT', '/api/catalog/items/i1')[0]?.body).toEqual({
    name: 'Підставка',
    plastics: [{ plastic_id: 'pla', usage_cg: 9500 }],
    print_time_s: 8100,
    filament_mappings: [{ filament_name: PLA, filament_color: '#FFFFFF', plastic_id: 'pla' }],
  })
})

test('a manual edit before confirming recomputes «стало» (AC-05, AC-14b)', async () => {
  const user = userEvent.setup()
  serve()
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/60,73 ₴/)

  const grams = screen.getByLabelText('Витрата, г')
  await user.clear(grams)
  await user.type(grams, '96')

  expect(await within(panel).findByText('PLA білий: 80 г → 96 г')).toBeInTheDocument()
  expect(await within(panel).findByText('Мінімальний донат: 80,63 ₴ → 61,50 ₴')).toBeInTheDocument()
})

test('cancelling sends nothing and keeps the saved item (AC-06)', async () => {
  const user = userEvent.setup()
  const api = serve()
  renderItem()
  const panel = await importResliced()

  await user.click(within(panel).getByRole('button', { name: 'Скасувати' }))

  expect(screen.queryByRole('region', { name: 'Було → стало' })).not.toBeInTheDocument()
  expect(screen.getByText('PLA білий — 80,00 г')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(0)
})

test('a rejected file changes nothing and sends no update (AC-06)', async () => {
  const api = serve({ parse: () => problem(422, 'importing.not_sliced') })
  renderItem()
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })

  await userEvent.upload(
    screen.getByLabelText('Файл слайсера'),
    new File([new Uint8Array([0x50, 0x4b])], 'project.3mf'),
  )

  expect(await screen.findByRole('alert')).toHaveTextContent('Файл не нарізаний')
  expect(screen.queryByRole('region', { name: 'Було → стало' })).not.toBeInTheDocument()
  expect(screen.getByText('PLA білий — 80,00 г')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(0)
})

test('«було» is the item as saved now — fresh from the server, not unsaved edits', async () => {
  const user = userEvent.setup()
  // Someone else saved 90 g meanwhile; the open page still shows 80 g.
  const changed = { ...SAVED, plastics: [{ plastic_id: 'pla', usage_cg: 9000 }] }
  serve({ items: [SAVED, changed] })
  renderItem()
  await screen.findByRole('heading', { level: 1, name: 'Підставка' })
  await user.click(screen.getByRole('button', { name: 'Змінити' }))
  const grams = screen.getAllByLabelText('Витрата, г')[0] as HTMLElement
  await user.clear(grams)
  await user.type(grams, '70')

  const panel = await importResliced()

  expect(within(panel).getByText('PLA білий: 90 г → 95 г')).toBeInTheDocument()
  expect(within(panel).queryByText(/70 г/)).not.toBeInTheDocument()
})

test('confirming with a mapped plastic deleted meanwhile says so, not "try again" (F5)', async () => {
  const user = userEvent.setup()
  serve({
    update: () =>
      problem(422, 'importing.plastic_not_found', { field: 'filament_mappings.0.plastic_id' }),
  })
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/60,73 ₴/)

  await user.click(within(panel).getByRole('button', { name: 'Підтвердити' }))

  expect(
    await screen.findByText(
      'Пластик, обраний для філамента з файлу, уже видалено — оберіть інший.',
    ),
  ).toBeInTheDocument()
  expect(screen.queryByText(/Спробуйте ще раз/)).not.toBeInTheDocument()
  expect(screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`)).toHaveValue('')
  expect(within(panel).getByRole('button', { name: 'Підтвердити' })).toBeDisabled()
})

test('a deleted mapped plastic disappears from the plastic choices after the rejected confirm (R4)', async () => {
  const user = userEvent.setup()
  let deleted = false
  serve({
    plastics: () => (deleted ? PLASTICS.filter((p) => p.id !== 'pla') : PLASTICS),
    update: () => {
      deleted = true
      return problem(422, 'importing.plastic_not_found', {
        field: 'filament_mappings.0.plastic_id',
      })
    },
  })
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/60,73 ₴/)
  const select = screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`)
  expect(within(select).getByRole('option', { name: 'PLA білий' })).toBeInTheDocument()

  await user.click(within(panel).getByRole('button', { name: 'Підтвердити' }))

  await screen.findByText('Пластик, обраний для філамента з файлу, уже видалено — оберіть інший.')
  await vi.waitFor(() =>
    expect(
      within(screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`)).queryByRole('option', {
        name: 'PLA білий',
      }),
    ).not.toBeInTheDocument(),
  )
})

const NEW_PARAMS = {
  ...SAVED,
  plastics: [{ plastic_id: 'pla', usage_cg: 9500 }],
  print_time_s: 8100,
}

test('«Скасувати» is disabled while the confirm is saving; the panel closes when it lands (AC-06, R5)', async () => {
  const user = userEvent.setup()
  let release = () => {}
  const held = new Promise<void>((resolve) => (release = resolve))
  const api = serve({
    items: [SAVED, SAVED, NEW_PARAMS],
    update: async (call) => {
      await held
      return json({ id: 'i1', ...(call.body as object) })
    },
  })
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/60,73 ₴/)

  await user.click(within(panel).getByRole('button', { name: 'Підтвердити' }))
  await vi.waitFor(() => expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(1))

  expect(within(panel).getByRole('button', { name: 'Скасувати' })).toBeDisabled()
  release()
  await vi.waitFor(() =>
    expect(screen.queryByRole('region', { name: 'Було → стало' })).not.toBeInTheDocument(),
  )
  expect(await screen.findByText('PLA білий — 95,00 г')).toBeInTheDocument()
})

test('a rejected confirm clears only the rejected choice, not one made while it was saving (R6)', async () => {
  const user = userEvent.setup()
  let release = () => {}
  const held = new Promise<void>((resolve) => (release = resolve))
  const two = {
    ...RESLICED,
    filaments: [
      RESLICED.filaments[0],
      {
        filament_name: PLA,
        filament_type: 'PLA',
        filament_color: '#000000',
        usage_mg: 20000,
        plastic_id: 'petg',
      },
    ],
  }
  const api = serve({
    parse: () => json(two),
    plastics: () => [...PLASTICS, { id: 'abs', name: 'ABS сірий', price_per_kg_kop: 50000 }],
    update: async () => {
      await held
      return problem(422, 'importing.plastic_not_found', {
        field: 'filament_mappings.0.plastic_id',
      })
    },
  })
  renderItem()
  const panel = await importResliced()
  await within(panel).findByText(/70,00 ₴/)
  await user.click(within(panel).getByRole('button', { name: 'Підтвердити' }))
  await vi.waitFor(() => expect(api.callsTo('PUT', '/api/catalog/items/i1')).toHaveLength(1))

  await user.selectOptions(screen.getByLabelText(`Пластик для ${PLA} #000000`), 'abs')
  release()

  await screen.findByText('Пластик, обраний для філамента з файлу, уже видалено — оберіть інший.')
  expect(screen.getByLabelText(`Пластик для ${PLA} #FFFFFF`)).toHaveValue('')
  expect(screen.getByLabelText(`Пластик для ${PLA} #000000`)).toHaveValue('abs')
})
