import type { PlasticInput } from '@/entities/plastic'
import { isProblem, issueField } from '@/shared/api'
import { parseDecimal } from '@/shared/lib'

export type PlasticErrors = Partial<Record<'name' | 'price' | 'form', string>>

const MAX_NAME = 100
const MAX_PRICE_KOP = 1_000_000_000
const PRICE_RANGE = 'більшою за нуль і не більшою за 10 000 000 ₴'

export function validatePlastic(
  name: string,
  price: string,
): { ok: true; input: PlasticInput } | { ok: false; errors: PlasticErrors } {
  const errors: PlasticErrors = {}
  const trimmed = name.trim()
  if (!trimmed) errors.name = 'Назва обов’язкова'
  else if (trimmed.length > MAX_NAME) errors.name = `Назва — не довше ${MAX_NAME} символів`

  const parsed = parseDecimal(price, 2)
  if (!parsed.ok) {
    errors.price = {
      empty: 'Вкажіть ціну за кілограм',
      not_a_number: 'Ціна має бути числом',
      too_precise: 'Ціна — з точністю до копійки (не більше двох знаків після коми)',
      too_large: 'Ціна — не більше 10 000 000 ₴ за кг',
      too_small: 'Ціна має бути більшою за нуль',
    }[parsed.reason]
  } else if (parsed.value <= 0) {
    errors.price = 'Ціна має бути більшою за нуль'
  } else if (parsed.value > MAX_PRICE_KOP) {
    errors.price = `Ціна — не більше 10 000 000 ₴ за кг`
  }

  if (errors.name || errors.price || !parsed.ok) return { ok: false, errors }
  return { ok: true, input: { name: trimmed, price_per_kg_kop: parsed.value } }
}

/** The server's word on a rejected save, placed next to the matching field. */
export function serverErrors(error: unknown): PlasticErrors {
  if (isProblem(error, 'pricing.name_taken')) return { name: 'Пластик з такою назвою вже є' }
  if (isProblem(error, 'validation_error')) {
    const fields = new Set((error.problem.errors ?? []).map(issueField))
    return {
      name: fields.has('name') ? 'Назва обов’язкова' : undefined,
      price: fields.has('price_per_kg_kop') ? `Ціна має бути ${PRICE_RANGE}` : undefined,
    }
  }
  return { form: 'Не вдалося зберегти пластик. Спробуйте ще раз.' }
}
