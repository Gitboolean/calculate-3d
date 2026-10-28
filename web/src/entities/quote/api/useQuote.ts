import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { api, unwrap, type Schemas } from '@/shared/api'

export type QuoteInput = Schemas['QuoteInput']
export type Quote = Schemas['Quote']

/** Pause in typing before the server is asked (cost-calculator ADR 0002). */
export const QUOTE_DEBOUNCE_MS = 200

/**
 * The server's quote for exactly `input`. The query key is the input itself, and while the
 * debounced key lags behind the current one nothing is returned — a donation on screen always
 * belongs to the values on screen (AC-06).
 */
export function useQuote(input: QuoteInput | null, delayMs = QUOTE_DEBOUNCE_MS) {
  const key = input ? JSON.stringify(input) : null
  const [settledKey, setSettledKey] = useState(key)

  useEffect(() => {
    const timer = setTimeout(() => setSettledKey(key), delayMs)
    return () => clearTimeout(timer)
  }, [key, delayMs])

  const query = useQuery({
    queryKey: ['quote', settledKey],
    queryFn: ({ signal }) =>
      unwrap(
        api.POST('/api/costing/quote', {
          body: JSON.parse(settledKey ?? 'null') as QuoteInput,
          signal,
        }),
      ),
    enabled: settledKey !== null,
    retry: false,
  })

  const settled = key !== null && settledKey === key
  return {
    quote: settled ? query.data : undefined,
    error: settled ? query.error : null,
    isCalculating: key !== null && (!settled || query.isFetching),
  }
}
