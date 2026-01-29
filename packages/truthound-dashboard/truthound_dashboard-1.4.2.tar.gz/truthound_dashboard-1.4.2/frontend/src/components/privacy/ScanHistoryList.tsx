/**
 * Scan history list component.
 *
 * Displays history of PII scans and masking operations.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDistanceToNow } from 'date-fns'
import { Eye, Lock, AlertTriangle, Shield, ChevronRight, Loader2 } from 'lucide-react'
import type { PIIScan, DataMaskListItem } from '@/api/client'

interface ScanHistoryListProps {
  scans: PIIScan[]
  masks: DataMaskListItem[]
  isLoading?: boolean
  onViewScan?: (scan: PIIScan) => void
  onViewMask?: (mask: DataMaskListItem) => void
}

export function ScanHistoryList({
  scans,
  masks,
  isLoading = false,
  onViewScan,
  onViewMask,
}: ScanHistoryListProps) {
  const t = useIntlayer('privacy')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Combine and sort by date
  const items = [
    ...scans.map((s) => ({ type: 'scan' as const, data: s, date: s.created_at })),
    ...masks.map((m) => ({ type: 'mask' as const, data: m, date: m.created_at })),
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
        <Eye className="h-8 w-8 text-muted-foreground" />
        <p className="text-muted-foreground">{t.empty.noScans}</p>
        <p className="text-sm text-muted-foreground">{t.empty.noScansDesc}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        if (item.type === 'scan') {
          const scan = item.data as PIIScan
          const hasPII = scan.columns_with_pii > 0

          return (
            <Card
              key={`scan-${scan.id}`}
              className="cursor-pointer transition-colors hover:bg-muted/50"
              onClick={() => onViewScan?.(scan)}
            >
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-4">
                  <div className={`rounded-lg p-2 ${hasPII ? 'bg-orange-500/10' : 'bg-green-500/10'}`}>
                    {hasPII ? (
                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                    ) : (
                      <Shield className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">PII Scan</span>
                      <Badge variant="outline">
                        {scan.total_columns_scanned} columns
                      </Badge>
                      {hasPII && (
                        <Badge variant="outline" className="text-orange-500 border-orange-500/20">
                          {scan.columns_with_pii} with PII
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon">
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )
        } else {
          const mask = item.data as DataMaskListItem

          return (
            <Card
              key={`mask-${mask.id}`}
              className="cursor-pointer transition-colors hover:bg-muted/50"
              onClick={() => onViewMask?.(mask)}
            >
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-blue-500/10 p-2">
                    <Lock className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Data Masking</span>
                      <Badge variant="outline">
                        {mask.columns_masked} columns
                      </Badge>
                      <Badge variant="secondary">{mask.strategy}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(mask.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon">
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )
        }
      })}
    </div>
  )
}
