"""Rule suggestion API endpoints.

This module provides endpoints for generating and applying
validation rule suggestions based on profile data.

Features:
    - Multiple strictness levels (loose, medium, strict)
    - Preset templates for different use cases
    - Multiple export formats (YAML, JSON, Python, TOML)
    - Category-based filtering
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

from truthound_dashboard.core.rule_generator import RuleGeneratorService
from truthound_dashboard.schemas import (
    ApplyRulesRequest,
    ApplyRulesResponse,
    ExportRulesRequest,
    ExportRulesResponse,
    PresetsResponse,
    RuleSuggestionRequest,
    RuleSuggestionResponse,
)

from .deps import (
    ProfileServiceDep,
    RuleGeneratorServiceDep,
    SchemaServiceDep,
    SourceServiceDep,
)

router = APIRouter(prefix="/sources", tags=["rule-suggestions"])
presets_router = APIRouter(prefix="/rule-suggestions", tags=["rule-suggestions"])


@router.post(
    "/{source_id}/rules/suggest",
    response_model=RuleSuggestionResponse,
    summary="Generate rule suggestions",
    description="""Generate validation rule suggestions based on profile data.

Supports:
- **Strictness levels**: loose, medium, strict
- **Presets**: default, strict, loose, minimal, comprehensive, ci_cd, schema_only, format_only, cross_column, data_integrity
- **Category filtering**: schema, stats, pattern, completeness, uniqueness, distribution, relationship, multi_column
- **Cross-column rules**: composite keys, column comparisons, arithmetic relationships, dependencies, coexistence
""",
)
async def suggest_rules(
    source_id: str,
    generator_service: RuleGeneratorServiceDep,
    profile_service: ProfileServiceDep,
    schema_service: SchemaServiceDep,
    source_service: SourceServiceDep,
    request: RuleSuggestionRequest | None = None,
) -> RuleSuggestionResponse:
    """Generate rule suggestions for a source.

    Args:
        source_id: Source ID.
        generator_service: Rule generator service.
        profile_service: Profile service.
        schema_service: Schema service.
        source_service: Source service.
        request: Optional request parameters.

    Returns:
        Rule suggestion response with single-column and cross-column suggestions.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Parse request
    if request is None:
        request = RuleSuggestionRequest()

    # Get profile
    if request.profile_id and not request.use_latest_profile:
        profile = await profile_service.get(request.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {request.profile_id} not found",
            )
    else:
        profile = await profile_service.get_latest(source_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No profile found for source {source_id}. Run profiling first.",
            )

    # Get schema (optional)
    schema = await schema_service.get_active(source_id)

    # Generate suggestions with advanced options including cross-column
    result = await generator_service.generate_suggestions(
        source,
        profile,
        schema,
        min_confidence=request.min_confidence,
        strictness=request.strictness,
        preset=request.preset,
        include_categories=request.include_categories,
        exclude_categories=request.exclude_categories,
        enable_cross_column=request.enable_cross_column,
        include_cross_column_types=request.include_cross_column_types,
        exclude_cross_column_types=request.exclude_cross_column_types,
    )

    return result


@router.post(
    "/{source_id}/rules/apply-suggestions",
    response_model=ApplyRulesResponse,
    summary="Apply rule suggestions",
    description="Apply selected rule suggestions to create validation rules.",
)
async def apply_rule_suggestions(
    source_id: str,
    request: ApplyRulesRequest,
    generator_service: RuleGeneratorServiceDep,
    source_service: SourceServiceDep,
) -> ApplyRulesResponse:
    """Apply selected rule suggestions.

    Args:
        source_id: Source ID.
        request: Apply rules request.
        generator_service: Rule generator service.
        source_service: Source service.

    Returns:
        Apply rules response.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Validate request
    if not request.suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suggestions provided to apply",
        )

    # Apply suggestions
    result = await generator_service.apply_suggestions(
        source,
        request.suggestions,
        rule_name=request.rule_name,
        rule_description=request.rule_description,
    )

    return result


@router.post(
    "/{source_id}/rules/export",
    response_model=ExportRulesResponse,
    summary="Export rules",
    description="""Export generated rules in various formats.

Supported formats:
- **yaml**: Human-readable YAML format
- **json**: Machine-readable JSON format
- **python**: Executable Python code
- **toml**: Configuration-friendly TOML format
""",
)
async def export_rules(
    source_id: str,
    request: ExportRulesRequest,
    generator_service: RuleGeneratorServiceDep,
    source_service: SourceServiceDep,
) -> ExportRulesResponse:
    """Export rules in specified format.

    Args:
        source_id: Source ID.
        request: Export request.
        generator_service: Rule generator service.
        source_service: Source service.

    Returns:
        Export response with content.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Validate request
    if not request.suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suggestions provided to export",
        )

    # Export rules
    result = generator_service.export_rules(
        request.suggestions,
        format=request.format,
        rule_name=request.rule_name,
        description=request.description,
        include_metadata=request.include_metadata,
    )

    return result


@router.post(
    "/{source_id}/rules/export/download",
    response_class=PlainTextResponse,
    summary="Download exported rules",
    description="Download rules as a file in the specified format.",
)
async def download_exported_rules(
    source_id: str,
    request: ExportRulesRequest,
    generator_service: RuleGeneratorServiceDep,
    source_service: SourceServiceDep,
) -> PlainTextResponse:
    """Download rules as a file.

    Args:
        source_id: Source ID.
        request: Export request.
        generator_service: Rule generator service.
        source_service: Source service.

    Returns:
        Plain text response with file content.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    if not request.suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suggestions provided to export",
        )

    # Export rules
    result = generator_service.export_rules(
        request.suggestions,
        format=request.format,
        rule_name=request.rule_name,
        description=request.description,
        include_metadata=request.include_metadata,
    )

    # Determine content type
    content_type_map = {
        "yaml": "application/x-yaml",
        "json": "application/json",
        "python": "text/x-python",
        "toml": "application/toml",
    }
    content_type = content_type_map.get(result.format.value, "text/plain")

    return PlainTextResponse(
        content=result.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        },
    )


# =============================================================================
# Presets Router
# =============================================================================


@presets_router.get(
    "/presets",
    response_model=PresetsResponse,
    summary="Get available presets",
    description="Get list of available presets, strictness levels, categories, and export formats.",
)
async def get_presets() -> PresetsResponse:
    """Get available rule generation presets and options.

    Returns:
        Presets response.
    """
    return RuleGeneratorService.get_presets()
