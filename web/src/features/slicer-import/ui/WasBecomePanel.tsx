import { formatDecimal, formatMoney } from '@/shared/lib'
import { Button } from '@/shared/ui'

import type { ItemDiff, PlasticDiff } from '../model/diff'

/** 8 000 cg → «80 г», 1 154 cg → «11,54 г». */
function grams(cg: number): string {
  return `${formatDecimal(cg, 2).replace(/,00$/, '')} г`
}

function time(seconds: number): string {
  const minutes = seconds / 60
  return `${Math.floor(minutes / 60)} год ${minutes % 60} хв`
}

function plasticLine(row: PlasticDiff, name: string): string {
  const was = row.wasCg === null ? 'немає' : grams(row.wasCg)
  const became = row.becameCg === null ? 'прибрано' : grams(row.becameCg)
  return `${name}: ${was} → ${became}`
}

/**
 * AC-05: the saved item («було») next to the import («стало») before anything is saved. Nothing
 * changes until «Підтвердити»; «Скасувати» leaves the item as it was (AC-06)
 * and is locked while the save is in flight.
 */
export function WasBecomePanel({
  diff,
  plasticName,
  wasDonationKop,
  becameDonationKop,
  canConfirm,
  isSaving,
  onConfirm,
  onCancel,
}: {
  diff: ItemDiff | null
  plasticName: (id: string) => string
  wasDonationKop: number
  becameDonationKop: number | null
  canConfirm: boolean
  isSaving: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <section aria-label="Було → стало" className="space-y-3 rounded-md border p-4">
      <h2 className="font-semibold">Було → стало</h2>
      {diff ? (
        <ul className="space-y-1 text-sm">
          {diff.plastics.map((row) => (
            <li key={row.plasticId} data-change={row.change}>
              {plasticLine(row, plasticName(row.plasticId))}
            </li>
          ))}
          <li data-change={diff.printTime.change}>
            Час друку: {time(diff.printTime.wasS)} → {time(diff.printTime.becameS)}
          </li>
          <li>
            Мінімальний донат: {formatMoney(wasDonationKop)} →{' '}
            {becameDonationKop === null ? '…' : formatMoney(becameDonationKop)}
          </li>
        </ul>
      ) : (
        <p className="text-muted-foreground text-sm">
          «Стало» з’явиться, коли кожен філамент матиме пластик, а поля — коректні значення.
        </p>
      )}
      <div className="flex gap-2">
        <Button type="button" disabled={!canConfirm || isSaving} onClick={onConfirm}>
          Підтвердити
        </Button>
        <Button type="button" variant="outline" disabled={isSaving} onClick={onCancel}>
          Скасувати
        </Button>
      </div>
    </section>
  )
}
