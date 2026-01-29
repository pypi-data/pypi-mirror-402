/**
 * Utility functions for lineage graph transformations.
 *
 * Provides conversions between different graph formats:
 * - React Flow nodes/edges
 * - Cytoscape.js format
 * - Mermaid diagram syntax
 */

import type { LineageNode, LineageEdge, LineageNodeType, LineageEdgeType } from '@/api/client'

// ============================================================================
// Types
// ============================================================================

/**
 * Cytoscape element format for nodes.
 */
export interface CytoscapeNode {
  data: {
    id: string
    label: string
    nodeType: LineageNodeType
    sourceId: string | null
    hasSource: boolean
  }
  position?: {
    x: number
    y: number
  }
}

/**
 * Cytoscape element format for edges.
 */
export interface CytoscapeEdge {
  data: {
    id: string
    source: string
    target: string
    edgeType: LineageEdgeType
    label: string
  }
}

/**
 * Combined Cytoscape elements.
 */
export interface CytoscapeElements {
  nodes: CytoscapeNode[]
  edges: CytoscapeEdge[]
}

/**
 * Available layout options for Cytoscape.
 */
export type CytoscapeLayout = 'dagre' | 'breadthfirst' | 'cose' | 'circle' | 'grid' | 'concentric'

// ============================================================================
// Cytoscape Conversion
// ============================================================================

/**
 * Convert lineage graph data to Cytoscape.js format.
 */
export function graphToCytoscape(
  nodes: LineageNode[],
  edges: LineageEdge[]
): CytoscapeElements {
  const cytoscapeNodes: CytoscapeNode[] = nodes.map((node) => ({
    data: {
      id: node.id,
      label: node.name,
      nodeType: node.node_type,
      sourceId: node.source_id,
      hasSource: !!node.source_id,
    },
    position:
      node.position_x !== null && node.position_y !== null
        ? { x: node.position_x, y: node.position_y }
        : undefined,
  }))

  const cytoscapeEdges: CytoscapeEdge[] = edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source_node_id,
      target: edge.target_node_id,
      edgeType: edge.edge_type,
      label: formatEdgeLabel(edge.edge_type),
    },
  }))

  return { nodes: cytoscapeNodes, edges: cytoscapeEdges }
}

/**
 * Get Cytoscape layout configuration.
 */
export function getCytoscapeLayoutConfig(layout: CytoscapeLayout) {
  const baseConfig = {
    fit: true,
    padding: 50,
    animate: true,
    animationDuration: 500,
  }

  switch (layout) {
    case 'dagre':
      return {
        name: 'dagre',
        ...baseConfig,
        rankDir: 'LR', // Left to right
        nodeSep: 50,
        rankSep: 100,
        edgeSep: 10,
      }
    case 'breadthfirst':
      return {
        name: 'breadthfirst',
        ...baseConfig,
        directed: true,
        spacingFactor: 1.5,
        circle: false,
      }
    case 'cose':
      return {
        name: 'cose',
        ...baseConfig,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        nestingFactor: 1.2,
        gravity: 1,
        numIter: 1000,
        randomize: false,
      }
    case 'circle':
      return {
        name: 'circle',
        ...baseConfig,
        avoidOverlap: true,
        spacingFactor: 1.5,
      }
    case 'grid':
      return {
        name: 'grid',
        ...baseConfig,
        avoidOverlap: true,
        condense: true,
        rows: undefined,
      }
    case 'concentric':
      return {
        name: 'concentric',
        ...baseConfig,
        concentric: (node: { degree: () => number }) => node.degree(),
        levelWidth: () => 2,
        minNodeSpacing: 50,
      }
    default:
      return {
        name: 'dagre',
        ...baseConfig,
        rankDir: 'LR',
      }
  }
}

// ============================================================================
// Mermaid Conversion
// ============================================================================

/**
 * Convert lineage graph data to Mermaid flowchart syntax.
 */
