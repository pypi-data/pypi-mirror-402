/**
 * Mock validator definitions factory.
 *
 * Provides complete validator registry matching the backend for MSW mocks.
 */

import type { ValidatorDefinition } from '@/types/validators'

// =============================================================================
// Cross-Table Validators (8 validators)
// =============================================================================

export const CROSS_TABLE_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'ForeignKey',
    display_name: 'Foreign Key',
    category: 'cross_table',
    description: 'Validates foreign key relationships between tables.',
    parameters: [
      { name: 'column', label: 'FK Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'reference_column', label: 'Reference Column', type: 'string', required: true },
    ],
    tags: ['foreign_key', 'relationship', 'integrity'],
    severity_default: 'critical',
  },
  {
    name: 'CompositeForeignKey',
    display_name: 'Composite Foreign Key',
    category: 'cross_table',
    description: 'Validates composite foreign key relationships.',
    parameters: [
      { name: 'columns', label: 'FK Columns', type: 'column_list', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'reference_columns', label: 'Reference Columns', type: 'string_list', required: true },
    ],
    tags: ['foreign_key', 'composite', 'relationship'],
    severity_default: 'critical',
  },
  {
    name: 'Orphan',
    display_name: 'Orphan Records',
    category: 'cross_table',
    description: 'Detects orphan records with no matching parent.',
    parameters: [
      { name: 'column', label: 'FK Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Parent Source', type: 'source_ref', required: true },
      { name: 'reference_column', label: 'Parent PK Column', type: 'string', required: true },
    ],
    tags: ['orphan', 'relationship', 'integrity'],
    severity_default: 'high',
  },
  {
    name: 'CrossTableRowCount',
    display_name: 'Cross-Table Row Count',
    category: 'cross_table',
    description: 'Compares row counts between related tables.',
    parameters: [
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'comparison', label: 'Comparison', type: 'select', required: true, options: [
        { value: 'equal', label: 'Equal' },
        { value: 'greater', label: 'Greater' },
        { value: 'less', label: 'Less' },
      ]},
    ],
    tags: ['count', 'comparison', 'cross_table'],
    severity_default: 'medium',
  },
  {
    name: 'CrossTableAggregate',
    display_name: 'Cross-Table Aggregate',
    category: 'cross_table',
    description: 'Validates aggregate relationships between tables.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'aggregate', label: 'Aggregate Function', type: 'select', required: true, options: [
        { value: 'sum', label: 'Sum' },
        { value: 'count', label: 'Count' },
        { value: 'avg', label: 'Average' },
      ]},
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'reference_column', label: 'Reference Column', type: 'string', required: true },
    ],
    tags: ['aggregate', 'cross_table', 'calculation'],
    severity_default: 'medium',
  },
  {
    name: 'ReferentialIntegrity',
    display_name: 'Referential Integrity',
    category: 'cross_table',
    description: 'Validates complete referential integrity constraints.',
    parameters: [
      { name: 'column', label: 'FK Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'reference_column', label: 'Reference Column', type: 'string', required: true },
      { name: 'on_violation', label: 'On Violation', type: 'select', options: [
        { value: 'error', label: 'Error' },
        { value: 'warn', label: 'Warning' },
      ], default: 'error' },
    ],
    tags: ['referential', 'integrity', 'constraint'],
    severity_default: 'critical',
  },
  {
    name: 'CrossTableUnique',
    display_name: 'Cross-Table Unique',
    category: 'cross_table',
    description: 'Validates uniqueness across multiple tables.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_sources', label: 'Reference Sources', type: 'string_list', required: true },
    ],
    tags: ['uniqueness', 'cross_table'],
    severity_default: 'high',
  },
  {
    name: 'JoinValidation',
    display_name: 'Join Validation',
    category: 'cross_table',
    description: 'Validates join conditions produce expected results.',
    parameters: [
      { name: 'join_column', label: 'Join Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'reference_column', label: 'Reference Column', type: 'string', required: true },
      { name: 'join_type', label: 'Join Type', type: 'select', options: [
        { value: 'inner', label: 'Inner' },
        { value: 'left', label: 'Left' },
        { value: 'outer', label: 'Outer' },
      ], default: 'inner' },
    ],
    tags: ['join', 'relationship'],
    severity_default: 'medium',
  },
]

