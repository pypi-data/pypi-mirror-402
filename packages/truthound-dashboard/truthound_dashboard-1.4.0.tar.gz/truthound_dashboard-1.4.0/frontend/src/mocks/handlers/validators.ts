/**
 * MSW handlers for validators registry API.
 *
 * Provides mock data for validator definitions and parameter schemas.
 * This file mirrors the backend validator registry for frontend development.
 */

import { http, HttpResponse } from 'msw'
import type { ValidatorDefinition, ValidatorCategory } from '@/types/validators'

// =============================================================================
// Mock Validator Registry - Complete definitions matching backend
// =============================================================================

// Schema Validators (14 validators)
const SCHEMA_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'ColumnExists',
    display_name: 'Column Exists',
    category: 'schema',
    description: 'Validates that specified columns exist in the dataset.',
    parameters: [
      {
        name: 'columns',
        label: 'Required Columns',
        type: 'column_list',
        description: 'Column names that must exist in the dataset',
        required: true,
      },
    ],
    tags: ['schema', 'structure', 'column'],
    severity_default: 'critical',
  },
  {
    name: 'ColumnNotExists',
    display_name: 'Column Not Exists',
    category: 'schema',
    description:
      'Ensures specified columns are absent (e.g., deprecated or sensitive fields).',
    parameters: [
      {
        name: 'columns',
        label: 'Forbidden Columns',
        type: 'string_list',
        description: 'Column names that must NOT exist in the dataset',
        required: true,
        placeholder: 'e.g., password, ssn, credit_card',
      },
    ],
    tags: ['schema', 'structure', 'column', 'security'],
    severity_default: 'high',
  },
  {
    name: 'ColumnCount',
    display_name: 'Column Count',
    category: 'schema',
    description: 'Validates the number of columns in the dataset.',
    parameters: [
      {
        name: 'expected',
        label: 'Expected Count',
        type: 'integer',
        description: 'Exact expected column count (use min/max for range)',
        min_value: 0,
      },
      {
        name: 'min_count',
        label: 'Minimum Count',
        type: 'integer',
        description: 'Minimum acceptable column count',
        min_value: 0,
      },
      {
        name: 'max_count',
        label: 'Maximum Count',
        type: 'integer',
        description: 'Maximum acceptable column count',
        min_value: 0,
      },
    ],
    tags: ['schema', 'structure', 'count'],
    severity_default: 'medium',
  },
  {
    name: 'RowCount',
    display_name: 'Row Count',
    category: 'schema',
    description: 'Validates the number of rows in the dataset.',
    parameters: [
      {
        name: 'expected',
        label: 'Expected Count',
        type: 'integer',
        description: 'Exact expected row count',
        min_value: 0,
      },
      {
        name: 'min_count',
        label: 'Minimum Count',
        type: 'integer',
        description: 'Minimum acceptable row count',
        min_value: 0,
      },
      {
        name: 'max_count',
        label: 'Maximum Count',
        type: 'integer',
        description: 'Maximum acceptable row count',
        min_value: 0,
      },
    ],
    tags: ['schema', 'structure', 'count', 'row'],
    severity_default: 'medium',
  },
  {
    name: 'ColumnType',
    display_name: 'Column Type',
    category: 'schema',
    description: 'Validates that a column conforms to an expected data type.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        description: 'Target column to validate',
        required: true,
      },
      {
        name: 'expected_type',
        label: 'Expected Type',
        type: 'select',
        description: 'Expected Polars data type',
        required: true,
        options: [
          { value: 'Int8', label: 'Int8' },
          { value: 'Int16', label: 'Int16' },
          { value: 'Int32', label: 'Int32' },
          { value: 'Int64', label: 'Int64' },
          { value: 'UInt8', label: 'UInt8' },
          { value: 'UInt16', label: 'UInt16' },
          { value: 'UInt32', label: 'UInt32' },
          { value: 'UInt64', label: 'UInt64' },
          { value: 'Float32', label: 'Float32' },
          { value: 'Float64', label: 'Float64' },
          { value: 'Boolean', label: 'Boolean' },
          { value: 'String', label: 'String (Utf8)' },
          { value: 'Date', label: 'Date' },
          { value: 'Datetime', label: 'Datetime' },
          { value: 'Duration', label: 'Duration' },
          { value: 'Time', label: 'Time' },
          { value: 'Categorical', label: 'Categorical' },
          { value: 'Object', label: 'Object' },
        ],
      },
    ],
    tags: ['schema', 'type', 'column'],
    severity_default: 'high',
  },
  {
    name: 'ColumnOrder',
    display_name: 'Column Order',
    category: 'schema',
    description: 'Ensures columns appear in the specified order.',
    parameters: [
      {
        name: 'expected_order',
        label: 'Expected Order',
        type: 'column_list',
        description: 'Columns in their expected order',
        required: true,
      },
      {
        name: 'strict',
        label: 'Strict Mode',
        type: 'boolean',
        description: 'If true, no additional columns are allowed',
        default: false,
      },
    ],
    tags: ['schema', 'structure', 'order'],
    severity_default: 'low',
  },
  {
    name: 'TableSchema',
    display_name: 'Table Schema',
    category: 'schema',
    description: 'Validates the complete schema against a reference specification.',
    parameters: [
      {
        name: 'schema',
        label: 'Schema Definition',
        type: 'schema',
        description: 'Column name to type mapping (JSON format)',
        required: true,
        placeholder: '{"id": "Int64", "name": "String", "email": "String"}',
      },
      {
        name: 'strict',
        label: 'Strict Mode',
        type: 'boolean',
        description: 'Reject extra columns not in schema',
        default: false,
      },
    ],
    tags: ['schema', 'structure', 'complete'],
    severity_default: 'critical',
  },
  {
    name: 'ColumnPair',
    display_name: 'Column Pair Relationship',
    category: 'schema',
    description: 'Validates relationships between two columns.',
    parameters: [
      {
        name: 'column_a',
        label: 'First Column',
        type: 'column',
        description: 'First column in the relationship',
        required: true,
      },
      {
        name: 'column_b',
        label: 'Second Column',
        type: 'column',
        description: 'Second column in the relationship',
        required: true,
      },
      {
        name: 'relationship',
        label: 'Relationship Type',
        type: 'select',
        description: 'Expected relationship between columns',
        required: true,
        options: [
          { value: 'equal', label: 'Equal' },
          { value: 'not_equal', label: 'Not Equal' },
          { value: 'greater', label: 'A > B' },
          { value: 'less', label: 'A < B' },
          { value: 'greater_equal', label: 'A >= B' },
          { value: 'less_equal', label: 'A <= B' },
        ],
      },
    ],
    tags: ['schema', 'relationship', 'comparison'],
    severity_default: 'medium',
  },
  {
    name: 'MultiColumnUnique',
    display_name: 'Multi-Column Unique',
    category: 'schema',
    description: 'Ensures uniqueness across a combination of columns (composite key).',
    parameters: [
      {
        name: 'columns',
        label: 'Composite Key Columns',
        type: 'column_list',
        description: 'Columns that form the composite unique key',
        required: true,
      },
    ],
    tags: ['schema', 'uniqueness', 'composite', 'key'],
    severity_default: 'critical',
  },
  {
    name: 'ReferentialIntegrity',
    display_name: 'Referential Integrity',
    category: 'schema',
    description: 'Validates foreign key relationships between tables.',
    parameters: [
      {
        name: 'column',
        label: 'Foreign Key Column',
        type: 'column',
        description: 'Foreign key column in the current table',
        required: true,
      },
      {
        name: 'reference_source_id',
        label: 'Reference Source',
        type: 'string',
        description: 'ID of the source containing the reference table',
        required: true,
      },
      {
        name: 'reference_column',
        label: 'Reference Column',
        type: 'string',
        description: 'Primary key column in the reference table',
        required: true,
      },
    ],
    tags: ['schema', 'foreign_key', 'relationship', 'integrity'],
    severity_default: 'critical',
  },
  {
    name: 'MultiColumnSum',
    display_name: 'Multi-Column Sum',
    category: 'schema',
    description: 'Validates that the sum of specified columns equals an expected value.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns to Sum',
        type: 'column_list',
        description: 'Columns whose values should be summed',
        required: true,
      },
      {
        name: 'expected_sum',
        label: 'Expected Sum',
        type: 'float',
        description: 'Expected sum value',
        required: true,
      },
      {
        name: 'tolerance',
        label: 'Tolerance',
        type: 'float',
        description: 'Acceptable tolerance for floating point comparison',
        default: 0.0001,
        min_value: 0,
      },
    ],
    tags: ['schema', 'arithmetic', 'sum', 'calculation'],
    severity_default: 'medium',
  },
  {
    name: 'MultiColumnCalculation',
    display_name: 'Multi-Column Calculation',
    category: 'schema',
    description: 'Validates arbitrary arithmetic relationships between columns.',
    parameters: [
      {
        name: 'expression',
        label: 'Expression',
        type: 'expression',
        description: "Mathematical expression (e.g., 'price * quantity == total')",
        required: true,
        placeholder: 'price * quantity == total',
      },
      {
        name: 'tolerance',
        label: 'Tolerance',
        type: 'float',
        description: 'Acceptable tolerance for comparison',
        default: 0.0001,
        min_value: 0,
      },
    ],
    tags: ['schema', 'arithmetic', 'expression', 'calculation'],
    severity_default: 'medium',
  },
  {
    name: 'ColumnPairInSet',
    display_name: 'Column Pair In Set',
    category: 'schema',
    description: 'Validates that column value pairs exist within a predefined set.',
    parameters: [
      {
        name: 'column_a',
        label: 'First Column',
        type: 'column',
        required: true,
      },
      {
        name: 'column_b',
        label: 'Second Column',
        type: 'column',
        required: true,
      },
      {
        name: 'valid_pairs',
        label: 'Valid Pairs',
        type: 'schema',
        description: 'JSON array of valid [a, b] pairs',
        required: true,
        placeholder: '[["US", "USD"], ["UK", "GBP"], ["EU", "EUR"]]',
      },
    ],
    tags: ['schema', 'pair', 'set', 'validation'],
    severity_default: 'medium',
  },
  {
    name: 'ColumnPairNotInSet',
    display_name: 'Column Pair Not In Set',
    category: 'schema',
    description: 'Ensures column value pairs do not exist within a forbidden set.',
    parameters: [
      {
        name: 'column_a',
        label: 'First Column',
        type: 'column',
        required: true,
      },
      {
        name: 'column_b',
        label: 'Second Column',
        type: 'column',
        required: true,
      },
      {
        name: 'forbidden_pairs',
        label: 'Forbidden Pairs',
        type: 'schema',
        description: 'JSON array of forbidden [a, b] pairs',
        required: true,
      },
    ],
    tags: ['schema', 'pair', 'set', 'forbidden'],
    severity_default: 'high',
  },
]

