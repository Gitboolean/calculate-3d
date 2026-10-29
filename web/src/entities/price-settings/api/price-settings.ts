import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, unwrap, type Schemas } from '@/shared/api'
import { evictPricedQueries } from '@/shared/lib'

export type PriceSettings = Schemas['PriceSettings']
export type PriceSettingsInput = Schemas['PriceSettingsInput']

export const priceSettingsKey = ['price-settings'] as const

/** `null` until the settings are saved for the first time (AC-09). */
export function usePriceSettings() {
  return useQuery({
    queryKey: priceSettingsKey,
    queryFn: () => unwrap(api.GET('/api/pricing/settings')),
  })
}

export function useReplacePriceSettings() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: PriceSettingsInput) => unwrap(api.PUT('/api/pricing/settings', { body })),
    onSuccess: (saved) => {
      evictPricedQueries(client)
      client.setQueryData(priceSettingsKey, saved)
    },
  })
}