// =============================================================================
// Multi-Column Validators (12 validators - subset)
// =============================================================================

export const MULTI_COLUMN_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'Correlation',
    display_name: 'Correlation',
    category: 'multi_column',
    description: 'Validates correlation between numeric columns.',
    parameters: [
      { name: 'column_a', label: 'Column A', type: 'column', required: true },
      { name: 'column_b', label: 'Column B', type: 'column', required: true },
      { name: 'min_correlation', label: 'Min Correlation', type: 'float', min_value: -1, max_value: 1 },
      { name: 'max_correlation', label: 'Max Correlation', type: 'float', min_value: -1, max_value: 1 },
    ],
    tags: ['correlation', 'statistical', 'relationship'],
    severity_default: 'medium',
  },
  {
    name: 'Dependency',
    display_name: 'Functional Dependency',
    category: 'multi_column',
    description: 'Validates functional dependencies between columns.',
    parameters: [
      { name: 'determinant', label: 'Determinant Column', type: 'column', required: true },
      { name: 'dependent', label: 'Dependent Column', type: 'column', required: true },
    ],
    tags: ['dependency', 'functional', 'relationship'],
    severity_default: 'high',
  },
  {
    name: 'Conditional',
    display_name: 'Conditional Validation',
    category: 'multi_column',
    description: 'Validates column values based on conditions in other columns.',
    parameters: [
      { name: 'condition_column', label: 'Condition Column', type: 'column', required: true },
      { name: 'condition_value', label: 'Condition Value', type: 'string', required: true },
      { name: 'target_column', label: 'Target Column', type: 'column', required: true },
      { name: 'expected_values', label: 'Expected Values', type: 'string_list', required: true },
    ],
    tags: ['conditional', 'business_rule'],
    severity_default: 'medium',
  },
  {
    name: 'ColumnSum',
    display_name: 'Column Sum',
    category: 'multi_column',
    description: 'Validates that sum of columns equals expected value.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'expected_column', label: 'Expected Sum Column', type: 'column', required: true },
      { name: 'tolerance', label: 'Tolerance', type: 'float', default: 0.0001, min_value: 0 },
    ],
    tags: ['sum', 'calculation', 'arithmetic'],
    severity_default: 'high',
  },
  {
    name: 'ColumnProduct',
    display_name: 'Column Product',
    category: 'multi_column',
    description: 'Validates column multiplication results.',
    parameters: [
      { name: 'column_a', label: 'Column A', type: 'column', required: true },
      { name: 'column_b', label: 'Column B', type: 'column', required: true },
      { name: 'result_column', label: 'Result Column', type: 'column', required: true },
      { name: 'tolerance', label: 'Tolerance', type: 'float', default: 0.0001, min_value: 0 },
    ],
    tags: ['product', 'calculation', 'arithmetic'],
    severity_default: 'high',
  },
  {
    name: 'ColumnComparison',
    display_name: 'Column Comparison',
    category: 'multi_column',
    description: 'Compares values between columns.',
    parameters: [
      { name: 'column_a', label: 'Column A', type: 'column', required: true },
      { name: 'column_b', label: 'Column B', type: 'column', required: true },
      { name: 'operator', label: 'Operator', type: 'select', required: true, options: [
        { value: 'eq', label: 'Equal (=)' },
        { value: 'ne', label: 'Not Equal (!=)' },
        { value: 'gt', label: 'Greater (>)' },
        { value: 'lt', label: 'Less (<)' },
        { value: 'gte', label: 'Greater or Equal (>=)' },
        { value: 'lte', label: 'Less or Equal (<=)' },
      ]},
    ],
    tags: ['comparison', 'relationship'],
    severity_default: 'medium',
  },
  {
    name: 'MutualExclusion',
    display_name: 'Mutual Exclusion',
    category: 'multi_column',
    description: 'Ensures only one of multiple columns has a value.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
    ],
    tags: ['exclusion', 'constraint'],
    severity_default: 'high',
  },
  {
    name: 'AtLeastOneNotNull',
    display_name: 'At Least One Not Null',
    category: 'multi_column',
    description: 'Ensures at least one column has a non-null value.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
    ],
    tags: ['completeness', 'null'],
    severity_default: 'high',
  },
  {
    name: 'AllOrNone',
    display_name: 'All Or None',
    category: 'multi_column',
    description: 'Ensures all columns are populated or none are.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
    ],
    tags: ['completeness', 'constraint'],
    severity_default: 'medium',
  },
  {
    name: 'DateSequence',
    display_name: 'Date Sequence',
    category: 'multi_column',
    description: 'Validates chronological order of date columns.',
    parameters: [
      { name: 'date_columns', label: 'Date Columns (in order)', type: 'column_list', required: true },
    ],
    tags: ['date', 'sequence', 'order'],
    severity_default: 'high',
  },
  {
    name: 'ConditionalRequired',
    display_name: 'Conditional Required',
    category: 'multi_column',
    description: 'Column is required when condition is met.',
    parameters: [
      { name: 'condition_column', label: 'Condition Column', type: 'column', required: true },
      { name: 'condition_value', label: 'Condition Value', type: 'string', required: true },
      { name: 'required_column', label: 'Required Column', type: 'column', required: true },
    ],
    tags: ['conditional', 'required', 'completeness'],
    severity_default: 'high',
  },
  {
    name: 'Expression',
    display_name: 'Expression Validation',
    category: 'multi_column',
    description: 'Validates custom expressions across columns.',
    parameters: [
      { name: 'expression', label: 'Expression', type: 'expression', required: true, placeholder: 'price * quantity == total' },
    ],
    tags: ['expression', 'custom', 'calculation'],
    severity_default: 'medium',
  },
]

