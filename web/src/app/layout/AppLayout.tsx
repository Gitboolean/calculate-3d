import { NavLink, Outlet } from 'react-router'

import { useHealth } from '@/entities/health'
import { Button } from '@/shared/ui'

const links = [
  { to: '/calculate', label: 'Розрахунок' },
  { to: '/catalog', label: 'Каталог' },
  { to: '/settings', label: 'Налаштування цін' },
] as const

const statusLabel = { ok: 'працює', down: 'не відповідає' } as const

function HealthStatus() {
  const health = useHealth()
  if (health.isPending) return <p>Перевіряю API…</p>
  if (health.isError) return <p className="text-destructive">API недоступне</p>
  return (
    <p>
      API: {statusLabel[health.data.status]} · База даних: {statusLabel[health.data.db]}
    </p>
  )
}

export function AppLayout() {
  return (
    <div className="mx-auto flex min-h-svh max-w-4xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
        <span className="font-semibold">calculate-3d</span>
        <nav aria-label="Розділи" className="flex gap-1">
          {links.map((link) => (
            <Button
              key={link.to}
              asChild
              variant="ghost"
              className="aria-[current=page]:bg-secondary"
            >
              <NavLink to={link.to}>{link.label}</NavLink>
            </Button>
          ))}
        </nav>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="text-muted-foreground border-t pt-4 text-xs">
        <HealthStatus />
      </footer>
    </div>
  )
}
