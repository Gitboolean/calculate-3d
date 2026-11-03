import type { QueryClient } from '@tanstack/react-query'

/**
 * Quotes and catalog prices are derived from plastics and price settings. After either changes,
 * drop them from the cache entirely (invalidated data would still be served on mount) so an old
 * donation is never shown as current (AC-06). Keys are string roots to keep entities independent.
 */
export function evictPricedQueries(client: QueryClient) {
  client.removeQueries({ queryKey: ['quote'] })
  client.removeQueries({ queryKey: ['items'] })
}
