import { useState } from 'react'

import { usePlastics } from '@/entities/plastic'
import { usePriceSettings } from '@/entities/price-settings'
import { useQuote } from '@/entities/quote'
import {
  emptyQuoteForm,
  MissingSettings,
  parseQuoteForm,
  QuoteError,
  QuoteForm,
  quoteFormFrom,
} from '@/features/quote-form'
import { SaveItemForm } from '@/features/save-item'
import {
  compose,
  FilamentMappingPanel,
  ImportFileButton,
  mappingsFor,
  startImport,
  type ImportState,
} from '@/features/slicer-import'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

export function CalculatePage() {
  const plastics = usePlastics()
  const settings = usePriceSettings()
  const [value, setValue] = useState(emptyQuoteForm)
  const [imported, setImported] = useState<ImportState | null>(null)
  const composition = imported && compose(imported.file, imported.choice, imported.confirmed)
  // An import with a filament still unmapped or an unconfirmed merge prices nothing (AC-09, AC-10).
  const importBlocks = composition !== null && composition.kind !== 'ready'
  const { input, errors } = parseQuoteForm(value)
  const { quote, error, isCalculating } = useQuote(importBlocks ? null : input)

  /** A ready import replaces every row and the time, manual or from an earlier file (AC-01). */
  function applyImport(next: ImportState) {
    setImported(next)
    const rows = compose(next.file, next.choice, next.confirmed)
    if (rows.kind === 'ready') setValue(quoteFormFrom(rows))
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
            <ImportFileButton onParsed={(file) => applyImport(startImport(file))} />
            {imported && <FilamentMappingPanel state={imported} onChange={applyImport} />}
            <QuoteForm value={value} onChange={setValue} plastics={plastics.data} errors={errors} />
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
            input={quote && !importBlocks ? input : null}
            filamentMappings={imported ? mappingsFor(imported.file, imported.choice) : []}
          />
        </CardContent>
      </Card>
    </section>
  )
}
