import { formatMoney } from './format-money'

test.each([
  [11525, '115,25 ₴'],
  [700, '7,00 ₴'],
  [0, '0,00 ₴'],
  [1, '0,01 ₴'],
  [3000000, '30 000,00 ₴'],
])('formats %i kopecks as %j', (kop, expected) => {
  expect(formatMoney(kop)).toBe(expected)
})