// =============================================================================
// Drift Validators (8 validators)
// =============================================================================

export const DRIFT_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'KSDrift',
    display_name: 'KS Test Drift',
    category: 'drift',
    description: 'Kolmogorov-Smirnov test for distribution drift.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold', label: 'P-value Threshold', type: 'float', default: 0.05, min_value: 0, max_value: 1 },
    ],
    tags: ['ks', 'distribution', 'statistical'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
  {
    name: 'PSIDrift',
    display_name: 'PSI Drift',
    category: 'drift',
    description: 'Population Stability Index for drift detection.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold', label: 'PSI Threshold', type: 'float', default: 0.2, min_value: 0 },
      { name: 'bins', label: 'Number of Bins', type: 'integer', default: 10, min_value: 2 },
    ],
    tags: ['psi', 'stability', 'distribution'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
  {
    name: 'ChiSquareDrift',
    display_name: 'Chi-Square Drift',
    category: 'drift',
    description: 'Chi-square test for categorical drift.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'alpha', label: 'Significance Level', type: 'float', default: 0.05, min_value: 0, max_value: 1 },
    ],
    tags: ['chi_square', 'categorical', 'statistical'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
  {
    name: 'JSDrift',
    display_name: 'Jensen-Shannon Drift',
    category: 'drift',
    description: 'Jensen-Shannon divergence for drift detection.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold', label: 'JS Threshold', type: 'float', default: 0.1, min_value: 0, max_value: 1 },
    ],
    tags: ['js', 'divergence', 'distribution'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
  {
    name: 'WassersteinDrift',
    display_name: 'Wasserstein Drift',
    category: 'drift',
    description: 'Wasserstein distance (Earth Mover\'s) for drift.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold', label: 'Distance Threshold', type: 'float', required: true, min_value: 0 },
    ],
    tags: ['wasserstein', 'emd', 'distribution'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
  {
    name: 'MeanDrift',
    display_name: 'Mean Drift',
    category: 'drift',
    description: 'Detects drift in column mean values.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold_percent', label: 'Threshold (%)', type: 'float', default: 10, min_value: 0 },
    ],
    tags: ['mean', 'statistical', 'simple'],
    severity_default: 'medium',
    requires_extra: 'drift',
  },
  {
    name: 'VarianceDrift',
    display_name: 'Variance Drift',
    category: 'drift',
    description: 'Detects drift in column variance.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'threshold_percent', label: 'Threshold (%)', type: 'float', default: 20, min_value: 0 },
    ],
    tags: ['variance', 'statistical'],
    severity_default: 'medium',
    requires_extra: 'drift',
  },
  {
    name: 'CategoryDrift',
    display_name: 'Category Drift',
    category: 'drift',
    description: 'Detects new or missing categories.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'reference_source', label: 'Reference Source', type: 'source_ref', required: true },
      { name: 'allow_new', label: 'Allow New Categories', type: 'boolean', default: false },
    ],
    tags: ['category', 'categorical'],
    severity_default: 'high',
    requires_extra: 'drift',
  },
]

