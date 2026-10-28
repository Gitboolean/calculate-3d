import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, unwrap, type Schemas } from '@/shared/api'

export type Plastic = Schemas['Plastic']
export type PlasticInput = Schemas['PlasticInput']

export const plasticsKey = ['plastics'] as const

export function usePlastics() {
  return useQuery({
    queryKey: plasticsKey,
    queryFn: async () => (await unwrap(api.GET('/api/pricing/plastics'))).items,
  })
}

function useInvalidatePlastics() {
  const client = useQueryClient()
  return () => client.invalidateQueries({ queryKey: plasticsKey })
}

export function useCreatePlastic() {
  const onSuccess = useInvalidatePlastics()
  return useMutation({
    mutationFn: (body: PlasticInput) => unwrap(api.POST('/api/pricing/plastics', { body })),
    onSuccess,
  })
}

export function useUpdatePlastic() {
  const onSuccess = useInvalidatePlastics()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: PlasticInput }) =>
      unwrap(
        api.PUT('/api/pricing/plastics/{plastic_id}', {
          params: { path: { plastic_id: id } },
          body,
        }),
      ),
    onSuccess,
  })
}

export function useDeletePlastic() {
  const onSuccess = useInvalidatePlastics()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/pricing/plastics/{plastic_id}', { params: { path: { plastic_id: id } } }),
      ),
    onSuccess,
  })
}
