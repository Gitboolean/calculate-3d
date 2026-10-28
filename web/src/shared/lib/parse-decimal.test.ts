import { formatDecimal, parseDecimal } from './parse-decimal'

test.each([
  ['650', 2, 65000],
  ['650,00', 2, 65000],
  ['650.00', 2, 65000],
  ['4,32', 2, 432],
  ['4.32', 2, 432],
  [' 1,5 ', 2, 150],
  ['30 000', 2, 3000000],
  ['10', 1, 100],
  ['7,2', 1, 72],
  ['150', 0, 150],
  ['120', 2, 12000],
  ['12,34', 2, 1234],
  ['0', 2, 0],
  [',5', 2, 50],
  ['650,000', 2, 65000],
  ['-5', 2, -500],
  ['-0,01', 2, -1],
])('parses %j with scale %i into %i', (input, scale, expected) => {
  expect(parseDecimal(input, scale)).toEqual({ ok: true, value: expected })
})

test.each([
  ['649,995', 2],
  ['4,3216', 2],
  ['7,25', 1],
  ['152,5', 0],
  ['12,345', 2],
])('rejects %j with scale %i as too precise instead of rounding', (input, scale) => {
  expect(parseDecimal(input, scale)).toEqual({ ok: false, reason: 'too_precise' })
})

test.each(['', '   '])('rejects blank %j as empty', (input) => {
  expect(parseDecimal(input, 2)).toEqual({ ok: false, reason: 'empty' })
})

test.each(['abc', '1,2,3', '1.2.3', '1e5', '12г', '--1', ',', 'Infinity', '99999999999999999999'])(
  'rejects %j as not a number',
  (input) => {
    expect(parseDecimal(input, 2)).toEqual({ ok: false, reason: 'not_a_number' })
  },
)

test.each([
  [65050, 2, '650,50'],
  [40000, 2, '400,00'],
  [5, 2, '0,05'],
  [100, 1, '10,0'],
  [150, 0, '150'],
  [-1, 2, '-0,01'],
])('formats %i with scale %i as %j, which parses back', (value, scale, text) => {
  expect(formatDecimal(value, scale)).toBe(text)
  expect(parseDecimal(text, scale)).toEqual({ ok: true, value })
})
