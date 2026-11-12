import type { Schemas } from '@/shared/api'

type SlicerFile = Schemas['SlicerFile']
type Filament = Schemas['SlicerFilament']
type PlasticUsage = Schemas['PlasticUsage']

/** A slicer filament's identity — the mapping key (name, color); unique within one parse. */
export function filamentKey(f: Pick<Filament, 'filament_name' | 'filament_color'>): string {
  return `${f.filament_name}\n${f.filament_color}`
}

/** filamentKey → chosen plastic id ('' = not chosen yet). */
export type FilamentChoice = Record<string, string>

export type MergeGroup = { plasticId: string; filaments: Filament[] }

export type Composition =
  | { kind: 'ready'; plastics: PlasticUsage[]; print_time_s: number }
  | { kind: 'unmapped'; filaments: Filament[] }
  | { kind: 'merge-conflict'; groups: MergeGroup[] }

/** The plastics the server substituted from remembered mappings (AC-07). */
export function initialChoice(file: SlicerFile): FilamentChoice {
  return Object.fromEntries(file.filaments.map((f) => [filamentKey(f), f.plastic_id ?? '']))
}

/** A confirmation of AC-10 covers exactly this plastic and this set of filaments. */
export function mergeKey(group: MergeGroup): string {
  return [group.plasticId, ...group.filaments.map(filamentKey).sort()].join('\0')
}

/**
 * Quote rows from exact milligrams (ADR 0004): group by the chosen plastic, add whole mg, round
 * only the sum up to a hundredth of a gram. Nothing is priced while a filament has no plastic
 * (AC-09) or two different filaments share one without the author's confirmation (AC-10).
 */
export function compose(
  file: SlicerFile,
  choice: FilamentChoice,
  confirmedMerges: ReadonlySet<string>,
): Composition {
  const unmapped = file.filaments.filter((f) => !choice[filamentKey(f)])
  if (unmapped.length > 0) return { kind: 'unmapped', filaments: unmapped }

  const groups = new Map<string, Filament[]>()
  for (const f of file.filaments) {
    const plasticId = choice[filamentKey(f)] ?? ''
    groups.set(plasticId, [...(groups.get(plasticId) ?? []), f])
  }
  const conflicts = [...groups]
    .map(([plasticId, filaments]) => ({ plasticId, filaments }))
    .filter((g) => g.filaments.length > 1 && !confirmedMerges.has(mergeKey(g)))
  if (conflicts.length > 0) return { kind: 'merge-conflict', groups: conflicts }

  const plastics = [...groups].map(([plastic_id, filaments]) => {
    const mg = filaments.reduce((sum, f) => sum + f.usage_mg, 0)
    return { plastic_id, usage_cg: ceilDiv10(mg) }
  })
  return { kind: 'ready', plastics, print_time_s: file.print_time_s }
}

/** Integer ceil(mg / 10) — no float (ADR 0004). */
function ceilDiv10(mg: number): number {
  const rest = mg % 10
  return (mg - rest) / 10 + (rest > 0 ? 1 : 0)
}

/** Every filament with a chosen plastic — even if its row is later removed by hand (AC-08). */
export function mappingsFor(
  file: SlicerFile,
  choice: FilamentChoice,
): Schemas['FilamentMappingInput'][] {
  return file.filaments.flatMap((f) => {
    const plastic_id = choice[filamentKey(f)]
    return plastic_id
      ? [{ filament_name: f.filament_name, filament_color: f.filament_color, plastic_id }]
      : []
  })
}
