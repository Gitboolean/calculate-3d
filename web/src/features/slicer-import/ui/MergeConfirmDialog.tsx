import type { Schemas } from '@/shared/api'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui'

import type { MergeGroup } from '../model/compose'
import { formatMg } from '../model/grams'

/** AC-10: never sum different filaments silently — ask whether they are one plastic. */
export function MergeConfirmDialog({
  group,
  plasticName,
  onMerge,
  onChooseOther,
}: {
  group: MergeGroup | null
  plasticName: string
  onMerge: (group: MergeGroup) => void
  onChooseOther: () => void
}) {
  return (
    <AlertDialog open={group !== null} onOpenChange={(open) => !open && onChooseOther()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Це справді той самий пластик?</AlertDialogTitle>
          <AlertDialogDescription>
            Різні філаменти слайсера ведуть до пластику «{plasticName}». Сумувати їхню витрату в
            один рядок чи обрати інший пластик для одного з них?
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ul className="space-y-1 text-sm">
          {group?.filaments.map((f: Schemas['SlicerFilament']) => (
            <li key={`${f.filament_name}${f.filament_color}`}>
              {f.filament_name} · {f.filament_color} · {formatMg(f.usage_mg)}
            </li>
          ))}
        </ul>
        <AlertDialogFooter>
          <AlertDialogCancel>Обрати інший пластик</AlertDialogCancel>
          <AlertDialogAction onClick={() => group && onMerge(group)}>Сумувати</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
