// Shared input parser (cost-calculator ADR 0004): the user types a decimal with a comma or a dot,
// the API takes an integer in the smallest unit. Extra precision is an error, never rounded.

export type ParseDecimalError = 'empty' | 'not_a_number' | 'too_precise' | 'too_large' | 'too_small'

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
  if (!Number.isSafeInteger(value)) return { ok: false, reason: sign ? 'too_small' : 'too_large' }
  return { ok: true, value: sign && value !== 0 ? -value : value }
}

/** The inverse of `parseDecimal` for pre-filling inputs: 65050 with scale 2 → «650,50». */
export function formatDecimal(value: number, scale: number): string {
  const digits = Math.abs(value)
    .toString()
    .padStart(scale + 1, '0')
  const whole = digits.slice(0, digits.length - scale)
  const fraction = digits.slice(digits.length - scale)
  return `${value < 0 ? '-' : ''}${whole}${scale > 0 ? `,${fraction}` : ''}`
}
