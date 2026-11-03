import { PlasticsSection } from './PlasticsSection'
import { PriceSettingsSection } from './PriceSettingsSection'

export function SettingsPage() {
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Налаштування цін</h1>
      <PlasticsSection />
      <PriceSettingsSection />
    </section>
  )
}
