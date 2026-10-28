import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

import { useCreateItem } from '@/entities/item'
import type { QuoteInput } from '@/entities/quote'
import { Button, FormField } from '@/shared/ui'

import { saveError, validateItemName } from '../model/name'

/**
 * Saves the shown calculation as a catalog item — its parameters only, never a price (AC-10).
 * `input` is null until the donation for the current values is on screen.
 */
export function SaveItemForm({ input }: { input: QuoteInput | null }) {
  const [name, setName] = useState('')
  const [errors, setErrors] = useState<{ name?: string; form?: string }>({})
  const create = useCreateItem()
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!input) return
    const nameError = validateItemName(name)
    if (nameError) {
      setErrors({ name: nameError })
      return
    }
    setErrors({})
    create.mutate(
      { name: name.trim(), ...input },
      {
        onSuccess: (item) => navigate(`/catalog/${item.id}`),
        onError: (error) => setErrors(saveError(error)),
      },
    )
  }

  return (
    <form aria-label="Зберегти в каталог" onSubmit={submit} noValidate className="space-y-3">
      <FormField
        label="Назва виробу"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={errors.name}
      />
      {!input && (
        <p className="text-muted-foreground text-sm">
          Зберегти можна, коли розрахунок показує мінімальний донат.
        </p>
      )}
      {errors.form && <p className="text-destructive text-sm">{errors.form}</p>}
      <Button type="submit" disabled={!input || create.isPending}>
        Зберегти в каталог
      </Button>
    </form>
  )
}
