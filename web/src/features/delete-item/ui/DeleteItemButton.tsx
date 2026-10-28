import { useState } from 'react'
import { useNavigate } from 'react-router'

import { useDeleteItem } from '@/entities/item'
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

/** Deletes for good after a confirmation, then returns to the catalog (AC-15). */
export function DeleteItemButton({ item }: { item: { id: string; name: string } }) {
  const remove = useDeleteItem()
  const navigate = useNavigate()
  const [failed, setFailed] = useState(false)

  return (
    <>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="outline" disabled={remove.isPending}>
            Видалити
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Видалити виріб «{item.name}»?</AlertDialogTitle>
            <AlertDialogDescription>
              Виріб назавжди зникне з каталогу. Цю дію не можна скасувати.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Скасувати</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                setFailed(false)
                remove.mutate(item.id, {
                  onSuccess: () => navigate('/catalog'),
                  onError: () => setFailed(true),
                })
              }}
            >
              Видалити
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      {failed && (
        <p role="alert" className="text-destructive text-sm">
          Не вдалося видалити виріб. Спробуйте ще раз.
        </p>
      )}
    </>
  )
}
