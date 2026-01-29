# API Reference

This document describes the Truthound Dashboard REST API.

## Base URL

```
http://localhost:8765/api/v1
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

### Pagination Response

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## Health

### GET /health

Check server status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.1"
}
```

---

## Sources

### GET /sources

Retrieve all data sources.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "abc123",
      "name": "Sales Data",
      "type": "file",
      "config": { "path": "/data/sales.csv" },
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### POST /sources

Create a new data source.

**Request:**
```json
{
  "name": "Sales Data",
  "type": "file",
  "config": {
    "path": "/data/sales.csv"
  }
}
```

**Source Types:**
- `file` - Local file (CSV, Parquet)
- `postgresql` - PostgreSQL
- `mysql` - MySQL
- `snowflake` - Snowflake
- `bigquery` - BigQuery

**Config by Type:**

**File:**
```json
{
  "path": "/path/to/file.csv"
}
```

**PostgreSQL / MySQL:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "table": "my_table",
  "schema": "public"
}
```

**Snowflake:**
```json
{
  "account": "abc123.us-east-1",
  "warehouse": "COMPUTE_WH",
  "database": "MY_DB",
  "schema": "PUBLIC",
  "table": "MY_TABLE",
  "username": "user",
  "password": "password"
}
```

**BigQuery:**
```json
{
  "project": "my-project",
  "dataset": "my_dataset",
  "table": "my_table",
  "credentials_json": "{...}"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "abc123",
    "name": "Sales Data",
    "type": "file",
    "config": { "path": "/data/sales.csv" },
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /sources/{id}

Retrieve a specific source.

### PUT /sources/{id}

Update source information.

**Request:**
```json
{
  "name": "Updated Name",
  "config": { "path": "/new/path.csv" }
}
```

### DELETE /sources/{id}

Delete a source.

### POST /sources/{id}/test

Test source connection.

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "row_count": 10000,
  "column_count": 15
}
```

---

## Schema

### GET /sources/{id}/schema

Retrieve the learned schema for a source.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "schema123",
    "source_id": "abc123",
    "schema_yaml": "columns:\n  order_id:\n    dtype: int64\n    nullable: false\n    unique: true",
    "schema_json": {
      "columns": {
        "order_id": {
          "dtype": "int64",
          "nullable": false,
          "unique": true
        }
      }
    },
    "row_count": 10000,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### PUT /sources/{id}/schema

Save schema (manual edit).

**Request:**
```json
{
  "schema_yaml": "columns:\n  order_id:\n    dtype: int64\n    nullable: false"
}
```

### POST /sources/{id}/learn

Generate schema automatically (th.learn).

Analyzes data to automatically generate a schema.

**Response:**
```json
{
  "success": true,
  "data": {
    "columns": {
      "order_id": {
        "name": "order_id",
        "dtype": "int64",
        "nullable": false,
        "unique": true,
        "min_value": 1,
        "max_value": 99999
      },
      "status": {
        "name": "status",
        "dtype": "object",
        "nullable": false,
        "unique": false,
        "allowed_values": ["pending", "completed", "cancelled"]
      }
    },
    "row_count": 10000,
    "version": "1.0.0"
  }
}
```

---

## Validations

### POST /sources/{id}/validate

Run validation (th.check).

**Request (Simple Mode):**
```json
{
  "validators": ["Null", "Unique", "ColumnExists"],
  "schema_path": "/path/to/schema.yaml",
  "auto_schema": false
}
```

**Request (Advanced Mode with validator_configs):**
```json
{
  "validator_configs": [
    {
      "name": "Between",
      "enabled": true,
      "params": {
        "column": "price",
        "min_value": 0,
        "max_value": 10000
      },
      "severity_override": "high"
    },
    {
      "name": "Regex",
      "enabled": true,
      "params": {
        "column": "email",
        "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
      }
    }
  ],
  "columns": ["price", "email", "status"],
  "min_severity": "medium",
  "parallel": true,
  "max_workers": 4
}
```

**Parameters:**
- `validators` (optional): List of validator names to run (simple mode)
- `validator_configs` (optional): Per-validator configuration with params (advanced mode, takes precedence)
- `schema_path` (optional): Path to schema file
- `auto_schema` (optional): If true, auto-generate schema before validation
- `columns` (optional): Specific columns to validate
- `min_severity` (optional): Minimum severity to report (low, medium, high, critical)
- `strict` (optional): Raise exception on failures
- `parallel` (optional): Enable parallel execution
- `max_workers` (optional): Max threads for parallel (1-32)
- `pushdown` (optional): Enable SQL query pushdown

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "val123",
    "source_id": "abc123",
    "status": "success",
    "passed": false,
    "has_critical": true,
    "has_high": false,
    "total_issues": 3,
    "critical_issues": 1,
    "high_issues": 0,
    "row_count": 10000,
    "column_count": 15,
    "issues": [
      {
        "column": "email",
        "issue_type": "null_values",
        "count": 150,
        "severity": "critical",
        "details": "150 null values found in non-nullable column",
        "expected": "no null values",
        "actual": "150 null values (1.5%)"
      }
    ],
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:05Z"
  }
}
```