// =============================================================================
// Anomaly Validators (8 validators)
// =============================================================================

export const ANOMALY_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'IsolationForest',
    display_name: 'Isolation Forest',
    category: 'anomaly',
    description: 'ML-based anomaly detection using Isolation Forest.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'contamination', label: 'Contamination', type: 'float', default: 0.1, min_value: 0, max_value: 0.5 },
      { name: 'n_estimators', label: 'Number of Trees', type: 'integer', default: 100, min_value: 10 },
    ],
    tags: ['isolation_forest', 'ml', 'multivariate'],
    severity_default: 'high',
    requires_extra: 'anomaly',
  },
  {
    name: 'IQRAnomaly',
    display_name: 'IQR Anomaly',
    category: 'anomaly',
    description: 'Detects anomalies using Interquartile Range.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'multiplier', label: 'IQR Multiplier', type: 'float', default: 1.5, min_value: 0 },
    ],
    tags: ['iqr', 'statistical', 'outlier'],
    severity_default: 'medium',
    requires_extra: 'anomaly',
  },
  {
    name: 'MahalanobisAnomaly',
    display_name: 'Mahalanobis Distance',
    category: 'anomaly',
    description: 'Multivariate anomaly detection using Mahalanobis distance.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'threshold', label: 'Distance Threshold', type: 'float', required: true, min_value: 0 },
    ],
    tags: ['mahalanobis', 'multivariate', 'statistical'],
    severity_default: 'high',
    requires_extra: 'anomaly',
  },
  {
    name: 'LOFAnomaly',
    display_name: 'Local Outlier Factor',
    category: 'anomaly',
    description: 'LOF-based anomaly detection.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'n_neighbors', label: 'Number of Neighbors', type: 'integer', default: 20, min_value: 1 },
      { name: 'contamination', label: 'Contamination', type: 'float', default: 0.1, min_value: 0, max_value: 0.5 },
    ],
    tags: ['lof', 'ml', 'density'],
    severity_default: 'high',
    requires_extra: 'anomaly',
  },
  {
    name: 'DBSCANAnomaly',
    display_name: 'DBSCAN Anomaly',
    category: 'anomaly',
    description: 'DBSCAN clustering-based anomaly detection.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'eps', label: 'Epsilon', type: 'float', default: 0.5, min_value: 0 },
      { name: 'min_samples', label: 'Min Samples', type: 'integer', default: 5, min_value: 1 },
    ],
    tags: ['dbscan', 'clustering', 'ml'],
    severity_default: 'high',
    requires_extra: 'anomaly',
  },
  {
    name: 'ZScoreAnomaly',
    display_name: 'Z-Score Anomaly',
    category: 'anomaly',
    description: 'Z-score based anomaly detection.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'threshold', label: 'Z-Score Threshold', type: 'float', default: 3.0, min_value: 0 },
    ],
    tags: ['zscore', 'statistical', 'univariate'],
    severity_default: 'medium',
    requires_extra: 'anomaly',
  },
  {
    name: 'ModifiedZScore',
    display_name: 'Modified Z-Score',
    category: 'anomaly',
    description: 'Modified Z-score using median absolute deviation.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'threshold', label: 'Threshold', type: 'float', default: 3.5, min_value: 0 },
    ],
    tags: ['mad', 'robust', 'statistical'],
    severity_default: 'medium',
    requires_extra: 'anomaly',
  },
  {
    name: 'OneClassSVM',
    display_name: 'One-Class SVM',
    category: 'anomaly',
    description: 'One-Class SVM for anomaly detection.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
      { name: 'nu', label: 'Nu Parameter', type: 'float', default: 0.1, min_value: 0, max_value: 1 },
      { name: 'kernel', label: 'Kernel', type: 'select', default: 'rbf', options: [
        { value: 'rbf', label: 'RBF' },
        { value: 'linear', label: 'Linear' },
        { value: 'poly', label: 'Polynomial' },
      ]},
    ],
    tags: ['svm', 'ml', 'multivariate'],
    severity_default: 'high',
    requires_extra: 'anomaly',
  },
]

