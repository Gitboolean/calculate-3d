import { useState, type FormEvent } from 'react'

import { useCreatePlastic, useUpdatePlastic, type Plastic } from '@/entities/plastic'
import { formatDecimal } from '@/shared/lib'
import { Button, FormField } from '@/shared/ui'

import { serverErrors, validatePlastic, type PlasticErrors } from '../model/validate'

type PlasticFormProps = {
  /** Edit this plastic; without it the form adds a new one. */
  plastic?: Plastic
  onDone?: () => void
}

export function PlasticForm({ plastic, onDone }: PlasticFormProps) {
  const [name, setName] = useState(plastic?.name ?? '')
  const [price, setPrice] = useState(plastic ? formatDecimal(plastic.price_per_kg_kop, 2) : '')
  const [errors, setErrors] = useState<PlasticErrors>({})
  const create = useCreatePlastic()
  const update = useUpdatePlastic()
  const saving = create.isPending || update.isPending

  function submit(event: FormEvent) {
    event.preventDefault()
    const result = validatePlastic(name, price)
    if (!result.ok) {
      setErrors(result.errors)
      return
    }
    setErrors({})
    const options = {
      onError: (error: unknown) => setErrors(serverErrors(error)),
      onSuccess: () => {
        if (!plastic) {
          setName('')
          setPrice('')
        }
        onDone?.()
      },
    }
    if (plastic) update.mutate({ id: plastic.id, body: result.input }, options)
    else create.mutate(result.input, options)
  }

  return (
    <form
      aria-label={plastic ? `Змінити пластик «${plastic.name}»` : 'Додати пластик'}
      onSubmit={submit}
      noValidate
      className="grid gap-3 sm:grid-cols-[1fr_12rem_auto] sm:items-start"
    >
      <FormField
        label="Назва"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={errors.name}
      />
      <FormField
        label="Ціна за кг, ₴"
        inputMode="decimal"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        error={errors.price}
      />
      <div className="flex gap-2 sm:mt-6">
        <Button type="submit" disabled={saving}>
          {plastic ? 'Зберегти' : 'Додати'}
        </Button>
        {plastic && (
          <Button type="button" variant="outline" onClick={onDone}>
            Скасувати
          </Button>
        )}
      </div>
      {errors.form && <p className="text-destructive text-sm sm:col-span-3">{errors.form}</p>}
    </form>
  )
}
