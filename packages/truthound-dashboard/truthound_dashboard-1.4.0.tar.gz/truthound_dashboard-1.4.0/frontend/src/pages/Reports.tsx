/**
 * Reports page component.
 *
 * Displays report history with statistics, filtering, and management actions.
 */
import { useEffect, useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { useNavigate, Link } from 'react-router-dom'
import {
  FileText,
  Download,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  HardDrive,
  BarChart3,
  Settings,
  ExternalLink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  listReportHistory,
  getReportStatistics,
  downloadSavedReport,
  deleteReportRecord,
  cleanupExpiredReports,
  type GeneratedReport,
  type ReportStatistics,
  type ReportStatus,
} from '@/api/client'

// Format file size for display
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Format generation time
function formatDuration(ms: number | undefined): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// Format date
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

// Status badge component
function StatusBadge({ status, t }: { status: ReportStatus; t: ReturnType<typeof useIntlayer<'reports'>> }) {
  const statusConfig: Record<ReportStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    pending: {
      variant: 'outline',
      icon: <Clock className="h-3 w-3" />,
      label: str(t.statusPending),
    },
    generating: {
      variant: 'secondary',
      icon: <RefreshCw className="h-3 w-3 animate-spin" />,
      label: str(t.statusGenerating),
    },
    completed: {
      variant: 'default',
      icon: <CheckCircle className="h-3 w-3" />,
      label: str(t.statusCompleted),
    },
    failed: {
      variant: 'destructive',
      icon: <XCircle className="h-3 w-3" />,
      label: str(t.statusFailed),
    },
    expired: {
      variant: 'outline',
      icon: <AlertCircle className="h-3 w-3" />,
      label: str(t.statusExpired),
    },
  }

  const config = statusConfig[status]
  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      {config.icon}
      {config.label}
    </Badge>
  )
}

