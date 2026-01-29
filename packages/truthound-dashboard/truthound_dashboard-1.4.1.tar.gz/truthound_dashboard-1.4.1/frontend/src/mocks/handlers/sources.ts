/**
 * Sources API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getStore,
  getAll,
  getById,
  create,
  update,
  remove,
  cleanupOrphanedData,
} from '../data/store'
import { createId } from '../factories'
import type { Source, SourceType } from '@/api/client'

const API_BASE = '/api/v1'

export const sourcesHandlers = [
  // List sources
  http.get(`${API_BASE}/sources`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let sources = getAll(getStore().sources)

    if (activeOnly) {
      sources = sources.filter((s) => s.is_active)
    }

    // Sort by created_at desc
    sources.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = sources.length
    const paginated = sources.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get source by ID
  http.get(`${API_BASE}/sources/:id`, async ({ params }) => {
    await delay(150)

    const source = getById(getStore().sources, params.id as string)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: source,
    })
  }),

  // Create source
  http.post(`${API_BASE}/sources`, async ({ request }) => {
    await delay(300)

    let body: {
      name: string
      type: string
      config: Record<string, unknown>
      description?: string
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const now = new Date().toISOString()

    // Create source with all provided data directly, not using factory defaults for user-provided fields
    const newSource: Source = {
      id: createId(),
      name: body.name,
      type: body.type as SourceType,
      config: body.config,
      description: body.description ?? '',
      is_active: true,
      has_schema: false,
      created_at: now,
      updated_at: now,
      last_validated_at: undefined,
      latest_validation_status: undefined,
    }

    create(getStore().sources, newSource)

    return HttpResponse.json({
      success: true,
      data: newSource,
    }, { status: 201 })
  }),

  // Update source
  http.put(`${API_BASE}/sources/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<{
      name: string
      config: Record<string, unknown>
      description: string
      is_active: boolean
    }>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Get existing source to merge config properly
    const existing = getById(getStore().sources, params.id as string)
    if (!existing) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Merge config with existing config (for partial updates)
    const updatedBody = { ...body }
    if (body.config && existing.config) {
      updatedBody.config = { ...existing.config, ...body.config }
    }

    const updated = update(getStore().sources, params.id as string, updatedBody)

    return HttpResponse.json({
      success: true,
      data: updated,
    })
  }),

  // Delete source
  http.delete(`${API_BASE}/sources/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().sources, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Clean up orphaned data (schedules, validations, schemas) referencing this source
    cleanupOrphanedData()

    return HttpResponse.json({ success: true, message: 'Source deleted successfully' })
  }),

  // Test source connection
  http.post(`${API_BASE}/sources/:id/test`, async ({ params }) => {
    await delay(500)

    const source = getById(getStore().sources, params.id as string)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Simulate 90% success rate
    const success = Math.random() > 0.1

    return HttpResponse.json({
      success: true,
      data: {
        success,
        message: success ? 'Connection successful' : undefined,
        error: success ? undefined : 'Connection timeout after 30s',
      },
    })
  }),

  // Get supported source types with full field definitions
  http.get(`${API_BASE}/sources/types/supported`, async () => {
    await delay(100)

    return HttpResponse.json({
      success: true,
      data: {
        types: [
          // File Sources
          {
            type: 'file',
            name: 'File',
            description: 'Local file (CSV, Parquet, JSON, Excel)',
            icon: 'file',
            category: 'file',
            fields: [
              { name: 'path', label: 'File Path', type: 'file_path', required: true, placeholder: '/path/to/data.csv', description: 'Path to the data file' },
              { name: 'format', label: 'Format', type: 'select', options: [{ value: 'auto', label: 'Auto-detect' }, { value: 'csv', label: 'CSV' }, { value: 'parquet', label: 'Parquet' }, { value: 'json', label: 'JSON' }, { value: 'excel', label: 'Excel' }], default: 'auto', description: 'File format' },
              { name: 'delimiter', label: 'Delimiter', type: 'text', placeholder: ',', default: ',', description: 'CSV delimiter', depends_on: 'format', depends_value: 'csv' },
              { name: 'encoding', label: 'Encoding', type: 'select', options: [{ value: 'utf-8', label: 'UTF-8' }, { value: 'utf-16', label: 'UTF-16' }, { value: 'iso-8859-1', label: 'ISO-8859-1' }], default: 'utf-8', description: 'File encoding' },
              { name: 'has_header', label: 'Has Header Row', type: 'boolean', default: true, description: 'First row contains column names' },
            ],
            required_fields: ['path'],
            optional_fields: ['format', 'delimiter', 'encoding', 'has_header'],
          },
          // Database Sources
          {
            type: 'postgresql',
            name: 'PostgreSQL',
            description: 'PostgreSQL database',
            icon: 'database',
            category: 'database',
            docs_url: 'https://www.postgresql.org/docs/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'localhost', description: 'Database server hostname' },
              { name: 'port', label: 'Port', type: 'number', default: 5432, min_value: 1, max_value: 65535, description: 'Database port' },
              { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'mydb', description: 'Database name' },
              { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'postgres', description: 'Database username' },
              { name: 'password', label: 'Password', type: 'password', description: 'Database password' },
              { name: 'schema', label: 'Schema', type: 'text', placeholder: 'public', default: 'public', description: 'Database schema' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
              { name: 'ssl_mode', label: 'SSL Mode', type: 'select', options: [{ value: 'disable', label: 'Disable' }, { value: 'require', label: 'Require' }, { value: 'verify-full', label: 'Verify Full' }], default: 'disable', description: 'SSL connection mode' },
            ],
            required_fields: ['host', 'database', 'username'],
            optional_fields: ['port', 'password', 'schema', 'table', 'ssl_mode'],
          },
          {
            type: 'mysql',
            name: 'MySQL',
            description: 'MySQL database',
            icon: 'database',
            category: 'database',
            docs_url: 'https://dev.mysql.com/doc/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'localhost', description: 'Database server hostname' },
              { name: 'port', label: 'Port', type: 'number', default: 3306, min_value: 1, max_value: 65535, description: 'Database port' },
              { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'mydb', description: 'Database name' },
              { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'root', description: 'Database username' },
              { name: 'password', label: 'Password', type: 'password', description: 'Database password' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
              { name: 'ssl', label: 'Use SSL', type: 'boolean', default: false, description: 'Enable SSL connection' },
            ],
            required_fields: ['host', 'database', 'username'],
            optional_fields: ['port', 'password', 'table', 'ssl'],
          },
          {
            type: 'sqlite',
            name: 'SQLite',
            description: 'SQLite database file',
            icon: 'database',
            category: 'database',
            docs_url: 'https://www.sqlite.org/docs.html',
            fields: [
              { name: 'path', label: 'Database Path', type: 'file_path', required: true, placeholder: '/path/to/database.db', description: 'Path to SQLite database file' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
            ],
            required_fields: ['path'],
            optional_fields: ['table'],
          },
          {
            type: 'oracle',
            name: 'Oracle',
            description: 'Oracle Database',
            icon: 'database',
            category: 'database',
            docs_url: 'https://docs.oracle.com/en/database/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'localhost', description: 'Database server hostname' },
              { name: 'port', label: 'Port', type: 'number', default: 1521, min_value: 1, max_value: 65535, description: 'Oracle listener port' },
              { name: 'service_name', label: 'Service Name', type: 'text', placeholder: 'ORCLPDB1', description: 'Oracle service name' },
              { name: 'sid', label: 'SID', type: 'text', placeholder: 'ORCL', description: 'Oracle SID (legacy)' },
              { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'SYSTEM', description: 'Database username' },
              { name: 'password', label: 'Password', type: 'password', description: 'Database password' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'MY_TABLE', description: 'Table name' },
            ],
            required_fields: ['host', 'username'],
            optional_fields: ['port', 'service_name', 'sid', 'password', 'table'],
          },
          {
            type: 'sqlserver',
            name: 'SQL Server',
            description: 'Microsoft SQL Server',
            icon: 'database',
            category: 'database',
            docs_url: 'https://docs.microsoft.com/en-us/sql/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'localhost', description: 'SQL Server hostname' },
              { name: 'port', label: 'Port', type: 'number', default: 1433, min_value: 1, max_value: 65535, description: 'SQL Server port' },
              { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'mydb', description: 'Database name' },
              { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'sa', description: 'SQL Server login' },
              { name: 'password', label: 'Password', type: 'password', description: 'SQL Server password' },
              { name: 'schema', label: 'Schema', type: 'text', placeholder: 'dbo', default: 'dbo', description: 'Database schema' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
              { name: 'driver', label: 'ODBC Driver', type: 'select', options: [{ value: 'ODBC Driver 17 for SQL Server', label: 'ODBC Driver 17' }, { value: 'ODBC Driver 18 for SQL Server', label: 'ODBC Driver 18' }], default: 'ODBC Driver 17 for SQL Server', description: 'ODBC driver' },
            ],
            required_fields: ['host', 'database', 'username'],
            optional_fields: ['port', 'password', 'schema', 'table', 'driver'],
          },
          // Data Warehouse Sources
          {
            type: 'snowflake',
            name: 'Snowflake',
            description: 'Snowflake data warehouse',
            icon: 'snowflake',
            category: 'warehouse',
            docs_url: 'https://docs.snowflake.com/',
            fields: [
              { name: 'account', label: 'Account', type: 'text', required: true, placeholder: 'xy12345.us-east-1', description: 'Snowflake account identifier' },
              { name: 'username', label: 'Username', type: 'text', required: true, description: 'Snowflake username' },
              { name: 'password', label: 'Password', type: 'password', description: 'Snowflake password' },
              { name: 'warehouse', label: 'Warehouse', type: 'text', required: true, placeholder: 'COMPUTE_WH', description: 'Snowflake warehouse name' },
              { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'MY_DB', description: 'Database name' },
              { name: 'schema', label: 'Schema', type: 'text', placeholder: 'PUBLIC', default: 'PUBLIC', description: 'Schema name' },
              { name: 'role', label: 'Role', type: 'text', placeholder: 'ACCOUNTADMIN', description: 'Snowflake role' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'MY_TABLE', description: 'Table name' },
            ],
            required_fields: ['account', 'username', 'warehouse', 'database'],
            optional_fields: ['password', 'schema', 'role', 'table'],
          },
          {
            type: 'bigquery',
            name: 'BigQuery',
            description: 'Google BigQuery',
            icon: 'cloud',
            category: 'warehouse',
            docs_url: 'https://cloud.google.com/bigquery/docs',
            fields: [
              { name: 'project', label: 'Project ID', type: 'text', required: true, placeholder: 'my-gcp-project', description: 'Google Cloud project ID' },
              { name: 'dataset', label: 'Dataset', type: 'text', placeholder: 'my_dataset', description: 'BigQuery dataset name' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
              { name: 'location', label: 'Location', type: 'select', options: [{ value: 'US', label: 'US (multi-region)' }, { value: 'EU', label: 'EU (multi-region)' }, { value: 'us-central1', label: 'Iowa' }, { value: 'asia-northeast1', label: 'Tokyo' }], default: 'US', description: 'Dataset location' },
              { name: 'credentials_path', label: 'Credentials File', type: 'file_path', placeholder: '/path/to/service-account.json', description: 'Path to service account JSON' },
            ],
            required_fields: ['project'],
            optional_fields: ['dataset', 'table', 'location', 'credentials_path'],
          },
          {
            type: 'redshift',
            name: 'Amazon Redshift',
            description: 'Amazon Redshift data warehouse',
            icon: 'cloud',
            category: 'warehouse',
            docs_url: 'https://docs.aws.amazon.com/redshift/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'cluster.region.redshift.amazonaws.com', description: 'Redshift cluster endpoint' },
              { name: 'port', label: 'Port', type: 'number', default: 5439, min_value: 1, max_value: 65535, description: 'Redshift port' },
              { name: 'database', label: 'Database', type: 'text', required: true, placeholder: 'dev', description: 'Database name' },
              { name: 'username', label: 'Username', type: 'text', required: true, placeholder: 'admin', description: 'Database username' },
              { name: 'password', label: 'Password', type: 'password', description: 'Database password' },
              { name: 'schema', label: 'Schema', type: 'text', placeholder: 'public', default: 'public', description: 'Database schema' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
              { name: 'iam_role', label: 'IAM Role ARN', type: 'text', placeholder: 'arn:aws:iam::123456789:role/MyRole', description: 'IAM role for S3 access' },
            ],
            required_fields: ['host', 'database', 'username'],
            optional_fields: ['port', 'password', 'schema', 'table', 'iam_role'],
          },
          // Big Data Sources
          {
            type: 'databricks',
            name: 'Databricks',
            description: 'Databricks (Unity Catalog / Delta Lake)',
            icon: 'layers',
            category: 'bigdata',
            docs_url: 'https://docs.databricks.com/',
            fields: [
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'adb-xxxxx.azuredatabricks.net', description: 'Databricks workspace URL' },
              { name: 'http_path', label: 'HTTP Path', type: 'text', required: true, placeholder: '/sql/1.0/warehouses/xxxxx', description: 'SQL warehouse HTTP path' },
              { name: 'token', label: 'Access Token', type: 'password', required: true, description: 'Databricks personal access token' },
              { name: 'catalog', label: 'Catalog', type: 'text', placeholder: 'main', description: 'Unity Catalog name' },
              { name: 'schema', label: 'Schema', type: 'text', placeholder: 'default', default: 'default', description: 'Schema name' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
            ],
            required_fields: ['host', 'http_path', 'token'],
            optional_fields: ['catalog', 'schema', 'table'],
          },
          {
            type: 'spark',
            name: 'Apache Spark',
            description: 'Apache Spark (via Hive/JDBC)',
            icon: 'zap',
            category: 'bigdata',
            docs_url: 'https://spark.apache.org/docs/latest/',
            fields: [
              { name: 'connection_type', label: 'Connection Type', type: 'select', options: [{ value: 'hive', label: 'Hive Metastore' }, { value: 'spark_thrift', label: 'Spark Thrift Server' }], default: 'hive', description: 'How to connect to Spark' },
              { name: 'host', label: 'Host', type: 'text', required: true, placeholder: 'localhost', description: 'Spark/Hive server hostname' },
              { name: 'port', label: 'Port', type: 'number', default: 10000, min_value: 1, max_value: 65535, description: 'Hive/Thrift server port' },
              { name: 'database', label: 'Database', type: 'text', placeholder: 'default', default: 'default', description: 'Hive database name' },
              { name: 'username', label: 'Username', type: 'text', description: 'Username (if authentication enabled)' },
              { name: 'password', label: 'Password', type: 'password', description: 'Password (if authentication enabled)' },
              { name: 'table', label: 'Table', type: 'text', placeholder: 'my_table', description: 'Table name' },
            ],
            required_fields: ['host'],
            optional_fields: ['connection_type', 'port', 'database', 'username', 'password', 'table'],
          },
        ],
        categories: [
          { value: 'file', label: 'Files', description: 'Local file sources' },
          { value: 'database', label: 'Databases', description: 'Relational databases' },
          { value: 'warehouse', label: 'Data Warehouses', description: 'Cloud data warehouses' },
          { value: 'bigdata', label: 'Big Data', description: 'Big data platforms' },
        ],
      },
    })
  }),

  // Test connection configuration (before creating source)
  http.post(`${API_BASE}/sources/test-connection`, async ({ request }) => {
    await delay(800) // Simulate connection attempt

    let body: { type: string; config: Record<string, unknown> }
    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Simulate 85% success rate
    const success = Math.random() > 0.15

    return HttpResponse.json({
      success: true,
      data: {
        success,
        message: success ? 'Connection successful! Ready to create source.' : undefined,
        error: success ? undefined : `Failed to connect to ${body.type}: Connection timeout after 30s`,
      },
    })
  }),
]