// Completeness Validators (7 validators)
const COMPLETENESS_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'Null',
    display_name: 'Null Values',
    category: 'completeness',
    description: 'Detects and reports null values within specified columns.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Target columns (leave empty for all columns)',
      },
      {
        name: 'mostly',
        label: 'Mostly (Threshold)',
        type: 'float',
        description:
          'Acceptable non-null ratio (0.0-1.0). E.g., 0.95 means 5% nulls allowed.',
        min_value: 0,
        max_value: 1,
        placeholder: '0.95',
      },
    ],
    tags: ['completeness', 'null', 'missing'],
    severity_default: 'high',
  },
  {
    name: 'NotNull',
    display_name: 'Not Null',
    category: 'completeness',
    description: 'Ensures the specified column contains no null values.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        description: 'Column that must not contain nulls',
        required: true,
      },
    ],
    tags: ['completeness', 'null', 'required'],
    severity_default: 'critical',
  },
  {
    name: 'CompletenessRatio',
    display_name: 'Completeness Ratio',
    category: 'completeness',
    description: 'Validates that the completeness ratio meets a minimum threshold.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_ratio',
        label: 'Minimum Ratio',
        type: 'float',
        description: 'Minimum completeness ratio (0.0-1.0)',
        required: true,
        min_value: 0,
        max_value: 1,
        default: 0.95,
      },
    ],
    tags: ['completeness', 'ratio', 'threshold'],
    severity_default: 'medium',
  },
  {
    name: 'EmptyString',
    display_name: 'Empty String',
    category: 'completeness',
    description: 'Detects empty strings in string columns.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Target string columns (leave empty for all string columns)',
      },
    ],
    tags: ['completeness', 'empty', 'string'],
    severity_default: 'medium',
  },
  {
    name: 'WhitespaceOnly',
    display_name: 'Whitespace Only',
    category: 'completeness',
    description: 'Identifies values containing only whitespace characters.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Target columns to check',
      },
    ],
    tags: ['completeness', 'whitespace', 'string'],
    severity_default: 'low',
  },
  {
    name: 'ConditionalNull',
    display_name: 'Conditional Null',
    category: 'completeness',
    description: 'Validates null values based on conditional logic.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        description: 'Column to check for nulls',
        required: true,
      },
      {
        name: 'condition',
        label: 'Condition Expression',
        type: 'expression',
        description: 'Polars expression defining when column must not be null',
        required: true,
        placeholder: 'status == "active"',
      },
    ],
    tags: ['completeness', 'conditional', 'null'],
    severity_default: 'high',
  },
  {
    name: 'DefaultValue',
    display_name: 'Default Value Detection',
    category: 'completeness',
    description: 'Detects values matching default or placeholder patterns.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'default_values',
        label: 'Default Values',
        type: 'string_list',
        description: 'Values considered as defaults/placeholders',
        required: true,
        placeholder: 'N/A, TBD, unknown, -1',
      },
    ],
    tags: ['completeness', 'default', 'placeholder'],
    severity_default: 'low',
  },
]

