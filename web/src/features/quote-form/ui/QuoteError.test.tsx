import { render, screen } from '@testing-library/react'

import { ApiError } from '@/shared/api'

import { QuoteError } from './QuoteError'

const problem = (status: number, code: string) =>
  new ApiError(status, { type: 'about:blank', title: 'Error', status, detail: 'x', code })

test('a validation_error says to check the fields, not to retry (AC-07)', () => {
  render(<QuoteError error={problem(422, 'validation_error')} />)

  expect(screen.getByRole('alert')).toHaveTextContent('Перевірте поля')
  expect(screen.queryByText(/Спробуйте ще раз/)).not.toBeInTheDocument()
})

test.each([
  ['a 500', problem(500, 'internal_error')],
  ['a network error', new TypeError('Failed to fetch')],
])('%s keeps the neutral retry message (AC-07)', (_name, error) => {
  render(<QuoteError error={error} />)

  expect(screen.getByRole('alert')).toHaveTextContent('Спробуйте ще раз')
})
