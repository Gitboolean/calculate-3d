import type { Schemas } from '@/shared/api'

import { initialChoice, mergeKey, type FilamentChoice, type MergeGroup } from './compose'

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
