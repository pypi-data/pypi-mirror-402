/**
 * MSW Handlers - centralized exports
 */

import { healthHandlers } from './health'
import { sourcesHandlers } from './sources'
import { validationsHandlers } from './validations'
import { schemasHandlers } from './schemas'
import { profileHandlers } from './profile'
import { historyHandlers } from './history'
import { driftHandlers } from './drift'
import { schedulesHandlers } from './schedules'
import { notificationsHandlers } from './notifications'
import { scanHandlers } from './scan'
import { maskHandlers } from './mask'
import { glossaryHandlers } from './glossary'
import { catalogHandlers } from './catalog'
import { collaborationHandlers } from './collaboration'
import { rulesHandlers } from './rules'
import { validatorsHandlers } from './validators'
import { reportHandlers } from './reports'
import { maintenanceHandlers } from './maintenance'
import { schemaEvolutionHandlers } from './schema-evolution'
import { ruleSuggestionsHandlers } from './rule-suggestions'
import { versioningHandlers } from './versioning'
import { notificationsAdvancedHandlers } from './notifications-advanced'
import { lineageHandlers } from './lineage'
import { anomalyHandlers } from './anomaly'
import { modelMonitoringHandlers } from './model-monitoring'
import { alertsHandlers } from './alerts'
import { crossAlertsHandlers } from './cross-alerts'
import { triggersHandlers } from './triggers'
import { pluginHandlers } from './plugins'
import { reportHistoryHandlers } from './report-history'

export const handlers = [
  ...healthHandlers,
  ...sourcesHandlers,
  ...validationsHandlers,
  ...schemasHandlers,
  ...profileHandlers,
  ...historyHandlers,
  ...driftHandlers,
  ...schedulesHandlers,
  ...notificationsHandlers,
  ...scanHandlers,
  ...maskHandlers,
  ...glossaryHandlers,
  ...catalogHandlers,
  ...collaborationHandlers,
  ...rulesHandlers,
  ...validatorsHandlers,
  ...reportHandlers,
  ...maintenanceHandlers,
  ...schemaEvolutionHandlers,
  ...ruleSuggestionsHandlers,
  ...versioningHandlers,
  ...notificationsAdvancedHandlers,
  ...lineageHandlers,
  ...anomalyHandlers,
  ...modelMonitoringHandlers,
  ...alertsHandlers,
  ...crossAlertsHandlers,
  ...triggersHandlers,
  ...pluginHandlers,
  ...reportHistoryHandlers,
]
