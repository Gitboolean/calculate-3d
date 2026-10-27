import { useHealth } from '@/entities/health'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui'

const statusLabel = { ok: 'працює', down: 'не відповідає' } as const

export function HomePage() {
  const health = useHealth()

  return (
    <main className="mx-auto flex min-h-svh max-w-xl items-center p-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>calculate-3d</CardTitle>
          <CardDescription>Собівартість 3D-друку — мінімальний донат у гривнях</CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          {health.isPending && <p>Перевіряю API…</p>}
          {health.isError && <p className="text-destructive">API недоступне</p>}
          {health.data && (
            <>
              <p>API: {statusLabel[health.data.status]}</p>
              <p>База даних: {statusLabel[health.data.db]}</p>
            </>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
