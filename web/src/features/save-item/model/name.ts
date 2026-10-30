import { isProblem, issueField } from '@/shared/api'
import { MAX_NAME_LENGTH, nameLength, normalizeName } from '@/shared/lib'

/**
 * AC-11: NFC, trimmed, 1–100 characters (code points, as the server counts);
 * uniqueness is the server's call.
 */
export function validateItemName(name: string): string | undefined {
  const trimmed = normalizeName(name)
  if (!trimmed) return 'Назва виробу обов’язкова'
  if (nameLength(trimmed) > MAX_NAME_LENGTH) return `Назва — не довше ${MAX_NAME_LENGTH} символів`
  return undefined
}

/** A rejected save → the message for the name field, or for the whole form. */
export function saveError(error: unknown): { name?: string; form?: string } {
  if (isProblem(error, 'catalog.name_taken'))
    return { name: 'Виріб з такою назвою вже є в каталозі' }
  if (isProblem(error, 'catalog.plastic_not_found'))
    return { form: 'Один із пластиків уже видалено з налаштувань — оберіть інший.' }
  if (isProblem(error, 'validation_error')) {
    const fields = (error.problem.errors ?? []).map(issueField)
    if (fields.includes('name')) return { name: `Назва — від 1 до ${MAX_NAME_LENGTH} символів` }
    return { form: 'Перевірте витрату пластику й час друку.' }
  }
  return { form: 'Не вдалося зберегти виріб. Спробуйте ще раз.' }
}
