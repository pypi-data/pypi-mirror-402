# Features

This document provides detailed descriptions of all Truthound Dashboard features.

## Data Sources

Connect and manage various data sources.

### Supported Source Types

| Type | Description | Config Fields |
|------|-------------|---------------|
| **File** | Local CSV, Parquet files | `path` |
| **PostgreSQL** | PostgreSQL database | `host`, `port`, `database`, `username`, `password`, `table` |
| **MySQL** | MySQL database | `host`, `port`, `database`, `username`, `password`, `table` |
| **Snowflake** | Snowflake data warehouse | `account`, `warehouse`, `database`, `schema`, `table` |
| **BigQuery** | Google BigQuery | `project`, `dataset`, `table`, `credentials_json` |

### Source Management

- **CRUD Operations**: Add, update, and delete data sources
- **Connection Testing**: Verify source connectivity
- **Table Listing**: Browse database tables
- **Activation Control**: Enable or disable sources

---

## Schema Management

Automatically learn or manually edit data schemas.

### Auto Schema Generation (th.learn)

Analyze data to automatically generate schemas using `th.learn`.

**Information Captured:**
- Column names and data types
- Nullable status (when null values exist)
- Unique constraints (when all values are unique)
- Numeric columns: min and max values
- String columns: allowed values for low-cardinality fields

**Example Output:**
```yaml
columns:
  order_id:
    dtype: int64
    nullable: false
    unique: true
    min_value: 1
    max_value: 99999

  status:
    dtype: object
    nullable: false
    allowed_values:
      - pending
      - completed
      - cancelled

  amount:
    dtype: float64
    nullable: true
    min_value: 0.0
    max_value: 10000.0
```

### Manual Schema Editing

Edit schemas directly in YAML format through the UI.

**Editable Properties:**
- `dtype`: Data type (int64, float64, object, datetime64, bool)
- `nullable`: Allow null values
- `unique`: Enforce unique values
- `min_value` / `max_value`: Numeric range
- `allowed_values`: List of allowed values
- `regex`: Regular expression pattern

---

## Validation

Execute data quality validations and review results.

### Validator Registry

Dashboard supports 150+ validators across 15 categories:

| Category | Description | Count |
|----------|-------------|-------|
| **Schema** | Structure, columns, data types | 14 |
| **Completeness** | Null values, missing data | 7 |
| **Uniqueness** | Duplicates, keys | 13 |
| **Distribution** | Value ranges, distributions | 15 |
| **String** | Pattern matching, format validation | 17 |
| **Datetime** | Date/time format and range | 10 |
| **Aggregate** | Statistical checks (mean, sum) | 8 |
| **Cross-Table** | Multi-table relationships | 5 |
| **Multi-Column** | Column relationships | 3 |
| **Query** | Expression-based validation | 2 |
| **Table** | Table metadata validation | 4 |
| **Geospatial** | Geographic coordinates | 4 |
| **Drift** | Distribution change detection | 5 |
| **Anomaly** | ML-based outlier detection | 6 |
| **Privacy** | PII detection, compliance | 3 |

### Validator Configuration

Configure individual validators with parameters:
- Per-validator parameter input forms
- Severity override support
- Real-time validation

### Validation Result

Validation results include:

```json
{
  "passed": false,
  "has_critical": true,
  "has_high": false,
  "total_issues": 3,
  "issues": [
    {
      "column": "email",
      "issue_type": "null_values",
      "count": 150,
      "severity": "critical",
      "details": "150 null values found",
      "expected": "no null values",
      "actual": "150 null values (1.5%)"
    }
  ]
}
```

### Issue Severity

| Severity | Description |
|----------|-------------|
| **Critical** | Requires immediate attention (e.g., null in required column) |
| **High** | Significant data quality issue |
| **Medium** | Issue requiring attention |
| **Low** | Minor issue |

---

## Validation History

Track data quality changes over time.

### Features

- **Trend Charts**: Visualize validation results
- **Failure Analysis**: Identify frequently failing validations
- **Filtering**: Filter by status and date range
- **Detail View**: Examine individual validation results

### Use Cases

1. **Quality Monitoring**: Track data quality trends
2. **Issue Tracking**: Analyze causes of quality degradation
3. **Reporting**: Generate periodic quality reports

---

## Data Profiling

Analyze statistical characteristics of data.

### Profile Information

**Overall Statistics:**
- Row count
- Column count
- File size (bytes)

**Per-Column Statistics:**
- Null count and percentage
- Unique value count and percentage
- Numeric: min, max, mean, std
- String: Top N values and frequencies

### Visualization

- Data type distribution charts
- Null percentage heatmap
- Numeric column distributions
- Categorical value frequencies

---