### GET /validations/{id}

Retrieve validation result details.

### GET /sources/{id}/validations

Retrieve validation history for a source.

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20)
- `status` (optional): "success", "failed", "error"

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "val123",
      "status": "success",
      "passed": true,
      "total_issues": 0,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

## Profile

### POST /sources/{id}/profile

Run data profiling (th.profile).

**Request:**
```json
{
  "sample_size": 10000
}
```

**Parameters:**
- `sample_size` (optional): Maximum rows to sample for profiling

**Response:**
```json
{
  "success": true,
  "data": {
    "source": "sales.csv",
    "row_count": 10000,
    "column_count": 15,
    "size_bytes": 1048576,
    "columns": [
      {
        "name": "order_id",
        "dtype": "int64",
        "null_count": 0,
        "null_percentage": 0.0,
        "unique_count": 10000,
        "unique_percentage": 100.0,
        "min": 1,
        "max": 10000,
        "mean": 5000.5,
        "std": 2886.89
      },
      {
        "name": "status",
        "dtype": "object",
        "null_count": 0,
        "null_percentage": 0.0,
        "unique_count": 3,
        "unique_percentage": 0.03,
        "top_values": [
          { "value": "completed", "count": 7500, "percentage": 75.0 },
          { "value": "pending", "count": 2000, "percentage": 20.0 },
          { "value": "cancelled", "count": 500, "percentage": 5.0 }
        ]
      }
    ]
  }
}
```

### GET /sources/{id}/profile

Retrieve the most recent profile result.

---

## Drift Detection

### POST /drift/compare

Compare two datasets (th.compare).

**Request:**
```json
{
  "baseline_source_id": "abc123",
  "current_source_id": "def456",
  "columns": ["price", "quantity"],
  "method": "psi",
  "threshold": 0.1,
  "correction": "bh",
  "sample_size": 10000
}
```

**Parameters:**
- `baseline_source_id` (required): Baseline source ID
- `current_source_id` (required): Current source ID to compare
- `columns` (optional): Columns to compare (null = all columns)
- `method` (optional): Detection method - auto, ks, psi, chi2, js, kl, wasserstein, cvm, anderson (default: auto)
- `threshold` (optional): Custom threshold (default varies by method)
- `correction` (optional): Multiple testing correction - none, bonferroni, holm, bh (default: bh for multiple columns)
- `sample_size` (optional): Sample size for large datasets

