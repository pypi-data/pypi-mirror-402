/**
 * Toolbar component for lineage graph actions.
 */

import { useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Plus, Wand2, Save, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { LineageNodeType } from '@/api/client'

interface LineageToolbarProps {
  onAddNode: (name: string, nodeType: LineageNodeType) => void
  onAutoDiscover: () => void
  onSavePositions: () => void
  onRefresh: () => void
  isDiscovering?: boolean
  isSaving?: boolean
}

export function LineageToolbar({
  onAddNode,
  onAutoDiscover,
  onSavePositions,
  onRefresh,
  isDiscovering = false,
  isSaving = false,
}: LineageToolbarProps) {
  const t = useIntlayer('lineage')
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newNodeName, setNewNodeName] = useState('')
  const [newNodeType, setNewNodeType] = useState<LineageNodeType>('transform')

  const handleAddNode = () => {
    if (newNodeName.trim()) {
      onAddNode(newNodeName.trim(), newNodeType)
      setNewNodeName('')
      setNewNodeType('transform')
      setIsAddDialogOpen(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Plus className="mr-2 h-4 w-4" />
              {t.addNode}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              {t.addNode}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="outline"
          size="sm"
          onClick={onAutoDiscover}
          disabled={isDiscovering}
        >
          <Wand2 className="mr-2 h-4 w-4" />
          {isDiscovering ? t.discovering : t.autoDiscover}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={onSavePositions}
          disabled={isSaving}
        >
          <Save className="mr-2 h-4 w-4" />
          {t.savePositions}
        </Button>

        <Button variant="ghost" size="sm" onClick={onRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          {t.refresh}
        </Button>
      </div>

      {/* Add Node Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.addNode}</DialogTitle>
            <DialogDescription>
              Add a new node to the lineage graph.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="nodeName">{t.nodeName}</Label>
              <Input
                id="nodeName"
                value={newNodeName}
                onChange={(e) => setNewNodeName(e.target.value)}
                placeholder="e.g., raw_customers"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="nodeType">{t.nodeType}</Label>
              <Select
                value={newNodeType}
                onValueChange={(v) => setNewNodeType(v as LineageNodeType)}
              >
                <SelectTrigger id="nodeType">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="source">{t.nodeTypes.source}</SelectItem>
                  <SelectItem value="transform">{t.nodeTypes.transform}</SelectItem>
                  <SelectItem value="sink">{t.nodeTypes.sink}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddNode} disabled={!newNodeName.trim()}>
              {t.addNode}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
