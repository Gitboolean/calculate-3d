import { useState, type FormEvent } from 'react'

import { useReplacePriceSettings, type PriceSettings } from '@/entities/price-settings'
import { isProblem, issueField } from '@/shared/api'
import { formatMoney } from '@/shared/lib'
import { Button, FormField } from '@/shared/ui'

import {
  FIELDS,
  initialValues,
  validate,
  type FieldErrors,
  type FieldName,
  type FieldValues,
} from '../model/fields'

export function PriceSettingsForm({ saved }: { saved: PriceSettings | null }) {
  const [values, setValues] = useState<FieldValues>(() => initialValues(saved))
  const [errors, setErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string>()
  const replace = useReplacePriceSettings()
  const current = replace.data ?? saved

  function submit(event: FormEvent) {
    event.preventDefault()
    const result = validate(values)
    setFormError(undefined)
    if (!result.ok) {
      setErrors(result.errors)
      return
    }
    setErrors({})
    replace.mutate(result.input, {
      onError: (error) => {
        if (!isProblem(error, 'validation_error')) {
          setFormError('Не вдалося зберегти налаштування. Спробуйте ще раз.')
          return
        }
        const invalid = new Set((error.problem.errors ?? []).map(issueField))
        setErrors(
          Object.fromEntries(
            FIELDS.filter((f) => invalid.has(f.name)).map((f) => [f.name, f.rule]),
          ),
        )
      },
    })
  }

  const set = (name: FieldName) => (value: string) => setValues((v) => ({ ...v, [name]: value }))

  return (
    <form aria-label="Налаштування цін" onSubmit={submit} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {FIELDS.map((field) => (
          <FormField
            key={field.name}
            label={field.label}
            inputMode={field.scale > 0 ? 'decimal' : 'numeric'}
            value={values[field.name]}
            onChange={(e) => set(field.name)(e.target.value)}
            error={errors[field.name]}
          />
        ))}
      </div>
      <p className="text-sm">
        {current
          ? `Знос за годину друку: ${formatMoney(current.wear_per_hour_kop)}`
          : 'Налаштування ще не збережено.'}
      </p>
      {formError && <p className="text-destructive text-sm">{formError}</p>}
      <Button type="submit" disabled={replace.isPending}>
        Зберегти налаштування
      </Button>
    </form>
  )
}
