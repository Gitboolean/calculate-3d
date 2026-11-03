import { nameLength, normalizeName } from './normalize-name'

// Server rule (core/text.py::normalize_name): NFC, then strip both ends of every char that is
// Python isspace() or Unicode category Cf. JS trim() alone misses the ones listed here.
const EDGE_CHARS = [
  ['U+200B zero width space', '\u200B'],
  ['U+00AD soft hyphen', '\u00AD'],
  ['U+2060 word joiner', '\u2060'],
  ['U+FEFF byte order mark', '\uFEFF'],
  ['U+200C zero width non-joiner', '\u200C'],
  ['U+200D zero width joiner', '\u200D'],
  ['U+061C arabic letter mark', '\u061C'],
  ['U+001C file separator', '\u001C'],
  ['U+001F unit separator', '\u001F'],
  ['U+0085 next line', '\u0085'],
] as const

describe.each(EDGE_CHARS)('%s', (_label, ch) => {
  test('is stripped from the start', () => {
    expect(normalizeName(`${ch}PETG`)).toBe('PETG')
  })

  test('is stripped from the end', () => {
    expect(normalizeName(`PETG${ch}`)).toBe('PETG')
  })

  test('is stripped when mixed with spaces at both ends', () => {
    expect(normalizeName(` ${ch} ${ch}PETG ${ch} `)).toBe('PETG')
  })

  test('a name of only this character is empty', () => {
    expect(normalizeName(ch + ch)).toBe('')
  })
})

test('an interior zero width space is kept', () => {
  expect(normalizeName('PE\u200BTG')).toBe('PE\u200BTG')
})

test('an interior soft hyphen is kept', () => {
  expect(normalizeName('PE\u00ADTG')).toBe('PE\u00ADTG')
})

test('interior is kept while the edges are stripped', () => {
  expect(normalizeName('\u200B PE\u200B\u00ADTG \u00AD')).toBe('PE\u200B\u00ADTG')
})

test('the name is NFC-normalised', () => {
  expect(normalizeName('e\u0301')).toBe('é')
})

test('NFC is applied before stripping', () => {
  expect(normalizeName('\u200Be\u0301\u00AD')).toBe('é')
})

test('nameLength counts code points', () => {
  expect(nameLength('😀😀')).toBe(2)
})

// Linear time: the trim must not backtrack over a long interior run (review R5-5).
const RUN = 100_000
const BUDGET_MS = 50

function timed(raw: string): { result: string; ms: number } {
  const start = performance.now()
  const result = normalizeName(raw)
  return { result, ms: performance.now() - start }
}

test('a long interior run of spaces is kept and normalises in linear time', () => {
  const { result, ms } = timed('a' + ' '.repeat(RUN) + 'b')

  expect(result).toHaveLength(RUN + 2)
  expect(result.startsWith('a')).toBe(true)
  expect(result.endsWith('b')).toBe(true)
  expect(ms).toBeLessThan(BUDGET_MS)
})

test('a long interior run of zero width spaces is kept and normalises in linear time', () => {
  const { result, ms } = timed('a' + '\u200B'.repeat(RUN) + 'b')

  expect(result).toHaveLength(RUN + 2)
  expect(result.startsWith('a')).toBe(true)
  expect(result.endsWith('b')).toBe(true)
  expect(ms).toBeLessThan(BUDGET_MS)
})

test('a long trailing run of spaces is stripped in linear time', () => {
  const { result, ms } = timed('a' + ' '.repeat(RUN))

  expect(result).toBe('a')
  expect(ms).toBeLessThan(BUDGET_MS)
})

test('a long leading run of spaces is stripped in linear time', () => {
  const { result, ms } = timed(' '.repeat(RUN) + 'a')

  expect(result).toBe('a')
  expect(ms).toBeLessThan(BUDGET_MS)
})