// Uniqueness Validators (13 validators)
const UNIQUENESS_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'Unique',
    display_name: 'Unique',
    category: 'uniqueness',
    description: 'Ensures all values in a column are unique.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'mostly',
        label: 'Mostly (Threshold)',
        type: 'float',
        description: 'Minimum unique ratio (0.0-1.0)',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['uniqueness', 'duplicate', 'distinct'],
    severity_default: 'high',
  },
  {
    name: 'UniqueRatio',
    display_name: 'Unique Ratio',
    category: 'uniqueness',
    description: 'Validates that the unique value ratio falls within a range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_ratio',
        label: 'Minimum Ratio',
        type: 'float',
        min_value: 0,
        max_value: 1,
      },
      {
        name: 'max_ratio',
        label: 'Maximum Ratio',
        type: 'float',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['uniqueness', 'ratio'],
    severity_default: 'medium',
  },
  {
    name: 'DistinctCount',
    display_name: 'Distinct Count',
    category: 'uniqueness',
    description: 'Validates the number of distinct values in a column.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_count',
        label: 'Minimum Count',
        type: 'integer',
        min_value: 0,
      },
      {
        name: 'max_count',
        label: 'Maximum Count',
        type: 'integer',
        min_value: 0,
      },
    ],
    tags: ['uniqueness', 'distinct', 'count'],
    severity_default: 'medium',
  },
  {
    name: 'Duplicate',
    display_name: 'Duplicate Detection',
    category: 'uniqueness',
    description: 'Detects duplicate values within specified columns.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Columns to check for duplicates (leave empty for all)',
      },
    ],
    tags: ['uniqueness', 'duplicate'],
    severity_default: 'high',
  },
  {
    name: 'DuplicateWithinGroup',
    display_name: 'Duplicate Within Group',
    category: 'uniqueness',
    description: 'Detects duplicates within specified groups.',
    parameters: [
      {
        name: 'column',
        label: 'Column to Check',
        type: 'column',
        description: 'Column to check for duplicates',
        required: true,
      },
      {
        name: 'group_by',
        label: 'Group By Columns',
        type: 'column_list',
        description: 'Columns to group by',
        required: true,
      },
    ],
    tags: ['uniqueness', 'duplicate', 'group'],
    severity_default: 'high',
  },
  {
    name: 'PrimaryKey',
    display_name: 'Primary Key',
    category: 'uniqueness',
    description: 'Validates primary key constraints (unique and non-null).',
    parameters: [
      {
        name: 'column',
        label: 'Primary Key Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['uniqueness', 'primary_key', 'constraint'],
    severity_default: 'critical',
  },
  {
    name: 'CompoundKey',
    display_name: 'Compound Key',
    category: 'uniqueness',
    description: 'Validates composite primary key constraints.',
    parameters: [
      {
        name: 'columns',
        label: 'Key Columns',
        type: 'column_list',
        description: 'Columns forming the compound key',
        required: true,
      },
    ],
    tags: ['uniqueness', 'compound_key', 'composite'],
    severity_default: 'critical',
  },
  {
    name: 'DistinctValuesInSet',
    display_name: 'Distinct Values In Set',
    category: 'uniqueness',
    description: 'Ensures all distinct values belong to a specified set.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'value_set',
        label: 'Allowed Values',
        type: 'string_list',
        description: 'Set of allowed values',
        required: true,
      },
    ],
    tags: ['uniqueness', 'set', 'enum'],
    severity_default: 'medium',
  },
  {
    name: 'DistinctValuesEqualSet',
    display_name: 'Distinct Values Equal Set',
    category: 'uniqueness',
    description: 'Validates that distinct values exactly match a specified set.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'value_set',
        label: 'Expected Values',
        type: 'string_list',
        description: 'Exact set of expected values',
        required: true,
      },
    ],
    tags: ['uniqueness', 'set', 'exact'],
    severity_default: 'medium',
  },
  {
    name: 'DistinctValuesContainSet',
    display_name: 'Distinct Values Contain Set',
    category: 'uniqueness',
    description: 'Ensures distinct values contain all elements of a specified set.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'required_values',
        label: 'Required Values',
        type: 'string_list',
        description: 'Values that must be present',
        required: true,
      },
    ],
    tags: ['uniqueness', 'set', 'contains'],
    severity_default: 'medium',
  },
  {
    name: 'DistinctCountBetween',
    display_name: 'Distinct Count Between',
    category: 'uniqueness',
    description: 'Validates that distinct count falls within a range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_count',
        label: 'Minimum Count',
        type: 'integer',
        required: true,
        min_value: 0,
      },
      {
        name: 'max_count',
        label: 'Maximum Count',
        type: 'integer',
        required: true,
        min_value: 0,
      },
    ],
    tags: ['uniqueness', 'distinct', 'range'],
    severity_default: 'medium',
  },
  {
    name: 'UniqueWithinRecord',
    display_name: 'Unique Within Record',
    category: 'uniqueness',
    description: 'Ensures specified columns have unique values within each record.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Columns to compare within each row',
        required: true,
      },
    ],
    tags: ['uniqueness', 'row', 'record'],
    severity_default: 'medium',
  },
  {
    name: 'AllColumnsUniqueWithinRecord',
    display_name: 'All Columns Unique Within Record',
    category: 'uniqueness',
    description: 'Validates that all values within each record are unique.',
    parameters: [
      {
        name: 'columns',
        label: 'Columns',
        type: 'column_list',
        description: 'Columns to check (leave empty for all)',
      },
    ],
    tags: ['uniqueness', 'row', 'all'],
    severity_default: 'low',
  },
]

