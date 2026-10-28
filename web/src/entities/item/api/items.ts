import { useMutation, useQueryClient } from '@tanstack/react-query'

import { api, unwrap, type Schemas } from '@/shared/api'

export type Item = Schemas['Item']
export type ItemInput = Schemas['ItemInput']

export const itemKeys = {
  all: ['items'] as const,
  list: (query: string) => ['items', 'list', query] as const,
  detail: (id: string) => ['items', 'detail', id] as const,
}

export function useCreateItem() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: ItemInput) => unwrap(api.POST('/api/catalog/items', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: itemKeys.all }),
  })
}
