/**
 * Chart showing anomaly score distribution.
 */

import { useIntlayer } from 'react-intlayer'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { AnomalyRecord } from '@/api/client'

interface AnomalyScoreChartProps {
  anomalies: AnomalyRecord[]
}

export function AnomalyScoreChart({ anomalies }: AnomalyScoreChartProps) {
  const t = useIntlayer('anomaly')

  // Bucket scores into ranges
  const buckets = [
    { range: '0.0-0.2', min: 0, max: 0.2, count: 0, color: '#22c55e' },
    { range: '0.2-0.4', min: 0.2, max: 0.4, count: 0, color: '#84cc16' },
    { range: '0.4-0.6', min: 0.4, max: 0.6, count: 0, color: '#eab308' },
    { range: '0.6-0.8', min: 0.6, max: 0.8, count: 0, color: '#f97316' },
    { range: '0.8-1.0', min: 0.8, max: 1.0, count: 0, color: '#ef4444' },
  ]

  for (const anomaly of anomalies) {
    for (const bucket of buckets) {
      if (anomaly.anomaly_score >= bucket.min && anomaly.anomaly_score < bucket.max) {
        bucket.count++
        break
      }
    }
    // Handle score === 1.0
    if (anomaly.anomaly_score >= 1.0) {
      buckets[buckets.length - 1].count++
    }
  }

  if (anomalies.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{t.scoreDistribution}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={buckets}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="range"
              tick={{ fontSize: 12 }}
              className="fill-muted-foreground"
            />
            <YAxis tick={{ fontSize: 12 }} className="fill-muted-foreground" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                borderColor: 'hsl(var(--border))',
                borderRadius: '0.5rem',
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {buckets.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
