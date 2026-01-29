/**
 * BulkActionBar - Multi-select and bulk operations UI
 *
 * Provides:
 * - Selection management (select all, clear)
 * - Bulk actions (enable, disable, delete)
 * - Action confirmation dialogs
 * - Progress indicators
 *
 * Designed to be reusable across all notification config types
 */

import { useState, useCallback, useMemo } from 'react'
import {
  CheckSquare,
  Square,
  Minus,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Loader2,
  AlertTriangle,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface BulkActionItem {
  id: string
  name: string
  is_active?: boolean
}

export type BulkActionType = 'enable' | 'disable' | 'delete'

export interface BulkActionCallbacks<T extends BulkActionItem> {
  onEnable?: (items: T[]) => Promise<void>
  onDisable?: (items: T[]) => Promise<void>
  onDelete?: (items: T[]) => Promise<void>
}

// =============================================================================
// Selection Hook
// =============================================================================

export function useBulkSelection<T extends BulkActionItem>(items: T[]) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const selectedItems = useMemo(
    () => items.filter((item) => selectedIds.has(item.id)),
    [items, selectedIds]
  )

  const isAllSelected = items.length > 0 && selectedIds.size === items.length
  const isSomeSelected = selectedIds.size > 0 && selectedIds.size < items.length
  const isNoneSelected = selectedIds.size === 0

  const toggleItem = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(items.map((item) => item.id)))
  }, [items])

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  const toggleAll = useCallback(() => {
    if (isAllSelected) {
      clearSelection()
    } else {
      selectAll()
    }
  }, [isAllSelected, clearSelection, selectAll])

  const isSelected = useCallback((id: string) => selectedIds.has(id), [selectedIds])

  return {
    selectedIds,
    selectedItems,
    selectedCount: selectedIds.size,
    isAllSelected,
    isSomeSelected,
    isNoneSelected,
    toggleItem,
    selectAll,
    clearSelection,
    toggleAll,
    isSelected,
  }
}

// =============================================================================
// Selection Checkbox Component
// =============================================================================

interface SelectionCheckboxProps {
  checked: boolean
  indeterminate?: boolean
  onCheckedChange: (checked: boolean) => void
  className?: string
}

export function SelectionCheckbox({ checked, indeterminate, onCheckedChange, className }: SelectionCheckboxProps) {
  return (
    <Checkbox
      checked={indeterminate ? 'indeterminate' : checked}
      onCheckedChange={(checked) => onCheckedChange(checked === true)}
      className={className}
    />
  )
}

// =============================================================================
// Bulk Action Bar Component
// =============================================================================

interface BulkActionBarProps<T extends BulkActionItem> {
  selectedItems: T[]
  selectedCount?: number
  totalCount?: number
  totalItems?: number // Alias for totalCount
  isAllSelected?: boolean
  isSomeSelected?: boolean
  onToggleAll?: () => void
  onClearSelection: () => void
  callbacks?: BulkActionCallbacks<T>
  // Direct callback props (alternative to callbacks object)
  onEnable?: (items: T[]) => Promise<void>
  onDisable?: (items: T[]) => Promise<void>
  onDelete?: (items: T[]) => Promise<void>
  className?: string
  showSelectAll?: boolean
  itemLabel?: string
}

