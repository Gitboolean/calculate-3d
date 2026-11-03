import { act, screen } from '@testing-library/react'

import { formatMoney } from '@/shared/lib'
import { json, mockApi, renderWithProviders, type ApiCall } from '@/shared/testing'

import { useQuote, type QuoteInput } from './useQuote'

function Probe({ input }: { input: QuoteInput | null }) {
  const { quote, isCalculating } = useQuote(input, 10)
  if (quote) return <p>Донат {formatMoney(quote.min_donation_kop)}</p>
  return <p>{isCalculating ? 'Рахую…' : 'Немає донату'}</p>
}

const input = (usage_cg: number): QuoteInput => ({
  plastics: [{ plastic_id: 'petg', usage_cg }],
  print_time_s: 12600,
})

function quoteFor(usage_cg: number) {
  return {
    min_donation_kop: usage_cg,
    breakdown: { plastic_kop: 0, electricity_kop: 0, wear_kop: 0, scrap_kop: 0 },
  }
}

afterEach(() => vi.unstubAllGlobals())

test('shows only the donation for the latest input when an older answer arrives late', async () => {
  const pending = new Map<number, (r: Response) => void>()
  const api = mockApi({
    'POST /api/costing/quote': (call: ApiCall) => {
      const usage = (call.body as QuoteInput).plastics[0]?.usage_cg ?? 0
      return new Promise<Response>((resolve) => pending.set(usage, resolve))
    },
  })
  const view = renderWithProviders(<Probe input={input(1000)} />)
  await vi.waitFor(() => expect(pending.has(1000)).toBe(true))

  view.rerender(<Probe input={input(2000)} />)
  expect(screen.getByText('Рахую…')).toBeInTheDocument()
  await vi.waitFor(() => expect(pending.has(2000)).toBe(true))

  await act(async () => pending.get(2000)?.(json(quoteFor(2000))))
  expect(await screen.findByText('Донат 20,00 ₴')).toBeInTheDocument()

  await act(async () => pending.get(1000)?.(json(quoteFor(1000))))
  expect(screen.getByText('Донат 20,00 ₴')).toBeInTheDocument()
  expect(screen.queryByText('Донат 10,00 ₴')).not.toBeInTheDocument()
  expect(api.callsTo('POST', '/api/costing/quote')).toHaveLength(2)
})

test('a changed input hides the previous donation until its own answer arrives', async () => {
  mockApi({
    'POST /api/costing/quote': (call: ApiCall) =>
      json(quoteFor((call.body as QuoteInput).plastics[0]?.usage_cg ?? 0)),
  })
  const view = renderWithProviders(<Probe input={input(1000)} />)
  expect(await screen.findByText('Донат 10,00 ₴')).toBeInTheDocument()

  view.rerender(<Probe input={input(3000)} />)

  expect(screen.queryByText('Донат 10,00 ₴')).not.toBeInTheDocument()
  expect(await screen.findByText('Донат 30,00 ₴')).toBeInTheDocument()
})

test('typing quickly sends one request for the settled input', async () => {
  const api = mockApi({ 'POST /api/costing/quote': json(quoteFor(1)) })
  const view = renderWithProviders(<Probe input={null} />)

  for (const usage of [1, 12, 120, 1200]) view.rerender(<Probe input={input(usage)} />)

  await screen.findByText('Донат 0,01 ₴')
  expect(api.callsTo('POST', '/api/costing/quote').map((c) => c.body)).toEqual([input(1200)])
})

test('no input means no request and no donation', () => {
  const api = mockApi({})
  renderWithProviders(<Probe input={null} />)

  expect(screen.getByText('Немає донату')).toBeInTheDocument()
  expect(api.calls).toHaveLength(0)
})
