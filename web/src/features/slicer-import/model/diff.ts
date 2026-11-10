import type { Schemas } from '@/shared/api'

type Parameters = { plastics: Schemas['PlasticUsage'][]; print_time_s: number }

export type Change = 'same' | 'changed' | 'added' | 'removed'
export type PlasticDiff = {
  plasticId: string
  wasCg: number | null
  becameCg: number | null
  change: Change
}
export type ItemDiff = {
  plastics: PlasticDiff[]
  printTime: { wasS: number; becameS: number; change: 'same' | 'changed' }
}

function changeOf(was: number | null, became: number | null): Change {
  if (was === null) return 'added'
  if (became === null) return 'removed'
  return was === became ? 'same' : 'changed'
}

/** «Було → стало» (AC-05): the saved item's rows first, then the plastics the file adds. */
export function diffItem(saved: Parameters, next: Parameters): ItemDiff {
  const became = new Map(next.plastics.map((p) => [p.plastic_id, p.usage_cg]))
  const wasIds = new Set(saved.plastics.map((p) => p.plastic_id))
  const rows: { id: string; was: number | null }[] = [
    ...saved.plastics.map((p) => ({ id: p.plastic_id, was: p.usage_cg })),
    ...next.plastics
      .filter((p) => !wasIds.has(p.plastic_id))
      .map((p) => ({ id: p.plastic_id, was: null })),
  ]
  const plastics = rows.map(({ id, was }) => {
    const becameCg = became.get(id) ?? null
    return { plasticId: id, wasCg: was, becameCg, change: changeOf(was, becameCg) }
  })
  const timeChange = saved.print_time_s === next.print_time_s ? 'same' : 'changed'
  return {
    plastics,
    printTime: { wasS: saved.print_time_s, becameS: next.print_time_s, change: timeChange },
  }
}
