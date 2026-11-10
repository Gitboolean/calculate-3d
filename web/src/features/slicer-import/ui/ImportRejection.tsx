import { Link } from 'react-router'

import { ApiError, isProblem, type Schemas } from '@/shared/api'
import { Button } from '@/shared/ui'

type Missing = Schemas['ImportSettingsMissingProblem']['missing'][number]

const MISSING_TEXT: Record<Missing, string> = {
  plastics: 'жодного пластику ще не додано',
  price_settings: 'тариф, потужність, знос і брак ще не збережено',
}

// One explanation per rejection code of the parse contract (AC-12, AC-13, AC-14).
const REJECTION_TEXT: Record<string, string> = {
  'importing.not_sliced':
    'Файл не нарізаний — у ньому немає витрати пластиків і часу друку. Наріжте пластину в ' +
    'слайсері й завантажте нарізаний файл пластини.',
  'importing.multiple_sliced_plates':
    'У файлі нарізано кілька пластин. Імпортується лише файл з однією нарізаною пластиною.',
  'importing.not_slicer_project':
    'Це не файл проєкту Bambu Studio. Завантажте нарізаний файл, збережений у Bambu Studio.',
  'importing.corrupted_file':
    'Файл пошкоджений або в ньому бракує даних нарізки — витрати чи часу друку.',
  'importing.file_too_large': 'Файл більший за 100 МБ — такий файл не імпортується.',
  'importing.print_time_out_of_range':
    'Час друку у файлі нульовий або понад 100 000 год — такий розрахунок неможливий.',
  'importing.no_filament_usage': 'У файлі немає витрати жодного пластику.',
}
const FALLBACK = 'Не вдалося імпортувати файл. Спробуйте ще раз.'

/** Why the file was not imported; nothing in the form changed (AC-04, AC-12…AC-14). */
export function ImportRejection({ error, onManual }: { error: unknown; onManual: () => void }) {
  const manual = (
    <Button type="button" variant="outline" onClick={onManual}>
      Ввести вручну
    </Button>
  )
  if (isProblem(error, 'importing.settings_missing')) {
    const missing = (error.problem.missing ?? []) as Missing[]
    return (
      <div role="alert" className="space-y-3">
        <p className="text-sm">
          Імпорт неможливий — бракує налаштувань цін:{' '}
          {missing.map((m) => MISSING_TEXT[m]).join('; ')}.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/settings">Перейти до налаштувань цін</Link>
          </Button>
          {manual}
        </div>
      </div>
    )
  }
  const code = error instanceof ApiError ? error.problem.code : ''
  return (
    <div role="alert" className="space-y-3">
      <p className="text-destructive text-sm">{REJECTION_TEXT[code] ?? FALLBACK}</p>
      <p className="text-muted-foreground text-sm">
        Розрахунок не змінено — можна ввести витрату й час вручну.
      </p>
      {manual}
    </div>
  )
}