// Distribution Validators (15 validators)
const DISTRIBUTION_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'Between',
    display_name: 'Value Between',
    category: 'distribution',
    description: 'Validates that values fall within a specified range (inclusive).',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Value',
        type: 'float',
        required: true,
      },
      {
        name: 'max_value',
        label: 'Maximum Value',
        type: 'float',
        required: true,
      },
      {
        name: 'mostly',
        label: 'Mostly (Threshold)',
        type: 'float',
        description: 'Acceptable pass ratio (0.0-1.0)',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['distribution', 'range', 'bounds'],
    severity_default: 'medium',
  },
  {
    name: 'Range',
    display_name: 'Range',
    category: 'distribution',
    description: 'Validates value ranges with optional inclusivity control.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Value',
        type: 'float',
      },
      {
        name: 'max_value',
        label: 'Maximum Value',
        type: 'float',
      },
      {
        name: 'inclusive_min',
        label: 'Include Minimum',
        type: 'boolean',
        default: true,
      },
      {
        name: 'inclusive_max',
        label: 'Include Maximum',
        type: 'boolean',
        default: true,
      },
    ],
    tags: ['distribution', 'range', 'bounds'],
    severity_default: 'medium',
  },
  {
    name: 'Positive',
    display_name: 'Positive Values',
    category: 'distribution',
    description: 'Ensures all values are strictly positive (> 0).',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['distribution', 'positive', 'numeric'],
    severity_default: 'high',
  },
  {
    name: 'NonNegative',
    display_name: 'Non-Negative Values',
    category: 'distribution',
    description: 'Ensures all values are non-negative (>= 0).',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['distribution', 'non-negative', 'numeric'],
    severity_default: 'high',
  },
  {
    name: 'InSet',
    display_name: 'In Set',
    category: 'distribution',
    description: 'Validates that values belong to a predefined set.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'value_set',
        label: 'Allowed Values',
        type: 'string_list',
        description: 'Set of allowed values',
        required: true,
      },
      {
        name: 'mostly',
        label: 'Mostly (Threshold)',
        type: 'float',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['distribution', 'set', 'enum'],
    severity_default: 'medium',
  },
  {
    name: 'NotInSet',
    display_name: 'Not In Set',
    category: 'distribution',
    description: 'Ensures values do not belong to a forbidden set.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'forbidden_set',
        label: 'Forbidden Values',
        type: 'string_list',
        description: 'Set of forbidden values',
        required: true,
      },
    ],
    tags: ['distribution', 'set', 'forbidden'],
    severity_default: 'high',
  },
  {
    name: 'Increasing',
    display_name: 'Increasing',
    category: 'distribution',
    description: 'Validates that values are monotonically increasing.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'strict',
        label: 'Strictly Increasing',
        type: 'boolean',
        description: 'If true, values must be strictly increasing (no equal values)',
        default: false,
      },
    ],
    tags: ['distribution', 'monotonic', 'increasing'],
    severity_default: 'medium',
  },
  {
    name: 'Decreasing',
    display_name: 'Decreasing',
    category: 'distribution',
    description: 'Validates that values are monotonically decreasing.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'strict',
        label: 'Strictly Decreasing',
        type: 'boolean',
        default: false,
      },
    ],
    tags: ['distribution', 'monotonic', 'decreasing'],
    severity_default: 'medium',
  },
  {
    name: 'Outlier',
    display_name: 'Outlier (IQR)',
    category: 'distribution',
    description: 'Detects statistical outliers using the IQR method.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'iqr_multiplier',
        label: 'IQR Multiplier',
        type: 'float',
        description: 'Multiplier for IQR (1.5 = standard, 3.0 = extreme)',
        default: 1.5,
        min_value: 0,
      },
    ],
    tags: ['distribution', 'outlier', 'iqr', 'anomaly'],
    severity_default: 'medium',
  },
  {
    name: 'ZScoreOutlier',
    display_name: 'Outlier (Z-Score)',
    category: 'distribution',
    description: 'Detects outliers using Z-score methodology.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'threshold',
        label: 'Z-Score Threshold',
        type: 'float',
        description: 'Z-score threshold (default: 3.0)',
        default: 3.0,
        min_value: 0,
      },
    ],
    tags: ['distribution', 'outlier', 'zscore', 'anomaly'],
    severity_default: 'medium',
  },
  {
    name: 'Quantile',
    display_name: 'Quantile',
    category: 'distribution',
    description: 'Validates that values fall within specified quantile bounds.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'quantile',
        label: 'Quantile',
        type: 'float',
        description: 'Quantile value (0.0-1.0, e.g., 0.95 for 95th percentile)',
        required: true,
        min_value: 0,
        max_value: 1,
      },
      {
        name: 'max_value',
        label: 'Maximum Value at Quantile',
        type: 'float',
        description: 'Maximum allowed value at the specified quantile',
        required: true,
      },
    ],
    tags: ['distribution', 'quantile', 'percentile'],
    severity_default: 'medium',
  },
  {
    name: 'Distribution',
    display_name: 'Distribution',
    category: 'distribution',
    description: 'Validates that data follows an expected distribution pattern.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'distribution',
        label: 'Expected Distribution',
        type: 'select',
        description: 'Expected distribution type',
        required: true,
        options: [
          { value: 'normal', label: 'Normal (Gaussian)' },
          { value: 'uniform', label: 'Uniform' },
          { value: 'exponential', label: 'Exponential' },
          { value: 'poisson', label: 'Poisson' },
          { value: 'binomial', label: 'Binomial' },
        ],
      },
    ],
    tags: ['distribution', 'statistical', 'pattern'],
    severity_default: 'low',
  },
  {
    name: 'KLDivergence',
    display_name: 'KL Divergence',
    category: 'distribution',
    description: 'Validates distribution similarity using Kullback-Leibler divergence.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'reference_distribution',
        label: 'Reference Distribution',
        type: 'schema',
        description: 'Reference probability distribution as JSON',
        required: true,
        placeholder: '{"A": 0.5, "B": 0.3, "C": 0.2}',
      },
      {
        name: 'threshold',
        label: 'Threshold',
        type: 'float',
        description: 'Maximum allowed KL divergence',
        required: true,
        default: 0.1,
        min_value: 0,
      },
    ],
    tags: ['distribution', 'kl', 'divergence', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'ChiSquare',
    display_name: 'Chi-Square Test',
    category: 'distribution',
    description: 'Performs chi-square goodness-of-fit testing.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'expected_frequencies',
        label: 'Expected Frequencies',
        type: 'schema',
        description: 'Expected frequency distribution as JSON',
        required: true,
      },
      {
        name: 'alpha',
        label: 'Significance Level',
        type: 'float',
        description: 'Significance level (default: 0.05)',
        default: 0.05,
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['distribution', 'chi-square', 'statistical', 'test'],
    severity_default: 'medium',
  },
  {
    name: 'MostCommonValue',
    display_name: 'Most Common Value',
    category: 'distribution',
    description: 'Validates the most common value and its frequency.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'expected_value',
        label: 'Expected Most Common Value',
        type: 'string',
      },
      {
        name: 'min_frequency',
        label: 'Minimum Frequency',
        type: 'float',
        description: 'Minimum frequency ratio (0.0-1.0)',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['distribution', 'frequency', 'mode'],
    severity_default: 'low',
  },
]