// =============================================================================
// Privacy Validators (8 validators)
// =============================================================================

export const PRIVACY_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'PIIDetection',
    display_name: 'PII Detection',
    category: 'privacy',
    description: 'Detects personally identifiable information.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list' },
      { name: 'pii_types', label: 'PII Types', type: 'multi_select', options: [
        { value: 'email', label: 'Email' },
        { value: 'phone', label: 'Phone' },
        { value: 'ssn', label: 'SSN' },
        { value: 'credit_card', label: 'Credit Card' },
        { value: 'name', label: 'Name' },
        { value: 'address', label: 'Address' },
      ]},
    ],
    tags: ['pii', 'detection', 'compliance'],
    severity_default: 'critical',
  },
  {
    name: 'GDPRCompliance',
    display_name: 'GDPR Compliance',
    category: 'privacy',
    description: 'Validates GDPR compliance requirements.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list' },
      { name: 'require_consent', label: 'Require Consent Column', type: 'boolean', default: true },
      { name: 'consent_column', label: 'Consent Column', type: 'column', depends_on: 'require_consent', depends_value: true },
    ],
    tags: ['gdpr', 'compliance', 'europe'],
    severity_default: 'critical',
  },
  {
    name: 'CCPACompliance',
    display_name: 'CCPA Compliance',
    category: 'privacy',
    description: 'Validates CCPA compliance requirements.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list' },
      { name: 'opt_out_column', label: 'Opt-Out Column', type: 'column' },
    ],
    tags: ['ccpa', 'compliance', 'california'],
    severity_default: 'critical',
  },
  {
    name: 'DataRetention',
    display_name: 'Data Retention',
    category: 'privacy',
    description: 'Validates data retention policies.',
    parameters: [
      { name: 'date_column', label: 'Date Column', type: 'column', required: true },
      { name: 'max_age_days', label: 'Max Age (Days)', type: 'integer', required: true, min_value: 1 },
    ],
    tags: ['retention', 'compliance', 'policy'],
    severity_default: 'high',
  },
  {
    name: 'SensitiveDataMasking',
    display_name: 'Sensitive Data Masking',
    category: 'privacy',
    description: 'Verifies sensitive data is properly masked.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'mask_pattern', label: 'Expected Mask Pattern', type: 'regex', required: true, placeholder: '^\\*{4}\\d{4}$' },
    ],
    tags: ['masking', 'sensitive', 'security'],
    severity_default: 'critical',
  },
  {
    name: 'EmailMasked',
    display_name: 'Email Masked',
    category: 'privacy',
    description: 'Validates email addresses are masked.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
    ],
    tags: ['email', 'masking', 'pii'],
    severity_default: 'high',
  },
  {
    name: 'PhoneMasked',
    display_name: 'Phone Masked',
    category: 'privacy',
    description: 'Validates phone numbers are masked.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
    ],
    tags: ['phone', 'masking', 'pii'],
    severity_default: 'high',
  },
  {
    name: 'NoRawPII',
    display_name: 'No Raw PII',
    category: 'privacy',
    description: 'Ensures no raw PII exists in specified columns.',
    parameters: [
      { name: 'columns', label: 'Columns', type: 'column_list', required: true },
    ],
    tags: ['pii', 'raw', 'security'],
    severity_default: 'critical',
  },
]

// =============================================================================
// Table Validators (8 validators)
// =============================================================================

