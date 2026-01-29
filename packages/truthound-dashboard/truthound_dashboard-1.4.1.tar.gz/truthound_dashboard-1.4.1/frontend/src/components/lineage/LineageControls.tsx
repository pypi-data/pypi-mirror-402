/**
 * Controls component for lineage graph zoom and viewport.
 */

import { useReactFlow } from 'reactflow'
import { useIntlayer } from 'react-intlayer'
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

export function LineageControls() {
  const { zoomIn, zoomOut, fitView, setViewport } = useReactFlow()
  const t = useIntlayer('lineage')

  const handleReset = () => {
    setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 200 })
  }

  return (
    <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-1 rounded-md border bg-background/95 p-1 shadow-sm">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => zoomIn({ duration: 200 })}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right">{t.zoomIn}</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => zoomOut({ duration: 200 })}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right">{t.zoomOut}</TooltipContent>
      </Tooltip>

      <div className="h-px bg-border" />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => fitView({ padding: 0.2, duration: 200 })}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right">{t.fitView}</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleReset}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right">{t.resetZoom}</TooltipContent>
      </Tooltip>
    </div>
  )
}