## Drift Detection

Compare two datasets to detect changes using th.compare().

### Use Cases

1. **Version Comparison**: Compare yesterday vs. today data
2. **Environment Comparison**: Production vs. Staging
3. **Model Monitoring**: Training vs. Serving data

### Detection Methods

| Method | Use Case | Description |
|--------|----------|-------------|
| **auto** | Smart selection | Automatically selects method based on data type |
| **ks** | Continuous data | Kolmogorov-Smirnov test |
| **psi** | Any distribution | Population Stability Index (industry standard) |
| **chi2** | Categorical data | Chi-Square test |
| **js** | Probability distributions | Jensen-Shannon divergence (symmetric, bounded) |

### Sampling Strategies

For large datasets, dashboard supports 4 sampling strategies:

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Random** | Simple random sampling | Unbiased sampling |
| **Stratified** | Proportional sampling by strata | Maintaining class distribution |
| **Reservoir** | Stream-based sampling | Large datasets or streaming data |
| **Systematic** | Every nth row | Fast sampling |

### Drift Monitoring Features

- **Trend Visualization**: Historical drift scores over time
- **Alerting**: Configurable thresholds for drift detection
- **Root Cause Analysis**: Identify columns causing drift
- **Remediation Suggestions**: Actionable recommendations
- **Large Dataset Support**: Chunked processing for datasets over 1M rows

### Comparison Result

```json
{
  "has_drift": true,
  "has_high_drift": false,
  "total_columns": 10,
  "drifted_columns": 2,
  "drift_percentage": 20.0,
  "columns": [
    {
      "column": "price",
      "drifted": true,
      "level": "medium",
      "method": "psi",
      "statistic": 0.15,
      "p_value": 0.02
    }
  ]
}
```

---

## PII Scan

Detect personally identifiable information in datasets using th.scan().

### Supported PII Types

- Email addresses
- Phone numbers
- Social Security Numbers (SSN)
- Credit card numbers
- IP addresses
- Dates of birth
- Physical addresses
- Personal names
- Passport numbers
- Driver's license numbers
- National ID numbers
- Bank account numbers
- Medical record numbers
- Biometric data

### Regulation Compliance

Check compliance with privacy regulations:

| Regulation | Description |
|------------|-------------|
| **GDPR** | EU General Data Protection Regulation |
| **CCPA** | California Consumer Privacy Act |
| **LGPD** | Brazil's General Data Protection Law |

### Scan Result

```json
{
  "total_columns_scanned": 15,
  "columns_with_pii": 3,
  "total_findings": 5,
  "findings": [
    {
      "column": "email",
      "pii_type": "email",
      "confidence": 0.95,
      "sample_count": 1000
    }
  ],
  "violations": [
    {
      "regulation": "gdpr",
      "column": "ssn",
      "pii_type": "ssn",
      "severity": "high"
    }
  ]
}
```

---

## Data Masking

Protect sensitive data using th.mask().

### Masking Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| **redact** | Replace with asterisks | `john@example.com` → `****` |
| **hash** | SHA256 hash (deterministic) | `john@example.com` → `a1b2c3...` |
| **fake** | Realistic fake data | `john@example.com` → `alice@test.org` |

### Features

- Auto-detection of PII columns
- Multiple output formats (CSV, Parquet, JSON)
- Deterministic hashing for join preservation
- Realistic fake data generation

### Mask Result

```json
{
  "strategy": "hash",
  "columns_masked": ["email", "ssn", "phone"],
  "auto_detected": true,
  "row_count": 10000,
  "output_path": "/tmp/masked_data.csv"
}
```

---

## Scheduled Validations

Configure automated validation runs using cron expressions.

### Cron Expression

Standard cron expression format:

```
minute hour day month weekday
*      *    *   *     *
```

**Examples:**
| Expression | Description |
|------------|-------------|
| `0 9 * * *` | Daily at 9 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 0 * * 1` | Every Monday at midnight |
| `0 0 1 * *` | First day of each month |
| `*/30 * * * *` | Every 30 minutes |

### Schedule Management

- **Create**: Add new schedules
- **Update**: Modify schedule settings
- **Delete**: Remove schedules
- **Pause/Resume**: Toggle schedule activation
- **Run Now**: Execute immediately

### Failure Notification

Receive notifications via configured channels when scheduled validations fail.

---

## Notifications

Receive alerts through various channels when validations fail.

### Supported Channels

#### Slack

Send notifications to Slack channels via webhook URL.

**Configuration:**
```json
{
  "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
}
```

**Message Format:**
```
Validation Failed

