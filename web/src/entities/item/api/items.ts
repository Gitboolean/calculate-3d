import {
  keepPreviousData,
  useIsMutating,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { api, unwrap, type Schemas } from '@/shared/api'

export type Item = Schemas['Item']
export type ItemInput = Schemas['ItemInput']
export type ItemSummary = Schemas['ItemSummary']
export type ItemDetail = Schemas['ItemDetail']

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
    placeholderData: keepPreviousData,
    staleTime: 0,
    refetchOnMount: 'always',
  })
}

const createItemKey = ['items', 'create'] as const

/** True while a create request is in flight, wherever the form that started it lives. */
export function useIsCreatingItem() {
  return useIsMutating({ mutationKey: createItemKey }) > 0
}

export function useCreateItem() {
  const client = useQueryClient()
  return useMutation({
    mutationKey: createItemKey,
    mutationFn: (body: ItemInput) => unwrap(api.POST('/api/catalog/items', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: itemKeys.all }),
  })
}

/** One item with its quote from current prices (AC-14); fetched fresh on every opening. */
export function useItem(id: string) {
  return useQuery({
    queryKey: itemKeys.detail(id),
    queryFn: () =>
      unwrap(api.GET('/api/catalog/items/{item_id}', { params: { path: { item_id: id } } })),
    staleTime: 0,
    refetchOnMount: 'always',
  })
}

const updateItemKey = ['items', 'update'] as const

/** True while an update request is in flight, wherever the screen that started it lives. */
export function useIsUpdatingItem() {
  return useIsMutating({ mutationKey: updateItemKey }) > 0
}

export function useUpdateItem() {
  const client = useQueryClient()
  return useMutation({
    mutationKey: updateItemKey,
    mutationFn: ({ id, body }: { id: string; body: ItemInput }) =>
      unwrap(api.PUT('/api/catalog/items/{item_id}', { params: { path: { item_id: id } }, body })),
    onSuccess: () => client.invalidateQueries({ queryKey: itemKeys.all }),
  })
}

export function useDeleteItem() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/api/catalog/items/{item_id}', { params: { path: { item_id: id } } })),
    onSuccess: (_, id) => {
      client.removeQueries({ queryKey: itemKeys.detail(id) })
      return client.invalidateQueries({ queryKey: ['items', 'list'] })
    },
  })
}