// String Validators (17 validators)
const STRING_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'Regex',
    display_name: 'Regex Pattern',
    category: 'string',
    description: 'Validates strings against a regular expression pattern.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'pattern',
        label: 'Regex Pattern',
        type: 'regex',
        description: 'Regular expression pattern',
        required: true,
        placeholder: '^[A-Z]{2,3}-\\d{4}$',
      },
      {
        name: 'mostly',
        label: 'Mostly (Threshold)',
        type: 'float',
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['string', 'regex', 'pattern'],
    severity_default: 'medium',
  },
  {
    name: 'RegexList',
    display_name: 'Regex List',
    category: 'string',
    description: 'Validates against multiple regex patterns (any match passes).',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'patterns',
        label: 'Patterns',
        type: 'string_list',
        description: 'List of regex patterns (any match is valid)',
        required: true,
      },
    ],
    tags: ['string', 'regex', 'pattern', 'list'],
    severity_default: 'medium',
  },
  {
    name: 'NotMatchRegex',
    display_name: 'Not Match Regex',
    category: 'string',
    description: 'Ensures values do not match a specified pattern.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'pattern',
        label: 'Forbidden Pattern',
        type: 'regex',
        required: true,
      },
    ],
    tags: ['string', 'regex', 'forbidden'],
    severity_default: 'high',
  },
  {
    name: 'Length',
    display_name: 'String Length',
    category: 'string',
    description: 'Validates string length constraints.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_length',
        label: 'Minimum Length',
        type: 'integer',
        min_value: 0,
      },
      {
        name: 'max_length',
        label: 'Maximum Length',
        type: 'integer',
        min_value: 0,
      },
    ],
    tags: ['string', 'length', 'size'],
    severity_default: 'medium',
  },
  {
    name: 'Email',
    display_name: 'Email Format',
    category: 'string',
    description: 'Validates email address format using RFC 5322 patterns.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'email', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'Url',
    display_name: 'URL Format',
    category: 'string',
    description: 'Validates URL format.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'url', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'Phone',
    display_name: 'Phone Number',
    category: 'string',
    description: 'Validates phone number format with international support.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'country_code',
        label: 'Country Code',
        type: 'string',
        description: "Expected country code (e.g., 'US', 'KR')",
        placeholder: 'US',
      },
    ],
    tags: ['string', 'phone', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'Uuid',
    display_name: 'UUID Format',
    category: 'string',
    description: 'Validates UUID format (versions 1-5).',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'uuid', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'IpAddress',
    display_name: 'IP Address',
    category: 'string',
    description: 'Validates IPv4 and IPv6 address formats.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'version',
        label: 'IP Version',
        type: 'select',
        description: 'IP version to validate',
        options: [
          { value: '', label: 'Any (IPv4 or IPv6)' },
          { value: '4', label: 'IPv4 only' },
          { value: '6', label: 'IPv6 only' },
        ],
      },
    ],
    tags: ['string', 'ip', 'network', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'Format',
    display_name: 'Common Format',
    category: 'string',
    description: 'Validates common format types.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'format_type',
        label: 'Format Type',
        type: 'select',
        required: true,
        options: [
          { value: 'email', label: 'Email' },
          { value: 'url', label: 'URL' },
          { value: 'phone', label: 'Phone' },
          { value: 'uuid', label: 'UUID' },
          { value: 'ipv4', label: 'IPv4' },
          { value: 'ipv6', label: 'IPv6' },
          { value: 'credit_card', label: 'Credit Card' },
          { value: 'ssn', label: 'SSN' },
        ],
      },
    ],
    tags: ['string', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'JsonParseable',
    display_name: 'JSON Parseable',
    category: 'string',
    description: 'Ensures string values are valid JSON.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'json', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'JsonSchema',
    display_name: 'JSON Schema',
    category: 'string',
    description: 'Validates JSON strings against a JSON Schema.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'schema',
        label: 'JSON Schema',
        type: 'schema',
        description: 'JSON Schema specification',
        required: true,
      },
    ],
    tags: ['string', 'json', 'schema'],
    severity_default: 'medium',
  },
  {
    name: 'Alphanumeric',
    display_name: 'Alphanumeric',
    category: 'string',
    description: 'Ensures values contain only alphanumeric characters.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'alphanumeric', 'characters'],
    severity_default: 'low',
  },
  {
    name: 'ConsistentCasing',
    display_name: 'Consistent Casing',
    category: 'string',
    description: 'Validates consistent casing patterns.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'casing',
        label: 'Casing Style',
        type: 'select',
        required: true,
        options: [
          { value: 'lower', label: 'lowercase' },
          { value: 'upper', label: 'UPPERCASE' },
          { value: 'title', label: 'Title Case' },
          { value: 'snake', label: 'snake_case' },
          { value: 'camel', label: 'camelCase' },
          { value: 'pascal', label: 'PascalCase' },
          { value: 'kebab', label: 'kebab-case' },
        ],
      },
    ],
    tags: ['string', 'casing', 'style'],
    severity_default: 'low',
  },
  {
    name: 'LikePattern',
    display_name: 'LIKE Pattern',
    category: 'string',
    description: 'SQL LIKE pattern matching with % and _ wildcards.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'pattern',
        label: 'LIKE Pattern',
        type: 'string',
        description: 'SQL LIKE pattern (use % for any, _ for single char)',
        required: true,
        placeholder: 'PRD-%',
      },
    ],
    tags: ['string', 'like', 'sql', 'pattern'],
    severity_default: 'medium',
  },
  {
    name: 'NotLikePattern',
    display_name: 'Not LIKE Pattern',
    category: 'string',
    description: 'Ensures values do not match a LIKE pattern.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'pattern',
        label: 'Forbidden LIKE Pattern',
        type: 'string',
        required: true,
      },
    ],
    tags: ['string', 'like', 'forbidden'],
    severity_default: 'high',
  },
  {
    name: 'DateutilParseable',
    display_name: 'Date Parseable',
    category: 'string',
    description: 'Validates that strings can be parsed as dates.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['string', 'date', 'parseable'],
    severity_default: 'medium',
  },
]

