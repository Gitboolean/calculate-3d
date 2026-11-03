// Shared name rules for plastics and items. Mirrors backend/src/calculate3d/core/text.py::normalize_name:
// NFC, then trim whitespace (Python `str.isspace()`) and invisible format characters (Unicode Cf)
// at both ends only. The server still has the last word.

export const MAX_NAME_LENGTH = 100

// JS `\s` plus the Python-only whitespace (U+001C..U+001F, U+0085) plus Cf.
// Tested one code point at a time from each end, so trimming stays linear (a regex with a `$`
// branch backtracks from every interior position).
// eslint-disable-next-line no-control-regex -- U+001C..U+001F are whitespace to the server's isspace()
const TRIMMABLE = /^[\s\p{Cf}\u001c-\u001f\u0085]$/u

/** NFC-normalizes `raw` and trims whitespace and invisible format characters at both ends, as the server does. */
export function normalizeName(raw: string): string {
  const chars = Array.from(raw.normalize('NFC'))
  let start = 0
  let end = chars.length
  while (start < end && TRIMMABLE.test(chars[start] ?? '')) start++
  while (end > start && TRIMMABLE.test(chars[end - 1] ?? '')) end--
  return chars.slice(start, end).join('')
}

/** Length in code points, as the server counts. */
export function nameLength(name: string): number {
  return [...name].length
}
