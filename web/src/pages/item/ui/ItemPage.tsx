import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { useItem } from '@/entities/item'
import { usePlastics } from '@/entities/plastic'
import { DeleteItemButton } from '@/features/delete-item'
import { MissingSettings } from '@/features/quote-form'
import { isProblem } from '@/shared/api'
import { formatDecimal } from '@/shared/lib'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

import { ItemEditor } from './ItemEditor'

function formatTime(seconds: number) {
  const minutes = seconds / 60
  return `${Math.floor(minutes / 60)} год ${minutes % 60} хв`
}

export function ItemPage() {
  const { itemId = '' } = useParams()
  const item = useItem(itemId)
  const plastics = usePlastics()
  const [editing, setEditing] = useState(false)

  if (isProblem(item.error, 'catalog.item_not_found')) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">Виріб</h1>
        <p className="text-sm">Виріб не знайдено.</p>
        <Button asChild variant="outline">
          <Link to="/catalog">До каталогу</Link>
        </Button>
      </section>
    )
  }
  if (isProblem(item.error, 'costing.settings_missing')) {
    return <MissingSettings missing={item.error.problem.missing ?? []} />
  }
  if (item.isError) return <p className="text-destructive text-sm">Не вдалося завантажити виріб.</p>
  if (!item.data || !plastics.data) return <p className="text-sm">Завантажую виріб…</p>

  const detail = item.data
  const names = new Map(plastics.data.map((p) => [p.id, p.name]))
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">{detail.name}</h1>
      {editing ? (
        <ItemEditor item={detail} plastics={plastics.data} onDone={() => setEditing(false)} />
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
            <Card>
              <CardHeader>
                <CardTitle>Параметри</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <ul className="space-y-1">
                  {detail.plastics.map((p) => (
                    <li key={p.plastic_id}>
                      {names.get(p.plastic_id) ?? 'Невідомий пластик'} —{' '}
                      {formatDecimal(p.usage_cg, 2)} г
                    </li>
                  ))}
                </ul>
                <p>Час друку: {formatTime(detail.print_time_s)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Собівартість за поточними цінами</CardTitle>
              </CardHeader>
              <CardContent>
                <CostBreakdown quote={detail.quote} />
              </CardContent>
            </Card>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => setEditing(true)}>Змінити</Button>
            <DeleteItemButton item={detail} />
          </div>
        </>
      )}
    </section>
  )
}
