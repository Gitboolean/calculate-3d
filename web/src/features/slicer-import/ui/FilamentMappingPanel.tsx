import { useState } from 'react'
import { Link } from 'react-router'

import { usePlastics } from '@/entities/plastic'
import {
  NativeSelect,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui'

import { compose, filamentKey, mergeKey } from '../model/compose'
import { formatMg } from '../model/grams'
import { choosePlastic, confirmMerge, type ImportState } from '../model/state'
import { MergeConfirmDialog } from './MergeConfirmDialog'

/**
 * The imported plate and its filaments as the slicer wrote them, each with a plastic to choose
 * (AC-02, AC-07). Names from the file are rendered as text only (PRD §6.1).
 */
export function FilamentMappingPanel({
  state,
  onChange,
}: {
  state: ImportState
  onChange: (state: ImportState) => void
}) {
  const plastics = usePlastics()
  const [dismissed, setDismissed] = useState<ReadonlySet<string>>(new Set())
  const composition = compose(state.file, state.choice, state.confirmed)
  const conflicts = composition.kind === 'merge-conflict' ? composition.groups : []
  const asking = conflicts.find((g) => !dismissed.has(mergeKey(g))) ?? null
  const names = new Map((plastics.data ?? []).map((p) => [p.id, p.name]))
  const { plate } = state.file

  return (
    <section aria-label="Філаменти з файлу" className="space-y-3">
      <p className="text-sm font-medium">
        {plate.name ? `Пластина ${plate.index} · ${plate.name}` : `Пластина ${plate.index}`}
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Філамент</TableHead>
            <TableHead>Тип</TableHead>
            <TableHead>Колір</TableHead>
            <TableHead>Витрата</TableHead>
            <TableHead>Пластик</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {state.file.filaments.map((f) => {
            const key = filamentKey(f)
            const chosen = state.choice[key] ?? ''
            return (
              <TableRow key={key} aria-label={`${f.filament_name} ${f.filament_color}`}>
                <TableCell>{f.filament_name}</TableCell>
                <TableCell>{f.filament_type}</TableCell>
                <TableCell>
                  <span className="inline-flex items-center gap-2">
                    <span
                      data-testid="swatch"
                      aria-hidden
                      className="border-border inline-block size-4 rounded-sm border"
                      style={{ backgroundColor: f.filament_color }}
                    />
                    {f.filament_color}
                  </span>
                </TableCell>
                <TableCell>{formatMg(f.usage_mg)}</TableCell>
                <TableCell className="space-y-1">
                  <NativeSelect
                    aria-label={`Пластик для ${f.filament_name} ${f.filament_color}`}
                    aria-invalid={!chosen}
                    value={chosen}
                    onChange={(e) => onChange(choosePlastic(state, key, e.target.value))}
                  >
                    <option value="">Оберіть пластик</option>
                    {(plastics.data ?? []).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </NativeSelect>
                  {chosen && chosen === f.plastic_id && (
                    <p className="text-muted-foreground text-xs">підставлено з зіставлення</p>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>

      {composition.kind === 'unmapped' && (
        <div role="status" className="space-y-1 text-sm">
          <p>
            Оберіть пластик для:{' '}
            {composition.filaments
              .map((f) => `${f.filament_name} (${f.filament_color})`)
              .join(', ')}
            . Мінімальний донат з’явиться, коли кожен філамент матиме пластик.
          </p>
          <p className="text-muted-foreground">
            Спершу додайте пластик у налаштуваннях цін, якщо потрібного ще немає, — після цього файл
            доведеться завантажити знову, бо розпочатий імпорт не зберігається.{' '}
            <Link to="/settings" className="underline">
              Налаштування цін
            </Link>
          </p>
        </div>
      )}
      {conflicts.length > 0 && !asking && (
        <p role="status" className="text-sm">
          Різні філаменти ведуть до одного пластику — оберіть інший пластик або підтвердьте
          сумування.{' '}
          <button type="button" className="underline" onClick={() => setDismissed(new Set())}>
            Сумувати…
          </button>
        </p>
      )}
      <MergeConfirmDialog
        group={asking}
        plasticName={asking ? (names.get(asking.plasticId) ?? '') : ''}
        onMerge={(group) => onChange(confirmMerge(state, group))}
        onChooseOther={() => asking && setDismissed(new Set([...dismissed, mergeKey(asking)]))}
      />
    </section>
  )
}
