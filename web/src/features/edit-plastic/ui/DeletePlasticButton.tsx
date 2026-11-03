import { useState } from 'react'

import { useDeletePlastic, type Plastic } from '@/entities/plastic'
import { isProblem } from '@/shared/api'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  Button,
} from '@/shared/ui'

export function DeletePlasticButton({ plastic }: { plastic: Plastic }) {
  const remove = useDeletePlastic()
  const [message, setMessage] = useState<string>()

  function confirm() {
    setMessage(undefined)
    remove.mutate(plastic.id, {
      onError: (error) =>
        setMessage(
          isProblem(error, 'pricing.plastic_in_use')
            ? `Пластик «${plastic.name}» не можна видалити: його використовують вироби ${(error.problem.items ?? []).join(', ')}.`
            : 'Не вдалося видалити пластик. Спробуйте ще раз.',
        ),
    })
  }

  return (
    <>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="ghost" size="sm" disabled={remove.isPending}>
            Видалити
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Видалити пластик «{plastic.name}»?</AlertDialogTitle>
            <AlertDialogDescription>
              Пластик зникне з налаштувань цін. Пластик, який використовують вироби, видалити не
              можна.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Скасувати</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirm}>
              Видалити
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      {message && (
        <p role="alert" className="text-destructive mt-1 text-sm whitespace-normal">
          {message}
        </p>
      )}
    </>
  )
}
