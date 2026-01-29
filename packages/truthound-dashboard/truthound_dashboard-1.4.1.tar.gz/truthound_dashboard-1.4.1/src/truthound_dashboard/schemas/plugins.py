"""Pydantic schemas for Plugin System.

This module defines schemas for plugin management including:
- Plugin metadata and versioning
- Custom validators
- Custom reporters
- Plugin marketplace
- Security and sandboxing
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, field_validator

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class PluginType(str, Enum):
    """Type of plugin."""

    VALIDATOR = "validator"
    REPORTER = "reporter"
    CONNECTOR = "connector"
    TRANSFORMER = "transformer"


class PluginStatus(str, Enum):
    """Installation status of a plugin."""

    AVAILABLE = "available"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"


class PluginSource(str, Enum):
    """Source of the plugin."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    LOCAL = "local"
    PRIVATE = "private"


class SecurityLevel(str, Enum):
    """Security level of the plugin."""

    TRUSTED = "trusted"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SANDBOXED = "sandboxed"


class ValidatorParamType(str, Enum):
    """Parameter types for custom validators."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    COLUMN = "column"
    COLUMN_LIST = "column_list"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    REGEX = "regex"
    JSON = "json"


class ReporterOutputFormat(str, Enum):
    """Output format for custom reporters."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    MARKDOWN = "markdown"
    CUSTOM = "custom"


# =============================================================================
# Plugin Version Management
# =============================================================================


class SemverVersion(BaseSchema):
    """Semantic version representation."""

    major: int = Field(ge=0, description="Major version (breaking changes)")
    minor: int = Field(ge=0, description="Minor version (new features)")
    patch: int = Field(ge=0, description="Patch version (bug fixes)")
    prerelease: str | None = Field(
        default=None, description="Pre-release identifier (e.g., 'beta.1')"
    )
    build: str | None = Field(default=None, description="Build metadata")

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> "SemverVersion":
        """Parse a version string into SemverVersion."""
        import re

        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$"
        match = re.match(pattern, version_str)
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )


class PluginDependency(BaseSchema):
    """Plugin dependency specification."""

    plugin_id: str = Field(description="ID of the dependent plugin")
    version_constraint: str = Field(
        description="Version constraint (e.g., '>=1.0.0', '^2.0.0')"
    )
    optional: bool = Field(default=False, description="Whether dependency is optional")


# =============================================================================
# Plugin Security
# =============================================================================


class PluginPermission(str, Enum):
    """Permissions that a plugin can request."""

    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM = "file_system"
    EXECUTE_CODE = "execute_code"
    SEND_NOTIFICATIONS = "send_notifications"
    ACCESS_SECRETS = "access_secrets"


class PluginSignature(BaseSchema):
    """Plugin signature information for verification."""

    algorithm: str = Field(default="ed25519", description="Signature algorithm")
    public_key: str = Field(description="Public key for verification")
    signature: str = Field(description="Signature of the plugin package")
    signed_at: datetime = Field(description="Timestamp of signing")
    signer_id: str | None = Field(default=None, description="ID of the signer")


class SandboxConfig(BaseSchema):
    """Sandbox configuration for plugin execution."""

    enabled: bool = Field(default=True, description="Whether sandbox is enabled")
    memory_limit_mb: int = Field(
        default=256, ge=64, le=2048, description="Memory limit in MB"
    )
    cpu_time_limit_seconds: int = Field(
        default=30, ge=1, le=300, description="CPU time limit in seconds"
    )
    network_enabled: bool = Field(
        default=False, description="Whether network access is allowed"
    )
    allowed_modules: list[str] = Field(
        default_factory=list, description="List of allowed Python modules"
    )
    blocked_modules: list[str] = Field(
        default_factory=lambda: ["os", "subprocess", "sys", "shutil"],
        description="List of blocked Python modules",
    )
    max_file_size_mb: int = Field(
        default=10, ge=1, le=100, description="Max file size in MB"
    )


