/**
 * Mermaid-based lineage graph renderer.
 *
 * Renders lineage as a Mermaid flowchart diagram, ideal for documentation
 * and export purposes. Shows both the rendered SVG and the Mermaid code.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import mermaid from 'mermaid'
import { useIntlayer } from 'react-intlayer'
import {
  Copy,
  Download,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  FileCode,
  ArrowRight,
  ArrowDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import { cn } from '@/lib/utils'
import {
  graphToMermaid,
  graphToMermaidSimple,
  copyToClipboard,
  downloadAsFile,
  downloadSvg,
} from '@/lib/lineage-utils'
import type { LineageNode, LineageEdge } from '@/api/client'

// Initialize mermaid with default configuration
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: {
    htmlLabels: true,
    curve: 'basis',
    padding: 20,
    nodeSpacing: 50,
    rankSpacing: 80,
  },
})

type MermaidDirection = 'LR' | 'TB' | 'RL' | 'BT'
type MermaidStyle = 'grouped' | 'simple'

interface MermaidLineageGraphProps {
  nodes: LineageNode[]
  edges: LineageEdge[]
  onNodeClick?: (node: LineageNode) => void
  className?: string
}

export function MermaidLineageGraph({
  nodes,
  edges,
  onNodeClick,
  className,
}: MermaidLineageGraphProps) {
  const t = useIntlayer('lineage')
  const { toast } = useToast()
  const containerRef = useRef<HTMLDivElement>(null)
  const [svgContent, setSvgContent] = useState<string>('')
  const [mermaidCode, setMermaidCode] = useState<string>('')
  const [isCodeVisible, setIsCodeVisible] = useState(false)
  const [direction, setDirection] = useState<MermaidDirection>('LR')
  const [style, setStyle] = useState<MermaidStyle>('grouped')
  const [error, setError] = useState<string | null>(null)
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Detect dark mode
  useEffect(() => {
    const checkDarkMode = () => {
      setIsDarkMode(document.documentElement.classList.contains('dark'))
    }
    checkDarkMode()

    const observer = new MutationObserver(checkDarkMode)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })

    return () => observer.disconnect()
  }, [])

  // Generate and render Mermaid diagram
  useEffect(() => {
    const renderDiagram = async () => {
      if (nodes.length === 0) {
        setSvgContent('')
        setMermaidCode('')
        return
      }

      // Generate Mermaid code
      const code =
        style === 'grouped'
          ? graphToMermaid(nodes, edges, direction)
          : graphToMermaidSimple(nodes, edges, direction)
      setMermaidCode(code)

      try {
        // Update mermaid theme based on dark mode
        mermaid.initialize({
          startOnLoad: false,
          theme: isDarkMode ? 'dark' : 'default',
          securityLevel: 'loose',
          flowchart: {
            htmlLabels: true,
            curve: 'basis',
            padding: 20,
            nodeSpacing: 50,
            rankSpacing: 80,
          },
        })

        // Render the diagram
        const { svg } = await mermaid.render(
          `mermaid-${Date.now()}`,
          code
        )
        setSvgContent(svg)
        setError(null)
      } catch (err) {
        console.error('Mermaid render error:', err)
        setError(err instanceof Error ? err.message : 'Failed to render diagram')
        setSvgContent('')
      }
    }

    renderDiagram()
  }, [nodes, edges, direction, style, isDarkMode])

  // Handle node clicks in SVG
  useEffect(() => {
    if (!containerRef.current || !onNodeClick) return

    const handleClick = (e: MouseEvent) => {
      const target = e.target as Element
      const nodeElement = target.closest('.node')
      if (nodeElement) {
        const nodeId = nodeElement.id?.replace(/_/g, '-')
        const node = nodes.find((n) => n.id === nodeId || n.id.replace(/-/g, '_') === nodeElement.id)
        if (node) {
          onNodeClick(node)
        }
      }
    }

    containerRef.current.addEventListener('click', handleClick)
    return () => {
      containerRef.current?.removeEventListener('click', handleClick)
    }
  }, [nodes, onNodeClick])

  // Copy Mermaid code to clipboard
  const handleCopyCode = useCallback(async () => {
    const success = await copyToClipboard(mermaidCode)
    if (success) {
      toast({ title: str(t.mermaid.codeCopied) })
    } else {
      toast({ title: str(t.mermaid.copyFailed), variant: 'destructive' })
    }
  }, [mermaidCode, toast, t])

  // Download as Mermaid file
  const handleDownloadMermaid = useCallback(() => {
    downloadAsFile(mermaidCode, 'lineage-diagram.mmd', 'text/plain')
    toast({ title: str(t.mermaid.fileDownloaded) })
  }, [mermaidCode, toast, t])

  // Download as SVG
  const handleDownloadSvg = useCallback(() => {
    if (!containerRef.current) return
    const svgElement = containerRef.current.querySelector('svg')
    if (svgElement) {
      downloadSvg(svgElement as SVGSVGElement, 'lineage-diagram.svg')
      toast({ title: str(t.mermaid.svgDownloaded) })
    }
  }, [toast, t])

  // Empty state
  if (nodes.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-[500px] gap-4 rounded-lg border-2 border-dashed', className)}>
        <FileCode className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">{t.noLineageYet}</p>
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col', className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b bg-background">
        <Select value={direction} onValueChange={(v) => setDirection(v as MermaidDirection)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder={t.mermaid.direction} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="LR">
              <div className="flex items-center gap-2">
                <ArrowRight className="h-4 w-4" />
                {t.mermaid.leftToRight}
              </div>
            </SelectItem>
            <SelectItem value="TB">
              <div className="flex items-center gap-2">
                <ArrowDown className="h-4 w-4" />
                {t.mermaid.topToBottom}
              </div>
            </SelectItem>
            <SelectItem value="RL">
              <div className="flex items-center gap-2">
                <ArrowRight className="h-4 w-4 rotate-180" />
                {t.mermaid.rightToLeft}
              </div>
            </SelectItem>
            <SelectItem value="BT">
              <div className="flex items-center gap-2">
                <ArrowDown className="h-4 w-4 rotate-180" />
                {t.mermaid.bottomToTop}
              </div>
            </SelectItem>
          </SelectContent>
        </Select>

        <Select value={style} onValueChange={(v) => setStyle(v as MermaidStyle)}>
          <SelectTrigger className="w-[130px]">
            <SelectValue placeholder={t.mermaid.style} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="grouped">{t.mermaid.grouped}</SelectItem>
            <SelectItem value="simple">{t.mermaid.simple}</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex items-center gap-1 ml-auto">
          <Button variant="ghost" size="sm" onClick={handleCopyCode} title={str(t.mermaid.copyCode)}>
            <Copy className="h-4 w-4 mr-1" />
            {t.mermaid.copy}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDownloadMermaid} title={str(t.mermaid.downloadMermaid)}>
            <Download className="h-4 w-4 mr-1" />
            .mmd
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDownloadSvg} title={str(t.mermaid.downloadSvg)}>
            <Download className="h-4 w-4 mr-1" />
            .svg
          </Button>
        </div>
      </div>

      {/* Diagram container */}
      <div className="flex-1 min-h-[400px] p-4 overflow-auto bg-background">
        {error ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-destructive">
            <p>{t.mermaid.renderError}</p>
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button variant="outline" size="sm" onClick={() => setError(null)}>
              <RotateCcw className="h-4 w-4 mr-1" />
              {t.refresh}
            </Button>
          </div>
        ) : (
          <div
            ref={containerRef}
            className="flex items-center justify-center mermaid-container"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}
      </div>

      {/* Collapsible code panel */}
      <Collapsible open={isCodeVisible} onOpenChange={setIsCodeVisible}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full rounded-none border-t justify-between">
            <span className="flex items-center gap-2">
              <FileCode className="h-4 w-4" />
              {t.mermaid.showCode}
            </span>
            {isCodeVisible ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="relative">
            <pre className="p-4 bg-muted overflow-x-auto text-sm max-h-[300px]">
              <code>{mermaidCode}</code>
            </pre>
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2"
              onClick={handleCopyCode}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Stats */}
      <div className="flex gap-2 p-2 border-t text-sm text-muted-foreground">
        <span>{t.totalNodes}: {nodes.length}</span>
        <span>|</span>
        <span>{t.totalEdges}: {edges.length}</span>
      </div>
    </div>
  )
}
