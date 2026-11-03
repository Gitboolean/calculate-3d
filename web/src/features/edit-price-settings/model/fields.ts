import type { PriceSettings, PriceSettingsInput } from '@/entities/price-settings'
import { formatDecimal, parseDecimal } from '@/shared/lib'

export type FieldName = keyof PriceSettingsInput

type FieldSpec = {
  name: FieldName
  label: string
  /** Decimal places the author may type; the API value is scaled by 10^scale. */
  scale: number
  min: number
  max?: number
  /** Range + precision, shown for any rejection of the value (AC-05). */
  rule: string
}

export const FIELDS: readonly FieldSpec[] = [
  {
    name: 'tariff_per_kwh_kop',
    label: 'Тариф, ₴ за кВт·год',
    scale: 2,
    min: 0,
    max: 1000000,
    rule: 'Тариф — від 0 до 10 000 ₴ за кВт·год з точністю до копійки',
  },
  {
    name: 'printer_power_w',
    label: 'Потужність принтера, Вт',
    scale: 0,
    min: 0,
    max: 1000000,
    rule: 'Потужність — ціле число ват від 0 до 1 000 000',
  },
  {
    name: 'printer_price_kop',
    label: 'Ціна принтера, ₴',
    scale: 2,
    min: 0,
    max: 10000000000,
    rule: 'Ціна принтера — від 0 до 100 000 000 ₴ з точністю до копійки',
  },
  {
    name: 'printer_lifetime_h',
    label: 'Термін служби, годин друку',
    scale: 0,
    min: 1,
    max: 1000000,
    rule: 'Термін служби — ціле число годин від 1 до 1 000 000',
  },
  {
    name: 'parts_per_hour_kop',
    label: 'Деталі, ₴ за годину друку',
    scale: 2,
    min: 0,
    max: 100000000,
    rule: 'Деталі — від 0 до 1 000 000 ₴ за годину з точністю до копійки',
  },
  {
    name: 'scrap_rate_permille',
    label: 'Брак, %',
    scale: 1,
    min: 0,
    max: 1000,
    rule: 'Брак — від 0 до 100 % з точністю до 0,1',
  },
]

export type FieldValues = Record<FieldName, string>
export type FieldErrors = Partial<Record<FieldName, string>>

export function initialValues(saved: PriceSettings | null | undefined): FieldValues {
  const entries = FIELDS.map((f) => [f.name, saved ? formatDecimal(saved[f.name], f.scale) : ''])
  return Object.fromEntries(entries) as FieldValues
}

/** Every field must be valid before anything is sent — one save for all six (AC-04, AC-05). */
export function validate(
  values: FieldValues,
): { ok: true; input: PriceSettingsInput } | { ok: false; errors: FieldErrors } {
  const input: Partial<PriceSettingsInput> = {}
  const errors: FieldErrors = {}
  for (const field of FIELDS) {
    const parsed = parseDecimal(values[field.name], field.scale)
    const inRange =
      parsed.ok &&
      parsed.value >= field.min &&
      (field.max === undefined || parsed.value <= field.max)
    if (parsed.ok && inRange) input[field.name] = parsed.value
    else errors[field.name] = field.rule
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors }
  return { ok: true, input: input as PriceSettingsInput }
}
