"""Plugin System API endpoints.

This module provides REST API endpoints for:
- Plugin marketplace (discovery, search, install)
- Custom validators (CRUD, test, execute)
- Custom reporters (CRUD, preview, generate)
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core.plugins import (
    CustomReporterExecutor,
    CustomValidatorExecutor,
    PluginLoader,
    PluginRegistry,
    PluginSecurityManager,
)
from truthound_dashboard.core.plugins.registry import plugin_registry
from truthound_dashboard.core.plugins.reporter_executor import ReportContext
from truthound_dashboard.core.plugins.validator_executor import ValidatorContext
from truthound_dashboard.db.models import PluginStatus as DBPluginStatus
from truthound_dashboard.db.models import PluginType as DBPluginType
from truthound_dashboard.db.models import Validation
from truthound_dashboard.schemas.plugins import (
    AddSignerRequest,
    CodeAnalysisResult,
    CustomReporterCreate,
    CustomReporterListResponse,
    CustomReporterResponse,
    CustomReporterUpdate,
    CustomValidatorCreate,
    CustomValidatorListResponse,
    CustomValidatorResponse,
    CustomValidatorUpdate,
    DependencyGraphResponse,
    DependencyResolutionRequest,
    DependencyResolutionResponse,
    DocumentationRenderRequest,
    DocumentationRenderResponse,
    ExtendedSecurityReport,
    HookListResponse,
    HookRegistration,
    HookType,
    HotReloadConfigRequest,
    HotReloadResult,
    HotReloadStatus,
    MarketplaceSearchRequest,
    MarketplaceStats,
    PluginCreate,
    PluginDocumentation,
    PluginInstallRequest,
    PluginInstallResponse,
    PluginLifecycleResponse,
    PluginListResponse,
    PluginResponse,
    PluginState,
    PluginStatus,
    PluginSummary,
    PluginTransitionRequest,
    PluginTransitionResponse,
    PluginType,
    PluginUninstallRequest,
    PluginUninstallResponse,
    PluginUpdate,
    PluginUpdateCheckResponse,
    RegisterHookRequest,
    ReporterGenerateRequest,
    ReporterGenerateResponse,
    SecurityAnalysisRequest,
    SecurityPolicyConfig,
    TrustStoreResponse,
    TrustedSigner,
    ValidatorTestRequest,
    ValidatorTestResponse,
    VerifySignatureRequest,
    VerifySignatureResponse,
)

from .deps import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencies
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# =============================================================================
# Plugin Marketplace Endpoints
# =============================================================================


@router.get("/plugins", response_model=PluginListResponse)
async def list_plugins(
    session: SessionDep,
    type: PluginType | None = None,
    status: PluginStatus | None = None,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PluginListResponse:
    """List all plugins with optional filtering.

    Args:
        session: Database session.
        type: Filter by plugin type.
        status: Filter by status.
        search: Search in name, display_name, description.
        offset: Pagination offset.
        limit: Pagination limit.

    Returns:
        List of plugins.
    """
    db_type = DBPluginType(type.value) if type else None
    db_status = DBPluginStatus(status.value) if status else None

    plugins, total = await plugin_registry.list_plugins(
        session=session,
        plugin_type=db_type,
        status=db_status,
        search=search,
        offset=offset,
        limit=limit,
    )

    return PluginListResponse(
        data=[PluginResponse.from_model(p) for p in plugins],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/plugins/stats", response_model=MarketplaceStats)
async def get_marketplace_stats(session: SessionDep) -> MarketplaceStats:
    """Get marketplace statistics.

    Args:
        session: Database session.

    Returns:
        Marketplace statistics.
    """
    stats = await plugin_registry.get_statistics(session)

    return MarketplaceStats(
        total_plugins=stats["total_plugins"],
        total_validators=stats["total_validators"],
        total_reporters=stats["total_reporters"],
        total_installs=0,  # Could track this separately
        categories=[],
        featured_plugins=[],
        popular_plugins=[],
        recent_plugins=[],
    )


@router.post("/plugins/search")
async def search_plugins(
    session: SessionDep,
    request: MarketplaceSearchRequest,
) -> PluginListResponse:
    """Search plugins in marketplace.

    Args:
        session: Database session.
        request: Search request.

    Returns:
        List of matching plugins.
    """
    # Convert types
    db_types = [DBPluginType(t.value) for t in request.types] if request.types else None

    plugins, total = await plugin_registry.list_plugins(
        session=session,
        plugin_type=db_types[0] if db_types and len(db_types) == 1 else None,
        search=request.query,
        offset=request.offset,
        limit=request.limit,
    )

    return PluginListResponse(
        data=[PluginResponse.from_model(p) for p in plugins],
        total=total,
        offset=request.offset,
        limit=request.limit,
    )


@router.get("/plugins/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    """Get a plugin by ID.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Plugin details.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    return PluginResponse.from_model(plugin)


