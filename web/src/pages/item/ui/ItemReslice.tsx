import { useState } from 'react'

import { useUpdateItem, type ItemDetail } from '@/entities/item'
import { useRefreshPlastics, type Plastic } from '@/entities/plastic'
import { useQuote } from '@/entities/quote'
import { parseQuoteForm, QuoteError, QuoteForm, quoteFormFrom } from '@/features/quote-form'
import { saveError } from '@/features/save-item'
import {
  clearRejectedChoice,
  compose,
  diffItem,
  FilamentMappingPanel,
  mappingsFor,
  WasBecomePanel,
  type ImportState,
} from '@/features/slicer-import'
import { isProblem } from '@/shared/api'

type ItemResliceProps = {
  /** The item as saved right now — refetched when the file was imported (AC-05 «було»). */
  item: ItemDetail
  plastics: Plastic[]
  imported: ImportState
  onImportedChange: (state: ImportState) => void
  /** Applies a rejection to the import as it is now, not as this render saw it (AC-08). */
  onImportedUpdate: (update: (current: ImportState) => ImportState) => void
  onDone: () => void
}

/** A re-sliced file for a catalog item: «було → стало», editable until confirmed (AC-05, AC-06). */
export function ItemReslice({
  item,
  plastics,
  imported,
  onImportedChange,
  onImportedUpdate,
  onDone,
}: ItemResliceProps) {
  const [value, setValue] = useState(() => {
    const rows = compose(imported.file, imported.choice, imported.confirmed)
    return quoteFormFrom(rows.kind === 'ready' ? rows : item)
  })
  const [saveFailure, setSaveFailure] = useState<string>()
  const update = useUpdateItem()
  const refreshPlastics = useRefreshPlastics()
  const ready = compose(imported.file, imported.choice, imported.confirmed).kind === 'ready'
  const { input, errors } = parseQuoteForm(value)
  const became = ready ? input : null
  const { quote, error } = useQuote(became)
  const names = new Map(plastics.map((p) => [p.id, p.name]))

  function changeImport(next: ImportState) {
    onImportedChange(next)
    const rows = compose(next.file, next.choice, next.confirmed)
    if (rows.kind === 'ready') setValue(quoteFormFrom(rows))
  }

  function confirm() {
    if (!became) return
    update.mutate(
      {
        id: item.id,
        body: {
          name: item.name,
          ...became,
          filament_mappings: mappingsFor(imported.file, imported.choice),
        },
      },
      {
        onSuccess: onDone,
        onError: (e) => {
          setSaveFailure(saveError(e).form ?? saveError(e).name)
          if (isProblem(e, 'importing.plastic_not_found')) void refreshPlastics()
          onImportedUpdate((current) => clearRejectedChoice(current, e))
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <FilamentMappingPanel state={imported} onChange={changeImport} />
      <QuoteForm
        value={value}
        onChange={setValue}
        plastics={plastics}
        errors={errors}
        showAllErrors
      />
      {error && <QuoteError error={error} />}
      <WasBecomePanel
        diff={became ? diffItem(item, became) : null}
        plasticName={(id) => names.get(id) ?? 'Невідомий пластик'}
        wasDonationKop={item.quote.min_donation_kop}
        becameDonationKop={became && quote ? quote.min_donation_kop : null}
        canConfirm={became !== null && !!quote && !error}
        isSaving={update.isPending}
        onConfirm={confirm}
        onCancel={onDone}
      />
      {saveFailure && <p className="text-destructive text-sm">{saveFailure}</p>}
    </div>
  )
}