// Datetime Validators (10 validators)
const DATETIME_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'DateFormat',
    display_name: 'Date Format',
    category: 'datetime',
    description: 'Validates date/datetime format.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'format',
        label: 'Date Format',
        type: 'string',
        description: 'Expected strptime format',
        required: true,
        placeholder: '%Y-%m-%d',
      },
    ],
    tags: ['datetime', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'DateBetween',
    display_name: 'Date Between',
    category: 'datetime',
    description: 'Validates dates within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_date',
        label: 'Minimum Date',
        type: 'string',
        description: 'Minimum date (YYYY-MM-DD)',
        placeholder: '2020-01-01',
      },
      {
        name: 'max_date',
        label: 'Maximum Date',
        type: 'string',
        description: 'Maximum date (YYYY-MM-DD)',
        placeholder: '2025-12-31',
      },
    ],
    tags: ['datetime', 'range', 'bounds'],
    severity_default: 'medium',
  },
  {
    name: 'FutureDate',
    display_name: 'Future Date',
    category: 'datetime',
    description: 'Ensures dates are in the future.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['datetime', 'future'],
    severity_default: 'medium',
  },
  {
    name: 'PastDate',
    display_name: 'Past Date',
    category: 'datetime',
    description: 'Ensures dates are in the past.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['datetime', 'past'],
    severity_default: 'medium',
  },
  {
    name: 'DateOrder',
    display_name: 'Date Order',
    category: 'datetime',
    description: 'Validates chronological ordering between date columns.',
    parameters: [
      {
        name: 'start_column',
        label: 'Start Date Column',
        type: 'column',
        required: true,
      },
      {
        name: 'end_column',
        label: 'End Date Column',
        type: 'column',
        required: true,
      },
    ],
    tags: ['datetime', 'order', 'chronological'],
    severity_default: 'high',
  },
  {
    name: 'Timezone',
    display_name: 'Timezone',
    category: 'datetime',
    description: 'Validates timezone-aware datetime values.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'expected_timezone',
        label: 'Expected Timezone',
        type: 'string',
        description: "Expected timezone (e.g., 'UTC', 'America/New_York')",
        placeholder: 'UTC',
      },
    ],
    tags: ['datetime', 'timezone'],
    severity_default: 'low',
  },
  {
    name: 'RecentData',
    display_name: 'Recent Data',
    category: 'datetime',
    description: 'Ensures data contains recent entries.',
    parameters: [
      {
        name: 'column',
        label: 'Datetime Column',
        type: 'column',
        required: true,
      },
      {
        name: 'max_age_days',
        label: 'Maximum Age (Days)',
        type: 'integer',
        description: 'Maximum age in days',
        required: true,
        min_value: 1,
      },
    ],
    tags: ['datetime', 'recent', 'freshness'],
    severity_default: 'high',
  },
  {
    name: 'DatePartCoverage',
    display_name: 'Date Part Coverage',
    category: 'datetime',
    description: 'Validates coverage across date parts.',
    parameters: [
      {
        name: 'column',
        label: 'Datetime Column',
        type: 'column',
        required: true,
      },
      {
        name: 'date_part',
        label: 'Date Part',
        type: 'select',
        required: true,
        options: [
          { value: 'day', label: 'Day of Month' },
          { value: 'weekday', label: 'Day of Week' },
          { value: 'month', label: 'Month' },
          { value: 'hour', label: 'Hour' },
          { value: 'quarter', label: 'Quarter' },
        ],
      },
      {
        name: 'min_coverage',
        label: 'Minimum Coverage',
        type: 'float',
        description: 'Minimum coverage ratio (0.0-1.0)',
        required: true,
        min_value: 0,
        max_value: 1,
      },
    ],
    tags: ['datetime', 'coverage', 'completeness'],
    severity_default: 'medium',
  },
  {
    name: 'GroupedRecentData',
    display_name: 'Grouped Recent Data',
    category: 'datetime',
    description: 'Validates recency within groups.',
    parameters: [
      {
        name: 'datetime_column',
        label: 'Datetime Column',
        type: 'column',
        required: true,
      },
      {
        name: 'group_column',
        label: 'Group Column',
        type: 'column',
        required: true,
      },
      {
        name: 'max_age_days',
        label: 'Maximum Age (Days)',
        type: 'integer',
        description: 'Maximum age per group in days',
        required: true,
        min_value: 1,
      },
    ],
    tags: ['datetime', 'recent', 'group'],
    severity_default: 'high',
  },
  {
    name: 'TimeSeriesGap',
    display_name: 'Time Series Gap',
    category: 'datetime',
    description: 'Detects gaps in time series data.',
    parameters: [
      {
        name: 'column',
        label: 'Datetime Column',
        type: 'column',
        required: true,
      },
      {
        name: 'expected_interval',
        label: 'Expected Interval',
        type: 'select',
        description: 'Expected time interval between records',
        required: true,
        options: [
          { value: '1h', label: 'Hourly' },
          { value: '1d', label: 'Daily' },
          { value: '1w', label: 'Weekly' },
          { value: '1M', label: 'Monthly' },
        ],
      },
      {
        name: 'max_gap_multiplier',
        label: 'Max Gap Multiplier',
        type: 'float',
        description: 'Maximum allowed gap as multiple of expected interval',
        default: 2.0,
        min_value: 1,
      },
    ],
    tags: ['datetime', 'timeseries', 'gap'],
    severity_default: 'high',
  },
]

// Aggregate Validators (8 validators)
const AGGREGATE_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'MeanBetween',
    display_name: 'Mean Between',
    category: 'aggregate',
    description: 'Validates that the column mean falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Mean',
        type: 'float',
        description: 'Minimum acceptable mean value',
      },
      {
        name: 'max_value',
        label: 'Maximum Mean',
        type: 'float',
        description: 'Maximum acceptable mean value',
      },
    ],
    tags: ['aggregate', 'mean', 'average', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'MedianBetween',
    display_name: 'Median Between',
    category: 'aggregate',
    description: 'Validates that the column median falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Median',
        type: 'float',
        description: 'Minimum acceptable median value',
      },
      {
        name: 'max_value',
        label: 'Maximum Median',
        type: 'float',
        description: 'Maximum acceptable median value',
      },
    ],
    tags: ['aggregate', 'median', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'StdBetween',
    display_name: 'Standard Deviation Between',
    category: 'aggregate',
    description:
      'Validates that the column standard deviation falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Std Dev',
        type: 'float',
        description: 'Minimum acceptable standard deviation',
        min_value: 0,
      },
      {
        name: 'max_value',
        label: 'Maximum Std Dev',
        type: 'float',
        description: 'Maximum acceptable standard deviation',
        min_value: 0,
      },
    ],
    tags: ['aggregate', 'std', 'standard_deviation', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'VarianceBetween',
    display_name: 'Variance Between',
    category: 'aggregate',
    description: 'Validates that the column variance falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Variance',
        type: 'float',
        description: 'Minimum acceptable variance',
        min_value: 0,
      },
      {
        name: 'max_value',
        label: 'Maximum Variance',
        type: 'float',
        description: 'Maximum acceptable variance',
        min_value: 0,
      },
    ],
    tags: ['aggregate', 'variance', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'SumBetween',
    display_name: 'Sum Between',
    category: 'aggregate',
    description: 'Validates that the column sum falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum Sum',
        type: 'float',
        description: 'Minimum acceptable sum value',
      },
      {
        name: 'max_value',
        label: 'Maximum Sum',
        type: 'float',
        description: 'Maximum acceptable sum value',
      },
    ],
    tags: ['aggregate', 'sum', 'total', 'statistical'],
    severity_default: 'medium',
  },
  {
    name: 'MinBetween',
    display_name: 'Min Value Between',
    category: 'aggregate',
    description:
      'Validates that the column minimum value falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum of Min',
        type: 'float',
        description: 'Lower bound for the column minimum',
      },
      {
        name: 'max_value',
        label: 'Maximum of Min',
        type: 'float',
        description: 'Upper bound for the column minimum',
      },
    ],
    tags: ['aggregate', 'min', 'minimum', 'bounds'],
    severity_default: 'medium',
  },
  {
    name: 'MaxBetween',
    display_name: 'Max Value Between',
    category: 'aggregate',
    description:
      'Validates that the column maximum value falls within a specified range.',
    parameters: [
      {
        name: 'column',
        label: 'Column',
        type: 'column',
        required: true,
      },
      {
        name: 'min_value',
        label: 'Minimum of Max',
        type: 'float',
        description: 'Lower bound for the column maximum',
      },
      {
        name: 'max_value',
        label: 'Maximum of Max',
        type: 'float',
        description: 'Upper bound for the column maximum',
      },
    ],
    tags: ['aggregate', 'max', 'maximum', 'bounds'],
    severity_default: 'medium',
  },
  {
    name: 'CountBetween',
    display_name: 'Count Between',
    category: 'aggregate',
    description: 'Validates that the row count falls within a specified range.',
    parameters: [
      {
        name: 'min_count',
        label: 'Minimum Count',
        type: 'integer',
        description: 'Minimum acceptable row count',
        min_value: 0,
      },
      {
        name: 'max_count',
        label: 'Maximum Count',
        type: 'integer',
        description: 'Maximum acceptable row count',
        min_value: 0,
      },
    ],
    tags: ['aggregate', 'count', 'rows'],
    severity_default: 'medium',
  },
]

