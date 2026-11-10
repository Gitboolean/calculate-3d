import type { Schemas } from '@/shared/api'

import { filamentKey } from './compose'
import { choosePlastic, confirmMerge, startImport } from './state'

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
