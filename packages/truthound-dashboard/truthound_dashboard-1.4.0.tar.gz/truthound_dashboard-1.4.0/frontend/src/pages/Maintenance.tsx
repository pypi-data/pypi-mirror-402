/**
 * Maintenance Page
 *
 * Provides UI for configuring retention policies and database maintenance.
 */

import { useIntlayer } from '@/providers'
import { MaintenanceSettings } from '@/components/maintenance'

export default function Maintenance() {
  const content = useIntlayer('maintenance')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{content.title}</h1>
        <p className="text-muted-foreground mt-2">{content.subtitle}</p>
      </div>

      <MaintenanceSettings />
    </div>
  )
}
