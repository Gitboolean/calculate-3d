import { useId, type ComponentProps } from 'react'

import { Input } from './input'
import { Label } from './label'

type FormFieldProps = Omit<ComponentProps<typeof Input>, 'id'> & {
  label: string
  error?: string
}

/** Label + input + the error explained right next to it (PRD: «пояснює біля поля»). */
export function FormField({ label, error, ...props }: FormFieldProps) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error && (
        <p id={errorId} className="text-destructive text-sm">
          {error}
        </p>
      )}
    </div>
  )
}