export function graphToMermaid(
  nodes: LineageNode[],
  edges: LineageEdge[],
  direction: 'LR' | 'TB' | 'RL' | 'BT' = 'LR'
): string {
  const lines: string[] = [`flowchart ${direction}`]
  lines.push('')

  // Add subgraphs for node types
  const sourceNodes = nodes.filter((n) => n.node_type === 'source')
  const transformNodes = nodes.filter((n) => n.node_type === 'transform')
  const sinkNodes = nodes.filter((n) => n.node_type === 'sink')

  // Define nodes with appropriate shapes
  if (sourceNodes.length > 0) {
    lines.push('  subgraph Sources')
    sourceNodes.forEach((node) => {
      lines.push(`    ${sanitizeId(node.id)}[(${sanitizeLabel(node.name)})]`)
    })
    lines.push('  end')
    lines.push('')
  }

  if (transformNodes.length > 0) {
    lines.push('  subgraph Transforms')
    transformNodes.forEach((node) => {
      lines.push(`    ${sanitizeId(node.id)}{{${sanitizeLabel(node.name)}}}`)
    })
    lines.push('  end')
    lines.push('')
  }

  if (sinkNodes.length > 0) {
    lines.push('  subgraph Sinks')
    sinkNodes.forEach((node) => {
      lines.push(`    ${sanitizeId(node.id)}[[${sanitizeLabel(node.name)}]]`)
    })
    lines.push('  end')
    lines.push('')
  }

  // Add edges
  edges.forEach((edge) => {
    const arrow = getArrowStyle(edge.edge_type)
    const label = formatEdgeLabel(edge.edge_type)
    lines.push(`  ${sanitizeId(edge.source_node_id)} ${arrow}|${label}| ${sanitizeId(edge.target_node_id)}`)
  })

  // Add styling
  lines.push('')
  lines.push('  %% Styling')
  lines.push('  classDef source fill:#3b82f6,stroke:#1d4ed8,color:#fff')
  lines.push('  classDef transform fill:#f59e0b,stroke:#d97706,color:#fff')
  lines.push('  classDef sink fill:#22c55e,stroke:#16a34a,color:#fff')

  if (sourceNodes.length > 0) {
    lines.push(`  class ${sourceNodes.map((n) => sanitizeId(n.id)).join(',')} source`)
  }
  if (transformNodes.length > 0) {
    lines.push(`  class ${transformNodes.map((n) => sanitizeId(n.id)).join(',')} transform`)
  }
  if (sinkNodes.length > 0) {
    lines.push(`  class ${sinkNodes.map((n) => sanitizeId(n.id)).join(',')} sink`)
  }

  return lines.join('\n')
}

/**
 * Generate simple Mermaid code without subgraphs (for cleaner output).
 */
export function graphToMermaidSimple(
  nodes: LineageNode[],
  edges: LineageEdge[],
  direction: 'LR' | 'TB' | 'RL' | 'BT' = 'LR'
): string {
  const lines: string[] = [`flowchart ${direction}`]
  lines.push('')

  // Define nodes with shapes based on type
  nodes.forEach((node) => {
    const shape = getNodeShape(node.node_type)
    lines.push(`  ${sanitizeId(node.id)}${shape.open}${sanitizeLabel(node.name)}${shape.close}`)
  })

  lines.push('')

  // Add edges
  edges.forEach((edge) => {
    const arrow = getArrowStyle(edge.edge_type)
    lines.push(`  ${sanitizeId(edge.source_node_id)} ${arrow} ${sanitizeId(edge.target_node_id)}`)
  })

  return lines.join('\n')
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Sanitize node ID for Mermaid (remove special characters).
 */
function sanitizeId(id: string): string {
  // Replace dashes with underscores and remove other special chars
  return id.replace(/-/g, '_').replace(/[^a-zA-Z0-9_]/g, '')
}

/**
 * Sanitize label for Mermaid (escape quotes and special chars).
 */
function sanitizeLabel(label: string): string {
  return label
    .replace(/"/g, "'")
    .replace(/\[/g, '(')
    .replace(/\]/g, ')')
    .replace(/\{/g, '(')
    .replace(/\}/g, ')')
}

/**
 * Get node shape markers for Mermaid based on node type.
 */
function getNodeShape(nodeType: LineageNodeType): { open: string; close: string } {
  switch (nodeType) {
    case 'source':
      return { open: '[(', close: ')]' } // Cylinder shape
    case 'transform':
      return { open: '{{', close: '}}' } // Hexagon shape
    case 'sink':
      return { open: '[[', close: ']]' } // Subroutine shape
    default:
      return { open: '[', close: ']' } // Default rectangle
  }
}

/**
 * Get arrow style for Mermaid based on edge type.
 */
function getArrowStyle(edgeType: LineageEdgeType): string {
  switch (edgeType) {
    case 'derives_from':
      return '-->'
    case 'transforms_to':
      return '==>'
    case 'feeds_into':
      return '-.->'}
  return '-->'
}

/**
 * Format edge type label for display.
 */
function formatEdgeLabel(edgeType: LineageEdgeType): string {
  switch (edgeType) {
    case 'derives_from':
      return 'derives'
    case 'transforms_to':
      return 'transforms'
    case 'feeds_into':
      return 'feeds'
    default:
      return edgeType
  }
}

// ============================================================================
// Export Utilities
// ============================================================================

/**
 * Copy text to clipboard.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    } catch {
      document.body.removeChild(textArea)
      return false
    }
  }
}

/**
 * Download text as a file.
 */
export function downloadAsFile(content: string, filename: string, mimeType: string = 'text/plain'): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Download SVG element as file.
 */
export function downloadSvg(svgElement: SVGSVGElement, filename: string): void {
  const serializer = new XMLSerializer()
  const svgString = serializer.serializeToString(svgElement)
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(svgBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Convert SVG to PNG and download.
 */
export async function downloadAsPng(
  svgElement: SVGSVGElement,
  filename: string,
  scale: number = 2
): Promise<void> {
  return new Promise((resolve, reject) => {
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svgElement)
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const rect = svgElement.getBoundingClientRect()
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
