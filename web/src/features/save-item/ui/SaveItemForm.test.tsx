import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders, type ApiCall } from '@/shared/testing'

import { SaveItemForm } from './SaveItemForm'

const INPUT = { plastics: [{ plastic_id: 'petg', usage_cg: 12000 }], print_time_s: 12600 }

afterEach(() => vi.unstubAllGlobals())

function renderForm(input: typeof INPUT | null) {
  return renderWithProviders(<SaveItemForm input={input} />, {
    path: '/calculate',
    pattern: '/calculate',
  })
}

async function save(name: string) {
  const user = userEvent.setup()
  if (name) await user.type(screen.getByLabelText('Назва виробу'), name)
  await user.click(screen.getByRole('button', { name: 'Зберегти в каталог' }))
}

test('saves exactly the entered parameters and a name — no price — then opens the item', async () => {
  const api = mockApi({
    'POST /api/catalog/items': (call: ApiCall) =>
      json({ id: 'item-1', ...(call.body as object) }, 201),
  })
  renderForm(INPUT)

  await save('Брелок-тризуб')

  expect(await screen.findByText('Інша сторінка')).toBeInTheDocument()
  expect(api.callsTo('POST', '/api/catalog/items')[0]?.body).toEqual({
    name: 'Брелок-тризуб',
    ...INPUT,
  })
})

test('saving is unavailable while no donation is shown (AC-10)', () => {
  renderForm(null)

  expect(screen.getByRole('button', { name: 'Зберегти в каталог' })).toBeDisabled()
  expect(
    screen.getByText('Зберегти можна, коли розрахунок показує мінімальний донат.'),
  ).toBeInTheDocument()
})

test('an empty name is explained and nothing is sent (AC-11)', async () => {
  const api = mockApi({})
  renderForm(INPUT)

  await save('   ')

  expect(screen.getByText('Назва виробу обов’язкова')).toBeInTheDocument()
  expect(api.calls).toHaveLength(0)
})

test('a name already in the catalog is explained next to the field (AC-11)', async () => {
  mockApi({
    'POST /api/catalog/items': problem(409, 'catalog.name_taken', { field: 'name' }),
  })
  renderForm(INPUT)

  await save('брелок-тризуб')

  expect(await screen.findByText('Виріб з такою назвою вже є в каталозі')).toBeInTheDocument()
  expect(screen.getByLabelText('Назва виробу')).toHaveAttribute('aria-invalid', 'true')
  expect(screen.queryByText('Інша сторінка')).not.toBeInTheDocument()
})

test('a name over 100 characters is explained next to the field and nothing is sent (AC-11)', async () => {
  const api = mockApi({})
  renderForm(INPUT)

  await save('я'.repeat(101))

  expect(screen.getByText('Назва — не довше 100 символів')).toBeInTheDocument()
  expect(screen.getByLabelText('Назва виробу')).toHaveAttribute('aria-invalid', 'true')
  expect(api.callsTo('POST', '/api/catalog/items')).toHaveLength(0)
  expect(api.callsTo('PUT', '/api/catalog/items')).toHaveLength(0)
})
