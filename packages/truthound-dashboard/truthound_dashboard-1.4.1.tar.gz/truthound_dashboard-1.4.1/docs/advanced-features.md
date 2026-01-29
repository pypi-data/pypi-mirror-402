# Advanced Features

This document describes advanced features added to truthound-dashboard based on truthound library capabilities.

## Anomaly Detection

ML-based outlier and anomaly detection using multiple algorithms.

### Supported Algorithms

- **IsolationForest**: Tree-based isolation for high-dimensional data
- **LocalOutlierFactor (LOF)**: Density-based local outlier detection
- **DBSCAN**: Density-based spatial clustering
- **OneClassSVM**: Boundary learning for novelty detection
- **EllipticEnvelope**: Gaussian distribution assumption
- **Ensemble**: Combines multiple algorithms for robust detection

### Features

- Streaming anomaly detection for real-time data
- Feature contribution analysis for explainability
- Batch detection with progress tracking
- Algorithm comparison and agreement scoring
- Confidence-based anomaly classification

### Usage

```json
POST /api/v1/anomaly/detect
{
  "source_id": 1,
  "algorithms": ["IsolationForest", "LOF"],
  "contamination": 0.1
}
```

---

## Data Lineage

Visual tracking of data flow and dependencies across assets.

### Visualization Options

- **D3.js**: Interactive force-directed graph with zoom/pan
- **Mermaid**: Declarative diagram generation
- **Cytoscape**: Network analysis and layout algorithms

### Features

- Column-level lineage tracking
- Impact analysis (upstream and downstream dependencies)
- OpenLineage standard integration
- Webhook support for lineage events
- Lazy loading and virtualization for large graphs
- Anomaly overlay on lineage graph

### OpenLineage Integration

```json
POST /api/v1/lineage/openlineage/webhook
{
  "url": "https://your-lineage-backend.com/api/lineage",
  "auth_header": "Bearer token",
  "events": ["START", "COMPLETE", "FAIL"]
}
```

---

## Schema Evolution

Track and manage schema changes over time.

### Change Detection

Automatically detects:
- Column additions/removals
- Data type changes
- Constraint modifications (nullable, unique)

### Change Classification

| Type | Description | Breaking |
|------|-------------|----------|
| Column Added | New column | No |
| Column Removed | Column deleted | Yes |
| Type Changed | Data type modified | Yes |
| Constraint Added | New constraint | Depends |
| Constraint Removed | Constraint deleted | No |

### Features

- Version timeline with visual comparison
- Breaking vs non-breaking change classification
- Change notifications
- Schema diff viewer

---

## Result Versioning

Version control for validation results with multiple strategies.

### Versioning Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| **Incremental** | Auto-increment | 1, 2, 3, ... |
| **Semantic** | Severity-based | 1.0.0, 1.1.0, 2.0.0 |
| **Timestamp** | ISO 8601 | 2026-01-16T10:30:00Z |
| **GitLike** | Hash-based | a1b2c3d, e4f5g6h |

### Features

- Version comparison (side-by-side diff)
- Change tracking (what changed between versions)
- Parent-child relationship (version history graph)
- Content-based deduplication (avoid duplicate storage)

---

## Profile Comparison

Compare data profiles across time or environments.

### Comparison Types

- **Temporal**: Compare profiles from different time periods
- **Environmental**: Compare production vs staging
- **Baseline**: Compare current state vs baseline

### Visualizations

- Row count trends over time
- Quality metrics (null%, unique%) trends
- Column distribution changes
- Statistical metric comparisons

### Granularity Options

- Daily
- Weekly
- Monthly
- Custom date range

---

## Rule Suggestions

AI-powered automatic rule generation from data profiles.

### Suggestion Categories

| Category | Generated Rules |
|----------|----------------|
| **Completeness** | null_count, not_null |
| **Uniqueness** | unique, duplicate_count |
| **Distribution** | min_value, max_value, value_range |
| **String** | regex_match, email_format, phone_format |
| **Datetime** | date_range, future_date |

### Confidence Scoring

- **High (>80%)**: Very confident based on data patterns
- **Medium (50-80%)**: Moderately confident
- **Low (<50%)**: Suggested for review

### Features

- Bulk rule application (select multiple suggestions)
- Preview before applying
- Category-based filtering
- Confidence threshold filtering

---

## Reports & Export

Generate comprehensive validation reports with flexible formats and management.

### Report Formats

- **HTML**: Interactive web reports with charts
- **PDF**: Printable documents with custom themes
- **CSV**: Tabular data for analysis
- **JSON**: Machine-readable structured data
- **Excel**: Multi-sheet workbooks
- **Markdown**: Documentation-friendly format

### Report Types

