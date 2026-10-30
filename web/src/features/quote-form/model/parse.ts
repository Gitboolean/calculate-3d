import type { QuoteInput } from '@/entities/quote'
import { formatDecimal, parseDecimal } from '@/shared/lib'

export type QuoteFormRow = { key: string; plasticId: string; grams: string }
export type QuoteFormValue = { rows: QuoteFormRow[]; hours: string; minutes: string }

/** Keys: `plastics`, `rows.<i>.plastic`, `rows.<i>.grams`, `hours`, `minutes`, `time`. */
export type QuoteFormErrors = Record<string, string>

let lastKey = 0
export function newRow(plasticId = '', grams = ''): QuoteFormRow {
  lastKey += 1
  return { key: `row-${lastKey}`, plasticId, grams }
}

export function emptyQuoteForm(): QuoteFormValue {
  return { rows: [newRow()], hours: '', minutes: '' }
}

/** A saved item's parameters back into the form's text (AC-14b editing). */
export function quoteFormFrom(input: QuoteInput): QuoteFormValue {
  const minutes = input.print_time_s / 60
  return {
    rows: input.plastics.map((p) => newRow(p.plastic_id, formatDecimal(p.usage_cg, 2))),
    hours: String(Math.floor(minutes / 60)),
    minutes: String(minutes % 60),
  }
}

const MAX_USAGE_CG = 100_000_000
const MAX_PRINT_TIME_S = 360_000_000
const MAX_ROWS = 32

const GRAMS_ERRORS = {
  empty: 'Вкажіть витрату пластику',
  not_a_number: 'Витрата має бути числом',
  too_precise: 'Витрата — з точністю до 0,01 г',
  too_large: 'Витрата — не більше 1 000 000 г',
  too_small: 'Витрата має бути більшою за нуль',
} as const

/** Whole, non-negative; an empty field counts as zero (AC-07). A number too big to represent is `Infinity`. */
function wholeNumber(text: string): number | null {
  if (!text.trim()) return 0
  const parsed = parseDecimal(text, 0)
  if (!parsed.ok) return parsed.reason === 'too_large' ? Infinity : null
  return parsed.value >= 0 ? parsed.value : null
}

/** The form's text → API units (AC-07 rules), or `null` with an explanation per field. */
export function parseQuoteForm(value: QuoteFormValue): {
  input: QuoteInput | null
  errors: QuoteFormErrors
} {
  const errors: QuoteFormErrors = {}
  const plastics: QuoteInput['plastics'] = []
  const seen = new Set<string>()

  if (value.rows.length === 0) errors.plastics = 'Додайте хоча б один пластик'
  else if (value.rows.length > MAX_ROWS)
    errors.plastics = `Не більше ${MAX_ROWS} пластиків в одному розрахунку`
  value.rows.forEach((row, i) => {
    if (!row.plasticId) errors[`rows.${i}.plastic`] = 'Оберіть пластик'
    else if (seen.has(row.plasticId))
      errors[`rows.${i}.plastic`] =
        'Цей пластик уже є в іншому рядку — об’єднайте витрату в одному рядку'
    seen.add(row.plasticId)

    const grams = parseDecimal(row.grams, 2)
    if (!grams.ok) errors[`rows.${i}.grams`] = GRAMS_ERRORS[grams.reason]
    else if (grams.value <= 0) errors[`rows.${i}.grams`] = 'Витрата має бути більшою за нуль'
    else if (grams.value > MAX_USAGE_CG)
      errors[`rows.${i}.grams`] = 'Витрата — не більше 1 000 000 г'
    else plastics.push({ plastic_id: row.plasticId, usage_cg: grams.value })
  })

  const hours = wholeNumber(value.hours)
  const minutes = wholeNumber(value.minutes)
  if (hours === null) errors.hours = 'Години — ціле невід’ємне число'
  if (minutes === null || minutes >= 60) errors.minutes = 'Хвилини — ціле число від 0 до 59'
  const printTimeS = ((hours ?? 0) * 60 + (minutes ?? 0)) * 60
  if (hours !== null && minutes !== null && printTimeS === 0)
    errors.time = 'Час друку має бути більшим за нуль'
  else if (printTimeS > MAX_PRINT_TIME_S) errors.time = 'Час друку — не більше 100 000 год'

  if (Object.keys(errors).length > 0) return { input: null, errors }
  return { input: { plastics, print_time_s: printTimeS }, errors }
}
