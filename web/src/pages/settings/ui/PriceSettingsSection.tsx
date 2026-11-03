import { usePriceSettings } from '@/entities/price-settings'
import { PriceSettingsForm } from '@/features/edit-price-settings'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui'

export function PriceSettingsSection() {
  const settings = usePriceSettings()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Тариф, знос і брак</CardTitle>
        <CardDescription>Усі шість значень зберігаються разом, однією дією.</CardDescription>
      </CardHeader>
      <CardContent>
        {settings.isPending && <p className="text-sm">Завантажую налаштування…</p>}
        {settings.isError && (
          <p className="text-destructive text-sm">Не вдалося завантажити налаштування.</p>
        )}
        {settings.isSuccess && <PriceSettingsForm saved={settings.data} />}
      </CardContent>
    </Card>
  )
}