- **Validation Reports**: th.check() execution results
- **Drift Detection Reports**: Data drift analysis
- **PII Scan Reports**: Privacy compliance checks
- **Profile Reports**: Data profiling summaries
- **Anomaly Reports**: Detected anomalies
- **Model Monitoring Reports**: ML model performance

### Management Features

**Statistics Dashboard**:
- Total reports count and size
- Download metrics
- Average generation time
- Expired reports tracking
- Active reporters count

**Search & Filtering**:
- Full-text search by name
- Format-based filtering (HTML/PDF/CSV/JSON/Excel/Markdown)
- Status filtering (Pending/Generating/Completed/Failed)
- Include/exclude expired reports toggle

**Report Lifecycle**:
- Automatic expiration based on retention policies
- Batch cleanup of expired reports
- Download tracking
- Version history

**Custom Themes**:
- Apply color schemes to HTML/PDF reports
- Logo and branding customization
- Custom CSS support

### Integration

- **Scheduled Reports**: Auto-generate via validation schedules
- **Notification Attachments**: Include reports in alerts
- **API Export**: Programmatic report generation

### Chart Libraries

- **Plotly**: Interactive JavaScript charts
- **Chart.js**: Lightweight canvas charts
- **ECharts**: Feature-rich visualization
- **SVG**: Static vector graphics

---

## Maintenance & Retention

Comprehensive system maintenance and data lifecycle management.

### Auto Maintenance Scheduling

- **Toggle Enable/Disable**: Control automatic maintenance execution
- **Status Monitoring**:
  - Last run timestamp
  - Next scheduled execution
  - Current maintenance status

### Retention Policies

**Validation History Retention** (1-365 days):
- Configurable retention period for validation runs
- Automatic cleanup of old results
- Preserves recent validation history
- Default: 90 days

**Profile Snapshots** (1-100 per source):
- Limit profile history per data source
- Prevents unbounded profile accumulation
- Maintains trend analysis capability
- Default: 10 profiles per source

**Notification Logs** (1-365 days):
- Retention period for notification delivery records
- Tracks alert history
- Supports audit requirements
- Default: 30 days

**Vacuum on Cleanup**:
- Optional SQLite VACUUM after cleanup
- Reclaims disk space
- Optimizes database performance
- Toggle on/off based on system load

### Manual Operations

**Run Cleanup**:
- On-demand execution of retention policies
- Remove expired validation runs
- Purge old notification logs
- Delete excess profile snapshots
- Real-time progress indicator

**Run Vacuum**:
- Manual database optimization
- Rebuild SQLite internal structures
- Reclaim fragmented space
- May temporarily lock database

**Clear Cache**:
- Invalidate all cached entries
- Force data refresh
- Useful after bulk updates
- Immediate effect

### Cache Statistics

Monitor caching effectiveness:

- **Total Entries**: All items in cache
- **Valid Entries**: Non-expired items
- **Expired Entries**: Stale items awaiting cleanup
- **Hit Rate**: Cache effectiveness (hits / total requests)

### Configuration Management

- **Save Settings**: Persist retention policy changes
- **Input Validation**: Range checks prevent invalid values
- **Real-time Application**: Settings active immediately after save
- **Audit Trail**: Log configuration changes

### Database Optimization

**Automatic**:
- Periodic VACUUM (if enabled)
- ANALYZE statistics updates
- Index maintenance

**Manual**:
- On-demand VACUUM execution
- Cache invalidation
- Cleanup operations

### Best Practices

1. **Validation Retention**: 90-365 days for compliance
2. **Profile Snapshots**: 10-30 for trend analysis
3. **Notification Logs**: 30-90 days for debugging
4. **Vacuum Frequency**: Weekly for active systems
5. **Cache Clearing**: After bulk data imports

### Legacy Policy Types

| Policy Type | Description | Example |
|-------------|-------------|---------|
| **Time-based** | Keep for N days | 90 days |
| **Count-based** | Keep last N records | 100 records per source |
| **Size-based** | Keep until size limit | 1GB total |
| **Status-based** | Retain specific statuses | Keep only "failed" |
| **Tag-based** | Retain tagged records | Keep "important" tag |
| **Composite** | Combine multiple | Time AND status |

### Maintenance Tasks

- **Auto Cleanup**: Scheduled removal of old data
- **Cache Management**: LRU/LFU/TTL caching strategies
- **Database Optimization**: VACUUM and ANALYZE
- **Statistics Tracking**: Cleanup history and metrics

---

## Advanced Notifications

Enhanced notification system with routing, deduplication, and escalation.

### Provider Channels

Nine supported channels:
- Slack
- Email
- Webhook
- Discord
- Telegram
- PagerDuty
- OpsGenie
- Microsoft Teams
- GitHub Issues