export const TABLE_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'TableExists',
    display_name: 'Table Exists',
    category: 'table',
    description: 'Validates that the table exists and is accessible.',
    parameters: [],
    tags: ['existence', 'metadata'],
    severity_default: 'critical',
  },
  {
    name: 'TableNotEmpty',
    display_name: 'Table Not Empty',
    category: 'table',
    description: 'Ensures the table contains data.',
    parameters: [],
    tags: ['empty', 'data'],
    severity_default: 'high',
  },
  {
    name: 'TableRowCountBetween',
    display_name: 'Row Count Between',
    category: 'table',
    description: 'Validates row count is within expected range.',
    parameters: [
      { name: 'min_count', label: 'Minimum Rows', type: 'integer', min_value: 0 },
      { name: 'max_count', label: 'Maximum Rows', type: 'integer', min_value: 0 },
    ],
    tags: ['count', 'rows', 'range'],
    severity_default: 'medium',
  },
  {
    name: 'TableColumnCountBetween',
    display_name: 'Column Count Between',
    category: 'table',
    description: 'Validates column count is within expected range.',
    parameters: [
      { name: 'min_count', label: 'Minimum Columns', type: 'integer', min_value: 0 },
      { name: 'max_count', label: 'Maximum Columns', type: 'integer', min_value: 0 },
    ],
    tags: ['count', 'columns', 'schema'],
    severity_default: 'medium',
  },
  {
    name: 'TableFreshness',
    display_name: 'Table Freshness',
    category: 'table',
    description: 'Validates table data is recent.',
    parameters: [
      { name: 'datetime_column', label: 'Datetime Column', type: 'column', required: true },
      { name: 'max_age_hours', label: 'Max Age (Hours)', type: 'integer', required: true, min_value: 1 },
    ],
    tags: ['freshness', 'staleness', 'time'],
    severity_default: 'high',
  },
  {
    name: 'TableSizeBytes',
    display_name: 'Table Size',
    category: 'table',
    description: 'Validates table size in bytes.',
    parameters: [
      { name: 'max_size_mb', label: 'Max Size (MB)', type: 'integer', min_value: 0 },
    ],
    tags: ['size', 'storage', 'bytes'],
    severity_default: 'low',
  },
  {
    name: 'TablePartitioned',
    display_name: 'Table Partitioned',
    category: 'table',
    description: 'Validates table has expected partitions.',
    parameters: [
      { name: 'partition_column', label: 'Partition Column', type: 'column', required: true },
    ],
    tags: ['partition', 'structure'],
    severity_default: 'low',
  },
  {
    name: 'TableMetadata',
    display_name: 'Table Metadata',
    category: 'table',
    description: 'Validates table metadata properties.',
    parameters: [
      { name: 'expected_metadata', label: 'Expected Metadata', type: 'schema', required: true },
    ],
    tags: ['metadata', 'properties'],
    severity_default: 'low',
  },
]

// =============================================================================
// Query Validators (6 validators)
// =============================================================================

export const QUERY_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'CustomQuery',
    display_name: 'Custom Query',
    category: 'query',
    description: 'Validates using a custom Polars expression.',
    parameters: [
      { name: 'expression', label: 'Expression', type: 'expression', required: true },
      { name: 'description', label: 'Description', type: 'string' },
    ],
    tags: ['custom', 'expression', 'flexible'],
    severity_default: 'medium',
  },
  {
    name: 'QueryRowCount',
    display_name: 'Query Row Count',
    category: 'query',
    description: 'Validates row count after filtering.',
    parameters: [
      { name: 'filter_expression', label: 'Filter Expression', type: 'expression', required: true },
      { name: 'expected_count', label: 'Expected Count', type: 'integer' },
      { name: 'min_count', label: 'Minimum Count', type: 'integer', min_value: 0 },
      { name: 'max_count', label: 'Maximum Count', type: 'integer', min_value: 0 },
    ],
    tags: ['filter', 'count', 'rows'],
    severity_default: 'medium',
  },
  {
    name: 'QueryAggregate',
    display_name: 'Query Aggregate',
    category: 'query',
    description: 'Validates aggregate result from filtered data.',
    parameters: [
      { name: 'filter_expression', label: 'Filter Expression', type: 'expression' },
      { name: 'aggregate', label: 'Aggregate Function', type: 'select', required: true, options: [
        { value: 'sum', label: 'Sum' },
        { value: 'mean', label: 'Mean' },
        { value: 'count', label: 'Count' },
        { value: 'min', label: 'Min' },
        { value: 'max', label: 'Max' },
      ]},
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'expected_value', label: 'Expected Value', type: 'float' },
    ],
    tags: ['aggregate', 'filter', 'calculation'],
    severity_default: 'medium',
  },
  {
    name: 'QueryUnique',
    display_name: 'Query Unique',
    category: 'query',
    description: 'Validates uniqueness after filtering.',
    parameters: [
      { name: 'filter_expression', label: 'Filter Expression', type: 'expression' },
      { name: 'column', label: 'Column', type: 'column', required: true },
    ],
    tags: ['unique', 'filter'],
    severity_default: 'high',
  },
  {
    name: 'QueryNotNull',
    display_name: 'Query Not Null',
    category: 'query',
    description: 'Validates no nulls after filtering.',
    parameters: [
      { name: 'filter_expression', label: 'Filter Expression', type: 'expression' },
      { name: 'column', label: 'Column', type: 'column', required: true },
    ],
    tags: ['null', 'filter', 'completeness'],
    severity_default: 'high',
  },
  {
    name: 'BusinessRule',
    display_name: 'Business Rule',
    category: 'query',
    description: 'Validates custom business rules.',
    parameters: [
      { name: 'rule_expression', label: 'Rule Expression', type: 'expression', required: true },
      { name: 'rule_name', label: 'Rule Name', type: 'string', required: true },
      { name: 'rule_description', label: 'Rule Description', type: 'string' },
    ],
    tags: ['business', 'rule', 'custom'],
    severity_default: 'high',
  },
]

