import { Link } from 'react-router'

import { Button } from '@/shared/ui'

const MISSING_TEXT: Record<string, string> = {
  plastics: 'жодного пластику ще не додано',
  price_settings: 'тариф, потужність, знос і брак ще не збережено',
}

/** AC-09: names what is missing and leads to the settings instead of showing a donation. */
export function MissingSettings({ missing }: { missing: readonly string[] }) {
  const parts = missing.map((m) => MISSING_TEXT[m] ?? m)
  return (
    <div role="alert" className="space-y-3">
      <p className="text-sm">Бракує налаштувань цін: {parts.join('; ')}.</p>
      <Button asChild variant="outline">
        <Link to="/settings">Перейти до налаштувань цін</Link>
      </Button>
    </div>
  )
}
