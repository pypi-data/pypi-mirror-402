/**
 * Export panel for lineage graph data.
 *
 * Provides options to export lineage in various formats:
 * - Mermaid code
 * - PNG image
 * - SVG image
 * - JSON data
 */

import { useCallback, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Download,
  Copy,
  FileCode,
  FileImage,
  FileJson,
  Check,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  graphToMermaid,
  copyToClipboard,
  downloadAsFile,
} from '@/lib/lineage-utils'
import type { LineageNode, LineageEdge } from '@/api/client'

interface LineageExportPanelProps {
  nodes: LineageNode[]
  edges: LineageEdge[]
  className?: string
}

export function LineageExportPanel({
  nodes,
  edges,
  className,
}: LineageExportPanelProps) {
  const t = useIntlayer('lineage')
  const { toast } = useToast()
  const [isExporting, setIsExporting] = useState(false)
  const [copiedFormat, setCopiedFormat] = useState<string | null>(null)

  // Copy Mermaid code to clipboard
  const handleCopyMermaid = useCallback(async () => {
    const mermaidCode = graphToMermaid(nodes, edges)
    const success = await copyToClipboard(mermaidCode)
    if (success) {
      setCopiedFormat('mermaid')
      toast({ title: str(t.export.mermaidCopied) })
      setTimeout(() => setCopiedFormat(null), 2000)
    } else {
      toast({ title: str(t.export.copyFailed), variant: 'destructive' })
    }
  }, [nodes, edges, toast, t])

  // Copy JSON data to clipboard
  const handleCopyJson = useCallback(async () => {
    const jsonData = JSON.stringify({ nodes, edges }, null, 2)
    const success = await copyToClipboard(jsonData)
    if (success) {
      setCopiedFormat('json')
      toast({ title: str(t.export.jsonCopied) })
      setTimeout(() => setCopiedFormat(null), 2000)
    } else {
      toast({ title: str(t.export.copyFailed), variant: 'destructive' })
    }
  }, [nodes, edges, toast, t])

  // Download as Mermaid file
  const handleDownloadMermaid = useCallback(() => {
    const mermaidCode = graphToMermaid(nodes, edges)
    downloadAsFile(mermaidCode, 'lineage-diagram.mmd', 'text/plain')
    toast({ title: str(t.export.fileDownloaded) })
  }, [nodes, edges, toast, t])

  // Download as JSON file
  const handleDownloadJson = useCallback(() => {
    const jsonData = JSON.stringify({ nodes, edges }, null, 2)
    downloadAsFile(jsonData, 'lineage-data.json', 'application/json')
    toast({ title: str(t.export.fileDownloaded) })
  }, [nodes, edges, toast, t])

  // Download as SVG (from current renderer)
  const handleDownloadSvg = useCallback(async () => {
    setIsExporting(true)
    try {
      // Try to find SVG from React Flow or other renderers
      const svgElement = document.querySelector('.react-flow__viewport svg') as SVGSVGElement
      if (svgElement) {
        const serializer = new XMLSerializer()
        const svgString = serializer.serializeToString(svgElement)
        downloadAsFile(svgString, 'lineage-diagram.svg', 'image/svg+xml')
        toast({ title: str(t.export.svgDownloaded) })
      } else {
        // Try Mermaid SVG
        const mermaidSvg = document.querySelector('.mermaid-container svg') as SVGSVGElement
        if (mermaidSvg) {
          const serializer = new XMLSerializer()
          const svgString = serializer.serializeToString(mermaidSvg)
          downloadAsFile(svgString, 'lineage-diagram.svg', 'image/svg+xml')
          toast({ title: str(t.export.svgDownloaded) })
        } else {
          toast({ title: str(t.export.noSvgFound), variant: 'destructive' })
        }
      }
    } catch (error) {
      console.error('SVG export error:', error)
      toast({ title: str(t.export.exportFailed), variant: 'destructive' })
    } finally {
      setIsExporting(false)
    }
  }, [toast, t])

  // Download as PNG (from Cytoscape if available)
  const handleDownloadPng = useCallback(async () => {
    setIsExporting(true)
    try {
      // Check if Cytoscape export function is available
      const cytoscapeExport = (window as unknown as { __cytoscapeExportPng?: () => Blob | null }).__cytoscapeExportPng
      if (cytoscapeExport) {
        const blob = cytoscapeExport()
        if (blob) {
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = 'lineage-diagram.png'
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(url)
          toast({ title: str(t.export.pngDownloaded) })
          return
        }
      }

      // Fallback: convert SVG to PNG
      const svgElement =
        (document.querySelector('.react-flow__viewport svg') as SVGSVGElement) ||
        (document.querySelector('.mermaid-container svg') as SVGSVGElement)

      if (svgElement) {
        await svgToPng(svgElement, 'lineage-diagram.png', 2)
        toast({ title: str(t.export.pngDownloaded) })
      } else {
        toast({ title: str(t.export.noSvgFound), variant: 'destructive' })
      }
    } catch (error) {
      console.error('PNG export error:', error)
      toast({ title: str(t.export.exportFailed), variant: 'destructive' })
    } finally {
      setIsExporting(false)
    }
  }, [toast, t])

  // Helper function to convert SVG to PNG
  const svgToPng = (svgElement: SVGSVGElement, filename: string, scale: number = 2): Promise<void> => {
    return new Promise((resolve, reject) => {
      const serializer = new XMLSerializer()
      const svgString = serializer.serializeToString(svgElement)
      const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)

      const img = new Image()
      img.onload = () => {
        const rect = svgElement.getBoundingClientRect()
        const canvas = document.createElement('canvas')
        canvas.width = rect.width * scale
        canvas.height = rect.height * scale

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          URL.revokeObjectURL(url)
          reject(new Error('Failed to get canvas context'))
          return
        }

        ctx.scale(scale, scale)
        ctx.drawImage(img, 0, 0, rect.width, rect.height)

        canvas.toBlob((blob) => {
          if (blob) {
            const pngUrl = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = pngUrl
            link.download = filename
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(pngUrl)
          }
          URL.revokeObjectURL(url)
          resolve()
        }, 'image/png')
      }
      img.onerror = () => {
        URL.revokeObjectURL(url)
        reject(new Error('Failed to load SVG image'))
      }
      img.src = url
    })
  }

  const isDisabled = nodes.length === 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={className}
          disabled={isDisabled || isExporting}
        >
          {isExporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          {t.export.export}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[200px]">
        {/* Copy to clipboard section */}
        <DropdownMenuItem onClick={handleCopyMermaid}>
          {copiedFormat === 'mermaid' ? (
            <Check className="mr-2 h-4 w-4 text-green-500" />
          ) : (
            <Copy className="mr-2 h-4 w-4" />
          )}
          {t.export.copyMermaid}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleCopyJson}>
          {copiedFormat === 'json' ? (
            <Check className="mr-2 h-4 w-4 text-green-500" />
          ) : (
            <Copy className="mr-2 h-4 w-4" />
          )}
          {t.export.copyJson}
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Download section */}
        <DropdownMenuItem onClick={handleDownloadMermaid}>
          <FileCode className="mr-2 h-4 w-4" />
          {t.export.downloadMermaid}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleDownloadJson}>
          <FileJson className="mr-2 h-4 w-4" />
          {t.export.downloadJson}
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Image export section */}
        <DropdownMenuItem onClick={handleDownloadSvg}>
          <FileImage className="mr-2 h-4 w-4" />
          {t.export.downloadSvg}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleDownloadPng}>
          <FileImage className="mr-2 h-4 w-4" />
          {t.export.downloadPng}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
