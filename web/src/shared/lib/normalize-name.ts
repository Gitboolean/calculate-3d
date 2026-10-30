// Shared name rules for plastics and items. Mirrors backend/src/calculate3d/core/text.py::normalize_name,
// except that the client only trims whitespace; the server also trims Cf characters at the edges
// and has the last word.

export const MAX_NAME_LENGTH = 100

/** NFC-normalizes `raw` and trims surrounding whitespace. */
export function normalizeName(raw: string): string {
  return raw.normalize('NFC').trim()
}

/** Length in code points, as the server counts. */
export function nameLength(name: string): number {
  return [...name].length
}
