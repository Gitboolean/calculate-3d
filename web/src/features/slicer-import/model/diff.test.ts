import { diffItem } from './diff'

test('«Підставка» re-sliced: PLA 80 → 95 g, PETG removed, 2:00 → 2:15 (AC-05)', () => {
  const saved = {
    plastics: [
      { plastic_id: 'pla', usage_cg: 8000 },
      { plastic_id: 'petg', usage_cg: 4000 },
    ],
    print_time_s: 7200,
  }
  const next = { plastics: [{ plastic_id: 'pla', usage_cg: 9500 }], print_time_s: 8100 }

  expect(diffItem(saved, next)).toEqual({
    plastics: [
      { plasticId: 'pla', wasCg: 8000, becameCg: 9500, change: 'changed' },
      { plasticId: 'petg', wasCg: 4000, becameCg: null, change: 'removed' },
    ],
    printTime: { wasS: 7200, becameS: 8100, change: 'changed' },
  })
})

test('a new plastic is added and an equal one is unchanged', () => {
  const saved = { plastics: [{ plastic_id: 'pla', usage_cg: 100 }], print_time_s: 60 }
  const next = {
    plastics: [
      { plastic_id: 'pla', usage_cg: 100 },
      { plastic_id: 'petg', usage_cg: 50 },
    ],
    print_time_s: 60,
  }

  expect(diffItem(saved, next)).toEqual({
    plastics: [
      { plasticId: 'pla', wasCg: 100, becameCg: 100, change: 'same' },
      { plasticId: 'petg', wasCg: null, becameCg: 50, change: 'added' },
    ],
    printTime: { wasS: 60, becameS: 60, change: 'same' },
  })
})