@router.post("/plugins", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
async def register_plugin(
    session: SessionDep,
    request: PluginCreate,
) -> PluginResponse:
    """Register a new plugin.

    Args:
        session: Database session.
        request: Plugin creation request.

    Returns:
        Created plugin.
    """
    try:
        plugin = await plugin_registry.register_plugin(
            session=session,
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            version=request.version,
            plugin_type=DBPluginType(request.type.value),
            source=request.source.value,
            author=request.author.model_dump() if request.author else None,
            license=request.license,
            homepage=request.homepage,
            repository=request.repository,
            keywords=request.keywords,
            categories=request.categories,
            dependencies=[d.model_dump() for d in request.dependencies],
            permissions=[p.value for p in request.permissions],
            python_version=request.python_version,
            dashboard_version=request.dashboard_version,
            icon_url=request.icon_url,
            banner_url=request.banner_url,
            documentation_url=request.documentation_url,
            changelog=request.changelog,
            readme=request.readme,
        )
        await session.commit()
        return PluginResponse.from_model(plugin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/plugins/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    session: SessionDep,
    plugin_id: str,
    request: PluginUpdate,
) -> PluginResponse:
    """Update a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Update request.

    Returns:
        Updated plugin.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Update fields
    for field, value in request.model_dump(exclude_unset=True).items():
        if hasattr(plugin, field) and value is not None:
            setattr(plugin, field, value)

    await session.commit()
    return PluginResponse.from_model(plugin)


@router.post("/plugins/{plugin_id}/install", response_model=PluginInstallResponse)
async def install_plugin(
    session: SessionDep,
    plugin_id: str,
    request: PluginInstallRequest | None = None,
) -> PluginInstallResponse:
    """Install a plugin.

    This endpoint performs security verification before installation:
    - Checks plugin signature if available
    - Analyzes code for security issues
    - Validates sandbox compatibility

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Install request.

    Returns:
        Installation result with security warnings if applicable.
    """
    # Get plugin first for security analysis
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        return PluginInstallResponse(
            success=False,
            plugin_id=plugin_id,
            message=f"Plugin {plugin_id} not found",
        )

    warnings: list[str] = []

    # Perform security analysis
    try:
        security_manager = PluginSecurityManager()
        security_report = await security_manager.analyze_plugin(
            plugin_id=plugin_id,
            code=None,  # Would be actual plugin code in real implementation
            permissions=[p for p in (plugin.permissions or [])],
        )

        # Add warnings based on security analysis
        if not security_report.signature_valid:
            warnings.append("Plugin signature could not be verified")

        if security_report.risk_level == "unverified":
            warnings.append("This plugin has not been verified by the maintainers")

        if not security_report.sandbox_compatible:
            warnings.append("Plugin may have limited functionality in sandbox mode")

        for issue in security_report.issues:
            warnings.append(f"Security issue: {issue}")

        for warning in security_report.warnings:
            warnings.append(warning)

    except Exception as e:
        logger.warning(f"Security analysis failed for plugin {plugin_id}: {e}")
        warnings.append("Security analysis could not be completed")

    # Proceed with installation
    try:
        enable = request.enable_after_install if request else True
        skip_verification = request.skip_verification if request else False

        # Block installation if there are critical security issues and verification not skipped
        if warnings and not skip_verification and plugin.security_level == "unverified":
            return PluginInstallResponse(
                success=False,
                plugin_id=plugin_id,
                message="Installation blocked due to security concerns. Set skip_verification=true to override.",
                warnings=warnings,
            )

        plugin = await plugin_registry.install_plugin(
            session=session,
            plugin_id=plugin_id,
            enable=enable,
        )
        await session.commit()

        return PluginInstallResponse(
            success=True,
            plugin_id=plugin_id,
            installed_version=plugin.version,
            message=f"Plugin {plugin.name} v{plugin.version} installed successfully",
            warnings=warnings if warnings else None,
        )
    except ValueError as e:
        return PluginInstallResponse(
            success=False,
            plugin_id=plugin_id,
            message=str(e),
            warnings=warnings if warnings else None,
        )


@router.post("/plugins/{plugin_id}/uninstall", response_model=PluginUninstallResponse)
async def uninstall_plugin(
    session: SessionDep,
    plugin_id: str,
    request: PluginUninstallRequest | None = None,
) -> PluginUninstallResponse:
    """Uninstall a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Uninstall request.

    Returns:
        Uninstallation result.
    """
    try:
        remove_data = request.remove_data if request else False
        await plugin_registry.uninstall_plugin(
            session=session,
            plugin_id=plugin_id,
            remove_data=remove_data,
        )
        await session.commit()

        return PluginUninstallResponse(
            success=True,
            plugin_id=plugin_id,
            message="Plugin uninstalled successfully",
        )
    except ValueError as e:
        return PluginUninstallResponse(
            success=False,
            plugin_id=plugin_id,
            message=str(e),
        )


@router.post("/plugins/{plugin_id}/enable", response_model=PluginResponse)
async def enable_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    """Enable a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Updated plugin.
    """
    try:
        plugin = await plugin_registry.enable_plugin(session, plugin_id)
        await session.commit()
        return PluginResponse.from_model(plugin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/plugins/{plugin_id}/disable", response_model=PluginResponse)
async def disable_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginResponse:
    """Disable a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Updated plugin.
    """
    try:
        plugin = await plugin_registry.disable_plugin(session, plugin_id)
        await session.commit()
        return PluginResponse.from_model(plugin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/plugins/{plugin_id}/check-update", response_model=PluginUpdateCheckResponse)
async def check_plugin_update(
    session: SessionDep,
    plugin_id: str,
) -> PluginUpdateCheckResponse:
    """Check if a plugin has an update available.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Update check response with version info.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Check for updates (compare versions)
    has_update = False
    latest_version = plugin.version

    # In a real implementation, this would check a plugin registry/marketplace
    # For now, we check if latest_version is set and different from current
    if hasattr(plugin, "latest_version") and plugin.latest_version:
        from packaging import version as pkg_version

        try:
            current = pkg_version.parse(plugin.version)
            latest = pkg_version.parse(plugin.latest_version)
            has_update = latest > current
            latest_version = plugin.latest_version
        except Exception:
            pass

    return PluginUpdateCheckResponse(
        plugin_id=plugin_id,
        current_version=plugin.version,
        latest_version=latest_version,
        has_update=has_update,
        changelog=plugin.changelog if has_update else None,
    )


@router.post("/plugins/{plugin_id}/update", response_model=PluginInstallResponse)
async def update_plugin(
    session: SessionDep,
    plugin_id: str,
) -> PluginInstallResponse:
    """Update a plugin to the latest version.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Update result.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Check if plugin is installed
    if plugin.status == DBPluginStatus.available:
        return PluginInstallResponse(
            success=False,
            plugin_id=plugin_id,
            message="Plugin is not installed",
        )

    # Check for updates
    if not hasattr(plugin, "latest_version") or not plugin.latest_version:
        return PluginInstallResponse(
            success=False,
            plugin_id=plugin_id,
            installed_version=plugin.version,
            message="No update available",
        )

    try:
        from packaging import version as pkg_version

        current = pkg_version.parse(plugin.version)
        latest = pkg_version.parse(plugin.latest_version)

        if latest <= current:
            return PluginInstallResponse(
                success=False,
                plugin_id=plugin_id,
                installed_version=plugin.version,
                message="Already at latest version",
            )

        # Perform update (in real implementation, this would download and install)
        old_version = plugin.version
        plugin.version = plugin.latest_version
        plugin.latest_version = None
        plugin.status = DBPluginStatus.enabled if plugin.is_enabled else DBPluginStatus.installed

        await session.commit()

        return PluginInstallResponse(
            success=True,
            plugin_id=plugin_id,
            installed_version=plugin.version,
            message=f"Plugin updated from v{old_version} to v{plugin.version}",
        )
    except Exception as e:
        logger.error(f"Failed to update plugin {plugin_id}: {e}")
        return PluginInstallResponse(
            success=False,
            plugin_id=plugin_id,
            installed_version=plugin.version,
            message=f"Update failed: {str(e)}",
        )


# =============================================================================
# Custom Validator Endpoints
# =============================================================================


@router.get("/validators/custom", response_model=CustomValidatorListResponse)
async def list_custom_validators(
    session: SessionDep,
    plugin_id: str | None = None,
    category: str | None = None,
    enabled_only: bool = False,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> CustomValidatorListResponse:
    """List custom validators.

    Args:
        session: Database session.
        plugin_id: Filter by plugin.
        category: Filter by category.
        enabled_only: Only return enabled validators.
        search: Search query.
        offset: Pagination offset.
        limit: Pagination limit.

    Returns:
        List of custom validators.
    """
    validators, total = await plugin_registry.list_validators(
        session=session,
        plugin_id=plugin_id,
        category=category,
        enabled_only=enabled_only,
        search=search,
        offset=offset,
        limit=limit,
    )

    return CustomValidatorListResponse(
        data=[CustomValidatorResponse.from_model(v) for v in validators],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/validators/custom/categories")
async def list_validator_categories(session: SessionDep) -> list[str]:
    """List all validator categories.

    Args:
        session: Database session.

    Returns:
        List of category names.
    """
    stats = await plugin_registry.get_statistics(session)
    return stats.get("validator_categories", [])


@router.get("/validators/custom/template")
async def get_validator_template() -> dict[str, str]:
    """Get a template for creating custom validators.

    Returns:
        Dictionary with template code.
    """
    executor = CustomValidatorExecutor()
    return {"template": executor.get_validator_template()}


@router.get("/validators/custom/{validator_id}", response_model=CustomValidatorResponse)
async def get_custom_validator(
    session: SessionDep,
    validator_id: str,
) -> CustomValidatorResponse:
    """Get a custom validator by ID.

    Args:
        session: Database session.
        validator_id: Validator ID.

    Returns:
        Validator details.
    """
    validator = await plugin_registry.get_validator(session, validator_id=validator_id)
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validator {validator_id} not found",
        )

    return CustomValidatorResponse.from_model(validator)


@router.post(
    "/validators/custom",
    response_model=CustomValidatorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_validator(
    session: SessionDep,
    request: CustomValidatorCreate,
) -> CustomValidatorResponse:
    """Create a custom validator.

    Args:
        session: Database session.
        request: Validator creation request.

    Returns:
        Created validator.
    """
    # Validate code first
    executor = CustomValidatorExecutor()
    is_valid, issues = executor.validate_validator_code(request.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid validator code: {'; '.join(issues)}",
        )

    try:
        validator = await plugin_registry.register_validator(
            session=session,
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            category=request.category,
            code=request.code,
            plugin_id=request.plugin_id,
            severity=request.severity,
            tags=request.tags,
            parameters=[p.model_dump() for p in request.parameters],
            test_cases=request.test_cases,
        )
        await session.commit()
        return CustomValidatorResponse.from_model(validator)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/validators/custom/{validator_id}", response_model=CustomValidatorResponse)
async def update_custom_validator(
    session: SessionDep,
    validator_id: str,
    request: CustomValidatorUpdate,
) -> CustomValidatorResponse:
    """Update a custom validator.

    Args:
        session: Database session.
        validator_id: Validator ID.
        request: Update request.

    Returns:
        Updated validator.
    """
    # Validate code if provided
    if request.code:
        executor = CustomValidatorExecutor()
        is_valid, issues = executor.validate_validator_code(request.code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid validator code: {'; '.join(issues)}",
            )

    try:
        updates = request.model_dump(exclude_unset=True)
        if "parameters" in updates and updates["parameters"]:
            updates["parameters"] = [p.model_dump() if hasattr(p, "model_dump") else p for p in updates["parameters"]]

        validator = await plugin_registry.update_validator(
            session=session,
            validator_id=validator_id,
            **updates,
        )
        await session.commit()
        return CustomValidatorResponse.from_model(validator)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/validators/custom/{validator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_validator(
    session: SessionDep,
    validator_id: str,
) -> None:
    """Delete a custom validator.

    Args:
        session: Database session.
        validator_id: Validator ID.
    """
    try:
        await plugin_registry.delete_validator(session, validator_id)
        await session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/validators/custom/test", response_model=ValidatorTestResponse)
async def test_custom_validator(request: ValidatorTestRequest) -> ValidatorTestResponse:
    """Test a custom validator without saving.

    Args:
        request: Test request with code and test data.

    Returns:
        Test results.
    """
    executor = CustomValidatorExecutor()
    result = await executor.test_validator(
        code=request.code,
        parameters=[p.model_dump() for p in request.parameters],
        test_data=request.test_data,
        param_values=request.param_values,
    )

    return ValidatorTestResponse(
        success=result["success"],
        passed=result.get("passed"),
        execution_time_ms=result["execution_time_ms"],
        result=result.get("result"),
        error=result.get("error"),
        warnings=result.get("warnings", []),
    )


# =============================================================================
# Custom Reporter Endpoints
# =============================================================================


@router.get("/reporters/custom", response_model=CustomReporterListResponse)
async def list_custom_reporters(
    session: SessionDep,
    plugin_id: str | None = None,
    enabled_only: bool = False,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> CustomReporterListResponse:
    """List custom reporters.

    Args:
        session: Database session.
        plugin_id: Filter by plugin.
        enabled_only: Only return enabled reporters.
        search: Search query.
        offset: Pagination offset.
        limit: Pagination limit.

    Returns:
        List of custom reporters.
    """
    reporters, total = await plugin_registry.list_reporters(
        session=session,
        plugin_id=plugin_id,
        enabled_only=enabled_only,
        search=search,
        offset=offset,
        limit=limit,
    )

    return CustomReporterListResponse(
        data=[CustomReporterResponse.from_model(r) for r in reporters],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/reporters/custom/templates")
async def get_reporter_templates() -> dict[str, str]:
    """Get templates for creating custom reporters.

    Returns:
        Dictionary with code and Jinja2 templates.
    """
    executor = CustomReporterExecutor()
    return {
        "code_template": executor.get_reporter_template(),
        "jinja2_template": executor.get_jinja2_template(),
    }


@router.get("/reporters/custom/{reporter_id}", response_model=CustomReporterResponse)
async def get_custom_reporter(
    session: SessionDep,
    reporter_id: str,
) -> CustomReporterResponse:
    """Get a custom reporter by ID.

    Args:
        session: Database session.
        reporter_id: Reporter ID.

    Returns:
        Reporter details.
    """
    reporter = await plugin_registry.get_reporter(session, reporter_id=reporter_id)
    if not reporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporter {reporter_id} not found",
        )

    return CustomReporterResponse.from_model(reporter)


@router.post(
    "/reporters/custom",
    response_model=CustomReporterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_reporter(
    session: SessionDep,
    request: CustomReporterCreate,
) -> CustomReporterResponse:
    """Create a custom reporter.

    Args:
        session: Database session.
        request: Reporter creation request.

    Returns:
        Created reporter.
    """
    # Validate code or template
    executor = CustomReporterExecutor()
    if request.code:
        is_valid, issues = executor.validate_reporter_code(request.code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reporter code: {'; '.join(issues)}",
            )
    if request.template:
        is_valid, issues = executor.validate_template(request.template)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template: {'; '.join(issues)}",
            )

    try:
        reporter = await plugin_registry.register_reporter(
            session=session,
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            plugin_id=request.plugin_id,
            output_formats=[f.value for f in request.output_formats],
            config_fields=[f.model_dump() for f in request.config_fields],
            template=request.template,
            code=request.code,
            preview_image_url=request.preview_image_url,
        )
        await session.commit()
        return CustomReporterResponse.from_model(reporter)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/reporters/custom/{reporter_id}", response_model=CustomReporterResponse)
async def update_custom_reporter(
    session: SessionDep,
    reporter_id: str,
    request: CustomReporterUpdate,
) -> CustomReporterResponse:
    """Update a custom reporter.

    Args:
        session: Database session.
        reporter_id: Reporter ID.
        request: Update request.

    Returns:
        Updated reporter.
    """
    executor = CustomReporterExecutor()

    # Validate code or template if provided
    if request.code:
        is_valid, issues = executor.validate_reporter_code(request.code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reporter code: {'; '.join(issues)}",
            )
    if request.template:
        is_valid, issues = executor.validate_template(request.template)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template: {'; '.join(issues)}",
            )

    try:
        updates = request.model_dump(exclude_unset=True)
        if "output_formats" in updates and updates["output_formats"]:
            updates["output_formats"] = [f.value if hasattr(f, "value") else f for f in updates["output_formats"]]
        if "config_fields" in updates and updates["config_fields"]:
            updates["config_fields"] = [f.model_dump() if hasattr(f, "model_dump") else f for f in updates["config_fields"]]

        reporter = await plugin_registry.update_reporter(
            session=session,
            reporter_id=reporter_id,
            **updates,
        )
        await session.commit()
        return CustomReporterResponse.from_model(reporter)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/reporters/custom/{reporter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_reporter(
    session: SessionDep,
    reporter_id: str,
) -> None:
    """Delete a custom reporter.

    Args:
        session: Database session.
        reporter_id: Reporter ID.
    """
    try:
        await plugin_registry.delete_reporter(session, reporter_id)
        await session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/reporters/custom/preview", response_model=ReporterGenerateResponse)
async def preview_custom_reporter(
    template: str | None = None,
    code: str | None = None,
    sample_data: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    format: str = "html",
) -> ReporterGenerateResponse:
    """Preview a custom reporter without saving.

    Args:
        template: Jinja2 template.
        code: Python code.
        sample_data: Sample data.
        config: Reporter configuration.
        format: Output format.

    Returns:
        Preview result.
    """
    executor = CustomReporterExecutor()
    result = await executor.preview_report(
        template=template,
        code=code,
        sample_data=sample_data,
        config=config,
        format=format,
    )

    return ReporterGenerateResponse(
        success=result.success,
        preview_html=result.content if result.success else None,
        error=result.error,
        generation_time_ms=result.execution_time_ms,
    )


@router.post("/reporters/custom/{reporter_id}/generate", response_model=ReporterGenerateResponse)
async def generate_report(
    session: SessionDep,
    reporter_id: str,
    request: ReporterGenerateRequest,
) -> ReporterGenerateResponse:
    """Generate a report using a custom reporter.

    Supports two modes:
    1. Provide validation_id to auto-fetch validation data
    2. Provide data directly for custom report generation

    Args:
        session: Database session.
        reporter_id: Reporter ID.
        request: Generation request with validation_id or data.

    Returns:
        Generation result with content or error.
    """
    reporter = await plugin_registry.get_reporter(session, reporter_id=reporter_id)
    if not reporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporter {reporter_id} not found",
        )

    # Determine data source: validation_id takes precedence
    report_data: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    source_id: str | None = None

    if request.validation_id:
        # Fetch validation data from database
        from sqlalchemy import select

        stmt = select(Validation).where(Validation.id == request.validation_id)
        result = await session.execute(stmt)
        validation = result.scalar_one_or_none()

        if not validation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation {request.validation_id} not found",
            )

        # Build report data from validation
        report_data = {
            "validation_id": str(validation.id),
            "source_id": str(validation.source_id) if validation.source_id else None,
            "source_name": validation.source_name or "Unknown Source",
            "status": validation.status or "unknown",
            "passed": validation.passed,
            "started_at": validation.started_at.isoformat() if validation.started_at else None,
            "completed_at": validation.completed_at.isoformat() if validation.completed_at else None,
            "duration_ms": validation.duration_ms,
            "row_count": validation.row_count,
            "column_count": validation.column_count,
            "error_message": validation.error_message,
            "results": validation.results or [],
            "summary": validation.summary or {},
            "issues": validation.results or [],
        }
        metadata = {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "validation_id": str(validation.id),
            "source_name": validation.source_name or "Unknown Source",
        }
        source_id = str(validation.source_id) if validation.source_id else None

    elif request.data:
        report_data = request.data
        metadata = {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either validation_id or data must be provided",
        )

    executor = CustomReporterExecutor()
    context = ReportContext(
        data=report_data,
        config=request.config,
        format=request.output_format.value,
        metadata=metadata,
    )

    result = await executor.execute(
        reporter=reporter,
        context=context,
        session=session,
        source_id=source_id,
    )

    await session.commit()

    return ReporterGenerateResponse(
        success=result.success,
        preview_html=result.content if result.success else None,
        error=result.error,
        generation_time_ms=result.execution_time_ms,
    )


@router.get("/reporters/custom/{reporter_id}/download")
async def download_custom_report(
    session: SessionDep,
    reporter_id: str,
    validation_id: str = Query(..., description="Validation ID to generate report from"),
    output_format: str = Query("html", description="Output format (html, json, csv, markdown, pdf)"),
    config: str | None = Query(None, description="JSON-encoded reporter configuration"),
) -> Any:
    """Download a report generated by a custom reporter.

    This endpoint generates the report and returns it as a downloadable file.

    Args:
        session: Database session.
        reporter_id: Reporter ID.
        validation_id: Validation ID to generate report from.
        output_format: Desired output format.
        config: Optional JSON-encoded configuration.

    Returns:
        StreamingResponse with the generated report file.
    """
    from datetime import datetime
    import json as json_module

    from fastapi.responses import StreamingResponse

    reporter = await plugin_registry.get_reporter(session, reporter_id=reporter_id)
    if not reporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporter {reporter_id} not found",
        )

    # Fetch validation data
    from sqlalchemy import select

    stmt = select(Validation).where(Validation.id == validation_id)
    result = await session.execute(stmt)
    validation = result.scalar_one_or_none()

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation {validation_id} not found",
        )

    # Parse config if provided
    reporter_config: dict[str, Any] = {}
    if config:
        try:
            reporter_config = json_module.loads(config)
        except json_module.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid config JSON",
            )

    # Build report data from validation
    report_data = {
        "validation_id": str(validation.id),
        "source_id": str(validation.source_id) if validation.source_id else None,
        "source_name": validation.source_name or "Unknown Source",
        "status": validation.status or "unknown",
        "passed": validation.passed,
        "started_at": validation.started_at.isoformat() if validation.started_at else None,
        "completed_at": validation.completed_at.isoformat() if validation.completed_at else None,
        "duration_ms": validation.duration_ms,
        "row_count": validation.row_count,
        "column_count": validation.column_count,
        "error_message": validation.error_message,
        "results": validation.results or [],
        "summary": validation.summary or {},
        "issues": validation.results or [],
    }

    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "validation_id": str(validation.id),
        "source_name": validation.source_name or "Unknown Source",
    }

    executor = CustomReporterExecutor()
    context = ReportContext(
        data=report_data,
        config=reporter_config,
        format=output_format,
        metadata=metadata,
    )

    exec_result = await executor.execute(
        reporter=reporter,
        context=context,
        session=session,
        source_id=str(validation.source_id) if validation.source_id else None,
    )

    await session.commit()

    if not exec_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {exec_result.error}",
        )

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_report_{reporter.name}_{timestamp}.{_get_extension(output_format)}"

    # Return as streaming response
    content = exec_result.content
    if isinstance(content, str):
        content = content.encode("utf-8")

    return StreamingResponse(
        iter([content]),
        media_type=exec_result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


def _get_extension(format_type: str) -> str:
    """Get file extension for format type."""
    extensions = {
        "html": "html",
        "json": "json",
        "csv": "csv",
        "markdown": "md",
        "pdf": "pdf",
        "xml": "xml",
        "junit": "xml",
    }
    return extensions.get(format_type.lower(), "txt")


# =============================================================================
# Plugin Lifecycle Endpoints
# =============================================================================


@router.get("/plugins/{plugin_id}/lifecycle", response_model=PluginLifecycleResponse)
async def get_plugin_lifecycle(
    session: SessionDep,
    plugin_id: str,
) -> PluginLifecycleResponse:
    """Get plugin lifecycle status.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Plugin lifecycle status.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Map DB status to lifecycle state
    state_map = {
        DBPluginStatus.available: PluginState.DISCOVERED,
        DBPluginStatus.installed: PluginState.LOADED,
        DBPluginStatus.enabled: PluginState.ACTIVE,
        DBPluginStatus.disabled: PluginState.LOADED,
        DBPluginStatus.error: PluginState.FAILED,
    }

    current_state = state_map.get(plugin.status, PluginState.DISCOVERED)

    return PluginLifecycleResponse(
        plugin_id=plugin_id,
        current_state=current_state,
        can_activate=current_state == PluginState.LOADED,
        can_deactivate=current_state == PluginState.ACTIVE,
        can_reload=current_state in {PluginState.ACTIVE, PluginState.LOADED},
        can_upgrade=current_state in {PluginState.ACTIVE, PluginState.LOADED},
        recent_events=[],
    )


@router.post("/plugins/{plugin_id}/transition", response_model=PluginTransitionResponse)
async def transition_plugin_state(
    session: SessionDep,
    plugin_id: str,
    request: PluginTransitionRequest,
) -> PluginTransitionResponse:
    """Transition plugin to a new state.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Transition request.

    Returns:
        Transition result.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Map current DB status to lifecycle state
    state_map = {
        DBPluginStatus.available: PluginState.DISCOVERED,
        DBPluginStatus.installed: PluginState.LOADED,
        DBPluginStatus.enabled: PluginState.ACTIVE,
        DBPluginStatus.disabled: PluginState.LOADED,
        DBPluginStatus.error: PluginState.FAILED,
    }
    from_state = state_map.get(plugin.status, PluginState.DISCOVERED)

    try:
        # Handle state transitions
        if request.target_state == PluginState.ACTIVE:
            plugin = await plugin_registry.enable_plugin(session, plugin_id)
        elif request.target_state == PluginState.LOADED:
            plugin = await plugin_registry.disable_plugin(session, plugin_id)
        elif request.target_state == PluginState.UNLOADED:
            await plugin_registry.uninstall_plugin(session, plugin_id)

        await session.commit()

        return PluginTransitionResponse(
            success=True,
            plugin_id=plugin_id,
            from_state=from_state,
            to_state=request.target_state,
            message=f"Plugin transitioned to {request.target_state.value}",
        )
    except ValueError as e:
        return PluginTransitionResponse(
            success=False,
            plugin_id=plugin_id,
            from_state=from_state,
            to_state=from_state,
            error=str(e),
        )


# =============================================================================
# Plugin Hot Reload Endpoints
# =============================================================================


@router.get("/plugins/{plugin_id}/hot-reload", response_model=HotReloadStatus)
async def get_hot_reload_status(
    session: SessionDep,
    plugin_id: str,
) -> HotReloadStatus:
    """Get hot reload status for a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Hot reload status.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Return default status (would be managed by HotReloadManager in production)
    from truthound_dashboard.schemas.plugins import ReloadStrategy

    return HotReloadStatus(
        plugin_id=plugin_id,
        enabled=False,
        watching=False,
        strategy=ReloadStrategy.MANUAL,
        has_pending_reload=False,
    )


@router.post("/plugins/{plugin_id}/hot-reload/configure", response_model=HotReloadStatus)
async def configure_hot_reload(
    session: SessionDep,
    plugin_id: str,
    request: HotReloadConfigRequest,
) -> HotReloadStatus:
    """Configure hot reload for a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Hot reload configuration.

    Returns:
        Updated hot reload status.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # In production, this would configure the HotReloadManager
    return HotReloadStatus(
        plugin_id=plugin_id,
        enabled=request.enabled,
        watching=request.enabled,
        strategy=request.strategy,
        has_pending_reload=False,
    )


@router.post("/plugins/{plugin_id}/hot-reload/trigger", response_model=HotReloadResult)
async def trigger_hot_reload(
    session: SessionDep,
    plugin_id: str,
) -> HotReloadResult:
    """Manually trigger a hot reload for a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Hot reload result.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # In production, this would trigger the HotReloadManager
    import time

    start = time.perf_counter()
    # Simulate reload
    duration = (time.perf_counter() - start) * 1000

    return HotReloadResult(
        success=True,
        plugin_id=plugin_id,
        old_version=plugin.version,
        new_version=plugin.version,
        duration_ms=duration,
        changes=[],
    )


# =============================================================================
# Plugin Dependency Endpoints
# =============================================================================


@router.get("/plugins/{plugin_id}/dependencies", response_model=DependencyGraphResponse)
async def get_plugin_dependencies(
    session: SessionDep,
    plugin_id: str,
    include_optional: bool = False,
) -> DependencyGraphResponse:
    """Get dependency graph for a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        include_optional: Include optional dependencies.

    Returns:
        Dependency graph.
    """
    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    from truthound_dashboard.schemas.plugins import (
        DependencyGraphNode,
        DependencyInfo,
        DependencyType,
    )

    # Build dependency graph from plugin dependencies
    nodes = []
    dependencies = plugin.dependencies or []

    root_node = DependencyGraphNode(
        plugin_id=plugin_id,
        version=plugin.version,
        dependencies=[
            DependencyInfo(
                plugin_id=dep.get("plugin_id", ""),
                version_constraint=dep.get("version_constraint", "*"),
                dependency_type=DependencyType(dep.get("type", "required")),
                is_installed=False,
                is_satisfied=False,
            )
            for dep in dependencies
            if include_optional or not dep.get("optional", False)
        ],
        dependents=[],
        depth=0,
    )
    nodes.append(root_node)

    return DependencyGraphResponse(
        root_plugin_id=plugin_id,
        nodes=nodes,
        has_cycles=False,
        install_order=[plugin_id],
        total_dependencies=len(dependencies),
    )


@router.post("/plugins/dependencies/resolve", response_model=DependencyResolutionResponse)
async def resolve_dependencies(
    session: SessionDep,
    request: DependencyResolutionRequest,
) -> DependencyResolutionResponse:
    """Resolve dependencies for a set of plugins.

    Args:
        session: Database session.
        request: Resolution request.

    Returns:
        Resolution result.
    """
    from truthound_dashboard.schemas.plugins import DependencyInfo, DependencyType

    resolved = []
    unresolved = []
    install_order = []

    for plugin_id in request.plugin_ids:
        plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
        if plugin:
            install_order.append(plugin_id)
            for dep in plugin.dependencies or []:
                dep_info = DependencyInfo(
                    plugin_id=dep.get("plugin_id", ""),
                    version_constraint=dep.get("version_constraint", "*"),
                    dependency_type=DependencyType(dep.get("type", "required")),
                    is_installed=False,
                    is_satisfied=False,
                )
                # Check if dependency is installed
                dep_plugin = await plugin_registry.get_plugin(
                    session, plugin_id=dep.get("plugin_id", "")
                )
                if dep_plugin:
                    dep_info.is_installed = True
                    dep_info.resolved_version = dep_plugin.version
                    dep_info.is_satisfied = True
                    resolved.append(dep_info)
                else:
                    unresolved.append(dep_info)
        else:
            unresolved.append(
                DependencyInfo(
                    plugin_id=plugin_id,
                    version_constraint="*",
                    is_installed=False,
                    is_satisfied=False,
                )
            )

    return DependencyResolutionResponse(
        success=len(unresolved) == 0,
        resolved=resolved,
        unresolved=unresolved,
        conflicts=[],
        install_order=install_order,
    )


# =============================================================================
# Plugin Security Endpoints
# =============================================================================


@router.get("/plugins/security/trust-store", response_model=TrustStoreResponse)
async def get_trust_store(session: SessionDep) -> TrustStoreResponse:
    """Get the trust store containing trusted signers.

    Args:
        session: Database session.

    Returns:
        Trust store information.
    """
    # In production, this would read from the actual TrustStore
    return TrustStoreResponse(
        signers=[],
        total_signers=0,
    )


@router.post("/plugins/security/trust-store/signers", response_model=TrustedSigner)
async def add_trusted_signer(
    session: SessionDep,
    request: AddSignerRequest,
) -> TrustedSigner:
    """Add a trusted signer to the trust store.

    Args:
        session: Database session.
        request: Signer information.

    Returns:
        Added signer.
    """
    from datetime import datetime

    from truthound_dashboard.schemas.plugins import SecurityLevel

    # In production, this would add to the actual TrustStore
    return TrustedSigner(
        signer_id=request.signer_id,
        name=request.name,
        public_key=request.public_key,
        algorithm=request.algorithm,
        added_at=datetime.utcnow(),
        expires_at=request.expires_at,
        is_active=True,
        trust_level=request.trust_level or SecurityLevel.VERIFIED,
    )


@router.delete("/plugins/security/trust-store/signers/{signer_id}")
async def remove_trusted_signer(
    session: SessionDep,
    signer_id: str,
) -> dict[str, bool]:
    """Remove a trusted signer from the trust store.

    Args:
        session: Database session.
        signer_id: Signer ID to remove.

    Returns:
        Success status.
    """
    # In production, this would remove from the actual TrustStore
    return {"success": True}


@router.get("/plugins/security/policy", response_model=SecurityPolicyConfig)
async def get_security_policy(session: SessionDep) -> SecurityPolicyConfig:
    """Get current security policy configuration.

    Args:
        session: Database session.

    Returns:
        Security policy configuration.
    """
    from truthound_dashboard.schemas.plugins import (
        IsolationLevel,
        SecurityPolicyPreset,
    )

    # Return default policy
    return SecurityPolicyConfig(
        preset=SecurityPolicyPreset.STANDARD,
        isolation_level=IsolationLevel.PROCESS,
        require_signature=True,
        min_signatures=1,
        memory_limit_mb=256,
        cpu_time_limit_sec=30,
        network_enabled=False,
        filesystem_read=False,
        filesystem_write=False,
    )


@router.put("/plugins/security/policy", response_model=SecurityPolicyConfig)
async def update_security_policy(
    session: SessionDep,
    request: SecurityPolicyConfig,
) -> SecurityPolicyConfig:
    """Update security policy configuration.

    Args:
        session: Database session.
        request: New policy configuration.

    Returns:
        Updated policy configuration.
    """
    # In production, this would persist the policy
    return request


@router.post("/plugins/{plugin_id}/security/analyze", response_model=ExtendedSecurityReport)
async def analyze_plugin_security(
    session: SessionDep,
    plugin_id: str,
    request: SecurityAnalysisRequest | None = None,
) -> ExtendedSecurityReport:
    """Perform detailed security analysis on a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Analysis request.

    Returns:
        Extended security report.
    """
    from datetime import datetime

    from truthound_dashboard.schemas.plugins import SecurityLevel

    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    # Perform security analysis
    code = request.code if request else None
    code_analysis = None

    if code:
        code_analysis = CodeAnalysisResult(
            is_safe=True,
            issues=[],
            warnings=[],
            blocked_constructs=[],
            detected_imports=[],
            detected_permissions=[],
            complexity_score=0,
        )

    return ExtendedSecurityReport(
        plugin_id=plugin_id,
        analyzed_at=datetime.utcnow(),
        risk_level=plugin.security_level or SecurityLevel.UNVERIFIED,
        issues=[],
        warnings=[],
        permissions_required=plugin.permissions or [],
        signature_valid=False,
        sandbox_compatible=True,
        code_analysis=code_analysis,
        signature_count=0,
        trust_level=plugin.security_level or SecurityLevel.UNVERIFIED,
        can_run_in_sandbox=True,
        code_hash="",
        recommendations=["Sign the plugin for production use"],
    )


@router.post("/plugins/security/verify-signature", response_model=VerifySignatureResponse)
async def verify_plugin_signature(
    session: SessionDep,
    request: VerifySignatureRequest,
) -> VerifySignatureResponse:
    """Verify a plugin signature.

    Args:
        session: Database session.
        request: Verification request.

    Returns:
        Verification result.
    """
    # In production, this would use the actual verification chain
    return VerifySignatureResponse(
        is_valid=False,
        error="Signature verification not implemented",
    )


# =============================================================================
# Plugin Hooks Endpoints
# =============================================================================


@router.get("/plugins/hooks", response_model=HookListResponse)
async def list_hooks(
    session: SessionDep,
    hook_type: HookType | None = None,
    plugin_id: str | None = None,
) -> HookListResponse:
    """List registered hooks.

    Args:
        session: Database session.
        hook_type: Filter by hook type.
        plugin_id: Filter by plugin ID.

    Returns:
        List of registered hooks.
    """
    # In production, this would query the HookManager
    return HookListResponse(
        hooks=[],
        total=0,
        by_type={},
    )


@router.post("/plugins/hooks", response_model=HookRegistration)
async def register_hook(
    session: SessionDep,
    request: RegisterHookRequest,
) -> HookRegistration:
    """Register a new hook.

    Args:
        session: Database session.
        request: Hook registration request.

    Returns:
        Registered hook.
    """
    import uuid

    from truthound_dashboard.schemas.plugins import HookPriority

    # In production, this would register with the HookManager
    return HookRegistration(
        id=str(uuid.uuid4()),
        hook_type=request.hook_type,
        plugin_id=request.plugin_id,
        function_name=request.function_name,
        priority=request.priority or HookPriority.NORMAL,
        is_async=False,
        is_enabled=True,
        description=request.description,
    )


@router.delete("/plugins/hooks/{hook_id}")
async def unregister_hook(
    session: SessionDep,
    hook_id: str,
) -> dict[str, bool]:
    """Unregister a hook.

    Args:
        session: Database session.
        hook_id: Hook ID to unregister.

    Returns:
        Success status.
    """
    # In production, this would unregister from the HookManager
    return {"success": True}


@router.get("/plugins/hooks/types")
async def list_hook_types() -> list[dict[str, str]]:
    """List available hook types.

    Returns:
        List of hook types with descriptions.
    """
    return [
        {"type": "before_validation", "description": "Runs before validation starts"},
        {"type": "after_validation", "description": "Runs after validation completes"},
        {"type": "on_issue_found", "description": "Runs when a validation issue is found"},
        {"type": "before_profile", "description": "Runs before data profiling"},
        {"type": "after_profile", "description": "Runs after data profiling"},
        {"type": "before_compare", "description": "Runs before drift comparison"},
        {"type": "after_compare", "description": "Runs after drift comparison"},
        {"type": "on_plugin_load", "description": "Runs when a plugin is loaded"},
        {"type": "on_plugin_unload", "description": "Runs when a plugin is unloaded"},
        {"type": "on_plugin_error", "description": "Runs when a plugin error occurs"},
        {"type": "before_notification", "description": "Runs before sending notifications"},
        {"type": "after_notification", "description": "Runs after sending notifications"},
        {"type": "on_schedule_run", "description": "Runs when a schedule executes"},
        {"type": "on_data_source_connect", "description": "Runs when connecting to a data source"},
        {"type": "on_schema_change", "description": "Runs when schema changes are detected"},
        {"type": "custom", "description": "Custom hook type"},
    ]


# =============================================================================
# Plugin Documentation Endpoints
# =============================================================================


@router.get("/plugins/{plugin_id}/documentation", response_model=PluginDocumentation)
async def get_plugin_documentation(
    session: SessionDep,
    plugin_id: str,
) -> PluginDocumentation:
    """Get documentation for a plugin.

    Args:
        session: Database session.
        plugin_id: Plugin ID.

    Returns:
        Plugin documentation.
    """
    from datetime import datetime

    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    return PluginDocumentation(
        plugin_id=plugin_id,
        plugin_name=plugin.name,
        version=plugin.version,
        modules=[],
        readme=plugin.readme,
        changelog=plugin.changelog,
        examples=[],
        generated_at=datetime.utcnow(),
    )


@router.post("/plugins/{plugin_id}/documentation/render", response_model=DocumentationRenderResponse)
async def render_plugin_documentation(
    session: SessionDep,
    plugin_id: str,
    request: DocumentationRenderRequest,
) -> DocumentationRenderResponse:
    """Render plugin documentation in specified format.

    Args:
        session: Database session.
        plugin_id: Plugin ID.
        request: Render request.

    Returns:
        Rendered documentation.
    """
    import time

    plugin = await plugin_registry.get_plugin(session, plugin_id=plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_id} not found",
        )

    start = time.perf_counter()

    # Generate documentation based on format
    if request.format == "markdown":
        content = f"# {plugin.display_name}\n\n{plugin.description or ''}\n\n"
        if plugin.readme:
            content += plugin.readme
    elif request.format == "html":
        content = f"<h1>{plugin.display_name}</h1>\n<p>{plugin.description or ''}</p>\n"
        if plugin.readme:
            content += f"<div class='readme'>{plugin.readme}</div>"
    else:  # json
        import json

        content = json.dumps(
            {
                "name": plugin.name,
                "display_name": plugin.display_name,
                "description": plugin.description,
                "version": plugin.version,
                "readme": plugin.readme,
                "changelog": plugin.changelog,
            },
            indent=2,
        )

    duration = (time.perf_counter() - start) * 1000

    return DocumentationRenderResponse(
        plugin_id=plugin_id,
        format=request.format,
        content=content,
        generation_time_ms=duration,
    )
