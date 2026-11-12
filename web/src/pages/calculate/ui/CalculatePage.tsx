import { useState } from 'react'

import { useIsCreatingItem } from '@/entities/item'
import { useRefreshPlastics, usePlastics } from '@/entities/plastic'
import { usePriceSettings } from '@/entities/price-settings'
import { useQuote } from '@/entities/quote'
import {
  emptyQuoteForm,
  MissingSettings,
  parseQuoteForm,
  QuoteError,
  QuoteForm,
  quoteFormFrom,
  type QuoteFormValue,
} from '@/features/quote-form'
import { SaveItemForm } from '@/features/save-item'
import {
  clearRejectedChoice,
  compose,
  FilamentMappingPanel,
  ImportFileButton,
  mappingsFor,
  startImport,
  useIsParsingSlicerFile,
  type ImportState,
} from '@/features/slicer-import'
import { isProblem } from '@/shared/api'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

interface PageState {
  value: QuoteFormValue
  imported: ImportState | null
  importRound: number
  beforeImport: QuoteFormValue | null
}

export function CalculatePage() {
  const plastics = usePlastics()
  const refreshPlastics = useRefreshPlastics()
  const settings = usePriceSettings()
  const isSaving = useIsCreatingItem()
  const isParsing = useIsParsingSlicerFile()
  // One object so every step is a functional update of the current state: TanStack mutation
  // callbacks fire from stale render closures (AC-07, AC-09b).
  const [state, setState] = useState<PageState>({
    value: emptyQuoteForm(),
    imported: null,
    // Counts imports so a re-imported file mounts a fresh mapping panel (AC-10).
    importRound: 0,
    // The form as it was before the first import, restored on cancel (AC-07).
    beforeImport: null,
  })
  const { value, imported, importRound } = state
  const composition = imported && compose(imported.file, imported.choice, imported.confirmed)
  // An import with a filament still unmapped or an unconfirmed merge prices nothing (AC-09, AC-10).
  const importBlocks = composition !== null && composition.kind !== 'ready'
  const { input, errors } = parseQuoteForm(value)
  const { quote, error, isCalculating } = useQuote(importBlocks ? null : input)

  /** A ready import replaces every row and the time, manual or from an earlier file (AC-01). */
  function applyImport(next: ImportState, isNewFile = false) {
    setState((s) => {
      const rows = compose(next.file, next.choice, next.confirmed)
      return {
        value: rows.kind === 'ready' ? quoteFormFrom(rows) : s.value,
        imported: next,
        importRound: isNewFile ? s.importRound + 1 : s.importRound,
        beforeImport: s.imported === null ? s.value : s.beforeImport,
      }
    })
  }

  function cancelImport() {
    setState((s) => ({
      ...s,
      value: s.beforeImport ?? s.value,
      imported: null,
      beforeImport: null,
    }))
  }

  const heading = <h1 className="text-2xl font-semibold">Розрахунок</h1>
  if (plastics.isError || settings.isError) {
    return (
      <section className="space-y-4">
        {heading}
        <p className="text-destructive text-sm">Не вдалося завантажити налаштування цін.</p>
      </section>
    )
  }
  if (!plastics.isSuccess || !settings.isSuccess) {
    return (
      <section className="space-y-4">
        {heading}
        <p className="text-sm">Завантажую налаштування цін…</p>
      </section>
    )
  }

  const missing: ('plastics' | 'price_settings')[] = [
    ...(plastics.data.length === 0 ? (['plastics'] as const) : []),
    ...(settings.data === null ? (['price_settings'] as const) : []),
  ]
  if (missing.length > 0) {
    return (
      <section className="space-y-4">
        {heading}
        <MissingSettings missing={missing} />
      </section>
    )
  }

  return (
    <section className="space-y-6">
      {heading}
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>Витрата й час зі слайсера</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ImportFileButton
              disabled={isSaving}
              onParsed={(file) => {
                applyImport(startImport(file), true)
              }}
            />
            {imported && (
              <>
                <FilamentMappingPanel key={importRound} state={imported} onChange={applyImport} />
                <Button type="button" variant="outline" disabled={isSaving} onClick={cancelImport}>
                  Скасувати імпорт
                </Button>
              </>
            )}
            <QuoteForm
              value={value}
              onChange={(next) => {
                setState((s) => ({ ...s, value: next }))
              }}
              plastics={plastics.data}
              errors={errors}
              showAllErrors={imported !== null}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Собівартість</CardTitle>
          </CardHeader>
          <CardContent>
            {importBlocks ? (
              <p className="text-muted-foreground text-sm">
                Мінімальний донат з’явиться, коли кожен філамент із файлу матиме пластик.
              </p>
            ) : error ? (
              <QuoteError error={error} />
            ) : quote || isCalculating ? (
              <CostBreakdown quote={quote} isCalculating={isCalculating} />
            ) : (
              <p className="text-muted-foreground text-sm">
                Заповніть витрату пластику й час друку — донат з’явиться автоматично.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Зберегти в каталог</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Only a calculation with its donation on screen can be saved (AC-10). */}
          <SaveItemForm
            disabled={isParsing}
            input={quote && !importBlocks ? input : null}
            filamentMappings={imported ? mappingsFor(imported.file, imported.choice) : []}
            onSaveError={(e, sent) => {
              if (isProblem(e, 'importing.plastic_not_found')) void refreshPlastics()
              setState((s) =>
                s.imported ? { ...s, imported: clearRejectedChoice(s.imported, e, sent) } : s,
              )
            }}
          />
        </CardContent>
      </Card>
    </section>
  )
}
