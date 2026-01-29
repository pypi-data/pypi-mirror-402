/**
 * PII findings table component.
 *
 * Displays detected PII with confidence scores and actions.
 */

import { useIntlayer } from 'react-intlayer'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, Shield, EyeOff, Check } from 'lucide-react'
import type { PIIFinding } from '@/api/client'

interface PIIFindingsTableProps {
  findings: PIIFinding[]
  onMaskColumn?: (column: string) => void
  onIgnoreColumn?: (column: string) => void
  onMarkSafe?: (column: string) => void
}

const getPIITypeColor = (piiType: string) => {
  const colors: Record<string, string> = {
    email: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    phone: 'bg-green-500/10 text-green-500 border-green-500/20',
    ssn: 'bg-red-500/10 text-red-500 border-red-500/20',
    credit_card: 'bg-red-500/10 text-red-500 border-red-500/20',
    ip_address: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
    date_of_birth: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    address: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    name: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    passport: 'bg-red-500/10 text-red-500 border-red-500/20',
    driver_license: 'bg-red-500/10 text-red-500 border-red-500/20',
  }
  return colors[piiType.toLowerCase()] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'
}

const getRiskLevel = (confidence: number) => {
  if (confidence >= 0.9) return { level: 'critical', color: 'text-red-500' }
  if (confidence >= 0.7) return { level: 'high', color: 'text-orange-500' }
  if (confidence >= 0.5) return { level: 'medium', color: 'text-yellow-500' }
  return { level: 'low', color: 'text-green-500' }
}

export function PIIFindingsTable({
  findings,
  onMaskColumn,
  onIgnoreColumn,
  onMarkSafe,
}: PIIFindingsTableProps) {
  const t = useIntlayer('privacy')

  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
        <Shield className="h-8 w-8 text-green-500" />
        <p className="font-medium text-green-500">{t.empty.noPIIFound}</p>
        <p className="text-sm text-muted-foreground">{t.empty.noPIIFoundDesc}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t.table.column}</TableHead>
            <TableHead>{t.table.piiType}</TableHead>
            <TableHead>{t.table.confidence}</TableHead>
            <TableHead>{t.table.sampleCount}</TableHead>
            <TableHead className="text-right">{t.table.actions}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {findings.map((finding, index) => {
            const risk = getRiskLevel(finding.confidence)

            return (
              <TableRow key={`${finding.column}-${finding.pii_type}-${index}`}>
                <TableCell className="font-mono text-sm">{finding.column}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={getPIITypeColor(finding.pii_type)}>
                    {finding.pii_type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress value={finding.confidence * 100} className="h-2 w-20" />
                    <span className={`text-sm font-medium ${risk.color}`}>
                      {(finding.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </TableCell>
                <TableCell>{finding.sample_count?.toLocaleString() ?? '-'}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {onMaskColumn && (
                        <DropdownMenuItem onClick={() => onMaskColumn(finding.column)}>
                          <EyeOff className="mr-2 h-4 w-4" />
                          {t.actions.maskColumn}
                        </DropdownMenuItem>
                      )}
                      {onMarkSafe && (
                        <DropdownMenuItem onClick={() => onMarkSafe(finding.column)}>
                          <Check className="mr-2 h-4 w-4" />
                          {t.actions.markSafe}
                        </DropdownMenuItem>
                      )}
                      {onIgnoreColumn && (
                        <DropdownMenuItem onClick={() => onIgnoreColumn(finding.column)}>
                          {t.actions.ignoreColumn}
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
