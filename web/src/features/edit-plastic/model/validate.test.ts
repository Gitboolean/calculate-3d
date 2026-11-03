import { ApiError } from '@/shared/api'

import { serverErrors, validatePlastic } from './validate'

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

const TOO_LONG = 'Назва — не довше 100 символів'

test('a name of 100 emoji (100 code points, 200 UTF-16 units) is accepted (AC-02)', () => {
  expect(validatePlastic('😀'.repeat(100), '100').ok).toBe(true)
})

test('a name of 101 emoji is rejected as too long (AC-02)', () => {
  const result = validatePlastic('😀'.repeat(101), '100')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.name).toBe(TOO_LONG)
})

// U+0344 NFC-splits into U+0308 U+0301, so each one counts as two code points.
test('a name that NFC-expands past 100 code points is rejected as too long (AC-02)', () => {
  const result = validatePlastic('\u0344'.repeat(60), '100')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.name).toBe(TOO_LONG)
})

test('the saved name is the NFC-normalised trimmed name (AC-02)', () => {
  const result = validatePlastic('  e\u0301  ', '100')

  expect(result.ok).toBe(true)
  if (!result.ok) return
  expect(result.input.name).toBe('é')
})

test('a server 422 on name says the length range, not "required" (AC-02)', () => {
  const error = new ApiError(422, {
    type: 'about:blank',
    title: 'Validation error',
    status: 422,
    detail: 'Invalid request',
    code: 'validation_error',
    errors: [{ loc: ['body', 'name'], msg: 'String should have at most 100 characters' }],
  })

  expect(serverErrors(error).name).toBe('Назва — від 1 до 100 символів')
})

test('a server 422 on price says the allowed range with the maximum (AC-02)', () => {
  const error = new ApiError(422, {
    type: 'about:blank',
    title: 'Validation error',
    status: 422,
    detail: 'Invalid request',
    code: 'validation_error',
    errors: [
      {
        loc: ['body', 'price_per_kg_kop'],
        msg: 'Input should be less than or equal to 1000000000',
      },
    ],
  })

  expect(serverErrors(error).price).toBe(
    'Ціна має бути більшою за нуль і не більшою за 10 000 000 ₴',
  )
})

test.each([
  ['U+200B', '\u200B'],
  ['U+00AD', '\u00AD'],
])('100 letters plus a trailing %s is accepted and sent without it (AC-02)', (_label, ch) => {
  const letters = 'а'.repeat(100)
  const result = validatePlastic(letters + ch, '100')

  expect(result.ok).toBe(true)
  if (!result.ok) return
  expect(result.input.name).toBe(letters)
})

test.each([
  ['U+200B', '\u200B'],
  ['U+00AD', '\u00AD'],
])('a name of only %s is "required" (AC-02)', (_label, ch) => {
  const result = validatePlastic(ch + ch, '100')

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors.name).toBe('Назва обов’язкова')
})
