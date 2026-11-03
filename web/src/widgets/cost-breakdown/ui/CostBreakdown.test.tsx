import { render, screen, within } from '@testing-library/react'

import { CostBreakdown } from './CostBreakdown'

function row(label: string) {
  const term = screen.getByText(label)
  const value = term.nextElementSibling
  if (!value) throw new Error(`no value for ${label}`)
  return value.textContent
}

test('shows the minimum donation and the four cost rows (AC-06)', () => {
  render(
    <CostBreakdown
      quote={{
        min_donation_kop: 11525,
        breakdown: { plastic_kop: 7800, electricity_kop: 227, wear_kop: 2450, scrap_kop: 1048 },
      }}
    />,
  )

  const donation = screen.getByRole('status', { name: 'Мінімальний донат' })
  expect(within(donation).getByText('115,25 ₴')).toBeInTheDocument()
  expect([row('Пластик'), row('Електрика'), row('Знос'), row('Брак')]).toEqual([
    '78,00 ₴',
    '2,27 ₴',
    '24,50 ₴',
    '10,48 ₴',
  ])
})

test('rows are shown as the server rounded them, even when they do not add up (AC-08b)', () => {
  render(
    <CostBreakdown
      quote={{
        min_donation_kop: 9674,
        breakdown: { plastic_kop: 6500, electricity_kop: 194, wear_kop: 2100, scrap_kop: 879 },
      }}
    />,
  )

  expect(screen.getByText('96,74 ₴')).toBeInTheDocument()
  expect(row('Брак')).toBe('8,79 ₴')
  expect(screen.queryByText('96,73 ₴')).not.toBeInTheDocument()
})

test('says it is calculating instead of showing a stale price', () => {
  render(<CostBreakdown isCalculating />)

  expect(screen.getByText('Рахую…')).toBeInTheDocument()
  expect(screen.queryByText(/₴/)).not.toBeInTheDocument()
})