// =============================================================================
// Import New Validator Categories from Factory
// =============================================================================

import {
  CROSS_TABLE_VALIDATORS,
  MULTI_COLUMN_VALIDATORS,
  DRIFT_VALIDATORS,
  ANOMALY_VALIDATORS,
  PRIVACY_VALIDATORS,
  TABLE_VALIDATORS,
  QUERY_VALIDATORS,
  GEOSPATIAL_VALIDATORS,
} from '../factories/validators'

// =============================================================================
// Combined Validator Registry
// =============================================================================

const MOCK_VALIDATORS: ValidatorDefinition[] = [
  ...SCHEMA_VALIDATORS,
  ...COMPLETENESS_VALIDATORS,
  ...UNIQUENESS_VALIDATORS,
  ...DISTRIBUTION_VALIDATORS,
  ...STRING_VALIDATORS,
  ...DATETIME_VALIDATORS,
  ...AGGREGATE_VALIDATORS,
  ...CROSS_TABLE_VALIDATORS,
  ...MULTI_COLUMN_VALIDATORS,
  ...DRIFT_VALIDATORS,
  ...ANOMALY_VALIDATORS,
  ...PRIVACY_VALIDATORS,
  ...TABLE_VALIDATORS,
  ...QUERY_VALIDATORS,
  ...GEOSPATIAL_VALIDATORS,
]

// =============================================================================
// Category Labels with Metadata
// =============================================================================

const CATEGORY_LABELS: { value: ValidatorCategory; label: string; description: string; icon?: string; color?: string; requires_extra?: string }[] = [
  { value: 'schema', label: 'Schema', description: 'Validate structure, columns, and data types', icon: 'layout', color: '#3b82f6' },
  { value: 'completeness', label: 'Completeness', description: 'Check for null values and missing data', icon: 'check-circle', color: '#22c55e' },
  { value: 'uniqueness', label: 'Uniqueness', description: 'Detect duplicates and validate keys', icon: 'fingerprint', color: '#8b5cf6' },
  { value: 'distribution', label: 'Distribution', description: 'Validate value ranges and distributions', icon: 'bar-chart', color: '#f59e0b' },
  { value: 'string', label: 'String', description: 'Pattern matching and format validation', icon: 'type', color: '#06b6d4' },
  { value: 'datetime', label: 'Datetime', description: 'Date/time format and range validation', icon: 'calendar', color: '#ec4899' },
  { value: 'aggregate', label: 'Aggregate', description: 'Statistical aggregate checks', icon: 'calculator', color: '#6366f1' },
  { value: 'cross_table', label: 'Cross-Table', description: 'Multi-table relationships and foreign keys', icon: 'link', color: '#14b8a6' },
  { value: 'multi_column', label: 'Multi-Column', description: 'Column relationships and calculations', icon: 'columns', color: '#84cc16' },
  { value: 'query', label: 'Query', description: 'Expression-based custom validation', icon: 'code', color: '#a855f7' },
  { value: 'table', label: 'Table', description: 'Table metadata and structure validation', icon: 'table', color: '#0ea5e9' },
  { value: 'geospatial', label: 'Geospatial', description: 'Geographic coordinate validation', icon: 'map-pin', color: '#10b981' },
  { value: 'drift', label: 'Drift', description: 'Distribution change detection', icon: 'trending-up', color: '#ef4444', requires_extra: 'drift' },
  { value: 'anomaly', label: 'Anomaly', description: 'ML-based outlier detection', icon: 'alert-triangle', color: '#f97316', requires_extra: 'anomaly' },
  { value: 'privacy', label: 'Privacy', description: 'PII detection and compliance', icon: 'shield', color: '#dc2626' },
]

// =============================================================================
// Unified Validator Types
// =============================================================================

type ValidatorSource = 'builtin' | 'custom'

interface UnifiedValidatorDefinition {
  id: string | null
  name: string
  display_name: string
  category: string
  description: string
  parameters: ValidatorDefinition['parameters']
  tags: string[]
  severity_default: 'low' | 'medium' | 'high' | 'critical'
  source: ValidatorSource
  is_enabled: boolean
  requires_extra: string | null
  experimental: boolean
  deprecated: boolean
  usage_count: number
  is_verified: boolean
}

interface UnifiedValidatorListResponse {
  data: UnifiedValidatorDefinition[]
  total: number
  builtin_count: number
  custom_count: number
  categories: Array<{
    name: string
    label: string
    builtin_count: number
    custom_count: number
    total: number
  }>
}

// Convert builtin validators to unified format
function toUnifiedValidator(v: ValidatorDefinition): UnifiedValidatorDefinition {
  return {
    id: null,
    name: v.name,
    display_name: v.display_name,
    category: v.category,
    description: v.description,
    parameters: v.parameters,
    tags: v.tags,
    severity_default: v.severity_default,
    source: 'builtin',
    is_enabled: true,
    requires_extra: v.requires_extra || null,
    experimental: v.experimental || false,
    deprecated: v.deprecated || false,
    usage_count: 0,
    is_verified: true,
  }
}

// =============================================================================
// Handlers
// =============================================================================

