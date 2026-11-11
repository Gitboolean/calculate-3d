import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { useIsUpdatingItem, useItem } from '@/entities/item'
import { usePlastics } from '@/entities/plastic'
import { DeleteItemButton } from '@/features/delete-item'
import { MissingSettings } from '@/features/quote-form'
import {
  ImportFileButton,
  startImport,
  useIsParsingSlicerFile,
  type ImportState,
} from '@/features/slicer-import'
import { isProblem } from '@/shared/api'
import { formatDecimal } from '@/shared/lib'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

import { ItemEditor } from './ItemEditor'
import { ItemReslice } from './ItemReslice'

function formatTime(seconds: number) {
  const minutes = seconds / 60
  return `${Math.floor(minutes / 60)} год ${minutes % 60} хв`
}

export function ItemPage() {
  const { itemId = '' } = useParams()
  const item = useItem(itemId)
  const plastics = usePlastics()
  const [editing, setEditing] = useState(false)
  const isUpdating = useIsUpdatingItem()
  const [imported, setImported] = useState<ImportState | null>(null)
  const [importRound, setImportRound] = useState(0)
  // From parse success until the re-read item is shown: the file is parsed but not yet imported.
  const [reading, setReading] = useState(false)
  const importing = useIsParsingSlicerFile() || reading

  /** «Було» is the item as saved now: unsaved edits are dropped and the item is re-read (AC-05). */
  async function importFile(file: Parameters<typeof startImport>[0]) {
    setEditing(false)
    setReading(true)
    try {
      await item.refetch()
      setImported(startImport(file))
      setImportRound((n) => n + 1)
    } finally {
      setReading(false)
    }
  }

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
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">Виріб</h1>
        <MissingSettings missing={item.error.problem.missing ?? []} />
      </section>
    )
  }
  if (item.isError) return <p className="text-destructive text-sm">Не вдалося завантажити виріб.</p>
  if (plastics.isError) {
    return <p className="text-destructive text-sm">Не вдалося завантажити пластики.</p>
  }
  if (!item.data || !plastics.data) return <p className="text-sm">Завантажую виріб…</p>

  const detail = item.data
  const names = new Map(plastics.data.map((p) => [p.id, p.name]))
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">{detail.name}</h1>
      <ImportFileButton disabled={isUpdating} onParsed={(file) => void importFile(file)} />
      {imported ? (
        <ItemReslice
          key={importRound}
          item={detail}
          plastics={plastics.data}
          imported={imported}
          importing={importing}
          onImportedChange={setImported}
          onImportedUpdate={(update) => {
            setImported((current) => current && update(current))
          }}
          onDone={() => setImported(null)}
        />
      ) : editing ? (
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