class SecurityReport(BaseSchema):
    """Security analysis report for a plugin."""

    plugin_id: str
    analyzed_at: datetime
    risk_level: SecurityLevel
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    permissions_required: list[PluginPermission] = Field(default_factory=list)
    signature_valid: bool = Field(default=False)
    sandbox_compatible: bool = Field(default=True)


# =============================================================================
# Custom Validator Plugin
# =============================================================================


class ValidatorParamDefinition(BaseSchema):
    """Definition of a validator parameter."""

    name: str = Field(description="Parameter name")
    type: ValidatorParamType = Field(description="Parameter type")
    description: str = Field(description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value")
    options: list[str] | None = Field(
        default=None, description="Options for select/multi_select types"
    )
    min_value: float | None = Field(
        default=None, description="Minimum value for numeric types"
    )
    max_value: float | None = Field(
        default=None, description="Maximum value for numeric types"
    )
    pattern: str | None = Field(
        default=None, description="Regex pattern for string validation"
    )


class CustomValidatorBase(BaseSchema):
    """Base schema for custom validator."""

    name: str = Field(max_length=100, description="Validator name")
    display_name: str = Field(max_length=200, description="Display name for UI")
    description: str = Field(description="Validator description")
    category: str = Field(max_length=50, description="Validator category")
    severity: Literal["error", "warning", "info"] = Field(
        default="error", description="Default severity"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for search/filter")
    parameters: list[ValidatorParamDefinition] = Field(
        default_factory=list, description="Validator parameters"
    )
    code: str = Field(description="Python code implementing the validator")
    test_cases: list[dict[str, Any]] = Field(
        default_factory=list, description="Test cases for validation"
    )


class CustomValidatorCreate(CustomValidatorBase):
    """Schema for creating a custom validator."""

    plugin_id: str | None = Field(
        default=None, description="Associated plugin ID if part of a plugin"
    )


class CustomValidatorUpdate(BaseSchema):
    """Schema for updating a custom validator."""

    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    severity: Literal["error", "warning", "info"] | None = None
    tags: list[str] | None = None
    parameters: list[ValidatorParamDefinition] | None = None
    code: str | None = None
    test_cases: list[dict[str, Any]] | None = None
    is_enabled: bool | None = None


class CustomValidatorResponse(CustomValidatorBase, IDMixin, TimestampMixin):
    """Response schema for custom validator."""

    plugin_id: str | None = None
    is_enabled: bool = True
    is_verified: bool = False
    usage_count: int = 0
    last_used_at: datetime | None = None

    @classmethod
    def from_model(cls, model: Any) -> "CustomValidatorResponse":
        return cls(
            id=str(model.id),
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            category=model.category,
            severity=model.severity,
            tags=model.tags or [],
            parameters=model.parameters or [],
            code=model.code,
            test_cases=model.test_cases or [],
            plugin_id=str(model.plugin_id) if model.plugin_id else None,
            is_enabled=model.is_enabled,
            is_verified=model.is_verified,
            usage_count=model.usage_count,
            last_used_at=model.last_used_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class CustomValidatorListResponse(ListResponseWrapper[CustomValidatorResponse]):
    """List response for custom validators."""

    pass


class ValidatorTestRequest(BaseSchema):
    """Request to test a custom validator."""

    code: str = Field(description="Validator code to test")
    parameters: list[ValidatorParamDefinition] = Field(
        default_factory=list, description="Parameter definitions"
    )
    test_data: dict[str, Any] = Field(description="Test data (column values)")
    param_values: dict[str, Any] = Field(
        default_factory=dict, description="Parameter values for test"
    )


class ValidatorTestResponse(BaseSchema):
    """Response from testing a custom validator."""

    success: bool
    passed: bool | None = None
    execution_time_ms: float
    result: dict[str, Any] | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# Custom Reporter Plugin
# =============================================================================


class ReporterFieldDefinition(BaseSchema):
    """Definition of a reporter configuration field."""

    name: str = Field(description="Field name")
    type: str = Field(description="Field type (string, boolean, select, etc.)")
    label: str = Field(description="Display label")
    description: str | None = Field(default=None, description="Field description")
    required: bool = Field(default=False)
    default: Any = Field(default=None)
    options: list[dict[str, str]] | None = Field(
        default=None, description="Options for select fields"
    )


class CustomReporterBase(BaseSchema):
    """Base schema for custom reporter."""

    name: str = Field(max_length=100, description="Reporter name")
    display_name: str = Field(max_length=200, description="Display name for UI")
    description: str = Field(description="Reporter description")
    output_formats: list[ReporterOutputFormat] = Field(
        default_factory=lambda: [ReporterOutputFormat.HTML],
        description="Supported output formats",
    )
    config_fields: list[ReporterFieldDefinition] = Field(
        default_factory=list, description="Configuration fields"
    )
    template: str | None = Field(
        default=None, description="Jinja2 template for report generation"
    )
    code: str | None = Field(
        default=None, description="Python code for custom report generation"
    )
    preview_image_url: str | None = Field(
        default=None, description="Preview image URL"
    )


class CustomReporterCreate(CustomReporterBase):
    """Schema for creating a custom reporter."""

    plugin_id: str | None = Field(default=None, description="Associated plugin ID")


class CustomReporterUpdate(BaseSchema):
    """Schema for updating a custom reporter."""

    display_name: str | None = None
    description: str | None = None
    output_formats: list[ReporterOutputFormat] | None = None
    config_fields: list[ReporterFieldDefinition] | None = None
    template: str | None = None
    code: str | None = None
    preview_image_url: str | None = None
    is_enabled: bool | None = None


class CustomReporterResponse(CustomReporterBase, IDMixin, TimestampMixin):
    """Response schema for custom reporter."""

    plugin_id: str | None = None
    is_enabled: bool = True
    is_verified: bool = False
    usage_count: int = 0

    @classmethod
    def from_model(cls, model: Any) -> "CustomReporterResponse":
        return cls(
            id=str(model.id),
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            output_formats=model.output_formats or [ReporterOutputFormat.HTML],
            config_fields=model.config_fields or [],
            template=model.template,
            code=model.code,
            preview_image_url=model.preview_image_url,
            plugin_id=str(model.plugin_id) if model.plugin_id else None,
            is_enabled=model.is_enabled,
            is_verified=model.is_verified,
            usage_count=model.usage_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class CustomReporterListResponse(ListResponseWrapper[CustomReporterResponse]):
    """List response for custom reporters."""

    pass


class ReporterGenerateRequest(BaseSchema):
    """Request to generate a report using a custom reporter."""

    output_format: ReporterOutputFormat = Field(description="Desired output format")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Reporter configuration"
    )
    # Either validation_id or data must be provided
    validation_id: str | None = Field(
        default=None,
        description="Validation ID to generate report from (auto-fetches data)",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Data to include in report (use if not providing validation_id)",
    )
    source_ids: list[str] | None = Field(
        default=None, description="Source IDs to include"
    )


class ReporterGenerateResponse(BaseSchema):
    """Response from generating a report."""

    success: bool
    report_id: str | None = None
    download_url: str | None = None
    preview_html: str | None = None
    error: str | None = None
    generation_time_ms: float = 0


# =============================================================================
# Plugin Metadata
# =============================================================================


class PluginAuthor(BaseSchema):
    """Plugin author information."""

    name: str = Field(description="Author name")
    email: str | None = Field(default=None, description="Author email")
    url: str | None = Field(default=None, description="Author website")


class PluginMetadata(BaseSchema):
    """Metadata for a plugin."""

    name: str = Field(max_length=100, description="Plugin name")
    display_name: str = Field(max_length=200, description="Display name for UI")
    description: str = Field(description="Plugin description")
    version: str = Field(description="Plugin version (semver)")
    type: PluginType = Field(description="Plugin type")
    source: PluginSource = Field(default=PluginSource.COMMUNITY)
    author: PluginAuthor | None = None
    license: str | None = Field(default=None, description="License identifier")
    homepage: str | None = Field(default=None, description="Plugin homepage URL")
    repository: str | None = Field(default=None, description="Repository URL")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    categories: list[str] = Field(default_factory=list, description="Plugin categories")
    dependencies: list[PluginDependency] = Field(
        default_factory=list, description="Plugin dependencies"
    )
    python_version: str | None = Field(
        default=None, description="Required Python version"
    )
    dashboard_version: str | None = Field(
        default=None, description="Required dashboard version"
    )
    permissions: list[PluginPermission] = Field(
        default_factory=list, description="Required permissions"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        SemverVersion.parse(v)  # Validate semver format
        return v


class PluginBase(PluginMetadata):
    """Base schema for plugin."""

    icon_url: str | None = Field(default=None, description="Plugin icon URL")
    banner_url: str | None = Field(default=None, description="Plugin banner URL")
    documentation_url: str | None = Field(
        default=None, description="Documentation URL"
    )
    changelog: str | None = Field(default=None, description="Changelog markdown")
    readme: str | None = Field(default=None, description="README markdown")


class PluginCreate(PluginBase):
    """Schema for creating/registering a plugin."""

    package_url: str | None = Field(
        default=None, description="URL to download plugin package"
    )
    signature: PluginSignature | None = Field(
        default=None, description="Plugin signature"
    )
    sandbox_config: SandboxConfig | None = Field(
        default=None, description="Sandbox configuration"
    )


class PluginUpdate(BaseSchema):
    """Schema for updating a plugin."""

    display_name: str | None = None
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    documentation_url: str | None = None
    changelog: str | None = None
    readme: str | None = None
    is_enabled: bool | None = None
    sandbox_config: SandboxConfig | None = None


class PluginResponse(PluginBase, IDMixin, TimestampMixin):
    """Response schema for a plugin."""

    status: PluginStatus = Field(default=PluginStatus.AVAILABLE)
    security_level: SecurityLevel = Field(default=SecurityLevel.UNVERIFIED)
    installed_version: str | None = Field(
        default=None, description="Currently installed version"
    )
    latest_version: str | None = Field(
        default=None, description="Latest available version"
    )
    is_enabled: bool = Field(default=False)
    install_count: int = Field(default=0, description="Total install count")
    rating: float | None = Field(
        default=None, ge=0, le=5, description="Average rating"
    )
    rating_count: int = Field(default=0, description="Number of ratings")
    validators_count: int = Field(default=0, description="Number of validators")
    reporters_count: int = Field(default=0, description="Number of reporters")
    last_updated: datetime | None = None
    installed_at: datetime | None = None

    @classmethod
    def from_model(cls, model: Any) -> "PluginResponse":
        return cls(
            id=str(model.id),
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            version=model.version,
            type=model.type,
            source=model.source,
            author=model.author,
            license=model.license,
            homepage=model.homepage,
            repository=model.repository,
            keywords=model.keywords or [],
            categories=model.categories or [],
            dependencies=model.dependencies or [],
            python_version=model.python_version,
            dashboard_version=model.dashboard_version,
            permissions=model.permissions or [],
            icon_url=model.icon_url,
            banner_url=model.banner_url,
            documentation_url=model.documentation_url,
            changelog=model.changelog,
            readme=model.readme,
            status=model.status,
            security_level=model.security_level,
            installed_version=model.installed_version,
            latest_version=model.latest_version,
            is_enabled=model.is_enabled,
            install_count=model.install_count,
            rating=model.rating,
            rating_count=model.rating_count,
            validators_count=model.validators_count,
            reporters_count=model.reporters_count,
            last_updated=model.last_updated,
            installed_at=model.installed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PluginListResponse(ListResponseWrapper[PluginResponse]):
    """List response for plugins."""

    pass


class PluginSummary(BaseSchema):
    """Summary of a plugin for list views."""

    id: str
    name: str
    display_name: str
    description: str
    version: str
    type: PluginType
    source: PluginSource
    status: PluginStatus
    security_level: SecurityLevel
    icon_url: str | None = None
    rating: float | None = None
    rating_count: int = 0
    install_count: int = 0


# =============================================================================
# Plugin Marketplace
# =============================================================================


class MarketplaceSearchRequest(BaseSchema):
    """Request to search plugins in marketplace."""

    query: str | None = Field(default=None, description="Search query")
    types: list[PluginType] | None = Field(
        default=None, description="Filter by plugin types"
    )
    sources: list[PluginSource] | None = Field(
        default=None, description="Filter by sources"
    )
    categories: list[str] | None = Field(
        default=None, description="Filter by categories"
    )
    keywords: list[str] | None = Field(default=None, description="Filter by keywords")
    min_rating: float | None = Field(
        default=None, ge=0, le=5, description="Minimum rating"
    )
    verified_only: bool = Field(default=False, description="Only show verified plugins")
    sort_by: Literal["relevance", "rating", "installs", "updated", "name"] = Field(
        default="relevance"
    )
    sort_order: Literal["asc", "desc"] = Field(default="desc")
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class MarketplaceCategory(BaseSchema):
    """Category in the marketplace."""

    name: str
    display_name: str
    description: str
    icon: str | None = None
    plugin_count: int = 0


class MarketplaceStats(BaseSchema):
    """Statistics about the marketplace."""

    total_plugins: int = 0
    total_validators: int = 0
    total_reporters: int = 0
    total_installs: int = 0
    categories: list[MarketplaceCategory] = Field(default_factory=list)
    featured_plugins: list[PluginSummary] = Field(default_factory=list)
    popular_plugins: list[PluginSummary] = Field(default_factory=list)
    recent_plugins: list[PluginSummary] = Field(default_factory=list)


class PluginInstallRequest(BaseSchema):
    """Request to install a plugin."""

    plugin_id: str = Field(description="Plugin ID to install")
    version: str | None = Field(
        default=None, description="Specific version to install"
    )
    force: bool = Field(default=False, description="Force reinstall if exists")
    enable_after_install: bool = Field(
        default=True, description="Enable plugin after installation"
    )
    skip_verification: bool = Field(
        default=False,
        description="Skip security verification (use with caution)",
    )


class PluginInstallResponse(BaseSchema):
    """Response from plugin installation."""

    success: bool
    plugin_id: str
    installed_version: str | None = None
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    security_report: SecurityReport | None = None


class PluginUninstallRequest(BaseSchema):
    """Request to uninstall a plugin."""

    plugin_id: str = Field(description="Plugin ID to uninstall")
    remove_data: bool = Field(
        default=False, description="Remove all plugin data and configuration"
    )


class PluginUninstallResponse(BaseSchema):
    """Response from plugin uninstallation."""

    success: bool
    plugin_id: str
    message: str | None = None


class PluginUpdateCheckResponse(BaseSchema):
    """Response from checking for plugin updates."""

    plugin_id: str
    current_version: str
    latest_version: str
    update_available: bool
    changelog: str | None = None
    breaking_changes: bool = False
    release_notes: str | None = None


class PluginRatingRequest(BaseSchema):
    """Request to rate a plugin."""

    plugin_id: str
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    review: str | None = Field(
        default=None, max_length=2000, description="Optional review text"
    )


class PluginRatingResponse(BaseSchema):
    """Response from rating a plugin."""

    success: bool
    plugin_id: str
    new_average_rating: float
    total_ratings: int


# =============================================================================
# Plugin Execution
# =============================================================================


class PluginExecutionContext(BaseSchema):
    """Context for plugin execution."""

    plugin_id: str
    execution_id: str
    source_id: str | None = None
    validation_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    sandbox_enabled: bool = True
    timeout_seconds: int = 30
    memory_limit_mb: int = 256


class PluginExecutionResult(BaseSchema):
    """Result of plugin execution."""

    execution_id: str
    plugin_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0
    memory_used_mb: float | None = None
    warnings: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)


# =============================================================================
# Plugin Lifecycle & State Management
# =============================================================================


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    FAILED = "failed"
    RELOADING = "reloading"
    UPGRADING = "upgrading"


class PluginLifecycleEvent(BaseSchema):
    """A plugin lifecycle event."""

    plugin_id: str
    from_state: PluginState
    to_state: PluginState
    trigger: str
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginLifecycleResponse(BaseSchema):
    """Plugin lifecycle status response."""

    plugin_id: str
    current_state: PluginState
    can_activate: bool = False
    can_deactivate: bool = False
    can_reload: bool = False
    can_upgrade: bool = False
    recent_events: list[PluginLifecycleEvent] = Field(default_factory=list)


class PluginTransitionRequest(BaseSchema):
    """Request to transition plugin state."""

    target_state: PluginState
    force: bool = Field(default=False, description="Force transition even if not allowed")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginTransitionResponse(BaseSchema):
    """Response from plugin state transition."""

    success: bool
    plugin_id: str
    from_state: PluginState
    to_state: PluginState
    message: str | None = None
    error: str | None = None


# =============================================================================
# Plugin Hot Reload
# =============================================================================


class ReloadStrategy(str, Enum):
    """Strategy for handling hot reloads."""

    IMMEDIATE = "immediate"
    DEBOUNCED = "debounced"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class HotReloadConfigRequest(BaseSchema):
    """Request to configure hot reload for a plugin."""

    strategy: ReloadStrategy = Field(default=ReloadStrategy.DEBOUNCED)
    debounce_delay_ms: int = Field(default=500, ge=0, le=5000)
    watch_paths: list[str] = Field(default_factory=list)
    enabled: bool = True


class HotReloadStatus(BaseSchema):
    """Hot reload status for a plugin."""

    plugin_id: str
    enabled: bool = False
    watching: bool = False
    strategy: ReloadStrategy = ReloadStrategy.MANUAL
    has_pending_reload: bool = False
    last_reload_at: datetime | None = None
    last_reload_duration_ms: float | None = None


class HotReloadResult(BaseSchema):
    """Result of a hot reload operation."""

    success: bool
    plugin_id: str
    old_version: str = ""
    new_version: str = ""
    duration_ms: float = 0
    error: str | None = None
    rolled_back: bool = False
    changes: list[str] = Field(default_factory=list)


# =============================================================================
# Plugin Dependencies
# =============================================================================


class DependencyType(str, Enum):
    """Type of dependency relationship."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    DEV = "dev"
    PEER = "peer"
    CONFLICT = "conflict"


class DependencyInfo(BaseSchema):
    """Detailed dependency information."""

    plugin_id: str
    version_constraint: str
    dependency_type: DependencyType = DependencyType.REQUIRED
    resolved_version: str | None = None
    is_installed: bool = False
    is_satisfied: bool = False


class DependencyGraphNode(BaseSchema):
    """A node in the dependency graph."""

    plugin_id: str
    version: str
    dependencies: list[DependencyInfo] = Field(default_factory=list)
    dependents: list[str] = Field(default_factory=list)
    depth: int = 0


class DependencyGraphResponse(BaseSchema):
    """Full dependency graph for visualization."""

    root_plugin_id: str
    nodes: list[DependencyGraphNode] = Field(default_factory=list)
    has_cycles: bool = False
    cycle_path: list[str] | None = None
    install_order: list[str] = Field(default_factory=list)
    total_dependencies: int = 0


class DependencyResolutionRequest(BaseSchema):
    """Request to resolve dependencies for installation."""

    plugin_ids: list[str] = Field(description="Plugin IDs to resolve")
    include_optional: bool = Field(default=False)
    include_dev: bool = Field(default=False)


class DependencyResolutionResponse(BaseSchema):
    """Result of dependency resolution."""

    success: bool
    resolved: list[DependencyInfo] = Field(default_factory=list)
    unresolved: list[DependencyInfo] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    install_order: list[str] = Field(default_factory=list)
    error: str | None = None


# =============================================================================
# Plugin Security - Extended
# =============================================================================


class IsolationLevel(str, Enum):
    """Sandbox isolation levels."""

    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms."""

    SHA256 = "sha256"
    SHA512 = "sha512"
    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA512 = "hmac_sha512"
    RSA_SHA256 = "rsa_sha256"
    ED25519 = "ed25519"


class TrustedSigner(BaseSchema):
    """A trusted signer in the trust store."""

    signer_id: str
    name: str
    public_key: str
    algorithm: SignatureAlgorithm
    added_at: datetime
    expires_at: datetime | None = None
    is_active: bool = True
    trust_level: SecurityLevel = SecurityLevel.VERIFIED


class TrustStoreResponse(BaseSchema):
    """Response containing trust store information."""

    signers: list[TrustedSigner] = Field(default_factory=list)
    total_signers: int = 0
    last_updated: datetime | None = None


class AddSignerRequest(BaseSchema):
    """Request to add a signer to the trust store."""

    signer_id: str
    name: str
    public_key: str
    algorithm: SignatureAlgorithm = SignatureAlgorithm.ED25519
    expires_at: datetime | None = None
    trust_level: SecurityLevel = SecurityLevel.VERIFIED


class SecurityPolicyPreset(str, Enum):
    """Pre-defined security policy presets."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    STRICT = "strict"
    AIRGAPPED = "airgapped"


class SecurityPolicyConfig(BaseSchema):
    """Full security policy configuration."""

    preset: SecurityPolicyPreset = SecurityPolicyPreset.STANDARD
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    require_signature: bool = True
    min_signatures: int = Field(default=1, ge=0, le=10)
    allowed_signers: list[str] = Field(default_factory=list)
    blocked_modules: list[str] = Field(default_factory=list)
    memory_limit_mb: int = Field(default=256, ge=64, le=4096)
    cpu_time_limit_sec: int = Field(default=30, ge=1, le=600)
    network_enabled: bool = False
    filesystem_read: bool = False
    filesystem_write: bool = False


class SecurityAnalysisRequest(BaseSchema):
    """Request to analyze plugin security."""

    plugin_id: str
    code: str | None = None
    deep_analysis: bool = Field(default=False, description="Perform deep AST analysis")


class CodeAnalysisResult(BaseSchema):
    """Result of code security analysis."""

    is_safe: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blocked_constructs: list[str] = Field(default_factory=list)
    detected_imports: list[str] = Field(default_factory=list)
    detected_permissions: list[str] = Field(default_factory=list)
    complexity_score: int = Field(default=0, ge=0, le=100)


class ExtendedSecurityReport(SecurityReport):
    """Extended security report with detailed analysis."""

    code_analysis: CodeAnalysisResult | None = None
    signature_count: int = 0
    trust_level: SecurityLevel = SecurityLevel.UNVERIFIED
    can_run_in_sandbox: bool = True
    code_hash: str = ""
    recommendations: list[str] = Field(default_factory=list)


class VerifySignatureRequest(BaseSchema):
    """Request to verify plugin signature."""

    plugin_id: str
    signature: str
    content_hash: str
    algorithm: SignatureAlgorithm = SignatureAlgorithm.ED25519


class VerifySignatureResponse(BaseSchema):
    """Response from signature verification."""

    is_valid: bool
    signer_id: str | None = None
    signer_name: str | None = None
    signed_at: datetime | None = None
    error: str | None = None


# =============================================================================
# Plugin Hooks
# =============================================================================


class HookType(str, Enum):
    """Types of hooks in the plugin system."""

    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"
    ON_ISSUE_FOUND = "on_issue_found"
    BEFORE_PROFILE = "before_profile"
    AFTER_PROFILE = "after_profile"
    BEFORE_COMPARE = "before_compare"
    AFTER_COMPARE = "after_compare"
    ON_PLUGIN_LOAD = "on_plugin_load"
    ON_PLUGIN_UNLOAD = "on_plugin_unload"
    ON_PLUGIN_ERROR = "on_plugin_error"
    BEFORE_NOTIFICATION = "before_notification"
    AFTER_NOTIFICATION = "after_notification"
    ON_SCHEDULE_RUN = "on_schedule_run"
    ON_DATA_SOURCE_CONNECT = "on_data_source_connect"
    ON_SCHEMA_CHANGE = "on_schema_change"
    CUSTOM = "custom"


class HookPriority(str, Enum):
    """Priority levels for hook execution."""

    HIGHEST = "highest"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    LOWEST = "lowest"


class HookRegistration(BaseSchema):
    """A registered hook."""

    id: str
    hook_type: HookType
    plugin_id: str
    function_name: str
    priority: HookPriority = HookPriority.NORMAL
    is_async: bool = False
    is_enabled: bool = True
    description: str | None = None


class HookListResponse(BaseSchema):
    """Response listing registered hooks."""

    hooks: list[HookRegistration] = Field(default_factory=list)
    total: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class RegisterHookRequest(BaseSchema):
    """Request to register a new hook."""

    hook_type: HookType
    plugin_id: str
    function_name: str
    priority: HookPriority = HookPriority.NORMAL
    description: str | None = None


class UnregisterHookRequest(BaseSchema):
    """Request to unregister a hook."""

    hook_id: str


class HookExecutionResult(BaseSchema):
    """Result of hook execution."""

    hook_id: str
    plugin_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0
    modified_data: bool = False


class HookExecutionSummary(BaseSchema):
    """Summary of all hook executions for an event."""

    hook_type: HookType
    total_hooks: int
    successful: int
    failed: int
    total_time_ms: float
    results: list[HookExecutionResult] = Field(default_factory=list)


# =============================================================================
# Plugin Documentation
# =============================================================================


class ParameterDoc(BaseSchema):
    """Documentation for a function parameter."""

    name: str
    type: str | None = None
    description: str | None = None
    default: str | None = None
    required: bool = True


class FunctionDoc(BaseSchema):
    """Documentation for a function."""

    name: str
    description: str | None = None
    parameters: list[ParameterDoc] = Field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None
    raises: dict[str, str] = Field(default_factory=dict)
    is_async: bool = False
    deprecated: bool = False
    examples: list[str] = Field(default_factory=list)


class ClassDoc(BaseSchema):
    """Documentation for a class."""

    name: str
    description: str | None = None
    bases: list[str] = Field(default_factory=list)
    init_params: list[ParameterDoc] = Field(default_factory=list)
    attributes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    methods: list[FunctionDoc] = Field(default_factory=list)
    deprecated: bool = False
    examples: list[str] = Field(default_factory=list)


class ModuleDoc(BaseSchema):
    """Documentation for a module."""

    name: str
    description: str | None = None
    file_path: str | None = None
    classes: list[ClassDoc] = Field(default_factory=list)
    functions: list[FunctionDoc] = Field(default_factory=list)
    constants: dict[str, Any] = Field(default_factory=dict)


class PluginDocumentation(BaseSchema):
    """Complete documentation for a plugin."""

    plugin_id: str
    plugin_name: str
    version: str
    modules: list[ModuleDoc] = Field(default_factory=list)
    readme: str | None = None
    changelog: str | None = None
    examples: list[dict[str, str]] = Field(default_factory=list)
    generated_at: datetime | None = None


class DocumentationRenderRequest(BaseSchema):
    """Request to render plugin documentation."""

    plugin_id: str
    format: Literal["markdown", "html", "json"] = "markdown"
    include_private: bool = False
    include_source: bool = False
    include_examples: bool = True


class DocumentationRenderResponse(BaseSchema):
    """Response with rendered documentation."""

    plugin_id: str
    format: str
    content: str
    generation_time_ms: float = 0
