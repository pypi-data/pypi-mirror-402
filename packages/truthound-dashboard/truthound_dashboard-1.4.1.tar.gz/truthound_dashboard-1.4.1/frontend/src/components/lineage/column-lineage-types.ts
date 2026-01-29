/**
 * Type definitions for column-level lineage.
 */

/**
 * Types of column transformations.
 */
export type ColumnTransformationType =
  | 'direct'      // Direct copy without transformation
  | 'derived'     // Derived from one or more source columns
  | 'aggregated'  // Result of aggregation (SUM, COUNT, etc.)
  | 'filtered'    // Filtered subset of data
  | 'joined'      // Result of join operation
  | 'renamed'     // Column rename only
  | 'cast'        // Data type conversion
  | 'computed'    // Complex computation/expression

/**
 * A column in a lineage node.
 */
export interface LineageColumn {
  name: string
  dataType: string
  nullable: boolean
  description?: string
  isPrimaryKey?: boolean
  isForeignKey?: boolean
  tags?: string[]
}

/**
 * Mapping between source and target columns.
 */
export interface ColumnMapping {
  id: string
  sourceColumn: string
  targetColumn: string
  sourceNodeId: string
  targetNodeId: string
  transformationType: ColumnTransformationType
  expression?: string
  description?: string
  confidence?: number // 0-1, for auto-discovered mappings
}

/**
 * Column lineage for a node.
 */
export interface NodeColumnLineage {
  nodeId: string
  nodeName: string
  columns: LineageColumn[]
  incomingMappings: ColumnMapping[]
  outgoingMappings: ColumnMapping[]
}

/**
 * Column impact analysis result.
 */
export interface ColumnImpactResult {
  sourceColumn: string
  sourceNodeId: string
  sourceNodeName: string
  affectedColumns: AffectedColumn[]
  totalAffected: number
  affectedTables: number
  impactPath: ColumnImpactPath[]
}

/**
 * A column affected by changes.
 */
export interface AffectedColumn {
  nodeId: string
  nodeName: string
  columnName: string
  transformationType: ColumnTransformationType
  depth: number // Distance from source
}

/**
 * Path showing how impact propagates.
 */
export interface ColumnImpactPath {
  fromNodeId: string
  fromNodeName: string
  fromColumn: string
  toNodeId: string
  toNodeName: string
  toColumn: string
  transformationType: ColumnTransformationType
}

/**
 * Edge with column mapping information.
 */
export interface EdgeColumnMappings {
  edgeId: string
  sourceNodeId: string
  targetNodeId: string
  mappings: ColumnMapping[]
}
