/**
 * CustomReporterManagement - Full CRUD management UI for custom reporters
 *
 * Features:
 * - List all custom reporters with filtering and search
 * - Create new reporters via editor dialog
 * - Edit existing reporters
 * - Delete reporters with confirmation
 * - Enable/disable reporters
 * - Preview reporter output
 * - Test reporter with sample data
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { useApi, useMutation } from '@/hooks/use-api'
import {
  listCustomReporters,
  deleteCustomReporter,
  updateCustomReporter,
  type CustomReporter,
} from '@/api/client'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { toast } from '@/hooks/use-toast'
import {
  Search,
  Plus,
  MoreVertical,
  Edit,
  Trash2,
  Power,
  PowerOff,
  FileText,
  RefreshCw,
  ShieldCheck,
  Code,
  FileCode,
  Download,
} from 'lucide-react'
import { ReporterEditorDialog } from '@/components/plugins'

interface CustomReporterManagementProps {
  className?: string
}

export function CustomReporterManagement({ className }: CustomReporterManagementProps) {
  const common = useIntlayer('common')

  // State
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all')
  const [selectedReporter, setSelectedReporter] = useState<CustomReporter | undefined>()
  const [showEditorDialog, setShowEditorDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [reporterToDelete, setReporterToDelete] = useState<CustomReporter | null>(null)

  // API queries
  const {
    data: reportersData,
    loading,
    refetch,
  } = useApi(
    () =>
      listCustomReporters({
        search: searchQuery || undefined,
        enabled_only: statusFilter === 'enabled',
        limit: 50,
      }),
    [searchQuery, statusFilter]
  )

  // Mutations
  const { mutate: doDelete, loading: deleting } = useMutation((reporterId: string) =>
    deleteCustomReporter(reporterId)
  )

  const { mutate: doToggle } = useMutation(
    (data: { reporterId: string; enabled: boolean }) =>
      updateCustomReporter(data.reporterId, { is_enabled: data.enabled })
  )

  // Handlers
  const handleCreate = useCallback(() => {
    setSelectedReporter(undefined)
    setShowEditorDialog(true)
  }, [])

  const handleEdit = useCallback((reporter: CustomReporter) => {
    setSelectedReporter(reporter)
    setShowEditorDialog(true)
  }, [])

  const handleDeleteClick = useCallback((reporter: CustomReporter) => {
    setReporterToDelete(reporter)
    setShowDeleteDialog(true)
  }, [])

  const handleDeleteConfirm = useCallback(async () => {
    if (!reporterToDelete) return

    try {
      await doDelete(reporterToDelete.id)
      toast({ title: 'Reporter deleted successfully' })
      setShowDeleteDialog(false)
      setReporterToDelete(null)
      refetch()
    } catch {
      toast({ title: 'Failed to delete reporter', variant: 'destructive' })
    }
  }, [reporterToDelete, doDelete, refetch])

  const handleToggle = useCallback(
    async (reporter: CustomReporter) => {
      try {
        await doToggle({ reporterId: reporter.id, enabled: !reporter.is_enabled })
        toast({
          title: reporter.is_enabled
            ? 'Reporter disabled'
            : 'Reporter enabled',
        })
        refetch()
      } catch {
        toast({ title: str(common.error), variant: 'destructive' })
      }
    },
    [doToggle, refetch, common]
  )

  const handleEditorSuccess = useCallback(() => {
    setShowEditorDialog(false)
    setSelectedReporter(undefined)
    refetch()
  }, [refetch])

  // Filter reporters
  const filteredReporters = reportersData?.data.filter((reporter) => {
    if (statusFilter === 'disabled' && reporter.is_enabled) return false
    return true
  })

  const renderReporterCard = (reporter: CustomReporter) => {
    const hasTemplate = !!reporter.template
    const hasCode = !!reporter.code

    return (
      <Card key={reporter.id} className="hover:border-primary/50 transition-colors">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{reporter.display_name}</CardTitle>
                <CardDescription className="text-xs font-mono">
                  {reporter.name}
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={reporter.is_enabled ? 'default' : 'secondary'}>
                {reporter.is_enabled ? 'Enabled' : 'Disabled'}
              </Badge>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleEdit(reporter)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleToggle(reporter)}>
                    {reporter.is_enabled ? (
                      <>
                        <PowerOff className="w-4 h-4 mr-2" />
                        Disable
                      </>
                    ) : (
                      <>
                        <Power className="w-4 h-4 mr-2" />
                        Enable
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive"
                    onClick={() => handleDeleteClick(reporter)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {reporter.description || 'No description provided'}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {/* Output formats */}
            {reporter.output_formats.map((format) => (
              <Badge key={format} variant="outline" className="text-xs">
                {format.toUpperCase()}
              </Badge>
            ))}
            {/* Editor type */}
            <Badge variant="secondary" className="text-xs gap-1">
              {hasTemplate ? (
                <>
                  <FileCode className="w-3 h-3" />
                  Jinja2
                </>
              ) : hasCode ? (
                <>
                  <Code className="w-3 h-3" />
                  Python
                </>
              ) : (
                'No template'
              )}
            </Badge>
            {/* Verified */}
            {reporter.is_verified && (
              <Badge variant="secondary" className="text-xs gap-1">
                <ShieldCheck className="w-3 h-3" />
                Verified
              </Badge>
            )}
          </div>
        </CardContent>
        <CardFooter className="pt-2 border-t text-xs text-muted-foreground">
          <div className="flex items-center justify-between w-full">
            <span>
              {reporter.config_fields?.length || 0} config fields
            </span>
            <span className="flex items-center gap-1">
              <Download className="w-3 h-3" />
              {reporter.usage_count || 0} uses
            </span>
          </div>
        </CardFooter>
      </Card>
    )
  }

  return (
    <div className={className}>
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search reporters..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as 'all' | 'enabled' | 'disabled')}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="enabled">Enabled</SelectItem>
            <SelectItem value="disabled">Disabled</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-2" />
          Create Reporter
        </Button>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Reporter Grid */}
      {loading ? (
        <div className="text-center py-12 text-muted-foreground">
          Loading reporters...
        </div>
      ) : !filteredReporters?.length ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? 'No reporters match your search'
              : 'No custom reporters found'}
          </p>
          <Button onClick={handleCreate}>
            <Plus className="w-4 h-4 mr-2" />
            Create your first reporter
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredReporters.map(renderReporterCard)}
        </div>
      )}

      {/* Editor Dialog */}
      <ReporterEditorDialog
        open={showEditorDialog}
        onOpenChange={setShowEditorDialog}
        reporter={selectedReporter}
        onSuccess={handleEditorSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Reporter</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{reporterToDelete?.display_name}"? This
              action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              {str(common.cancel)}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : str(common.delete)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default CustomReporterManagement