**Detection Methods:**
| Method | Use Case | Default Threshold |
|--------|----------|-------------------|
| auto | Smart selection based on data type | 0.05 |
| ks | Continuous distributions | 0.05 |
| psi | Industry standard, any distribution | 0.1 |
| chi2 | Categorical data | 0.05 |
| js | Symmetric, bounded (0-1) | 0.1 |
| kl | Information loss measure | 0.1 |
| wasserstein | Earth Mover's Distance | 0.1 |
| cvm | Sensitive to tail differences | 0.05 |
| anderson | Weighted for tail sensitivity | 0.05 |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "drift123",
    "has_drift": true,
    "has_high_drift": false,
    "drifted_columns": ["price", "quantity"],
    "columns": [
      {
        "name": "order_id",
        "has_drift": false,
        "drift_score": 0.02
      },
      {
        "name": "price",
        "has_drift": true,
        "drift_score": 0.45,
        "drift_type": "distribution_shift",
        "source_stats": { "mean": 100.5, "std": 25.3 },
        "target_stats": { "mean": 145.2, "std": 32.1 }
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /drift/{id}

Retrieve drift comparison result.

### GET /drift/comparisons

List drift comparisons with optional filters.

**Query Parameters:**
- `baseline_source_id` (optional): Filter by baseline source
- `current_source_id` (optional): Filter by current source
- `limit` (default: 20): Maximum results (1-100)

---

## Validators

### GET /validators

List all available validators with their parameter definitions.

**Query Parameters:**
- `category` (optional): Filter by category (schema, completeness, uniqueness, etc.)
- `search` (optional): Search by name, description, or tags

**Response:**
```json
[
  {
    "name": "Between",
    "display_name": "Value Between",
    "category": "distribution",
    "description": "Validates that values fall within a specified range",
    "parameters": [
      {
        "name": "column",
        "label": "Column",
        "type": "column",
        "required": true
      },
      {
        "name": "min_value",
        "label": "Minimum Value",
        "type": "float",
        "required": true
      },
      {
        "name": "max_value",
        "label": "Maximum Value",
        "type": "float",
        "required": true
      }
    ],
    "tags": ["distribution", "range", "bounds"],
    "severity_default": "medium"
  }
]
```

### GET /validators/categories

List all validator categories with metadata.

**Response:**
```json
[
  {
    "value": "schema",
    "label": "Schema",
    "description": "Validate structure, columns, and data types",
    "icon": "layout",
    "color": "#3b82f6",
    "validator_count": 14
  }
]
```

### GET /validators/{name}

Get a specific validator definition by name.

---

## PII Scan

### POST /scans/sources/{id}/scan

Run PII scan on a data source (th.scan).

**Request:**
```json
{
  "columns": ["email", "phone", "ssn"],
  "regulations": ["gdpr", "ccpa"],
  "min_confidence": 0.8
}
```

**Parameters:**
- `columns` (optional): Columns to scan (null = all columns)
- `regulations` (optional): Privacy regulations to check - gdpr, ccpa, lgpd
- `min_confidence` (optional): Confidence threshold (0.0-1.0, default: 0.8)

**Response:**
```json
{
  "id": "scan123",
  "source_id": "abc123",
  "status": "success",
  "total_columns_scanned": 15,
  "columns_with_pii": 3,
  "total_findings": 5,
  "has_violations": true,
  "total_violations": 2,
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
      "message": "SSN data requires explicit consent under GDPR",
      "severity": "high"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /scans/{id}

Get PII scan result by ID.

### GET /scans/sources/{id}/scans

List PII scan history for a source.

### GET /scans/sources/{id}/scans/latest

Get the most recent PII scan for a source.

---

## Data Masking

### POST /masks/sources/{id}/mask

Run data masking on a source (th.mask).

**Request:**
```json
{
  "columns": ["email", "ssn", "phone"],
  "strategy": "hash",
  "output_format": "csv"
}
```

**Parameters:**
- `columns` (optional): Columns to mask (null = auto-detect PII columns)
- `strategy` (optional): Masking strategy - redact, hash, fake (default: redact)
- `output_format` (optional): Output format - csv, parquet, json (default: csv)

**Masking Strategies:**
| Strategy | Description |
|----------|-------------|
| redact | Replace values with asterisks (e.g., "john@example.com" → "****") |
| hash | Replace with SHA256 hash (deterministic, can be used for joins) |
| fake | Replace with realistic fake data (e.g., "john@example.com" → "alice@test.org") |

**Response:**
```json
{
  "id": "mask123",
  "source_id": "abc123",
  "status": "success",
  "strategy": "hash",
  "output_path": "/tmp/masked_data.csv",
  "columns_masked": ["email", "ssn", "phone"],
  "auto_detected": false,
  "row_count": 10000,
  "column_count": 15,
  "duration_ms": 1500,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /masks/{id}

Get mask operation by ID.

### GET /masks/sources/{id}/masks

List mask operations for a source.

### GET /masks/sources/{id}/masks/latest

Get the most recent mask operation for a source.

---

## Schedules

### GET /schedules

Retrieve all schedules.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "sched123",
      "name": "Daily Sales Check",
      "source_id": "abc123",
      "cron_expression": "0 9 * * *",
      "is_active": true,
      "notify_on_failure": true,
      "last_run_at": "2024-01-15T09:00:00Z",
      "next_run_at": "2024-01-16T09:00:00Z",
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /schedules

Create a new schedule.

**Request:**
```json
{
  "name": "Daily Sales Check",
  "source_id": "abc123",
  "cron_expression": "0 9 * * *",
  "notify_on_failure": true
}
```

**Cron Expression Examples:**
- `0 9 * * *` - Daily at 9 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Every Monday at midnight
- `0 0 1 * *` - First day of each month at midnight

### GET /schedules/{id}

Retrieve schedule details.

### PUT /schedules/{id}

Update a schedule.

### DELETE /schedules/{id}

Delete a schedule.

### POST /schedules/{id}/pause

Pause a schedule.

### POST /schedules/{id}/resume

Resume a schedule.

### POST /schedules/{id}/run

Run a schedule immediately.

---

## Notifications

### GET /notifications/channels

Retrieve notification channels.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ch123",
      "name": "Dev Team Slack",
      "type": "slack",
      "is_active": true,
      "config_summary": "Webhook: ...abcdef",
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /notifications/channels

Create a new notification channel.

**Slack Channel:**
```json
{
  "name": "Dev Team Slack",
  "type": "slack",
  "config": {
    "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
  }
}
```

**Email Channel:**
```json
{
  "name": "Team Email",
  "type": "email",
  "config": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "user@gmail.com",
    "smtp_password": "app-password",
    "from_email": "alerts@company.com",
    "recipients": ["team@company.com", "lead@company.com"],
    "use_tls": true
  }
}
```

**Webhook Channel:**
```json
{
  "name": "Custom Webhook",
  "type": "webhook",
  "config": {
    "url": "https://api.example.com/webhook",
    "headers": {
      "Authorization": "Bearer token123"
    }
  }
}
```

### DELETE /notifications/channels/{id}

Delete a channel.

### POST /notifications/channels/{id}/test

Send a test notification.

**Response:**
```json
{
  "success": true,
  "message": "Test sent"
}
```

### GET /notifications/rules

Retrieve notification rules.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "rule123",
      "name": "Alert on Critical Issues",
      "condition": "validation_failed",
      "condition_value": null,
      "channel_ids": ["ch123", "ch456"],
      "is_active": true,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /notifications/rules

Create a new notification rule.

**Request:**
```json
{
  "name": "Alert on Critical Issues",
  "condition": "validation_failed",
  "condition_value": null,
  "channel_ids": ["ch123"]
}
```

**Condition Types:**
- `validation_failed` - When validation fails
- `critical_issues` - When critical severity issues occur
- `high_issues` - When high severity issues occur
- `schedule_failed` - When scheduled execution fails

### DELETE /notifications/rules/{id}

Delete a rule.

### GET /notifications/logs

Retrieve notification delivery logs.

**Query Parameters:**
- `limit` (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "log123",
      "channel_id": "ch123",
      "status": "sent",
      "message": "Validation Failed: Sales Data...",
      "error": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Business Glossary

### GET /glossary/terms

Retrieve glossary terms.

**Query Parameters:**
- `search` (optional): Search term names and definitions
- `category_id` (optional): Filter by category
- `status` (optional): Filter by status (`draft`, `approved`, `deprecated`)
- `page` (default: 1)
- `per_page` (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "term123",
      "name": "Customer",
      "definition": "An individual or organization that purchases products",
      "category_id": "cat123",
      "category_name": "Business",
      "status": "approved",
      "owner": "data-team",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### POST /glossary/terms

Create a new term.

**Request:**
```json
{
  "name": "Customer",
  "definition": "An individual or organization that purchases products",
  "category_id": "cat123",
  "status": "draft",
  "owner": "data-team"
}
```

### GET /glossary/terms/{id}

Retrieve term details including relationships.

### PUT /glossary/terms/{id}

Update a term. Changes are automatically tracked in history.

### DELETE /glossary/terms/{id}

Delete a term.

### GET /glossary/terms/{id}/history

Retrieve term change history.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "hist123",
      "term_id": "term123",
      "field_name": "definition",
      "old_value": "Previous definition",
      "new_value": "Updated definition",
      "changed_by": "user@example.com",
      "changed_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### GET /glossary/terms/{id}/relationships

Retrieve term relationships.

### GET /glossary/categories

Retrieve all categories.

### POST /glossary/categories

Create a new category.

**Request:**
```json
{
  "name": "Business",
  "description": "Business-related terms",
  "parent_id": null
}
```

### PUT /glossary/categories/{id}

Update a category.

### DELETE /glossary/categories/{id}

Delete a category.

### POST /glossary/relationships

Create a relationship between terms.

**Request:**
```json
{
  "source_term_id": "term123",
  "target_term_id": "term456",
  "relationship_type": "synonym"
}
```

**Relationship Types:**
- `synonym` - Terms with the same meaning
- `related` - Related terms

### DELETE /glossary/relationships/{id}

Delete a relationship.

---

## Data Catalog

### GET /catalog/assets

Retrieve data assets.

**Query Parameters:**
- `search` (optional): Search asset names and descriptions
- `asset_type` (optional): Filter by type (`table`, `file`, `api`)
- `source_id` (optional): Filter by data source
- `page` (default: 1)
- `per_page` (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "asset123",
      "name": "customers",
      "asset_type": "table",
      "description": "Customer master data",
      "source_id": "src123",
      "source_name": "Production DB",
      "owner": "data-team",
      "quality_score": 85,
      "column_count": 12,
      "tag_count": 3,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### POST /catalog/assets

Create a new asset.

**Request:**
```json
{
  "name": "customers",
  "asset_type": "table",
  "description": "Customer master data",
  "source_id": "src123",
  "owner": "data-team",
  "quality_score": 85
}
```

### GET /catalog/assets/{id}

Retrieve asset details including columns and tags.

### PUT /catalog/assets/{id}

Update an asset.

### DELETE /catalog/assets/{id}

Delete an asset.

### GET /catalog/assets/{id}/columns

Retrieve asset columns.

### POST /catalog/assets/{id}/columns

Add a column to an asset.

**Request:**
```json
{
  "name": "customer_id",
  "data_type": "integer",
  "description": "Unique customer identifier",
  "is_nullable": false,
  "is_primary_key": true,
  "sensitivity_level": "internal"
}
```

**Sensitivity Levels:**
- `public` - No restrictions
- `internal` - Internal use only
- `confidential` - Restricted access
- `restricted` - Highly sensitive

### PUT /catalog/columns/{id}

Update a column.

### DELETE /catalog/columns/{id}

Delete a column.

### PUT /catalog/columns/{id}/term

Map a column to a glossary term.

**Request:**
```json
{
  "term_id": "term123"
}
```

### DELETE /catalog/columns/{id}/term

Remove column-term mapping.

### GET /catalog/assets/{id}/tags

Retrieve asset tags.

### POST /catalog/assets/{id}/tags

Add a tag to an asset.

**Request:**
```json
{
  "tag_name": "domain",
  "tag_value": "sales"
}
```

### DELETE /catalog/tags/{id}

Delete a tag.

---

## Collaboration

### GET /comments

Retrieve comments for a resource.

**Query Parameters:**
- `resource_type` (required): `term`, `asset`, or `column`
- `resource_id` (required): ID of the resource

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "cmt123",
      "resource_type": "term",
      "resource_id": "term123",
      "content": "This definition needs clarification",
      "author": "user@example.com",
      "parent_id": null,
      "replies": [],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### POST /comments

Create a comment.

**Request:**
```json
{
  "resource_type": "term",
  "resource_id": "term123",
  "content": "This definition needs clarification",
  "author": "user@example.com",
  "parent_id": null
}
```

### PUT /comments/{id}

Update a comment.

### DELETE /comments/{id}

Delete a comment.

### GET /activities

Retrieve activity feed.

**Query Parameters:**
- `resource_type` (optional): Filter by resource type
- `resource_id` (optional): Filter by resource ID
- `limit` (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "act123",
      "resource_type": "term",
      "resource_id": "term123",
      "action": "updated",
      "actor": "user@example.com",
      "description": "Updated term definition",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Action Types:**
- `created` - Resource created
- `updated` - Resource updated
- `deleted` - Resource deleted
- `commented` - Comment added

---

## Advanced Features

### Anomaly Detection

#### POST /anomaly/detect

Run ML-based anomaly detection.

**Request:**
```json
{
  "source_id": "abc123",
  "algorithms": ["IsolationForest", "LOF"],
  "contamination": 0.1,
  "columns": ["price", "quantity"]
}
```

**Algorithms:**
- `IsolationForest` - Tree-based isolation
- `LOF` - Local Outlier Factor
- `DBSCAN` - Density-based clustering
- `OneClassSVM` - SVM-based boundary
- `EllipticEnvelope` - Gaussian distribution

---

### Data Lineage

#### GET /lineage

Retrieve data lineage information.

#### POST /lineage/openlineage/webhook

Configure OpenLineage webhook.

**Request:**
```json
{
  "url": "https://your-lineage-backend.com/api/lineage",
  "auth_header": "Bearer token",
  "events": ["START", "COMPLETE", "FAIL"]
}
```

---

### Schema Evolution

#### GET /schema-evolution/{source_id}

Get schema change history.

**Response:**
```json
{
  "success": true,
  "data": {
    "changes": [
      {
        "version": 2,
        "change_type": "column_added",
        "column": "new_column",
        "breaking": false,
        "detected_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### Advanced Notifications

#### GET /notifications-advanced/routing

Get routing rules.

#### POST /notifications-advanced/routing

Create routing rule.

**Request:**
```json
{
  "name": "Critical to PagerDuty",
  "condition": {
    "type": "severity",
    "operator": "equals",
    "value": "critical"
  },
  "actions": ["pagerduty", "slack"]
}
```

#### GET /notifications-advanced/dedup

Get deduplication settings.

#### GET /notifications-advanced/throttle

Get throttling settings.

#### GET /notifications-advanced/escalation

Get escalation policies.

---

### Model Monitoring

#### POST /model-monitoring/models

Register a model for monitoring.

**Request:**
```json
{
  "name": "fraud_detector",
  "version": "1.0.0",
  "metrics": ["accuracy", "precision", "recall"],
  "thresholds": {
    "accuracy": {"operator": "less_than", "value": 0.85}
  }
}
```

#### POST /model-monitoring/metrics

Record model metrics.

---

### Triggers

#### GET /triggers

List all triggers.

#### POST /triggers

Create a trigger.

**Request:**
```json
{
  "name": "Daily validation",
  "type": "cron",
  "expression": "0 9 * * *",
  "source_id": "abc123",
  "is_active": true
}
```

#### POST /triggers/webhook

External webhook trigger endpoint.

---

### Plugins

#### GET /plugins

List available plugins.

#### POST /plugins/{id}/install

Install a plugin.

#### POST /plugins/{id}/uninstall

Uninstall a plugin.

#### GET /validators/custom

List custom validators.

#### POST /validators/custom

Create custom validator.

**Request:**
```json
{
  "name": "custom_check",
  "code": "def validate(df, column): ...",
  "description": "Custom validation logic"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `SOURCE_NOT_FOUND` | Data source not found |
| `VALIDATION_ERROR` | Error during validation execution |
| `CONNECTION_ERROR` | Database connection failed |
| `SCHEDULE_ERROR` | Scheduled task failed |
| `NOTIFICATION_ERROR` | Notification delivery failed |
| `RATE_LIMIT_EXCEEDED` | Request limit exceeded |
| `INTERNAL_ERROR` | Internal server error |

---

## Rate Limiting

By default, requests are limited to 120 per minute.

When rate limit is exceeded:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later."
  }
}
```

---

## Authentication (Optional)

When authentication is enabled, all API requests require Basic Auth headers:

```bash
curl -u :password http://localhost:8765/api/v1/health
```

Enable authentication via environment variables:
```bash
TRUTHOUND_AUTH_ENABLED=true
TRUTHOUND_AUTH_PASSWORD=your-secret-password
```
