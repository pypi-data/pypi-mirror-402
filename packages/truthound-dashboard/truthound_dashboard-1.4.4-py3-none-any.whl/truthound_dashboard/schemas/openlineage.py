"""OpenLineage schema definitions.

This module implements the OpenLineage specification for data lineage interoperability.
See: https://openlineage.io/spec/

The OpenLineage spec defines a standard for lineage metadata, enabling interoperability
between data tools like Airflow, Spark, dbt, and Truthound.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from .base import BaseSchema


# =============================================================================
# OpenLineage Enums
# =============================================================================


class RunState(str, Enum):
    """OpenLineage run state.

    Defines the lifecycle of a job run.
    """

    START = "START"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    ABORT = "ABORT"


class DatasetType(str, Enum):
    """Dataset types for categorization."""

    TABLE = "table"
    FILE = "file"
    STREAM = "stream"
    VIEW = "view"
    QUERY = "query"


# =============================================================================
# OpenLineage Facets
# =============================================================================


class BaseFacet(BaseSchema):
    """Base facet with producer information.

    All facets include metadata about what produced them.
    """

    model_config = {"populate_by_name": True}

    producer: str = Field(
        default="truthound-dashboard",
        serialization_alias="_producer",
        validation_alias="_producer",
        description="URI identifying the producer of this metadata",
    )
    schemaURL: str = Field(
        default="https://openlineage.io/spec/facets/1-0-0/",
        serialization_alias="_schemaURL",
        validation_alias="_schemaURL",
        description="URL to the JSON schema for this facet",
    )


class SchemaField(BaseSchema):
    """Schema field definition for dataset schema facet."""

    name: str = Field(..., description="Field name")
    type: str = Field(default="string", description="Field data type")
    description: str | None = Field(default=None, description="Field description")


class SchemaDatasetFacet(BaseFacet):
    """Dataset schema facet.

    Describes the schema of a dataset including column definitions.
    """

    fields: list[SchemaField] = Field(
        default_factory=list,
        description="List of schema fields",
    )


class DataQualityMetricsInputDatasetFacet(BaseFacet):
    """Data quality metrics facet for input datasets."""

    row_count: int | None = Field(default=None, description="Total row count")
    bytes: int | None = Field(default=None, description="Total bytes")
    column_metrics: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description="Per-column metrics (null_count, distinct_count, etc.)",
    )


class DataQualityAssertionsDatasetFacet(BaseFacet):
    """Data quality assertions facet.

    Records validation results from data quality checks.
    """

    assertions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of quality assertions",
    )


class ColumnLineageDatasetFacet(BaseFacet):
    """Column-level lineage facet.

    Tracks how individual columns are derived from source columns.
    """

    fields: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Column-level lineage mapping",
    )


class DocumentationDatasetFacet(BaseFacet):
    """Documentation facet for datasets."""

    description: str = Field(..., description="Dataset description")


class OwnershipDatasetFacet(BaseFacet):
    """Ownership information facet."""

    owners: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of owners with name and type",
    )


class LifecycleStateChangeDatasetFacet(BaseFacet):
    """Lifecycle state change facet."""

    lifecycle_state_change: str = Field(
        ...,
        description="State change type (CREATE, DROP, TRUNCATE, ALTER, etc.)",
    )
    previous_identifier: dict[str, str] | None = Field(
        default=None,
        description="Previous dataset identifier if renamed",
    )


class SourceCodeJobFacet(BaseFacet):
    """Source code information for jobs."""

    language: str = Field(default="python", description="Programming language")
    source_code: str | None = Field(default=None, description="Source code snippet")
    source_code_url: str | None = Field(default=None, description="URL to source code")


class SQLJobFacet(BaseFacet):
    """SQL query facet for jobs."""

    query: str = Field(..., description="SQL query text")


class ErrorMessageRunFacet(BaseFacet):
    """Error message facet for failed runs."""

    message: str = Field(..., description="Error message")
    programming_language: str = Field(default="python", description="Language")
    stack_trace: str | None = Field(default=None, description="Stack trace")


class ParentRunFacet(BaseFacet):
    """Parent run reference for nested runs."""

    run: dict[str, str] = Field(..., description="Parent run ID reference")
    job: dict[str, str] = Field(..., description="Parent job reference")


class NominalTimeRunFacet(BaseFacet):
    """Nominal time facet for scheduling information."""

    nominal_start_time: str = Field(..., description="Scheduled start time (ISO 8601)")
    nominal_end_time: str | None = Field(default=None, description="Scheduled end time")


class ProcessingEngineRunFacet(BaseFacet):
    """Processing engine information."""

    version: str = Field(..., description="Engine version")
    name: str = Field(default="truthound", description="Engine name")
    openlineage_adapter_version: str = Field(
        default="1.0.0",
        description="OpenLineage adapter version",
    )


# =============================================================================
# OpenLineage Core Objects
# =============================================================================


class OpenLineageDataset(BaseSchema):
    """OpenLineage dataset representation.

    Datasets are the fundamental unit of data in OpenLineage.
    They can be inputs (consumed) or outputs (produced) by jobs.
    """

    namespace: str = Field(
        ...,
        description="Namespace (e.g., 'file://', 'postgresql://host:5432')",
        examples=["file://local", "postgresql://localhost:5432/mydb"],
    )
    name: str = Field(
        ...,
        description="Dataset name (table name, file path, etc.)",
        examples=["customers", "/data/sales.csv"],
    )
    facets: dict[str, Any] = Field(
        default_factory=dict,
        description="Dataset facets (schema, quality, etc.)",
    )

    @classmethod
    def from_source(
        cls,
        source_id: str,
        source_name: str,
        source_type: str,
        namespace: str,
        schema_fields: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "OpenLineageDataset":
        """Create dataset from a dashboard source.

        Args:
            source_id: Source unique identifier.
            source_name: Human-readable source name.
            source_type: Source type (file, postgresql, etc.).
            namespace: Namespace URI.
            schema_fields: Optional schema field definitions.
            metadata: Optional additional metadata.

        Returns:
            OpenLineageDataset instance.
        """
        facets: dict[str, Any] = {}

        # Add schema facet if fields provided
        if schema_fields:
            facets["schema"] = SchemaDatasetFacet(
                fields=[
                    SchemaField(
                        name=f.get("name", ""),
                        type=f.get("type", "string"),
                        description=f.get("description"),
                    )
                    for f in schema_fields
                ]
            ).model_dump(by_alias=True)

        # Add documentation facet
        if metadata and metadata.get("description"):
            facets["documentation"] = DocumentationDatasetFacet(
                description=metadata["description"]
            ).model_dump(by_alias=True)

        # Add custom facet for truthound metadata
        facets["truthound"] = {
            "_producer": "truthound-dashboard",
            "_schemaURL": "https://truthound.io/spec/facets/1-0-0/TruthoundDatasetFacet.json",
            "source_id": source_id,
            "source_type": source_type,
        }

        return cls(
            namespace=namespace,
            name=source_name,
            facets=facets,
        )


class OpenLineageJob(BaseSchema):
    """OpenLineage job representation.

    Jobs represent data processing tasks that consume and produce datasets.
    """

    namespace: str = Field(
        ...,
        description="Job namespace (typically the orchestrator or system)",
        examples=["truthound-dashboard", "airflow://prod"],
    )
    name: str = Field(
        ...,
        description="Job name",
        examples=["data_validation", "etl_pipeline"],
    )
    facets: dict[str, Any] = Field(
        default_factory=dict,
        description="Job facets (source code, documentation, etc.)",
    )


class OpenLineageRun(BaseSchema):
    """OpenLineage run representation.

    Runs are instances of job executions with a unique ID and lifecycle.
    """

    run_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique run identifier (UUID)",
    )
    facets: dict[str, Any] = Field(
        default_factory=dict,
        description="Run facets (parent, error, timing, etc.)",
    )


class OpenLineageEvent(BaseSchema):
    """OpenLineage event.

    Events capture state changes in a run's lifecycle.
    This is the primary output format for OpenLineage export.
    """

    event_time: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Event timestamp (ISO 8601 with timezone)",
    )
    event_type: RunState = Field(
        ...,
        alias="eventType",
        description="Event type (START, RUNNING, COMPLETE, FAIL, ABORT)",
    )
    producer: str = Field(
        default="https://github.com/truthound/truthound-dashboard",
        description="URI identifying the producer",
    )
    schema_url: str = Field(
        default="https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent",
        alias="schemaURL",
        description="URL to the OpenLineage schema",
    )
    run: OpenLineageRun = Field(..., description="Run information")
    job: OpenLineageJob = Field(..., description="Job information")
    inputs: list[OpenLineageDataset] = Field(
        default_factory=list,
        description="Input datasets consumed by the job",
    )
    outputs: list[OpenLineageDataset] = Field(
        default_factory=list,
        description="Output datasets produced by the job",
    )

    class Config:
        populate_by_name = True


# =============================================================================
# Export Request/Response Schemas
# =============================================================================


class OpenLineageExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    NDJSON = "ndjson"  # Newline-delimited JSON (for streaming)


class OpenLineageExportRequest(BaseSchema):
    """Request to export lineage as OpenLineage events."""

    job_namespace: str = Field(
        default="truthound-dashboard",
        description="Namespace for the job",
    )
    job_name: str = Field(
        default="lineage_export",
        description="Name for the job",
    )
    source_id: str | None = Field(
        default=None,
        description="Optional source ID to filter lineage",
    )
    include_schema: bool = Field(
        default=True,
        description="Include schema information in dataset facets",
    )
    include_quality_metrics: bool = Field(
        default=False,
        description="Include data quality metrics if available",
    )
    format: OpenLineageExportFormat = Field(
        default=OpenLineageExportFormat.JSON,
        description="Export format",
    )


class OpenLineageExportResponse(BaseSchema):
    """Response containing OpenLineage events."""

    events: list[OpenLineageEvent] = Field(
        ...,
        description="List of OpenLineage events",
    )
    total_events: int = Field(..., description="Total number of events")
    total_datasets: int = Field(..., description="Total unique datasets")
    total_jobs: int = Field(..., description="Total jobs represented")
    export_time: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Export timestamp",
    )


class OpenLineageWebhookConfig(BaseSchema):
    """Configuration for OpenLineage webhook emission."""

    url: str = Field(
        ...,
        description="Webhook URL to send events to",
        examples=["https://api.openlineage.io/v1/lineage"],
    )
    api_key: str | None = Field(
        default=None,
        description="Optional API key for authentication",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers to include",
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of events to send per batch",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )


class OpenLineageEmitRequest(BaseSchema):
    """Request to emit OpenLineage events to an external system."""

    webhook: OpenLineageWebhookConfig = Field(
        ...,
        description="Webhook configuration",
    )
    source_id: str | None = Field(
        default=None,
        description="Optional source ID to filter lineage",
    )
    job_namespace: str = Field(
        default="truthound-dashboard",
        description="Namespace for the job",
    )
    job_name: str = Field(
        default="lineage_export",
        description="Name for the job",
    )


class OpenLineageEmitResponse(BaseSchema):
    """Response from emitting OpenLineage events."""

    success: bool = Field(..., description="Whether emission was successful")
    events_sent: int = Field(..., description="Number of events sent")
    failed_events: int = Field(default=0, description="Number of failed events")
    error_message: str | None = Field(
        default=None,
        description="Error message if emission failed",
    )


# =============================================================================
# Webhook Configuration Schemas
# =============================================================================


class WebhookEventType(str, Enum):
    """Types of OpenLineage events for webhook configuration."""

    JOB = "job"
    DATASET = "dataset"
    ALL = "all"


class WebhookCreate(BaseSchema):
    """Schema for creating a new OpenLineage webhook."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for the webhook",
        examples=["Marquez Production", "DataHub Dev"],
    )
    url: str = Field(
        ...,
        description="Target URL for the webhook",
        examples=["https://api.marquez.io/v1/lineage", "http://localhost:5000/api/v1/lineage"],
    )
    is_active: bool = Field(
        default=True,
        description="Whether the webhook is enabled",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers to include (excluding Authorization)",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication (sent as Bearer token)",
    )
    event_types: WebhookEventType = Field(
        default=WebhookEventType.ALL,
        description="Types of events to emit",
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of events per batch",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )


class WebhookUpdate(BaseSchema):
    """Schema for updating an existing webhook."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Human-readable name for the webhook",
    )
    url: str | None = Field(
        default=None,
        description="Target URL for the webhook",
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the webhook is enabled",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Custom headers to include",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication",
    )
    event_types: WebhookEventType | None = Field(
        default=None,
        description="Types of events to emit",
    )
    batch_size: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description="Number of events per batch",
    )
    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )


class WebhookResponse(BaseSchema):
    """Schema for webhook response."""

    id: str = Field(..., description="Unique webhook ID")
    name: str = Field(..., description="Webhook name")
    url: str = Field(..., description="Target URL")
    is_active: bool = Field(..., description="Whether webhook is enabled")
    headers: dict[str, str] = Field(default_factory=dict, description="Custom headers")
    event_types: str = Field(..., description="Event types to emit")
    batch_size: int = Field(..., description="Batch size")
    timeout_seconds: int = Field(..., description="Timeout in seconds")
    last_sent_at: str | None = Field(default=None, description="Last successful emission time")
    success_count: int = Field(default=0, description="Total successful emissions")
    failure_count: int = Field(default=0, description="Total failed emissions")
    last_error: str | None = Field(default=None, description="Last error message")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")


class WebhookListResponse(BaseSchema):
    """Response for listing webhooks."""

    data: list[WebhookResponse] = Field(..., description="List of webhooks")
    total: int = Field(..., description="Total number of webhooks")


class WebhookTestRequest(BaseSchema):
    """Request to test a webhook connection."""

    url: str = Field(
        ...,
        description="URL to test",
        examples=["https://api.marquez.io/v1/lineage"],
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Headers to include in test request",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication",
    )
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Test request timeout",
    )


class WebhookTestResult(BaseSchema):
    """Result of a webhook test."""

    success: bool = Field(..., description="Whether the test was successful")
    status_code: int | None = Field(default=None, description="HTTP status code")
    response_time_ms: int | None = Field(default=None, description="Response time in ms")
    error_message: str | None = Field(default=None, description="Error message if failed")
    response_body: str | None = Field(default=None, description="Response body (truncated)")


# =============================================================================
# Dataset Namespace Helpers
# =============================================================================


def build_dataset_namespace(source_type: str, config: dict[str, Any] | None = None) -> str:
    """Build a namespace URI from source configuration.

    Args:
        source_type: Type of data source.
        config: Source configuration dictionary.

    Returns:
        Namespace URI string.
    """
    config = config or {}

    if source_type == "file":
        return f"file://{config.get('base_path', 'local')}"

    if source_type == "postgresql":
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database", "")
        return f"postgresql://{host}:{port}/{database}"

    if source_type == "mysql":
        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        database = config.get("database", "")
        return f"mysql://{host}:{port}/{database}"

    if source_type == "snowflake":
        account = config.get("account", "")
        database = config.get("database", "")
        return f"snowflake://{account}/{database}"

    if source_type == "bigquery":
        project = config.get("project", "")
        dataset = config.get("dataset", "")
        return f"bigquery://{project}.{dataset}"

    if source_type == "redshift":
        host = config.get("host", "")
        database = config.get("database", "")
        return f"redshift://{host}/{database}"

    if source_type == "databricks":
        workspace = config.get("workspace_url", "")
        return f"databricks://{workspace}"

    # Default namespace
    return f"{source_type}://truthound"
