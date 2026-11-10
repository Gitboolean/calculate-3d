import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ApiError } from '@/shared/api'
import { renderWithProviders } from '@/shared/testing'

import { ImportRejection } from './ImportRejection'

const reject = (status: number, code: string, extra: object = {}) =>
  new ApiError(status, { type: 'about:blank', title: 'x', status, detail: code, code, ...extra })

const CASES: [number, string, RegExp][] = [
  [422, 'importing.not_sliced', /не нарізаний.*наріжте пластину.*нарізаний файл/is],
  [422, 'importing.multiple_sliced_plates', /лише файл з однією нарізаною пластиною/i],
  [422, 'importing.not_slicer_project', /не файл проєкту Bambu Studio/i],
  [422, 'importing.corrupted_file', /пошкоджений/i],
  [413, 'importing.file_too_large', /100 МБ/],
  [422, 'importing.print_time_out_of_range', /час друку/i],
  [422, 'importing.no_filament_usage', /немає витрати/i],
  [415, 'unsupported_media_type', /не вдалося імпортувати/i],
  [500, 'something_new', /не вдалося імпортувати/i],
]

test.each(CASES)(
  '%s %s is explained in Ukrainian with manual entry offered',
  (status, code, text) => {
    const onManual = vi.fn()
    renderWithProviders(<ImportRejection error={reject(status, code)} onManual={onManual} />)

    expect(screen.getByRole('alert')).toHaveTextContent(text)
    expect(screen.getByRole('button', { name: 'Ввести вручну' })).toBeInTheDocument()
  },
)

test('missing settings name what is missing and lead to the settings (AC-04)', async () => {
  const onManual = vi.fn()
  renderWithProviders(
    <ImportRejection
      error={reject(409, 'importing.settings_missing', { missing: ['plastics', 'price_settings'] })}
      onManual={onManual}
    />,
  )

  const alert = screen.getByRole('alert')
  expect(alert).toHaveTextContent('жодного пластику ще не додано')
  expect(alert).toHaveTextContent('тариф, потужність, знос і брак ще не збережено')
  expect(screen.getByRole('link', { name: 'Перейти до налаштувань цін' })).toHaveAttribute(
    'href',
    '/settings',
  )
  await userEvent.click(screen.getByRole('button', { name: 'Ввести вручну' }))
  expect(onManual).toHaveBeenCalled()
})
