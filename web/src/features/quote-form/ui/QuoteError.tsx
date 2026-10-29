import { isProblem } from '@/shared/api'

import { MissingSettings } from './MissingSettings'

/** Why a live quote failed: missing settings, a deleted plastic, or a neutral retry (AC-07, AC-09). */
export function QuoteError({ error }: { error: unknown }) {
  if (isProblem(error, 'costing.settings_missing')) {
    return <MissingSettings missing={error.problem.missing ?? []} />
  }
  const message = isProblem(error, 'costing.plastic_not_found')
    ? 'Один із пластиків уже видалено з налаштувань — оберіть інший'
    : 'Не вдалося порахувати. Спробуйте ще раз.'
  return (
    <p role="alert" className="text-destructive text-sm">
      {message}
    </p>
  )
}
