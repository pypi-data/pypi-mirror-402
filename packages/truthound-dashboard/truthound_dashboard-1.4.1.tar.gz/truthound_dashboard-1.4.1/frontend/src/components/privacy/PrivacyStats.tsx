/**
 * Privacy statistics cards.
 *
 * Displays overview statistics for PII scans and masking operations.
 */

import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Shield, AlertTriangle, Eye, Lock } from 'lucide-react'

interface PrivacyStatsProps {
  totalScans: number
  totalFindings: number
  columnsProtected: number
  complianceScore: number
}

export function PrivacyStats({
  totalScans,
  totalFindings,
  columnsProtected,
  complianceScore,
}: PrivacyStatsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Total Scans</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-blue-500" />
            <span className="text-2xl font-bold">{totalScans}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>PII Findings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            <span className="text-2xl font-bold text-orange-500">{totalFindings}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Columns Protected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-green-500" />
            <span className="text-2xl font-bold text-green-500">{columnsProtected}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Compliance Score</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Shield
              className={`h-5 w-5 ${
                complianceScore >= 80
                  ? 'text-green-500'
                  : complianceScore >= 50
                    ? 'text-orange-500'
                    : 'text-red-500'
              }`}
            />
            <span className="text-2xl font-bold">{complianceScore}%</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
