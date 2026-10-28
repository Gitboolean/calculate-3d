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

test('there is no upper bound for grams or hours', () => {
  expect(parseQuoteForm(form([['petg', '100000']], '500', '0')).input).toEqual({
    plastics: [{ plastic_id: 'petg', usage_cg: 10000000 }],
    print_time_s: 1800000,
  })
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
