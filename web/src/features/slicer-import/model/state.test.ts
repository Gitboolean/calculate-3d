import { ApiError, type Schemas } from '@/shared/api'

import { filamentKey } from './compose'
import { choosePlastic, clearRejectedChoice, confirmMerge, startImport } from './state'

const FILE: Schemas['SlicerFile'] = {
  plate: { index: 1, name: '' },
  print_time_s: 60,
  filaments: [
    {
      filament_name: 'A',
      filament_type: 'PLA',
      filament_color: '#FFFFFF',
      usage_mg: 1,
      plastic_id: 'pla',
    },
  ],
}

test('a fresh import starts from the substituted plastics and no confirmations', () => {
  const state = startImport(FILE)

  expect(state.choice).toEqual({
    [filamentKey({ filament_name: 'A', filament_color: '#FFFFFF' })]: 'pla',
  })
  expect(state.confirmed.size).toBe(0)
})

test('choosing and confirming return new states without mutating the old one', () => {
  const start = startImport(FILE)
  const key = filamentKey({ filament_name: 'A', filament_color: '#FFFFFF' })

  const chosen = choosePlastic(start, key, 'petg')
  const confirmed = confirmMerge(chosen, { plasticId: 'petg', filaments: FILE.filaments })

  expect(start.choice[key]).toBe('pla')
  expect(chosen.choice[key]).toBe('petg')
  expect(confirmed.confirmed.size).toBe(1)
  expect(chosen.confirmed.size).toBe(0)
})

test('a rejected mapping is cleared only while the filament still holds the plastic that was sent (AC-08, R9)', () => {
  const key = filamentKey({ filament_name: 'A', filament_color: '#FFFFFF' })
  const sent = [{ filament_name: 'A', filament_color: '#FFFFFF', plastic_id: 'pla' }]
  const rejected = new ApiError(422, {
    type: 'about:blank',
    title: 'Plastic not found',
    status: 422,
    detail: 'Plastic not found',
    code: 'importing.plastic_not_found',
    field: 'filament_mappings.0.plastic_id',
  })
  const unchanged = startImport(FILE)
  const rechosen = choosePlastic(unchanged, key, 'petg')

  expect(clearRejectedChoice(unchanged, rejected, sent).choice[key]).toBe('')
  expect(clearRejectedChoice(rechosen, rejected, sent).choice[key]).toBe('petg')
})