export function BulkActionBar<T extends BulkActionItem>({
  selectedItems,
  selectedCount: selectedCountProp,
  totalCount: totalCountProp,
  totalItems,
  isAllSelected: isAllSelectedProp,
  isSomeSelected: isSomeSelectedProp,
  onToggleAll,
  onClearSelection,
  callbacks,
  onEnable,
  onDisable,
  onDelete,
  className,
  showSelectAll = true,
}: BulkActionBarProps<T>) {
  // Support both totalCount and totalItems props
  const totalCount = totalCountProp ?? totalItems ?? 0
  const selectedCount = selectedCountProp ?? selectedItems.length
  const isAllSelected = isAllSelectedProp ?? (totalCount > 0 && selectedCount === totalCount)
  const isSomeSelected = isSomeSelectedProp ?? (selectedCount > 0 && selectedCount < totalCount)

  // Merge callbacks from both sources
  const mergedCallbacks: BulkActionCallbacks<T> = {
    onEnable: callbacks?.onEnable ?? onEnable,
    onDisable: callbacks?.onDisable ?? onDisable,
    onDelete: callbacks?.onDelete ?? onDelete,
  }
  const { toast } = useToast()
  const [actionType, setActionType] = useState<BulkActionType | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)

  const hasSelection = selectedCount > 0

  // Count active/inactive items
  const activeCount = selectedItems.filter((item) => item.is_active).length
  const inactiveCount = selectedCount - activeCount

  const openConfirmDialog = (action: BulkActionType) => {
    setActionType(action)
    setConfirmOpen(true)
  }

  const executeAction = useCallback(async () => {
    if (!actionType || selectedItems.length === 0) return

    setProcessing(true)
    setProgress(0)

    try {
      const callback =
        actionType === 'enable'
          ? mergedCallbacks.onEnable
          : actionType === 'disable'
            ? mergedCallbacks.onDisable
            : mergedCallbacks.onDelete

      if (callback) {
        await callback(selectedItems)
      }

      toast({
        title: `${actionType === 'delete' ? 'Deleted' : actionType === 'enable' ? 'Enabled' : 'Disabled'} ${selectedCount} items`,
      })
      onClearSelection()
    } catch (e) {
      toast({
        title: `Failed to ${actionType} items`,
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setProcessing(false)
      setProgress(0)
      setConfirmOpen(false)
      setActionType(null)
    }
  }, [actionType, selectedItems, callbacks, selectedCount, onClearSelection, toast])

  const getConfirmMessage = () => {
    switch (actionType) {
      case 'enable':
        return `Enable ${selectedCount} item${selectedCount > 1 ? 's' : ''}?`
      case 'disable':
        return `Disable ${selectedCount} item${selectedCount > 1 ? 's' : ''}?`
      case 'delete':
        return `Delete ${selectedCount} item${selectedCount > 1 ? 's' : ''}? This action cannot be undone.`
      default:
        return ''
    }
  }

  if (!hasSelection && !showSelectAll) return null

  return (
    <>
      <div
        className={cn(
          'flex items-center justify-between p-2 bg-muted/50 rounded-md border',
          className
        )}
      >
        <div className="flex items-center gap-3">
          {/* Select All Checkbox */}
          {showSelectAll && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleAll}
                className="h-7 px-2"
              >
                {isAllSelected ? (
                  <CheckSquare className="h-4 w-4" />
                ) : isSomeSelected ? (
                  <Minus className="h-4 w-4" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
              </Button>
              <span className="text-sm text-muted-foreground">
                {hasSelection ? (
                  <>
                    <span className="font-medium">{selectedCount}</span> of {totalCount} selected
                  </>
                ) : (
                  `${totalCount} items`
                )}
              </span>
            </div>
          )}

          {/* Selection Summary */}
          {hasSelection && (
            <div className="flex items-center gap-1 border-l pl-3 ml-1">
              {activeCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {activeCount} active
                </Badge>
              )}
              {inactiveCount > 0 && (
                <Badge variant="outline" className="text-xs">
                  {inactiveCount} inactive
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        {hasSelection && (
          <div className="flex items-center gap-1">
            {mergedCallbacks.onEnable && inactiveCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openConfirmDialog('enable')}
                disabled={processing}
                className="h-7 text-xs"
              >
                <ToggleRight className="h-3 w-3 mr-1" />
                Enable
              </Button>
            )}

            {mergedCallbacks.onDisable && activeCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openConfirmDialog('disable')}
                disabled={processing}
                className="h-7 text-xs"
              >
                <ToggleLeft className="h-3 w-3 mr-1" />
                Disable
              </Button>
            )}

            {mergedCallbacks.onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openConfirmDialog('delete')}
                disabled={processing}
                className="h-7 text-xs text-destructive hover:text-destructive"
              >
                <Trash2 className="h-3 w-3 mr-1" />
                Delete
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              disabled={processing}
              className="h-7 px-2"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              {actionType === 'delete' && (
                <AlertTriangle className="h-5 w-5 text-destructive" />
              )}
              Confirm {actionType}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {getConfirmMessage()}
              {selectedCount > 5 && (
                <div className="mt-2 p-2 bg-muted rounded text-xs">
                  Selected items:
                  <ul className="mt-1 max-h-[100px] overflow-auto">
                    {selectedItems.slice(0, 10).map((item) => (
                      <li key={item.id} className="truncate">• {item.name}</li>
                    ))}
                    {selectedCount > 10 && (
                      <li className="text-muted-foreground">... and {selectedCount - 10} more</li>
                    )}
                  </ul>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>

          {processing && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-xs text-center text-muted-foreground">
                Processing... {Math.round(progress)}%
              </p>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel disabled={processing}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault()
                executeAction()
              }}
              disabled={processing}
              className={actionType === 'delete' ? 'bg-destructive hover:bg-destructive/90' : ''}
            >
              {processing ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              {actionType === 'delete' ? 'Delete' : actionType === 'enable' ? 'Enable' : 'Disable'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

// =============================================================================
// Table Row with Selection
// =============================================================================

interface SelectableRowProps {
  id: string
  isSelected: boolean
  onToggle: () => void
  children: React.ReactNode
  className?: string
}

export function SelectableRow({
  isSelected,
  onToggle,
  children,
  className,
}: SelectableRowProps) {
  return (
    <tr
      className={cn(
        'border-b transition-colors hover:bg-muted/50',
        isSelected && 'bg-primary/5',
        className
      )}
    >
      <td className="p-2 w-[40px]">
        <SelectionCheckbox
          checked={isSelected}
          onCheckedChange={onToggle}
        />
      </td>
      {children}
    </tr>
  )
}

// =============================================================================
// Floating Action Bar (for bottom of page)
// =============================================================================

interface FloatingBulkBarProps<T extends BulkActionItem> {
  selectedItems: T[]
  selectedCount?: number
  onClearSelection: () => void
  callbacks?: BulkActionCallbacks<T>
  onEnable?: (items: T[]) => Promise<void>
  onDisable?: (items: T[]) => Promise<void>
  onDelete?: (items: T[]) => Promise<void>
}

export function FloatingBulkBar<T extends BulkActionItem>({
  selectedItems,
  selectedCount: selectedCountProp,
  onClearSelection,
  callbacks,
  onEnable,
  onDisable,
  onDelete,
}: FloatingBulkBarProps<T>) {
  const { toast } = useToast()
  const [processing, setProcessing] = useState(false)

  const selectedCount = selectedCountProp ?? selectedItems.length
  const mergedCallbacks: BulkActionCallbacks<T> = {
    onEnable: callbacks?.onEnable ?? onEnable,
    onDisable: callbacks?.onDisable ?? onDisable,
    onDelete: callbacks?.onDelete ?? onDelete,
  }

  if (selectedCount === 0) return null

  const activeCount = selectedItems.filter((item) => item.is_active).length
  const inactiveCount = selectedCount - activeCount

  const handleAction = async (action: BulkActionType) => {
    setProcessing(true)
    try {
      const callback =
        action === 'enable'
          ? mergedCallbacks.onEnable
          : action === 'disable'
            ? mergedCallbacks.onDisable
            : mergedCallbacks.onDelete

      if (callback) {
        await callback(selectedItems)
      }

      toast({
        title: `${action === 'delete' ? 'Deleted' : action === 'enable' ? 'Enabled' : 'Disabled'} ${selectedCount} items`,
      })
      onClearSelection()
    } catch (e) {
      toast({
        title: `Failed to ${action} items`,
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-2 px-4 py-2 bg-background border shadow-lg rounded-full">
        <Badge variant="secondary">{selectedCount} selected</Badge>

        {mergedCallbacks.onEnable && inactiveCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleAction('enable')}
            disabled={processing}
          >
            <ToggleRight className="h-4 w-4 mr-1" />
            Enable
          </Button>
        )}

        {mergedCallbacks.onDisable && activeCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleAction('disable')}
            disabled={processing}
          >
            <ToggleLeft className="h-4 w-4 mr-1" />
            Disable
          </Button>
        )}

        {mergedCallbacks.onDelete && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleAction('delete')}
            disabled={processing}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Delete
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          disabled={processing}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