export const validatorsHandlers = [
  // GET /api/v1/validators - List all validators (builtin only)
  http.get('/api/v1/validators', ({ request }) => {
    const url = new URL(request.url)
    const category = url.searchParams.get('category') as ValidatorCategory | null
    const search = url.searchParams.get('search')

    let result = [...MOCK_VALIDATORS]

    // Filter by category
    if (category) {
      result = result.filter((v) => v.category === category)
    }

    // Filter by search
    if (search) {
      const query = search.toLowerCase()
      result = result.filter(
        (v) =>
          v.name.toLowerCase().includes(query) ||
          v.display_name.toLowerCase().includes(query) ||
          v.description.toLowerCase().includes(query) ||
          v.tags.some((t) => t.toLowerCase().includes(query))
      )
    }

    return HttpResponse.json(result)
  }),

  // GET /api/v1/validators/unified - List all validators (builtin + custom)
  http.get('/api/v1/validators/unified', ({ request }) => {
    const url = new URL(request.url)
    const category = url.searchParams.get('category')
    const source = url.searchParams.get('source') as ValidatorSource | null
    const search = url.searchParams.get('search')
    const enabledOnly = url.searchParams.get('enabled_only') === 'true'
    const offset = parseInt(url.searchParams.get('offset') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '100')

    // Get builtin validators
    let builtinValidators: UnifiedValidatorDefinition[] = []
    if (!source || source === 'builtin') {
      builtinValidators = MOCK_VALIDATORS.map(toUnifiedValidator)
    }

    // Get custom validators from mock store (import from plugins handler)
    let customValidators: UnifiedValidatorDefinition[] = []
    if (!source || source === 'custom') {
      // Import custom validators from the store
      const { mockStore } = require('../data/store')
      const customFromStore = mockStore.customValidators || []
      customValidators = customFromStore.map((cv: { id: string; name: string; display_name: string; category: string; description: string; parameters?: unknown[]; tags?: string[]; severity?: string; is_enabled: boolean; is_verified: boolean; usage_count: number }) => ({
        id: cv.id,
        name: `custom:${cv.name}`,
        display_name: cv.display_name,
        category: cv.category,
        description: cv.description,
        parameters: cv.parameters || [],
        tags: cv.tags || [],
        severity_default: cv.severity || 'medium',
        source: 'custom' as const,
        is_enabled: cv.is_enabled,
        requires_extra: null,
        experimental: false,
        deprecated: false,
        usage_count: cv.usage_count || 0,
        is_verified: cv.is_verified || false,
      }))
    }

    // Combine
    let allValidators = [...builtinValidators, ...customValidators]

    // Filter by category
    if (category) {
      allValidators = allValidators.filter((v) => v.category === category)
    }

    // Filter by enabled
    if (enabledOnly) {
      allValidators = allValidators.filter((v) => v.is_enabled)
    }

    // Filter by search
    if (search) {
      const query = search.toLowerCase()
      allValidators = allValidators.filter(
        (v) =>
          v.name.toLowerCase().includes(query) ||
          v.display_name.toLowerCase().includes(query) ||
          v.description.toLowerCase().includes(query) ||
          v.tags.some((t) => t.toLowerCase().includes(query))
      )
    }

    // Calculate category summary
    const categoryMap = new Map<string, { builtin: number; custom: number }>()
    allValidators.forEach((v) => {
      const counts = categoryMap.get(v.category) || { builtin: 0, custom: 0 }
      if (v.source === 'builtin') {
        counts.builtin++
      } else {
        counts.custom++
      }
      categoryMap.set(v.category, counts)
    })

    const categories = Array.from(categoryMap.entries()).map(([name, counts]) => ({
      name,
      label: name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      builtin_count: counts.builtin,
      custom_count: counts.custom,
      total: counts.builtin + counts.custom,
    })).sort((a, b) => a.name.localeCompare(b.name))

    // Count
    const builtinCount = allValidators.filter((v) => v.source === 'builtin').length
    const customCount = allValidators.filter((v) => v.source === 'custom').length

    // Paginate
    const total = allValidators.length
    const paginated = allValidators.slice(offset, offset + limit)

    const response: UnifiedValidatorListResponse = {
      data: paginated,
      total,
      builtin_count: builtinCount,
      custom_count: customCount,
      categories,
    }

    return HttpResponse.json(response)
  }),

  // GET /api/v1/validators/categories - List all categories
  http.get('/api/v1/validators/categories', () => {
    return HttpResponse.json(CATEGORY_LABELS)
  }),

  // GET /api/v1/validators/:name - Get validator by name
  http.get('/api/v1/validators/:name', ({ params }) => {
    const { name } = params
    const validator = MOCK_VALIDATORS.find(
      (v) => v.name.toLowerCase() === (name as string).toLowerCase()
    )
    return HttpResponse.json(validator || null)
  }),

  // POST /api/v1/validators/custom/:validatorId/execute - Execute custom validator
  http.post('/api/v1/validators/custom/:validatorId/execute', async ({ params, request }) => {
    const { validatorId } = params
    const body = await request.json() as {
      source_id: string
      column_name: string
      param_values?: Record<string, unknown>
    }

    // Get custom validator from store
    const { mockStore } = require('../data/store')
    const validator = mockStore.customValidators?.find((v: { id: string }) => v.id === validatorId)

    if (!validator) {
      return HttpResponse.json({ detail: `Custom validator ${validatorId} not found` }, { status: 404 })
    }

    if (!validator.is_enabled) {
      return HttpResponse.json({ detail: `Custom validator ${validator.name} is disabled` }, { status: 400 })
    }

    // Simulate execution
    const passed = Math.random() > 0.3 // 70% pass rate
    const issues = passed ? [] : [
      {
        row: Math.floor(Math.random() * 1000),
        message: `Validation failed for ${body.column_name}`,
        severity: 'warning',
      },
    ]

    return HttpResponse.json({
      success: true,
      passed,
      execution_time_ms: Math.random() * 100 + 10,
      issues,
      message: passed ? 'Validation passed' : `Found ${issues.length} issues`,
      details: {
        column: body.column_name,
        validator: validator.name,
        params_used: body.param_values || {},
      },
    })
  }),

  // POST /api/v1/validators/custom/:validatorId/execute-preview - Preview execution
  http.post('/api/v1/validators/custom/:validatorId/execute-preview', async ({ params, request }) => {
    const { validatorId } = params
    const body = await request.json() as {
      column_name?: string
      values?: unknown[]
      params?: Record<string, unknown>
    }

    // Get custom validator from store
    const { mockStore } = require('../data/store')
    const validator = mockStore.customValidators?.find((v: { id: string }) => v.id === validatorId)

    if (!validator) {
      return HttpResponse.json({ detail: `Custom validator ${validatorId} not found` }, { status: 404 })
    }

    const values = body.values || []
    const nullCount = values.filter((v) => v === null || v === undefined).length
    const passed = nullCount === 0

    return HttpResponse.json({
      success: true,
      passed,
      execution_time_ms: Math.random() * 50 + 5,
      issues: passed ? [] : [
        {
          message: `Found ${nullCount} null values`,
          severity: 'warning',
        },
      ],
      message: passed ? 'All values valid' : `Found ${nullCount} issues`,
      details: {
        total_values: values.length,
        null_count: nullCount,
      },
    })
  }),
]

// Export for testing
export { MOCK_VALIDATORS, CATEGORY_LABELS }
