import { useState, type FormEvent } from 'react'

import { useUpdateItem, type ItemDetail } from '@/entities/item'
import type { Plastic } from '@/entities/plastic'
import { useQuote } from '@/entities/quote'
import { parseQuoteForm, QuoteError, QuoteForm, quoteFormFrom } from '@/features/quote-form'
import { saveError, validateItemName } from '@/features/save-item'
import { Button, FormField } from '@/shared/ui'
import { CostBreakdown } from '@/widgets/cost-breakdown'

type ItemEditorProps = { item: ItemDetail; plastics: Plastic[]; onDone: () => void }

/** Name + the same quote form as /calculate, with a live donation (AC-14b, AC-14c). */
export function ItemEditor({ item, plastics, onDone }: ItemEditorProps) {
  const [name, setName] = useState(item.name)
  const [value, setValue] = useState(() => quoteFormFrom(item))
  const [showAllErrors, setShowAllErrors] = useState(false)
  const [errors, setErrors] = useState<{ name?: string; form?: string }>({})
  const update = useUpdateItem()
  const { input, errors: formErrors } = parseQuoteForm(value)
  const { quote, error, isCalculating } = useQuote(input)

  function submit(event: FormEvent) {
    event.preventDefault()
    const nameError = validateItemName(name)
    if (nameError || !input) {
      // Nothing is sent: the item keeps its saved parameters (AC-14c).
      setShowAllErrors(true)
      setErrors({ name: nameError })
      return
    }
    setErrors({})
    update.mutate(
      { id: item.id, body: { name: name.trim(), ...input } },
      { onSuccess: onDone, onError: (error) => setErrors(saveError(error)) },
    )
  }

  return (
    <form aria-label="Змінити виріб" onSubmit={submit} noValidate className="space-y-6">
      <div className="max-w-md">
        <FormField
          label="Назва виробу"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />
      </div>
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <QuoteForm
          value={value}
          onChange={setValue}
          plastics={plastics}
          errors={formErrors}
          showAllErrors={showAllErrors}
        />
        {error ? (
          <QuoteError error={error} />
        ) : (
          <CostBreakdown quote={quote} isCalculating={isCalculating} />
        )}
      </div>
      {errors.form && <p className="text-destructive text-sm">{errors.form}</p>}
      <div className="flex gap-2">
        <Button type="submit" disabled={update.isPending || !!error || (input !== null && !quote)}>
          Зберегти зміни
        </Button>
        <Button type="button" variant="outline" onClick={onDone}>
          Скасувати
        </Button>
      </div>
    </form>
  )
}
