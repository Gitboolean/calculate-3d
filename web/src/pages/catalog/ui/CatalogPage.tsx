import { Link, useSearchParams } from 'react-router'

import { useItems } from '@/entities/item'
import { MissingSettings } from '@/features/quote-form'
import { isProblem } from '@/shared/api'
import { formatMoney, useDebouncedValue } from '@/shared/lib'
import {
  FormField,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui'

const CATALOG_SEARCH_DEBOUNCE_MS = 200

export function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const settledQuery = useDebouncedValue(query, CATALOG_SEARCH_DEBOUNCE_MS)
  const items = useItems(settledQuery)

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Каталог</h1>
      <div className="max-w-sm">
        <FormField
          label="Пошук за назвою"
          type="search"
          value={query}
          onChange={(e) =>
            setParams(e.target.value ? { q: e.target.value } : {}, { replace: true })
          }
        />
      </div>
      {items.data === undefined && items.isPending && (
        <p className="text-sm">Завантажую каталог…</p>
      )}
      {isProblem(items.error, 'costing.settings_missing') ? (
        <MissingSettings missing={items.error.problem.missing ?? []} />
      ) : (
        items.isError && <p className="text-destructive text-sm">Не вдалося завантажити каталог.</p>
      )}
      {/* Placeholder rows belong to the previous search; its empty state would misdescribe this one. */}
      {items.data?.length === 0 && !items.isPlaceholderData && (
        <p className="text-muted-foreground text-sm">
          {settledQuery.trim()
            ? `Нічого не знайдено за запитом «${settledQuery.trim()}».`
            : 'Каталог порожній. Збережіть розрахунок на сторінці «Розрахунок».'}
        </p>
      )}
      {!!items.data?.length && (
        // Server order: Latin first, then the Ukrainian alphabet (AC-12) — not re-sorted here.
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Назва</TableHead>
              <TableHead className="text-right">Мінімальний донат</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.data.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Link to={`/catalog/${item.id}`} className="underline-offset-4 hover:underline">
                    {item.name}
                  </Link>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(item.min_donation_kop)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  )
}
