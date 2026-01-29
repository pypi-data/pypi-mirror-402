import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Database,
  Play,
  FileCode,
  History,
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Settings2,
  BarChart3,
  Sliders,
  Pencil,
  RefreshCw,
  Loader2,
  Eye,
  EyeOff,
  Shield,
  Server,
  GitBranch,
  Network,
  BrainCircuit,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  getSource,
  getSourceSchema,
  listSourceValidations,
  runValidation,
  learnSchema,
  listValidators,
  listUnifiedValidators,
  testSourceConnection,
  getSupportedSourceTypes,
  type Source,
  type Schema,
  type Validation,
  type ValidatorDefinition,
  type ValidatorConfig,
  type SourceTypeDefinition,
  type UnifiedValidatorDefinition,
} from '@/api/client'
import type { CustomValidatorSelectionConfig } from '@/components/validators/ValidatorSelector'
import { formatDate, formatDuration, formatNumber } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ValidatorSelector } from '@/components/validators'
import { EditSourceDialog } from '@/components/sources'
import { AnomalyDetectionPanel } from '@/components/anomaly'
import { LineageGraph } from '@/components/lineage'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'

// Fields that should be masked by default
const SENSITIVE_FIELDS = ['password', 'token', 'secret', 'api_key', 'credentials', 'private_key']

// Check if a field is sensitive
function isSensitiveField(fieldName: string): boolean {
  const lowerName = fieldName.toLowerCase()
  return SENSITIVE_FIELDS.some((sf) => lowerName.includes(sf))
}

