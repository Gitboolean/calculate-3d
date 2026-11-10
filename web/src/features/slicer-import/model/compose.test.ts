import type { Schemas } from '@/shared/api'

import { compose, filamentKey, initialChoice, mappingsFor, mergeKey } from './compose'

type Filament = Schemas['SlicerFilament']

const PLA = 'Bambu PLA Basic @BBL A1M'
const PETG = 'Bambu PETG Basic @BBL A1M'

const filament = (
  usage_mg: number,
  filament_color = '#FFFFFF',
  plastic_id: string | null = 'pla',
  filament_name = PLA,
): Filament => ({ filament_name, filament_type: 'PLA', filament_color, usage_mg, plastic_id })

const file = (...filaments: Filament[]): Schemas['SlicerFile'] => ({
  plate: { index: 1, name: '' },
  print_time_s: 5880,
  filaments,
})

const none = new Set<string>()

function at<T>(items: readonly T[], index: number): T {
  const item = items[index]
  if (item === undefined) throw new Error(`no item ${index}`)
  return item
}

test('vtulka_A: 11 540 mg of a mapped filament is one 1 154 cg row (AC-01, as in T10)', () => {
  const parsed = file(filament(11_540))

  expect(compose(parsed, initialChoice(parsed), none)).toEqual({
    kind: 'ready',
    plastics: [{ plastic_id: 'pla', usage_cg: 1154 }],
    print_time_s: 5880,
  })
})

test('extra precision rounds up to the next hundredth of a gram (AC-03)', () => {
  const parsed = file(filament(11_543))

  expect(compose(parsed, initialChoice(parsed), none)).toMatchObject({
    plastics: [{ plastic_id: 'pla', usage_cg: 1155 }],
  })
})

test('only the sum of merged filaments is rounded: 2 001 + 2 001 mg → 401 cg (AC-03, AC-10)', () => {
  const parsed = file(filament(2_001, '#FFFFFF'), filament(2_001, '#000000', 'pla', PETG))
  const choice = initialChoice(parsed)
  const conflict = compose(parsed, choice, none)
  expect(conflict.kind).toBe('merge-conflict')
  if (conflict.kind !== 'merge-conflict') return

  const confirmed = new Set([mergeKey(at(conflict.groups, 0))])

  expect(compose(parsed, choice, confirmed)).toEqual({
    kind: 'ready',
    plastics: [{ plastic_id: 'pla', usage_cg: 401 }],
    print_time_s: 5880,
  })
})

test('an unmapped filament blocks the rows and is named (AC-09)', () => {
  const yellow = filament(2_360, '#FEC600', null)
  const parsed = file(filament(15_490, '#3F8E43'), yellow)

  expect(compose(parsed, initialChoice(parsed), none)).toEqual({
    kind: 'unmapped',
    filaments: [yellow],
  })
})

test('choosing a plastic for the unmapped filament makes the rows ready', () => {
  const parsed = file(filament(15_490, '#3F8E43'), filament(2_360, '#FEC600', null))
  const choice = { ...initialChoice(parsed), [filamentKey(at(parsed.filaments, 1))]: 'yellow' }

  expect(compose(parsed, choice, none)).toEqual({
    kind: 'ready',
    plastics: [
      { plastic_id: 'pla', usage_cg: 1549 },
      { plastic_id: 'yellow', usage_cg: 236 },
    ],
    print_time_s: 5880,
  })
})

test('two different filaments on one plastic are a conflict until confirmed (AC-10)', () => {
  const white = filament(1_000, '#FFFFFF')
  const black = filament(2_000, '#000000')
  const parsed = file(white, black)

  expect(compose(parsed, initialChoice(parsed), none)).toEqual({
    kind: 'merge-conflict',
    groups: [{ plasticId: 'pla', filaments: [white, black] }],
  })
})

test('a confirmation is for exactly that set of filaments', () => {
  const parsed = file(filament(1_000, '#FFFFFF'), filament(2_000, '#000000'))
  const twoConfirmed = new Set([mergeKey({ plasticId: 'pla', filaments: parsed.filaments })])
  const withThird = file(...parsed.filaments, filament(3_000, '#FEC600'))

  expect(compose(withThird, initialChoice(withThird), twoConfirmed).kind).toBe('merge-conflict')
})

test('the remembered mappings are every filament with a chosen plastic (AC-07, AC-08)', () => {
  const parsed = file(filament(1_000, '#FFFFFF'), filament(2_000, '#000000', null, PETG))
  const choice = { ...initialChoice(parsed), [filamentKey(at(parsed.filaments, 1))]: 'petg' }

  expect(mappingsFor(parsed, choice)).toEqual([
    { filament_name: PLA, filament_color: '#FFFFFF', plastic_id: 'pla' },
    { filament_name: PETG, filament_color: '#000000', plastic_id: 'petg' },
  ])
  expect(mappingsFor(parsed, initialChoice(parsed))).toEqual([
    { filament_name: PLA, filament_color: '#FFFFFF', plastic_id: 'pla' },
  ])
})
