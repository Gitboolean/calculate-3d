import type { Quote } from '@/entities/quote'
import { formatMoney } from '@/shared/lib'

type CostBreakdownProps = { quote?: Quote; isCalculating?: boolean }

/** Shows the server's numbers as-is — the UI never adds or rounds money (ADR 0002, AC-08). */
export function CostBreakdown({ quote, isCalculating = false }: CostBreakdownProps) {
  if (!quote) return isCalculating ? <p className="text-muted-foreground text-sm">Рахую…</p> : null

  const rows = [
    ['Пластик', quote.breakdown.plastic_kop],
    ['Електрика', quote.breakdown.electricity_kop],
    ['Знос', quote.breakdown.wear_kop],
    ['Брак', quote.breakdown.scrap_kop],
  ] as const

  return (
    <div className="space-y-4">
      <div role="status" aria-label="Мінімальний донат" className="space-y-1">
        <p className="text-muted-foreground text-sm">Мінімальний донат</p>
        <p className="text-3xl font-semibold tabular-nums">{formatMoney(quote.min_donation_kop)}</p>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
        {rows.map(([label, kop]) => (
          <div key={label} className="contents">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="text-right tabular-nums">{formatMoney(kop)}</dd>
          </div>
        ))}
      </dl>
      <p className="text-muted-foreground text-xs">
        Донат округлено вгору з точної суми; рядки округлено до копійки окремо.
      </p>
    </div>
  )
}
