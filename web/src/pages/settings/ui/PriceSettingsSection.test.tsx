import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { json, mockApi, renderWithProviders, type ApiCall } from '@/shared/testing'

import { PriceSettingsSection } from './PriceSettingsSection'

const AC04 = {
  tariff_per_kwh_kop: 432,
  printer_power_w: 150,
  printer_price_kop: 3000000,
  printer_lifetime_h: 5000,
  parts_per_hour_kop: 100,
  scrap_rate_permille: 100,
}

const LABELS = {
  tariff: 'Тариф, ₴ за кВт·год',
  power: 'Потужність принтера, Вт',
  price: 'Ціна принтера, ₴',
  lifetime: 'Термін служби, годин друку',
  parts: 'Деталі, ₴ за годину друку',
  scrap: 'Брак, %',
} as const

const RULES = {
  tariff: 'Тариф — число від 0 з точністю до копійки',
  power: 'Потужність — ціле число ват від 0',
  price: 'Ціна принтера — число від 0 з точністю до копійки',
  lifetime: 'Термін служби — ціле число годин, більше за 0',
  parts: 'Деталі — число від 0 з точністю до копійки',
  scrap: 'Брак — від 0 до 100 % з точністю до 0,1',
} as const

type Field = keyof typeof LABELS

function serve(saved: typeof AC04 | null) {
  return mockApi({
    'GET /api/pricing/settings': () =>
      json(
        saved && {
          ...saved,
          wear_per_hour_kop:
            Math.round(saved.printer_price_kop / saved.printer_lifetime_h) +
            saved.parts_per_hour_kop,
        },
      ),
    'PUT /api/pricing/settings': (call: ApiCall) => {
      saved = call.body as typeof AC04
      return json({ ...saved, wear_per_hour_kop: 700 })
    },
  })
}

afterEach(() => vi.unstubAllGlobals())

async function fill(values: Partial<Record<Field, string>>) {
  const user = userEvent.setup()
  const form = await screen.findByRole('form', { name: 'Налаштування цін' })
  for (const [field, value] of Object.entries(values) as [Field, string][]) {
    const input = within(form).getByLabelText(LABELS[field])
    await user.clear(input)
    if (value) await user.type(input, value)
  }
  await user.click(within(form).getByRole('button', { name: 'Зберегти налаштування' }))
  return form
}

const VALID: Record<Field, string> = {
  tariff: '4,32',
  power: '150',
  price: '30 000',
  lifetime: '5000',
  parts: '1,00',
  scrap: '10',
}

test('all six settings are saved together and wear per hour is shown', async () => {
  const api = serve(null)
  renderWithProviders(<PriceSettingsSection />)

  await fill(VALID)

  expect(await screen.findByText('Знос за годину друку: 7,00 ₴')).toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/pricing/settings')).toHaveLength(1)
  expect(api.callsTo('PUT', '/api/pricing/settings')[0]?.body).toEqual(AC04)
})

test('saved settings pre-fill the form', async () => {
  serve(AC04)
  renderWithProviders(<PriceSettingsSection />)

  const form = await screen.findByRole('form', { name: 'Налаштування цін' })

  expect(within(form).getByLabelText(LABELS.tariff)).toHaveValue('4,32')
  expect(within(form).getByLabelText(LABELS.price)).toHaveValue('30000,00')
  expect(within(form).getByLabelText(LABELS.scrap)).toHaveValue('10,0')
  expect(screen.getByText('Знос за годину друку: 7,00 ₴')).toBeInTheDocument()
})

test.each<[Field, string]>([
  ['tariff', ''],
  ['tariff', '4,3216'],
  ['tariff', '-1'],
  ['power', '152,5'],
  ['power', 'abc'],
  ['price', '-100'],
  ['lifetime', '0'],
  ['lifetime', '2,5'],
  ['parts', '1,005'],
  ['scrap', '7,25'],
  ['scrap', '101'],
  ['scrap', '-0,1'],
])('%s = %j is explained next to the field and nothing is sent', async (field, value) => {
  const api = serve(null)
  renderWithProviders(<PriceSettingsSection />)

  const form = await fill({ ...VALID, [field]: value })

  expect(within(form).getByText(RULES[field])).toBeInTheDocument()
  expect(within(form).getByLabelText(LABELS[field])).toHaveAttribute('aria-invalid', 'true')
  expect(api.callsTo('PUT', '/api/pricing/settings')).toHaveLength(0)
})

test('every invalid field is explained at once', async () => {
  const api = serve(AC04)
  renderWithProviders(<PriceSettingsSection />)

  const form = await fill({ tariff: '', lifetime: '0', scrap: '7,25' })

  for (const field of ['tariff', 'lifetime', 'scrap'] as const) {
    expect(within(form).getByText(RULES[field])).toBeInTheDocument()
  }
  expect(within(form).queryByText(RULES.power)).not.toBeInTheDocument()
  expect(api.callsTo('PUT', '/api/pricing/settings')).toHaveLength(0)
})

test('zero is a valid tariff, power, printer price, parts and scrap', async () => {
  const api = serve(null)
  renderWithProviders(<PriceSettingsSection />)

  await fill({ tariff: '0', power: '0', price: '0', lifetime: '1', parts: '0', scrap: '0' })

  await screen.findByText(/Знос за годину друку/)
  expect(api.callsTo('PUT', '/api/pricing/settings')[0]?.body).toEqual({
    tariff_per_kwh_kop: 0,
    printer_power_w: 0,
    printer_price_kop: 0,
    printer_lifetime_h: 1,
    parts_per_hour_kop: 0,
    scrap_rate_permille: 0,
  })
})

test('unsaved settings say so', async () => {
  serve(null)
  renderWithProviders(<PriceSettingsSection />)

  expect(await screen.findByText('Налаштування ще не збережено.')).toBeInTheDocument()
})
