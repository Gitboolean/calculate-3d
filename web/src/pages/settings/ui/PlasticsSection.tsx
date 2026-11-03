import { useState } from 'react'

import { usePlastics } from '@/entities/plastic'
import { DeletePlasticButton, PlasticForm } from '@/features/edit-plastic'
import { formatMoney } from '@/shared/lib'
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui'

export function PlasticsSection() {
  const plastics = usePlastics()
  const [editingId, setEditingId] = useState<string>()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Пластики</CardTitle>
        <CardDescription>Поточна ціна кожного пластику за кілограм.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {plastics.isPending && <p className="text-sm">Завантажую пластики…</p>}
        {plastics.isError && (
          <p className="text-destructive text-sm">Не вдалося завантажити пластики.</p>
        )}
        {plastics.data?.length === 0 && (
          <p className="text-muted-foreground text-sm">Пластиків ще немає</p>
        )}
        {!!plastics.data?.length && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Назва</TableHead>
                <TableHead className="text-right">Ціна за кг</TableHead>
                <TableHead className="w-0">
                  <span className="sr-only">Дії</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plastics.data.map((plastic) =>
                plastic.id === editingId ? (
                  <TableRow key={plastic.id}>
                    <TableCell colSpan={3} className="whitespace-normal">
                      <PlasticForm plastic={plastic} onDone={() => setEditingId(undefined)} />
                    </TableCell>
                  </TableRow>
                ) : (
                  <TableRow key={plastic.id}>
                    <TableCell>{plastic.name}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(plastic.price_per_kg_kop)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => setEditingId(plastic.id)}>
                        Змінити
                      </Button>
                      <DeletePlasticButton plastic={plastic} />
                    </TableCell>
                  </TableRow>
                ),
              )}
            </TableBody>
          </Table>
        )}
        <PlasticForm />
      </CardContent>
    </Card>
  )
}