// =============================================================================
// Geospatial Validators (6 validators)
// =============================================================================

export const GEOSPATIAL_VALIDATORS: ValidatorDefinition[] = [
  {
    name: 'LatitudeRange',
    display_name: 'Latitude Range',
    category: 'geospatial',
    description: 'Validates latitude values are within valid range.',
    parameters: [
      { name: 'column', label: 'Latitude Column', type: 'column', required: true },
    ],
    tags: ['latitude', 'coordinate', 'range'],
    severity_default: 'high',
  },
  {
    name: 'LongitudeRange',
    display_name: 'Longitude Range',
    category: 'geospatial',
    description: 'Validates longitude values are within valid range.',
    parameters: [
      { name: 'column', label: 'Longitude Column', type: 'column', required: true },
    ],
    tags: ['longitude', 'coordinate', 'range'],
    severity_default: 'high',
  },
  {
    name: 'CoordinatePair',
    display_name: 'Coordinate Pair',
    category: 'geospatial',
    description: 'Validates lat/lon pairs are valid coordinates.',
    parameters: [
      { name: 'lat_column', label: 'Latitude Column', type: 'column', required: true },
      { name: 'lon_column', label: 'Longitude Column', type: 'column', required: true },
    ],
    tags: ['coordinate', 'pair', 'location'],
    severity_default: 'high',
  },
  {
    name: 'WithinBoundingBox',
    display_name: 'Within Bounding Box',
    category: 'geospatial',
    description: 'Validates coordinates are within a bounding box.',
    parameters: [
      { name: 'lat_column', label: 'Latitude Column', type: 'column', required: true },
      { name: 'lon_column', label: 'Longitude Column', type: 'column', required: true },
      { name: 'min_lat', label: 'Min Latitude', type: 'float', required: true, min_value: -90, max_value: 90 },
      { name: 'max_lat', label: 'Max Latitude', type: 'float', required: true, min_value: -90, max_value: 90 },
      { name: 'min_lon', label: 'Min Longitude', type: 'float', required: true, min_value: -180, max_value: 180 },
      { name: 'max_lon', label: 'Max Longitude', type: 'float', required: true, min_value: -180, max_value: 180 },
    ],
    tags: ['bounding_box', 'region', 'boundary'],
    severity_default: 'medium',
  },
  {
    name: 'PostalCode',
    display_name: 'Postal Code',
    category: 'geospatial',
    description: 'Validates postal/ZIP code format.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'country', label: 'Country', type: 'select', options: [
        { value: 'US', label: 'United States' },
        { value: 'UK', label: 'United Kingdom' },
        { value: 'CA', label: 'Canada' },
        { value: 'DE', label: 'Germany' },
        { value: 'KR', label: 'South Korea' },
      ]},
    ],
    tags: ['postal', 'zip', 'format'],
    severity_default: 'medium',
  },
  {
    name: 'CountryCode',
    display_name: 'Country Code',
    category: 'geospatial',
    description: 'Validates ISO country codes.',
    parameters: [
      { name: 'column', label: 'Column', type: 'column', required: true },
      { name: 'format', label: 'Format', type: 'select', options: [
        { value: 'alpha2', label: 'ISO 3166-1 Alpha-2 (US, KR)' },
        { value: 'alpha3', label: 'ISO 3166-1 Alpha-3 (USA, KOR)' },
      ], default: 'alpha2' },
    ],
    tags: ['country', 'iso', 'code'],
    severity_default: 'medium',
  },
]
