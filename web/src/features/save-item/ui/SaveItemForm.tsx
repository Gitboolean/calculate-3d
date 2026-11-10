import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

import { useCreateItem } from '@/entities/item'
import type { QuoteInput } from '@/entities/quote'
import type { Schemas } from '@/shared/api'
import { normalizeName } from '@/shared/lib'
import { Button, FormField } from '@/shared/ui'

import { saveError, validateItemName } from '../model/name'

/**
 * Saves the shown calculation as a catalog item — its parameters only, never a price (AC-10).
 * `input` is null until the donation for the current values is on screen. `filamentMappings`
 * from a slicer import are remembered together with the item, never on their own (ADR 0003).
 */
export function SaveItemForm({
  input,
  filamentMappings = [],
  onSaveError,
}: {
  input: QuoteInput | null
  filamentMappings?: Schemas['FilamentMappingInput'][]
  /** Lets the screen react to a rejected save, e.g. ask for a deleted plastic again. */
  onSaveError?: (error: unknown) => void
}) {
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
      {
        name: normalizeName(name),
        ...input,
        ...(filamentMappings.length > 0 ? { filament_mappings: filamentMappings } : {}),
      },
      {
        onSuccess: (item) => navigate(`/catalog/${item.id}`),
        onError: (error) => {
          setErrors(saveError(error))
          onSaveError?.(error)
        },
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