Source: Sales Data
Severity: Critical
Total Issues: 3
Validation ID: val123
```

#### Email

Send email notifications via SMTP.

**Configuration:**
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "user@gmail.com",
  "smtp_password": "app-password",
  "from_email": "alerts@company.com",
  "recipients": ["team@company.com"],
  "use_tls": true
}
```

#### Webhook

Send JSON payloads to custom HTTP endpoints.

**Configuration:**
```json
{
  "url": "https://api.example.com/webhook",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

**Payload Format:**
```json
{
  "event": "validation_failed",
  "source": "Sales Data",
  "has_critical": true,
  "has_high": false,
  "total_issues": 3,
  "validation_id": "val123"
}
```

### Notification Rules

Configure rules to trigger notifications based on conditions.

| Condition | Description |
|-----------|-------------|
| `validation_failed` | When validation fails |
| `critical_issues` | When critical issues occur |
| `high_issues` | When high severity issues occur |
| `schedule_failed` | When scheduled execution fails |

---

## Business Glossary

Manage business terminology with definitions, categories, and relationships.

### Term Management

- **CRUD Operations**: Create, read, update, and delete business terms
- **Categories**: Organize terms into hierarchical categories
- **Status Tracking**: Track term lifecycle (draft, approved, deprecated)
- **Change History**: Automatic tracking of all term modifications

### Term Relationships

Define connections between terms:

| Relationship Type | Description |
|-------------------|-------------|
| **Synonym** | Terms with the same meaning |
| **Related** | Terms that are conceptually related |

### Search and Filter

- Full-text search across term names and definitions
- Filter by category
- Filter by status

---

## Data Catalog

Register and manage data assets with metadata.

### Asset Types

| Type | Description |
|------|-------------|
| **Table** | Database tables |
| **File** | Data files (CSV, Parquet, etc.) |
| **API** | API endpoints |

### Asset Management

- **Registration**: Register data assets with descriptions
- **Source Linking**: Link assets to data sources
- **Quality Score**: Track data quality (0-100 scale)
- **Ownership**: Assign asset owners

### Column Metadata

Manage column-level information:

- Column name and data type
- Description
- Nullable and primary key flags
- Term mapping (link columns to glossary terms)
- Sensitivity classification

### Sensitivity Levels

| Level | Description |
|-------|-------------|
| **Public** | No restrictions |
| **Internal** | Internal use only |
| **Confidential** | Restricted access |
| **Restricted** | Highly sensitive data |

### Tagging

Apply custom tags to assets for flexible categorization.

---

## Collaboration

Enable team collaboration on data assets.

### Comments

- Add comments to terms, assets, and columns
- Threaded replies for discussions
- Edit and delete own comments

### Activity Feed

Track all changes across the system:

- Term creation, updates, and deletion
- Asset modifications
- Comment activity
- Column-term mappings

---

## UI Features

### Dark Mode

Select theme manually or follow system settings.

- Light Mode
- Dark Mode
- System (automatic)

### Internationalization (i18n)

Multiple languages supported:

- English (en)
- Korean (ko)

Language is auto-detected from browser settings or can be changed manually.

### Responsive Design

Optimized for various screen sizes:

- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (< 768px)

---

## Security Features

### Connection Encryption

Database connection credentials (passwords, etc.) are encrypted at rest.

- Fernet symmetric encryption
- Device-specific keys auto-generated
- Automatic detection and encryption of sensitive fields

### Rate Limiting

API requests are limited to 120 per minute by default.

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### Optional Authentication

Enable password protection when needed.

---

## Performance

### Large Dataset Handling

Large datasets are automatically sampled:
- Files over 100MB: automatic sampling
- Default sample size: 100,000 rows
- Configurable via settings

### Caching

Frequently accessed data is cached:
- Source list: 30-second TTL
- Profile results: 5-minute TTL

### Database Maintenance

Automatic cleanup tasks are scheduled:
- Delete validation results older than 90 days
- Delete notification logs older than 30 days
- Weekly VACUUM execution

---

## Reports & Export

Generate and manage validation reports in multiple formats.

### Features

- **Multi-Format Export**: HTML, PDF, CSV, JSON, Excel, Markdown
- **Report Types**: Validation, Drift Detection, PII Scan, Profile, Anomaly, Model Monitoring
- **Statistics Dashboard**:
  - Total Reports count
  - Total Size (MB/GB)
  - Total Downloads
  - Average Generation Time
  - Expired Reports count
  - Reporters Used count

### Report Management

**Search & Filter**:
- Search by report name
- Filter by format (HTML/PDF/CSV/JSON/Excel/Markdown)
- Filter by status (Pending/Generating/Completed/Failed)
- Include/exclude expired reports toggle

**Report Actions**:
- Download reports
- Delete individual reports
- Cleanup expired reports (batch operation)

**Report History**:
- View generation timestamp
- Track expiration dates
- Monitor download counts
- Review file sizes

**Pagination**: Navigate large report lists

### Customization

- **Themes**: Apply color themes to HTML/PDF reports
- **Custom Reporters**: Create custom report formats via plugin system

---

## Plugins

Extend Truthound with custom validators, reporters, connectors, and transformers.

### Plugin Marketplace

Browse and install community plugins:

- **Plugin Types**:
  - **Validators**: Custom validation logic
  - **Reporters**: Custom report formats
  - **Connectors**: Data source integrations
  - **Transformers**: Data transformation logic

- **Plugin Information**:
  - Name, version, author
  - Description and documentation
  - Security level (Trusted/Verified/Unverified/Sandboxed)
  - Install count and rating
  - Last update date

### Plugin Management

**5 Management Tabs**:
1. **Marketplace**: Discover and install plugins
2. **Installed**: Manage installed plugins
3. **Validators**: Custom validator registry
4. **Reporters**: Custom reporter registry
5. **Settings**: Plugin system configuration

**Plugin Operations**:
- Install/Uninstall plugins
- Enable/Disable plugins
- View plugin details
- Security warnings for unverified plugins

**Filter & Search**:
- Filter by type (validator/reporter/connector/transformer)
- Filter by status (available/installed/enabled/disabled)
- Search by name/description

### Custom Validators

Create custom validation logic:

**Configuration Fields**:
- Validator name and code
- Severity level (Critical/Warning/Info)
- Category assignment
- Tags for organization
- Parameters (name, type, default, required)

**Validation Types**:
- Column-level validators
- Row-level validators
- Table-level validators

### Custom Reporters

Create custom report formats:

**Configuration Fields**:
- Reporter name and code
- Output format
- Template support
- File extension

**Supported Outputs**:
- HTML, PDF, CSV, JSON
- Excel, Markdown
- Custom formats

### Plugin Statistics

Monitor plugin ecosystem:

- Total Plugins count
- Total Validators count
- Total Reporters count
- Installed Plugins count
- Enabled Plugins count

---

## Maintenance & System Health

Manage data retention, perform database maintenance, and monitor cache performance.

### Auto Maintenance

Schedule automatic maintenance tasks:

- **Enable/Disable**: Toggle auto maintenance on/off
- **Last Run**: View last execution timestamp
- **Next Scheduled Run**: Preview upcoming maintenance window

### Retention Policies

Configure data retention settings:

**Validation Retention Days** (1-365 days):
- Keep validation run results
- Default: 90 days
- Older records auto-deleted

**Profile Keep Per Source** (1-100 count):
- Number of profile snapshots to retain per data source
- Default: 10 profiles
- Prevents profile history bloat

**Notification Log Retention Days** (1-365 days):
- Keep notification delivery logs
- Default: 30 days
- Older logs auto-purged

**Run Vacuum on Cleanup** (toggle):
- Execute SQLite VACUUM after cleanup
- Reclaims disk space
- May increase cleanup duration

### Manual Operations

Execute maintenance tasks on-demand:

**Run Cleanup**:
- Remove expired validation runs
- Remove old notification logs
- Remove excess profile snapshots
- Progress indicator during execution

**Run Vacuum**:
- Optimize SQLite database file
- Reclaim unused space
- Rebuild internal structures
- May lock database briefly

**Clear Cache**:
- Invalidate all cached entries
- Force fresh data retrieval
- Useful after bulk data changes

### Cache Statistics

Monitor cache performance:

- **Total Entries**: All cached items
- **Valid Entries**: Non-expired cache items
- **Expired Entries**: Outdated cache items
- **Hit Rate**: Cache effectiveness percentage

### Configuration Persistence

- **Save Button**: Persist retention policy changes
- **Validation**: Range checks on input values
- **Real-time Updates**: Settings apply immediately after save

---

## Advanced Features

For detailed documentation on advanced features, see [Advanced Features](./advanced-features.md).

### Quick Reference

| Feature | Description | Endpoint |
|---------|-------------|----------|
| **Anomaly Detection** | ML-based outlier detection | `/anomaly` |
| **Data Lineage** | Data flow visualization | `/lineage` |
| **Schema Evolution** | Schema change tracking | `/schema-evolution` |
| **Result Versioning** | Validation result versioning | `/versioning` |
| **Profile Comparison** | Profile trend analysis | `/profile-comparison` |
| **Rule Suggestions** | AI-powered rule generation | `/rule-suggestions` |
| **Model Monitoring** | ML model performance tracking | `/model-monitoring` |
| **Advanced Notifications** | Routing, deduplication, escalation | `/notifications-advanced` |
| **Triggers** | Advanced trigger system | `/triggers` |
