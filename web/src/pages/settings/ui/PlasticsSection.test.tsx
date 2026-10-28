import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, problem, renderWithProviders, type ApiCall } from '@/shared/testing'

import { PlasticsSection } from './PlasticsSection'

const PLA = { id: 'pla', name: 'PLA білий', price_per_kg_kop: 40000 }

function serve(initial: (typeof PLA)[]) {
  let plastics = [...initial]
  return mockApi({
    'GET /api/pricing/plastics': () => json({ items: plastics }),
    'POST /api/pricing/plastics': (call: ApiCall) => {
      const created = { id: 'new', ...(call.body as { name: string; price_per_kg_kop: number }) }
      plastics = [...plastics, created]
      return json(created, 201)
    },
    'PUT /api/pricing/plastics/pla': (call: ApiCall) => {
      plastics = [{ id: 'pla', ...(call.body as { name: string; price_per_kg_kop: number }) }]
      return json(plastics[0])
    },
    'DELETE /api/pricing/plastics/pla': problem(409, 'pricing.plastic_in_use', {
      items: ['Органайзер', 'Підставка'],
    }),
  })
}

afterEach(() => vi.unstubAllGlobals())

async function findRow(name: string) {
  const row = (await screen.findByText(name)).closest('tr')
  if (!row) throw new Error(`no table row for ${name}`)
  return row
}

async function addPlastic(name: string, price: string) {
  const user = userEvent.setup()
  const form = screen.getByRole('form', { name: 'Додати пластик' })
  if (name) await user.type(within(form).getByLabelText('Назва'), name)
  if (price) await user.type(within(form).getByLabelText('Ціна за кг, ₴'), price)
  await user.click(within(form).getByRole('button', { name: 'Додати' }))
  return form
}

test('lists plastics with their price per kilogram', async () => {
  serve([PLA])
  renderWithProviders(<PlasticsSection />)

  const row = await findRow('PLA білий')
  expect(within(row).getByText('400,00 ₴')).toBeInTheDocument()
})

test('an added plastic appears in the list; a comma decimal is accepted', async () => {
  const api = serve([])
  renderWithProviders(<PlasticsSection />)
  await screen.findByText('Пластиків ще немає')

  await addPlastic('PETG чорний', '650,5')

  expect(await screen.findByText('PETG чорний')).toBeInTheDocument()
  expect(screen.getByText('650,50 ₴')).toBeInTheDocument()
  expect(api.callsTo('POST', '/api/pricing/plastics')[0]?.body).toEqual({
    name: 'PETG чорний',
    price_per_kg_kop: 65050,
  })
})

test.each([
  ['   ', '650', 'Назва обов’язкова'],
  ['PETG', '', 'Вкажіть ціну за кілограм'],
  ['PETG', 'abc', 'Ціна має бути числом'],
  ['PETG', '649,995', 'Ціна — з точністю до копійки (не більше двох знаків після коми)'],
  ['PETG', '0', 'Ціна має бути більшою за нуль'],
  ['PETG', '-5', 'Ціна має бути більшою за нуль'],
])(
  'invalid input %j / %j is explained next to the field and not sent',
  async (name, price, message) => {
    const api = serve([])
    renderWithProviders(<PlasticsSection />)
    await screen.findByText('Пластиків ще немає')

    const form = await addPlastic(name, price)

    expect(within(form).getByText(message)).toBeInTheDocument()
    expect(api.callsTo('POST', '/api/pricing/plastics')).toHaveLength(0)
  },
)

test('a taken name is reported next to the name field', async () => {
  serve([PLA])
  mockApi({
    'GET /api/pricing/plastics': json({ items: [PLA] }),
    'POST /api/pricing/plastics': problem(409, 'pricing.name_taken', { field: 'name' }),
  })
  renderWithProviders(<PlasticsSection />)
  await screen.findByText('PLA білий')

  const form = await addPlastic('pla білий', '400')

  const name = within(form).getByLabelText('Назва')
  expect(await within(form).findByText('Пластик з такою назвою вже є')).toBeInTheDocument()
  expect(name).toHaveAttribute('aria-invalid', 'true')
})

test('a plastic used by items is not deleted and the items are named', async () => {
  const user = userEvent.setup()
  const api = serve([PLA])
  renderWithProviders(<PlasticsSection />)
  const row = await findRow('PLA білий')

  await user.click(within(row).getByRole('button', { name: 'Видалити' }))
  await user.click(
    within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Видалити' }),
  )

  expect(
    await screen.findByText(
      'Пластик «PLA білий» не можна видалити: його використовують вироби Органайзер, Підставка.',
    ),
  ).toBeInTheDocument()
  expect(api.callsTo('DELETE', '/api/pricing/plastics/pla')).toHaveLength(1)
  expect(screen.getByText('PLA білий')).toBeInTheDocument()
})

test('cancelling the confirmation deletes nothing', async () => {
  const user = userEvent.setup()
  const api = serve([PLA])
  renderWithProviders(<PlasticsSection />)
  const row = await findRow('PLA білий')

  await user.click(within(row).getByRole('button', { name: 'Видалити' }))
  await user.click(
    within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Скасувати' }),
  )

  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  expect(api.callsTo('DELETE', '/api/pricing/plastics/pla')).toHaveLength(0)
})

test('a plastic price can be changed', async () => {
  const user = userEvent.setup()
  const api = serve([PLA])
  renderWithProviders(<PlasticsSection />)
  const row = await findRow('PLA білий')

  await user.click(within(row).getByRole('button', { name: 'Змінити' }))
  const form = screen.getByRole('form', { name: 'Змінити пластик «PLA білий»' })
  const price = within(form).getByLabelText('Ціна за кг, ₴')
  expect(price).toHaveValue('400,00')
  await user.clear(price)
  await user.type(price, '450')
  await user.click(within(form).getByRole('button', { name: 'Зберегти' }))

  expect(await screen.findByText('450,00 ₴')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/pricing/plastics/pla')[0]?.body).toEqual({
    name: 'PLA білий',
    price_per_kg_kop: 45000,
  })
})

test('names are rendered as plain text', async () => {
  serve([{ ...PLA, name: '<b>PLA</b>' }])
  renderWithProviders(<PlasticsSection />)

  expect(await screen.findByText('<b>PLA</b>')).toBeInTheDocument()
})
