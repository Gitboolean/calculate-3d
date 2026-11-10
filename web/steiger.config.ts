import fsd from '@feature-sliced/steiger-plugin'
import { defineConfig } from 'steiger'

export default defineConfig([
  ...fsd.configs.recommended,
  {
    // Baseline precedent from docs/architecture-map.md §Frontend: new screens copy this
    // entity, so it stays a slice even while the app shell is its only consumer.
    files: ['./src/entities/health/**'],
    rules: { 'fsd/insignificant-slice': 'off' },
  },
  {
    // `app/providers` is the agreed name for the provider composition (architecture-map).
    files: ['./src/app/providers/**'],
    rules: { 'fsd/segments-by-purpose': 'off' },
  },
  {
    // Entity slices are named after the domain glossary (CONTEXT.md): `plastic`, `item`,
    // `quote`, `price-settings` (one settings record) and the uncountable `health`.
    files: ['./src/entities/**'],
    rules: { 'fsd/inconsistent-naming': 'off' },
  },
  {
    // User actions from the cost-calculator SAD, kept as features even with one page using
    // them so the pages stay thin compositions (tasks T14, T15, T20).
    files: [
      './src/features/edit-plastic/**',
      './src/features/edit-price-settings/**',
      './src/features/delete-item/**',
    ],
    rules: { 'fsd/insignificant-slice': 'off' },
  },
  {
    // TEMPORARY (print-file-import T12–T15): the slice is built bottom-up and gets its two
    // consumers — the calculate (T15) and item (T16) pages — later. T16 removes this block.
    files: ['./src/features/slicer-import/**'],
    rules: { 'fsd/insignificant-slice': 'off' },
  },
])
