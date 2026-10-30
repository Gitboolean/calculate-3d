import { validatePlastic } from './validate'

const SEP = '[\\s  ]?'

test('a price of exactly 10 000 000 ₴/кг is accepted (AC-02)', () => {
  expect(validatePlastic('PETG', '10000000')).toEqual({
    ok: true,
    input: { name: 'PETG', price_per_kg_kop: 1000000000 },
  })
})

test('a price over 10 000 000 ₴/кг is rejected with a message naming the maximum (AC-02)', () => {
  const result = validatePlastic('PETG', '10000000,01')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.price).toMatch(new RegExp(['10', '000', '000'].join(SEP)))
  expect(result.errors.price).not.toMatch(/більшою за нуль/)
})

test('a price too large for a safe integer is over the cap, not "not a number" (AC-02)', () => {
  const result = validatePlastic('PETG', '100000000000000000')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.price).toBe('Ціна — не більше 10 000 000 ₴ за кг')
})

test('a hugely negative price is "must be above zero" (AC-02)', () => {
  const result = validatePlastic('PETG', '-100000000000000000')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.price).toBe('Ціна має бути більшою за нуль')
})
