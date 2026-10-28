// Shared input parser (cost-calculator ADR 0004): the user types a decimal with a comma or a dot,
// the API takes an integer in the smallest unit. Extra precision is an error, never rounded.

export type ParseDecimalError = 'empty' | 'not_a_number' | 'too_precise'

export type ParseDecimalResult =
  { ok: true; value: number } | { ok: false; reason: ParseDecimalError }

const DECIMAL = /^(-?)(\d*)(?:[.,](\d*))?$/

/** Parses `input` into an integer scaled by 10^`scale` (`650,5` with scale 2 → 65050). */
export function parseDecimal(input: string, scale: number): ParseDecimalResult {
  // Spaces are digit-group separators («30 000»).
  const text = input.replace(/\s/g, '')
  if (text === '') return { ok: false, reason: 'empty' }

  const match = DECIMAL.exec(text)
  if (!match) return { ok: false, reason: 'not_a_number' }
  const [, sign, whole, fraction = ''] = match
  if (whole === '' && fraction === '') return { ok: false, reason: 'not_a_number' }
  if (fraction.replace(/0+$/, '').length > scale) return { ok: false, reason: 'too_precise' }

  const value = Number(whole + fraction.padEnd(scale, '0').slice(0, scale))
  if (!Number.isSafeInteger(value)) return { ok: false, reason: 'not_a_number' }
  return { ok: true, value: sign && value !== 0 ? -value : value }
}
