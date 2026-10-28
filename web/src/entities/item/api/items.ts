import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, unwrap, type Schemas } from '@/shared/api'

export type Item = Schemas['Item']
export type ItemInput = Schemas['ItemInput']
export type ItemSummary = Schemas['ItemSummary']

export const itemKeys = {
  all: ['items'] as const,
  list: (query: string) => ['items', 'list', query] as const,
  detail: (id: string) => ['items', 'detail', id] as const,
}

/** Prices are recomputed by the server on every read, so every opening asks again (AC-13). */
export function useItems(query: string) {
  const q = query.trim()
  return useQuery({
    queryKey: itemKeys.list(q),
    queryFn: async () =>
      (await unwrap(api.GET('/api/catalog/items', { params: { query: q ? { q } : {} } }))).items,
    staleTime: 0,
    refetchOnMount: 'always',
  })
}

export function useCreateItem() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: ItemInput) => unwrap(api.POST('/api/catalog/items', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: itemKeys.all }),
  })
}
