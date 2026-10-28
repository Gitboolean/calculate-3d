import { useState } from 'react'

import { usePlastics } from '@/entities/plastic'
import { usePriceSettings } from '@/entities/price-settings'
import { useQuote } from '@/entities/quote'
import { emptyQuoteForm, MissingSettings, parseQuoteForm, QuoteForm } from '@/features/quote-form'
import { isProblem } from '@/shared/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

export function CalculatePage() {
  const plastics = usePlastics()
  const settings = usePriceSettings()
  const [value, setValue] = useState(emptyQuoteForm)
  const { input, errors } = parseQuoteForm(value)
  const { quote, error, isCalculating } = useQuote(input)

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

  const missing = [
    ...(plastics.data.length === 0 ? ['plastics'] : []),
    ...(settings.data === null ? ['price_settings'] : []),
  ]
  if (missing.length > 0) {
    return (
      <section className="space-y-4">
        {heading}
        <MissingSettings missing={missing} />
      </section>
    )
  }

  const serverMissing = isProblem(error, 'costing.settings_missing')
    ? (error.problem.missing ?? [])
    : null
  return (
    <section className="space-y-6">
      {heading}
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>Витрата й час зі слайсера</CardTitle>
          </CardHeader>
          <CardContent>
            <QuoteForm value={value} onChange={setValue} plastics={plastics.data} errors={errors} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Собівартість</CardTitle>
          </CardHeader>
          <CardContent>
            {serverMissing ? (
              <MissingSettings missing={serverMissing} />
            ) : error ? (
              <p className="text-destructive text-sm">Не вдалося порахувати. Перевірте поля.</p>
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
    </section>
  )
}
