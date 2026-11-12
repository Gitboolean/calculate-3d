import { isProblem, type Schemas } from '@/shared/api'

import {
  filamentKey,
  initialChoice,
  mergeKey,
  type FilamentChoice,
  type MergeGroup,
} from './compose'

/**
 * An import in progress — screen memory only: it is gone after save, cancel or reload, so an
 * import interrupted to add a plastic must be uploaded again (AC-09b).
 */
export type ImportState = {
  file: Schemas['SlicerFile']
  choice: FilamentChoice
  confirmed: ReadonlySet<string>
}

export function startImport(file: Schemas['SlicerFile']): ImportState {
  return { file, choice: initialChoice(file), confirmed: new Set() }
}

export function choosePlastic(state: ImportState, key: string, plasticId: string): ImportState {
  return { ...state, choice: { ...state.choice, [key]: plasticId } }
}

/** The author confirmed these filaments are the same plastic (AC-10). */
export function confirmMerge(state: ImportState, group: MergeGroup): ImportState {
  return { ...state, confirmed: new Set([...state.confirmed, mergeKey(group)]) }
}

/**
 * A save rejected for a deleted mapped plastic (`filament_mappings.<i>.plastic_id`): ask for that
 * filament's plastic again. `<i>` indexes the array that was `sent` with the request, not the
 * current choices; a choice changed since then is left alone.
 */
export function clearRejectedChoice(
  state: ImportState,
  error: unknown,
  sent: readonly Schemas['FilamentMappingInput'][],
): ImportState {
  const field = isProblem(error, 'importing.plastic_not_found') ? error.problem.field : undefined
  const index = Number(/^filament_mappings\.(\d+)\./.exec(field ?? '')?.[1])
  const rejected = sent[index]
  if (!rejected) return state
  const key = filamentKey(rejected)
  return state.choice[key] === rejected.plastic_id ? choosePlastic(state, key, '') : state
}
