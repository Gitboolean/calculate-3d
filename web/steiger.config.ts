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
    // them so /settings stays a thin composition (tasks T14).
    files: ['./src/features/edit-plastic/**', './src/features/edit-price-settings/**'],
    rules: { 'fsd/insignificant-slice': 'off' },
  },
  {
    // TEMPORARY until T17: the quote form on /calculate becomes the second consumer.
    files: ['./src/entities/plastic/**', './src/entities/price-settings/**'],
    rules: { 'fsd/insignificant-slice': 'off' },
  },
])