// Mask a sensitive value
function maskValue(value: unknown): string {
  if (typeof value !== 'string' || !value) return ''
  if (value.length <= 4) return '****'
  return value.slice(0, 2) + '*'.repeat(Math.min(value.length - 4, 8)) + value.slice(-2)
}

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const [source, setSource] = useState<Source | null>(null)
  const [schema, setSchema] = useState<Schema | null>(null)
  const [validations, setValidations] = useState<Validation[]>([])
  const [loading, setLoading] = useState(true)
  const [validating, setValidating] = useState(false)
  const [validationDialogOpen, setValidationDialogOpen] = useState(false)
  const [validators, setValidators] = useState<ValidatorDefinition[]>([])
  const [validatorConfigs, setValidatorConfigs] = useState<ValidatorConfig[]>([])
  const [customValidators, setCustomValidators] = useState<UnifiedValidatorDefinition[]>([])
  const [customValidatorConfigs, setCustomValidatorConfigs] = useState<CustomValidatorSelectionConfig[]>([])
  const [loadingValidators, setLoadingValidators] = useState(false)
  const { toast } = useToast()
  const sources_t = useSafeIntlayer('sources')
  const common = useSafeIntlayer('common')

  // Edit dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  // Connection test state
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionTestResult, setConnectionTestResult] = useState<{
    success: boolean
    message?: string
    error?: string
  } | null>(null)

  // Source type definition for connection info display
  const [sourceTypeDefinition, setSourceTypeDefinition] = useState<SourceTypeDefinition | null>(null)

  // Show/hide sensitive fields
  const [showSensitive, setShowSensitive] = useState<Record<string, boolean>>({})

  const loadData = useCallback(async () => {
    if (!id) return
    try {
      setLoading(true)
      const [sourceData, schemaData, validationsData, typesResponse] = await Promise.all([
        getSource(id),
        getSourceSchema(id),
        listSourceValidations(id),
        getSupportedSourceTypes(),
      ])
      setSource(sourceData)
      setSchema(schemaData)
      setValidations(validationsData.data)

      // Find the source type definition
      if (typesResponse.success && sourceData) {
        const typeDef = typesResponse.data.types.find((t) => t.type === sourceData.type)
        setSourceTypeDefinition(typeDef || null)
      }
    } catch {
      toast({
        title: str(common.error),
        description: 'Failed to load source details',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [id, toast, common])

  const loadValidators = useCallback(async () => {
    if (validators.length > 0) return // Already loaded
    try {
      setLoadingValidators(true)
      // Load both built-in and custom validators
      const [validatorDefs, unifiedResponse] = await Promise.all([
        listValidators(),
        listUnifiedValidators({ source: 'custom', enabled_only: true }),
      ])
      setValidators(validatorDefs)
      setCustomValidators(unifiedResponse.data)
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load validators',
        variant: 'destructive',
      })
    } finally {
      setLoadingValidators(false)
    }
  }, [validators.length, toast])

  useEffect(() => {
    loadData()
  }, [loadData])

  async function handleValidate() {
    if (!id) return
    try {
      setValidating(true)
      // Get enabled validators with their configurations
      const enabledConfigs = validatorConfigs.filter((c) => c.enabled)

      // Get enabled custom validators
      const enabledCustomConfigs = customValidatorConfigs
        .filter((c) => c.enabled && c.column)
        .map((c) => ({
          validator_id: c.validator_id,
          column: c.column,
          params: c.params || {},
        }))

      const options: Parameters<typeof runValidation>[1] = {}
      if (enabledConfigs.length > 0) {
        options.validator_configs = enabledConfigs
      }
      if (enabledCustomConfigs.length > 0) {
        options.custom_validators = enabledCustomConfigs
      }

      const result = await runValidation(id, options)
      setValidations((prev) => [result, ...prev])
      setValidationDialogOpen(false)
      toast({
        title: result.passed ? 'Validation Passed' : 'Validation Failed',
        description: `Found ${result.total_issues} issues`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to run validation',
        variant: 'destructive',
      })
    } finally {
      setValidating(false)
    }
  }

  async function handleQuickValidate() {
    if (!id) return
    try {
      setValidating(true)
      const result = await runValidation(id, {})
      setValidations((prev) => [result, ...prev])
      toast({
        title: result.passed ? 'Validation Passed' : 'Validation Failed',
        description: `Found ${result.total_issues} issues`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to run validation',
        variant: 'destructive',
      })
    } finally {
      setValidating(false)
    }
  }

  function handleOpenValidationDialog() {
    loadValidators()
    setValidationDialogOpen(true)
  }

  async function handleLearnSchema() {
    if (!id) return
    try {
      toast({
        title: 'Learning Schema',
        description: 'Analyzing data structure...',
      })
      const result = await learnSchema(id)
      setSchema(result)
      toast({
        title: 'Schema Learned',
        description: `Found ${result.column_count} columns`,
      })
    } catch (err) {
      toast({
        title: str(common.error),
        description: 'Failed to learn schema',
        variant: 'destructive',
      })
    }
  }

  // Test connection
  async function handleTestConnection() {
    if (!id) return
    try {
      setTestingConnection(true)
      setConnectionTestResult(null)
      const response = await testSourceConnection(id)
      setConnectionTestResult(response.data)
      toast({
        title: response.data.success ? str(sources_t.testConnection.success) : str(sources_t.testConnection.failed),
        description: response.data.success ? response.data.message : response.data.error,
        variant: response.data.success ? 'default' : 'destructive',
      })
    } catch (err) {
      setConnectionTestResult({
        success: false,
        error: err instanceof Error ? err.message : str(sources_t.testConnection.failed),
      })
      toast({
        title: str(common.error),
        description: str(sources_t.testConnection.failed),
        variant: 'destructive',
      })
    } finally {
      setTestingConnection(false)
    }
  }

  // Handle edit success
  function handleEditSuccess() {
    loadData()
    setConnectionTestResult(null)
  }

  // Toggle sensitive field visibility
  function toggleSensitiveVisibility(fieldName: string) {
    setShowSensitive((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }))
  }

  // Get display value for config field
  function getConfigDisplayValue(fieldName: string, value: unknown): string {
    if (value === undefined || value === null || value === '') {
      return str(sources_t.connectionInfo.notSet)
    }
    // Check if this field should be masked
    const fieldDef = sourceTypeDefinition?.fields.find((f) => f.name === fieldName)
    const shouldMask = fieldDef?.type === 'password' || isSensitiveField(fieldName)

    if (shouldMask && !showSensitive[fieldName]) {
      return maskValue(value)
    }
    return String(value)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!source) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <XCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-muted-foreground">Source not found</p>
        <Button asChild className="mt-4">
          <Link to="/sources">Back to Sources</Link>
        </Button>
      </div>
    )
  }

  const latestValidation = validations[0]

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/sources"
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Sources
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-lg bg-primary/10 flex items-center justify-center">
            <Database className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">{source.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">{source.type}</Badge>
              {source.is_active ? (
                <Badge variant="success">Active</Badge>
              ) : (
                <Badge variant="secondary">Inactive</Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap justify-end">
          <Button variant="outline" onClick={() => setEditDialogOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            {str(sources_t.editSource)}
          </Button>
          <Button variant="outline" onClick={handleTestConnection} disabled={testingConnection}>
            {testingConnection ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            {testingConnection ? str(sources_t.testConnection.testing) : str(sources_t.testConnection.test)}
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/rules`}>
              <Settings2 className="mr-2 h-4 w-4" />
              Rules
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/profile`}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Profile
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/history`}>
              <History className="mr-2 h-4 w-4" />
              History
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/versions`}>
              <GitBranch className="mr-2 h-4 w-4" />
              Versions
            </Link>
          </Button>
          <Button variant="outline" onClick={handleLearnSchema}>
            <FileCode className="mr-2 h-4 w-4" />
            Learn Schema
          </Button>
          <Button variant="outline" onClick={handleQuickValidate} disabled={validating}>
            <Play className="mr-2 h-4 w-4" />
            {validating ? 'Validating...' : 'Quick Validate'}
          </Button>
          <Dialog open={validationDialogOpen} onOpenChange={setValidationDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={handleOpenValidationDialog} disabled={validating}>
                <Sliders className="mr-2 h-4 w-4" />
                Configure & Run
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Configure Validation</DialogTitle>
                <DialogDescription>
                  Select and configure validators to run against this data source.
                  Use presets for quick setup or customize individual validators.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                {loadingValidators ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                  </div>
                ) : (
                  <ValidatorSelector
                    validators={validators}
                    configs={validatorConfigs}
                    onChange={setValidatorConfigs}
                    columns={schema?.columns || []}
                    customValidators={customValidators}
                    customValidatorConfigs={customValidatorConfigs}
                    onCustomValidatorChange={setCustomValidatorConfigs}
                  />
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setValidationDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleValidate} disabled={validating}>
                  <Play className="mr-2 h-4 w-4" />
                  {validating ? 'Validating...' : 'Run Validation'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <div className="flex items-center gap-2 mt-1">
                  {latestValidation?.passed ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <span className="font-semibold text-green-600">Passed</span>
                    </>
                  ) : latestValidation ? (
                    <>
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="font-semibold text-red-600">Failed</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <span className="font-semibold text-yellow-600">
                        Not Validated
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Issues</p>
            <p className="text-2xl font-bold mt-1">
              {formatNumber(latestValidation?.total_issues)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Rows</p>
            <p className="text-2xl font-bold mt-1">
              {formatNumber(latestValidation?.row_count)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Last Validation</p>
            <p className="text-lg font-medium mt-1">
              {formatDate(source.last_validated_at)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for different views */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Database className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="anomaly" className="gap-2">
            <BrainCircuit className="h-4 w-4" />
            Anomaly Detection
          </TabsTrigger>
          <TabsTrigger value="lineage" className="gap-2">
            <Network className="h-4 w-4" />
            Lineage
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Connection Info Card */}
          {source.config && Object.keys(source.config).length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-5 w-5" />
                    <CardTitle>{str(sources_t.connectionInfo.title)}</CardTitle>
                  </div>
                  {connectionTestResult && (
                    <Badge variant={connectionTestResult.success ? 'success' : 'destructive'}>
                      {connectionTestResult.success ? (
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                      ) : (
                        <XCircle className="mr-1 h-3 w-3" />
                      )}
                      {connectionTestResult.success ? str(sources_t.testConnection.success) : str(sources_t.testConnection.failed)}
                    </Badge>
                  )}
                </div>
                {source.description && (
                  <CardDescription>{source.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2">
                  {sourceTypeDefinition?.fields.map((field) => {
                    const value = source.config[field.name]
                    if (value === undefined && !field.required) return null

                    const isSensitive = field.type === 'password' || isSensitiveField(field.name)

                    return (
                      <div key={field.name} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-muted/30">
                        <div className="flex items-center gap-2 min-w-0">
                          {isSensitive && (
                            <Shield className="h-4 w-4 text-amber-500 flex-shrink-0" />
                          )}
                          <span className="text-sm text-muted-foreground truncate">{field.label}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <code className="text-sm bg-background px-2 py-0.5 rounded max-w-[200px] truncate">
                            {getConfigDisplayValue(field.name, value)}
                          </code>
                          {isSensitive && value !== undefined && value !== null && value !== '' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => toggleSensitiveVisibility(field.name)}
                            >
                              {showSensitive[field.name] ? (
                                <EyeOff className="h-3 w-3" />
                              ) : (
                                <Eye className="h-3 w-3" />
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                  {/* Show any config fields not in the type definition */}
                  {Object.entries(source.config)
                    .filter(([key]) => !sourceTypeDefinition?.fields.find((f) => f.name === key))
                    .map(([key, value]) => {
                      const isSensitive = isSensitiveField(key)
                      return (
                        <div key={key} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-muted/30">
                          <div className="flex items-center gap-2 min-w-0">
                            {isSensitive && (
                              <Shield className="h-4 w-4 text-amber-500 flex-shrink-0" />
                            )}
                            <span className="text-sm text-muted-foreground truncate">{key}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <code className="text-sm bg-background px-2 py-0.5 rounded max-w-[200px] truncate">
                              {getConfigDisplayValue(key, value)}
                            </code>
                            {isSensitive && value !== undefined && value !== null && value !== '' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => toggleSensitiveVisibility(key)}
                              >
                                {showSensitive[key] ? (
                                  <EyeOff className="h-3 w-3" />
                                ) : (
                                  <Eye className="h-3 w-3" />
                                )}
                              </Button>
                            )}
                          </div>
                        </div>
                      )
                    })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Latest Issues */}
          {latestValidation && latestValidation.issues.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  Issues Found ({latestValidation.total_issues})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {latestValidation.issues.slice(0, 10).map((issue, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            issue.severity === 'critical'
                              ? 'critical'
                              : issue.severity === 'high'
                              ? 'high'
                              : issue.severity === 'medium'
                              ? 'medium'
                              : 'low'
                          }
                        >
                          {issue.severity}
                        </Badge>
                        <div>
                          <p className="font-medium">
                            {issue.column}: {issue.issue_type}
                          </p>
                          {issue.details && (
                            <p className="text-sm text-muted-foreground">
                              {issue.details}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {formatNumber(issue.count)} occurrences
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Schema */}
          {schema && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileCode className="h-5 w-5" />
                  Schema ({schema.column_count} columns)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {schema.columns.map((col) => (
                    <Badge key={col} variant="outline">
                      {col}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Validation History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Validation History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {validations.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No validations yet. Run your first validation to see results here.
                </p>
              ) : (
                <div className="space-y-3">
                  {validations.map((validation) => (
                    <Link
                      key={validation.id}
                      to={`/validations/${validation.id}`}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {validation.passed ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}
                        <div>
                          <p className="font-medium">
                            {validation.passed ? 'Passed' : 'Failed'} -{' '}
                            {formatNumber(validation.total_issues)} issues
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {formatDate(validation.created_at)} •{' '}
                            {formatDuration(validation.duration_ms)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {validation.critical_issues > 0 && (
                          <Badge variant="critical">
                            {validation.critical_issues} critical
                          </Badge>
                        )}
                        {validation.high_issues > 0 && (
                          <Badge variant="high">{validation.high_issues} high</Badge>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Anomaly Detection Tab */}
        <TabsContent value="anomaly">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="h-5 w-5" />
                Anomaly Detection
              </CardTitle>
              <CardDescription>
                Detect anomalies in your data using machine learning algorithms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnomalyDetectionPanel
                sourceId={id!}
                columns={schema?.columns || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Lineage Tab */}
        <TabsContent value="lineage">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                Data Lineage
              </CardTitle>
              <CardDescription>
                Visualize data flow and dependencies for this source
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LineageGraph sourceId={id} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Source Dialog */}
      <EditSourceDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        source={source}
        onSuccess={handleEditSuccess}
      />
    </div>
  )
}