### Rule-based Routing

Route notifications based on conditions:

- **Severity**: Critical, High, Medium, Low
- **Issue Count**: Number of issues detected
- **Pass Rate**: Percentage of passing validations
- **Time Window**: Time-based conditions
- **Tag**: Custom tags on sources
- **Data Asset**: Specific assets
- **Metadata**: Custom metadata fields
- **Status**: Validation status
- **Error**: Error message patterns

### Deduplication

Prevent duplicate notifications:

**Window Strategies:**
- **Sliding**: Rolling time window
- **Tumbling**: Non-overlapping windows
- **Session**: Gap-based sessions
- **Adaptive**: Dynamic window adjustment

**Policies:**
- **None**: No deduplication
- **Basic**: Simple fingerprinting
- **Severity-based**: Group by severity
- **Issue-based**: Group by issue type
- **Strict**: Exact match only
- **Custom**: User-defined rules

### Throttling

Limit notification frequency:

- **TokenBucket**: Burst allowed with refill rate
- **LeakyBucket**: Smooth rate limiting
- **FixedWindow**: Hard limit per time window
- **SlidingWindow**: Rolling window limit
- **Adaptive**: Dynamic rate adjustment

### Escalation

Multi-level escalation for critical alerts:

1. Initial notification to on-call engineer
2. If unacknowledged, escalate to team lead (after N minutes)
3. If still unacknowledged, escalate to management
4. Auto-resolve on successful validation

**State Machine:**
- Pending → Triggered → Acknowledged → Resolved
- Pending → Triggered → Escalated → Acknowledged → Resolved

---

## Unified Alerts

Centralized alert management across all features.

### Alert Sources

- Validation failures
- Drift detection
- Anomaly detection
- Schema changes
- Model performance degradation
- Schedule execution failures

### Features

- Severity filtering (Critical, High, Medium, Low)
- Alert correlation (group related alerts)
- Action tracking (acknowledged, resolved, commented)
- Alert history and timeline
- Search and filter

---

## Cross-Table Validation

Validate relationships between multiple tables.

### Validation Types

- **Referential Integrity**: Foreign key checks
- **Join Validation**: Verify join operations
- **Count Matching**: Row count comparisons
- **SQL Queries**: Custom SQL validation

### Example

```json
POST /api/v1/cross-alerts
{
  "name": "Order-Customer FK Check",
  "source_table_id": 1,
  "target_table_id": 2,
  "validation_type": "foreign_key",
  "source_column": "customer_id",
  "target_column": "id"
}
```

---

## Model Monitoring

Track ML model performance and data quality.

### Monitored Metrics

- **Classification**: Accuracy, Precision, Recall, F1, AUC-ROC
- **Regression**: MSE, RMSE, MAE, R²
- **Custom**: User-defined metrics

### Alert Rules

Set thresholds for automatic alerts:

```json
{
  "metric": "accuracy",
  "operator": "less_than",
  "threshold": 0.85,
  "severity": "high"
}
```

### Features

- Model registration and versioning
- Performance trend visualization
- Metric history tracking
- Automated retraining triggers

---

## Automated Triggers

Advanced trigger system for automated validation execution.

### Trigger Types

| Type | Description |
|------|-------------|
| **Cron** | Time-based with cron expressions |
| **Interval** | Every N seconds/minutes/hours |
| **Data Change** | Triggered by data modifications |
| **Composite** | AND/OR combinations of triggers |

### Data Change Detection

Triggers based on:
- Row count changes (threshold or percentage)
- Schema modifications
- File modification time
- Database table updates

### Composite Triggers

Combine multiple conditions:

```json
{
  "type": "composite",
  "operator": "OR",
  "triggers": [
    {"type": "cron", "expression": "0 9 * * *"},
    {"type": "data_change", "threshold": 1000}
  ]
}
```

---

## Performance Optimizations

### Caching

ML operations and expensive computations are cached:

- **Anomaly Detection**: Model training results
- **Drift Detection**: Distribution calculations
- **Profile Generation**: Statistical summaries
- **Rule Suggestions**: Generated rules

Cache strategies:
- **LRU**: Least Recently Used eviction
- **LFU**: Least Frequently Used eviction
- **TTL**: Time-To-Live expiration

### Large Dataset Handling

- **Sampling**: Automatic sampling for datasets > 1M rows
- **Chunked Processing**: Process data in chunks
- **Lazy Loading**: Load data on demand
- **Virtualization**: Render only visible items in UI

### Database Optimizations

- **Indexing**: Optimized indexes for common queries
- **Partitioning**: Time-based partitioning for large tables
- **VACUUM**: Regular cleanup of deleted records
- **ANALYZE**: Update query planner statistics
