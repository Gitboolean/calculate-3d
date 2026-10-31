// Shared name rules for plastics and items. Mirrors backend/src/calculate3d/core/text.py::normalize_name:
// NFC, then trim whitespace (Python `str.isspace()`) and invisible format characters (Unicode Cf)
// at both ends only. The server still has the last word.

export const MAX_NAME_LENGTH = 100

// JS `\s` plus the Python-only whitespace (U+001C..U+001F, U+0085) plus Cf.
// eslint-disable-next-line no-control-regex -- U+001C..U+001F are whitespace to the server's isspace()
const EDGE_TRIMMABLE = /^[\s\p{Cf}\u001c-\u001f\u0085]+|[\s\p{Cf}\u001c-\u001f\u0085]+$/gu

/** NFC-normalizes `raw` and trims whitespace and invisible format characters at both ends, as the server does. */
export function normalizeName(raw: string): string {
  return raw.normalize('NFC').replace(EDGE_TRIMMABLE, '')
}

/** Length in code points, as the server counts. */
export function nameLength(name: string): number {
  return [...name].length
}
