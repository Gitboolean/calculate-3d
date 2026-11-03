import { parseQuoteForm, quoteFormFrom, type QuoteFormValue } from './parse'

const form = (rows: [string, string][], hours = '3', minutes = '30'): QuoteFormValue => ({
  rows: rows.map(([plasticId, grams], i) => ({ key: String(i), plasticId, grams })),
  hours,
  minutes,
})

test('valid rows and time become a quote input in API units', () => {
  expect(
    parseQuoteForm(
      form([
        ['petg', '120'],
        ['pla', '12,34'],
      ]),
    ),
  ).toEqual({
    input: {
      plastics: [
        { plastic_id: 'petg', usage_cg: 12000 },
        { plastic_id: 'pla', usage_cg: 1234 },
      ],
      print_time_s: 12600,
    },
    errors: {},
  })
})

test('empty hours count as zero', () => {
  expect(parseQuoteForm(form([['petg', '1']], '', '45')).input?.print_time_s).toBe(2700)
})

test.each([
  [form([]), 'plastics', 'Додайте хоча б один пластик'],
  [form([['', '120']]), 'rows.0.plastic', 'Оберіть пластик'],
  [form([['petg', '']]), 'rows.0.grams', 'Вкажіть витрату пластику'],
  [form([['petg', 'abc']]), 'rows.0.grams', 'Витрата має бути числом'],
  [form([['petg', '12,345']]), 'rows.0.grams', 'Витрата — з точністю до 0,01 г'],
  [form([['petg', '0']]), 'rows.0.grams', 'Витрата має бути більшою за нуль'],
  [form([['petg', '-1']]), 'rows.0.grams', 'Витрата має бути більшою за нуль'],
  [
    form([
      ['petg', '1'],
      ['petg', '2'],
    ]),
    'rows.1.plastic',
    'Цей пластик уже є в іншому рядку — об’єднайте витрату в одному рядку',
  ],
  [form([['petg', '1']], '2,5'), 'hours', 'Години — ціле невід’ємне число'],
  [form([['petg', '1']], '-1'), 'hours', 'Години — ціле невід’ємне число'],
  [form([['petg', '1']], '1', '60'), 'minutes', 'Хвилини — ціле число від 0 до 59'],
  [form([['petg', '1']], '1', '7,5'), 'minutes', 'Хвилини — ціле число від 0 до 59'],
  [form([['petg', '1']], '0', '0'), 'time', 'Час друку має бути більшим за нуль'],
  [form([['petg', '1']], '', ''), 'time', 'Час друку має бути більшим за нуль'],
])('%#: an invalid form gives no input and explains %s', (value, field, message) => {
  const { input, errors } = parseQuoteForm(value)

  expect(input).toBeNull()
  expect(errors[field]).toBe(message)
})

// Digit groups may be separated by a space, NBSP or narrow NBSP.
const SEP = '[\\s\u00a0\u202f]?'
const num = (...groups: string[]) => new RegExp(groups.join(SEP))

test('usage and time exactly at the caps are accepted (AC-07)', () => {
  expect(parseQuoteForm(form([['petg', '1000000']], '100000', '0')).input).toEqual({
    plastics: [{ plastic_id: 'petg', usage_cg: 100000000 }],
    print_time_s: 360000000,
  })
})

test('usage over 1 000 000 g is rejected on its row with a message naming the maximum (AC-07)', () => {
  const { input, errors } = parseQuoteForm(form([['petg', '1000000,01']]))

  expect(input).toBeNull()
  expect(errors['rows.0.grams']).toMatch(num('1', '000', '000'))
})

test('print time over 100 000 h is rejected with a message naming the maximum (AC-07)', () => {
  const { input, errors } = parseQuoteForm(form([['petg', '1']], '100000', '1'))

  expect(input).toBeNull()
  expect(Object.values(errors).join(' ')).toMatch(num('100', '000'))
  expect(Object.values(errors).join(' ')).toMatch(/год/)
})

test('32 plastic rows are accepted, 33 are rejected with a message naming 32 (AC-07)', () => {
  const rows = (n: number): [string, string][] =>
    Array.from({ length: n }, (_, i) => [`p${i}`, '1'] as [string, string])

  expect(parseQuoteForm(form(rows(32))).input?.plastics).toHaveLength(32)
  const { input, errors } = parseQuoteForm(form(rows(33)))
  expect(input).toBeNull()
  expect(Object.values(errors).join(' ')).toMatch(/32/)
})

test('a saved input fills the form and parses back to itself', () => {
  const input = {
    plastics: [
      { plastic_id: 'petg', usage_cg: 12000 },
      { plastic_id: 'pla', usage_cg: 1234 },
    ],
    print_time_s: 12600,
  }

  const value = quoteFormFrom(input)

  expect(value.rows.map((r) => [r.plasticId, r.grams])).toEqual([
    ['petg', '120,00'],
    ['pla', '12,34'],
  ])
  expect([value.hours, value.minutes]).toEqual(['3', '30'])
  expect(parseQuoteForm(value).input).toEqual(input)
})

test('usage too large for a safe integer is over the cap, not "not a number" (AC-07)', () => {
  const { input, errors } = parseQuoteForm(form([['petg', '100 000 000 000 000']]))

  expect(input).toBeNull()
  expect(errors['rows.0.grams']).toBe('Витрата — не більше 1 000 000 г')
})

test('a hugely negative usage is "must be above zero", not "not a number" (AC-07)', () => {
  const { errors } = parseQuoteForm(form([['petg', '-100000000000000']]))

  expect(errors['rows.0.grams']).toBe('Витрата має бути більшою за нуль')
})

test('hours too large for a safe integer are over the cap, not "not whole" (AC-07)', () => {
  const { input, errors } = parseQuoteForm(form([['petg', '1']], '100000000000000000', '0'))

  expect(input).toBeNull()
  expect(errors.time).toBe('Час друку — не більше 100 000 год')
  expect(errors.hours).toBeUndefined()
})

test.each([
  ['0', '99999999999999999999'],
  ['0', '6000001'],
  ['1', '60'],
])('invalid minutes %s h %s min explain only minutes, not the time cap (AC-07)', (h, m) => {
  const { input, errors } = parseQuoteForm(form([['petg', '1']], h, m))

  expect(input).toBeNull()
  expect(errors.minutes).toBe('Хвилини — ціле число від 0 до 59')
  expect(errors.time).toBeUndefined()
})

test('hours over the cap with valid minutes give only the time cap message (AC-07)', () => {
  const { input, errors } = parseQuoteForm(form([['petg', '1']], '100000', '1'))

  expect(input).toBeNull()
  expect(errors).toEqual({ time: 'Час друку — не більше 100 000 год' })
})