// Statistics cards component
function StatisticsCards({ stats, t }: { stats: ReportStatistics | null; t: ReturnType<typeof useIntlayer<'reports'>> }) {
  if (!stats) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalReports)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.total_reports}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalSize)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{formatFileSize(stats.total_size_bytes)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalDownloads)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.total_downloads}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.avgGenerationTime)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{formatDuration(stats.avg_generation_time_ms ?? undefined)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.expiredReports)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.expired_count}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.reportersUsed)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.reporters_used}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Reports() {
  const t = useIntlayer('reports')
  const common = useIntlayer('common')
  const { toast } = useToast()
  const navigate = useNavigate()

  // State
  const [reports, setReports] = useState<GeneratedReport[]>([])
  const [statistics, setStatistics] = useState<ReportStatistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Filters
  const [search, setSearch] = useState('')
  const [formatFilter, setFormatFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [includeExpired, setIncludeExpired] = useState(false)

  // Dialogs
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; report: GeneratedReport | null }>({
    open: false,
    report: null,
  })
  const [cleanupDialog, setCleanupDialog] = useState(false)

  // Fetch reports
  const fetchReports = useCallback(async () => {
    try {
      setLoading(true)
      const response = await listReportHistory({
        search: search || undefined,
        format: formatFilter !== 'all' ? formatFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        include_expired: includeExpired,
        page,
        page_size: pageSize,
      })
      setReports(response.items)
      setTotal(response.total)
    } catch (error) {
      toast({
        title: str(common.error),
        description: error instanceof Error ? error.message : str(common.unknownError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [search, formatFilter, statusFilter, includeExpired, page, toast, common])

  // Fetch statistics
  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await getReportStatistics()
      setStatistics(stats)
    } catch (error) {
      // Silent fail for stats
      console.error('Failed to fetch statistics:', error)
    }
  }, [])

  useEffect(() => {
    fetchReports()
    fetchStatistics()
  }, [fetchReports, fetchStatistics])

  // Handle download
  const handleDownload = async (report: GeneratedReport) => {
    if (report.status !== 'completed') {
      toast({
        title: str(common.error),
        description: 'Report is not ready for download',
        variant: 'destructive',
      })
      return
    }

    try {
      const blob = await downloadSavedReport(report.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.name}.${report.format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: str(t.downloadSuccess),
        description: str(t.reportDownloaded),
      })

      // Refresh to update download count
      fetchReports()
    } catch (error) {
      toast({
        title: str(t.downloadFailed),
        description: error instanceof Error ? error.message : str(common.unknownError),
        variant: 'destructive',
      })
    }
  }

  // Handle delete
  const handleDelete = async () => {
    if (!deleteDialog.report) return

    try {
      await deleteReportRecord(deleteDialog.report.id)
      toast({
        title: str(common.success),
        description: str(t.deleteSuccess),
      })
      setDeleteDialog({ open: false, report: null })
      fetchReports()
      fetchStatistics()
    } catch (error) {
      toast({
        title: str(common.error),
        description: error instanceof Error ? error.message : str(common.unknownError),
        variant: 'destructive',
      })
    }
  }

  // Handle cleanup
  const handleCleanup = async () => {
    try {
      const result = await cleanupExpiredReports()
      toast({
        title: str(common.success),
        description: `${result.deleted} ${str(t.cleanupSuccess)}`,
      })
      setCleanupDialog(false)
      fetchReports()
      fetchStatistics()
    } catch (error) {
      toast({
        title: str(common.error),
        description: error instanceof Error ? error.message : str(common.unknownError),
        variant: 'destructive',
      })
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{str(t.pageTitle)}</h1>
          <p className="text-muted-foreground">{str(t.pageDescription)}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/plugins">
              <Settings className="h-4 w-4 mr-2" />
              {str(t.manageReporters)}
            </Link>
          </Button>
          {statistics && statistics.expired_count > 0 && (
            <Button variant="outline" onClick={() => setCleanupDialog(true)}>
              <Trash2 className="h-4 w-4 mr-2" />
              {str(t.cleanupExpired)}
            </Button>
          )}
        </div>
      </div>

      {/* Statistics */}
      <StatisticsCards stats={statistics} t={t} />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            {str(t.reportHistory)}
          </CardTitle>
          <CardDescription>{str(t.historyDescription)}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={str(t.searchPlaceholder)}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <Select value={formatFilter} onValueChange={setFormatFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder={str(t.filterByFormat)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.allFormats)}</SelectItem>
                <SelectItem value="html">{str(t.formatHtml)}</SelectItem>
                <SelectItem value="pdf">{str(t.formatPdf)}</SelectItem>
                <SelectItem value="csv">{str(t.formatCsv)}</SelectItem>
                <SelectItem value="json">{str(t.formatJson)}</SelectItem>
                <SelectItem value="markdown">{str(t.formatMarkdown)}</SelectItem>
                <SelectItem value="excel">{str(t.formatExcel)}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder={str(t.filterByStatus)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.allStatuses)}</SelectItem>
                <SelectItem value="pending">{str(t.statusPending)}</SelectItem>
                <SelectItem value="generating">{str(t.statusGenerating)}</SelectItem>
                <SelectItem value="completed">{str(t.statusCompleted)}</SelectItem>
                <SelectItem value="failed">{str(t.statusFailed)}</SelectItem>
                <SelectItem value="expired">{str(t.statusExpired)}</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              <Checkbox
                id="includeExpired"
                checked={includeExpired}
                onCheckedChange={(checked) => setIncludeExpired(checked === true)}
              />
              <label htmlFor="includeExpired" className="text-sm">
                {str(t.includeExpired)}
              </label>
            </div>
          </div>

          {/* Reports Table */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">{str(t.noReports)}</h3>
              <p className="text-muted-foreground">{str(t.noReportsDescription)}</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.reportName)}</TableHead>
                    <TableHead>{str(t.format)}</TableHead>
                    <TableHead>{str(t.status)}</TableHead>
                    <TableHead>{str(t.source)}</TableHead>
                    <TableHead>{str(t.fileSize)}</TableHead>
                    <TableHead>{str(t.downloadCount)}</TableHead>
                    <TableHead>{str(t.createdAt)}</TableHead>
                    <TableHead className="text-right">{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell className="font-medium">{report.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{report.format.toUpperCase()}</Badge>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={report.status} t={t} />
                      </TableCell>
                      <TableCell>
                        {report.source_name ? (
                          <Link
                            to={`/sources/${report.source_id}`}
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            {report.source_name}
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">{str(t.noSource)}</span>
                        )}
                      </TableCell>
                      <TableCell>{report.file_size ? formatFileSize(report.file_size) : '-'}</TableCell>
                      <TableCell>{report.downloaded_count}</TableCell>
                      <TableCell>{formatDate(report.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(report)}
                            disabled={report.status !== 'completed'}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteDialog({ open: true, report })}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    {str(common.showing)} {(page - 1) * pageSize + 1}-
                    {Math.min(page * pageSize, total)} {str(common.of)} {total}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      {str(common.previous)}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      {str(common.next)}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, report: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.deleteConfirmTitle)}</DialogTitle>
            <DialogDescription>{str(t.deleteConfirmMessage)}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog({ open: false, report: null })}>
              {str(common.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              {str(t.delete)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialog} onOpenChange={setCleanupDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.cleanupTitle)}</DialogTitle>
            <DialogDescription>
              {str(t.cleanupDescription)}
              <br />
              <br />
              {str(t.cleanupConfirm)}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCleanupDialog(false)}>
              {str(common.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleCleanup}>
              {str(t.cleanupExpired)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
