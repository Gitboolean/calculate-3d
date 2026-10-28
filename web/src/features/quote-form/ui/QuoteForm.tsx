import { useId, useState } from 'react'

import type { Plastic } from '@/entities/plastic'
import { Button, Input, Label, NativeSelect } from '@/shared/ui'

import {
  newRow,
  type QuoteFormErrors,
  type QuoteFormRow,
  type QuoteFormValue,
} from '../model/parse'

type QuoteFormProps = {
  value: QuoteFormValue
  onChange: (value: QuoteFormValue) => void
  plastics: Plastic[]
  errors: QuoteFormErrors
  /** Explain every invalid field, not only the ones the author has touched (e.g. on save). */
  showAllErrors?: boolean
}

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? (
    <p id={id} className="text-destructive text-sm">
      {message}
    </p>
  ) : null
}

/** Plastic usage rows + print time. Controlled; the page turns the value into a quote. */
export function QuoteForm({ value, onChange, plastics, errors, showAllErrors }: QuoteFormProps) {
  const id = useId()
  const [touched, setTouched] = useState<ReadonlySet<string>>(new Set())
  const shown = (field: string, ...touchKeys: string[]) =>
    showAllErrors || [field, ...touchKeys].some((k) => touched.has(k)) ? errors[field] : undefined
  const touch = (...fields: string[]) => setTouched((t) => new Set([...t, ...fields]))

  function setRow(index: number, patch: Partial<QuoteFormRow>, field: string) {
    touch(`rows.${index}.${field}`)
    onChange({ ...value, rows: value.rows.map((r, i) => (i === index ? { ...r, ...patch } : r)) })
  }

  const timeError = shown('time', 'hours', 'minutes')
  return (
    <div className="space-y-4">
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Витрата пластику</legend>
        {value.rows.map((row, i) => {
          const plasticError = shown(`rows.${i}.plastic`)
          const gramsError = shown(`rows.${i}.grams`)
          return (
            <div key={row.key} className="grid gap-2 sm:grid-cols-[1fr_10rem_auto] sm:items-start">
              <div className="grid gap-1.5">
                <Label htmlFor={`${id}-${row.key}-plastic`}>Пластик</Label>
                <NativeSelect
                  id={`${id}-${row.key}-plastic`}
                  value={row.plasticId}
                  aria-invalid={plasticError ? true : undefined}
                  aria-describedby={plasticError ? `${id}-${row.key}-plastic-error` : undefined}
                  onChange={(e) => setRow(i, { plasticId: e.target.value }, 'plastic')}
                >
                  <option value="">Оберіть пластик…</option>
                  {plastics.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </NativeSelect>
                <FieldError id={`${id}-${row.key}-plastic-error`} message={plasticError} />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor={`${id}-${row.key}-grams`}>Витрата, г</Label>
                <Input
                  id={`${id}-${row.key}-grams`}
                  inputMode="decimal"
                  value={row.grams}
                  aria-invalid={gramsError ? true : undefined}
                  aria-describedby={gramsError ? `${id}-${row.key}-grams-error` : undefined}
                  onChange={(e) => setRow(i, { grams: e.target.value }, 'grams')}
                />
                <FieldError id={`${id}-${row.key}-grams-error`} message={gramsError} />
              </div>
              <Button
                type="button"
                variant="ghost"
                className="sm:mt-6"
                aria-label={`Прибрати рядок ${i + 1}`}
                onClick={() => {
                  touch('plastics')
                  onChange({ ...value, rows: value.rows.filter((_, j) => j !== i) })
                }}
              >
                Прибрати
              </Button>
            </div>
          )
        })}
        <FieldError id={`${id}-plastics-error`} message={errors.plastics} />
        <Button
          type="button"
          variant="outline"
          onClick={() => onChange({ ...value, rows: [...value.rows, newRow()] })}
        >
          Додати пластик
        </Button>
      </fieldset>
      <fieldset className="space-y-1.5">
        <legend className="text-sm font-medium">Час друку</legend>
        <div className="grid grid-cols-2 gap-2 sm:max-w-xs">
          {(['hours', 'minutes'] as const).map((field) => (
            <div key={field} className="grid gap-1.5">
              <Label htmlFor={`${id}-${field}`}>{field === 'hours' ? 'Години' : 'Хвилини'}</Label>
              <Input
                id={`${id}-${field}`}
                inputMode="numeric"
                value={value[field]}
                aria-invalid={shown(field) || timeError ? true : undefined}
                onChange={(e) => {
                  touch(field)
                  onChange({ ...value, [field]: e.target.value })
                }}
              />
            </div>
          ))}
        </div>
        <FieldError id={`${id}-hours-error`} message={shown('hours')} />
        <FieldError id={`${id}-minutes-error`} message={shown('minutes')} />
        <FieldError id={`${id}-time-error`} message={timeError} />
      </fieldset>
    </div>
  )
}
