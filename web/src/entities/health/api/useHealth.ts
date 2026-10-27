import { useQuery } from '@tanstack/react-query'

import { api, type Schemas } from '@/shared/api'

export type Health = Schemas['HealthOut']

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async (): Promise<Health> => {
      const { data, error } = await api.GET('/api/health')
      if (error || !data) throw new Error('Health check failed')
      return data
    },
  })
}
