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
 * filament's plastic again. `<i>` indexes the array `mappingsFor` built — chosen filaments only.
 */
export function clearRejectedChoice(state: ImportState, error: unknown): ImportState {
  const field = isProblem(error, 'importing.plastic_not_found') ? error.problem.field : undefined
  const index = Number(/^filament_mappings\.(\d+)\./.exec(field ?? '')?.[1])
  const chosen = state.file.filaments.filter((f) => state.choice[filamentKey(f)])
  const rejected = chosen[index]
  return rejected ? choosePlastic(state, filamentKey(rejected), '') : state
}
