"""Reports API endpoints.

This module provides endpoints for generating and downloading validation reports
with internationalization (i18n) support for 15 languages.

Includes Report History management for tracking generated reports.
"""

from __future__ import annotations

import time
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response
from pydantic import BaseModel

from truthound_dashboard.core.reporters import (
    ReportFormat,
    ReportTheme,
    generate_report,
    get_available_formats,
)
from truthound_dashboard.core.reporters.registry import get_report_locales
from truthound_dashboard.core.reporters.i18n import SupportedLocale
from truthound_dashboard.schemas import (
    AvailableFormatsResponse,
    ReportGenerateRequest,
    ReportMetadataResponse,
    ReportResponse,
)
from truthound_dashboard.schemas.reports import (
    BulkReportGenerateRequest,
    BulkReportGenerateResponse,
    GeneratedReportCreate,
    GeneratedReportListResponse,
    GeneratedReportResponse,
    GeneratedReportUpdate,
    ReportHistoryQuery,
    ReportStatistics,
    ReportStatus,
)

from .deps import ReportHistoryServiceDep, ValidationServiceDep

router = APIRouter()


class LocaleInfo(BaseModel):
    """Locale information for API responses."""

    code: str
    english_name: str
    native_name: str
    flag: str
    rtl: bool


class AvailableFormatsWithLocalesResponse(BaseModel):
    """Response with formats, themes, and supported locales."""

    formats: list[str]
    themes: list[str]
    locales: list[LocaleInfo]


@router.get(
    "/formats",
    response_model=AvailableFormatsWithLocalesResponse,
    summary="Get available report formats, themes, and locales",
    description="List all available report formats, themes, and supported languages",
)
async def list_formats() -> AvailableFormatsWithLocalesResponse:
    """Get list of available report formats, themes, and locales.

    Returns:
        Available formats, themes, and supported locales.
    """
    formats = get_available_formats()
    themes = [t.value for t in ReportTheme]
    locales_raw = get_report_locales()

    locales = [
        LocaleInfo(
            code=loc["code"],
            english_name=loc["english_name"],
            native_name=loc["native_name"],
            flag=loc["flag"],
            rtl=loc["rtl"],
        )
        for loc in locales_raw
    ]

    return AvailableFormatsWithLocalesResponse(
        formats=formats,
        themes=themes,
        locales=locales,
    )


@router.get(
    "/locales",
    response_model=list[LocaleInfo],
    summary="Get supported report languages",
    description="List all supported languages for report generation",
)
async def list_locales() -> list[LocaleInfo]:
    """Get list of supported locales for report generation.

    Supports 15 languages as per truthound documentation:
    en, ko, ja, zh, de, fr, es, pt, it, ru, ar, th, vi, id, tr

    Returns:
        List of locale information.
    """
    locales_raw = get_report_locales()
    return [
        LocaleInfo(
            code=loc["code"],
            english_name=loc["english_name"],
            native_name=loc["native_name"],
            flag=loc["flag"],
            rtl=loc["rtl"],
        )
        for loc in locales_raw
    ]


@router.post(
    "/validations/{validation_id}/report",
    response_model=ReportResponse,
    summary="Generate validation report metadata",
    description="Generate a report and return metadata (use download endpoint for content)",
)
async def generate_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    request: ReportGenerateRequest,
) -> ReportResponse:
    """Generate a validation report.

    This endpoint returns report metadata. Use the download endpoint
    to get the actual report content.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        request: Report generation options (including locale).

    Returns:
        Report metadata and download information.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format or locale is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Get locale from request (default to English)
    locale = getattr(request, "locale", "en") or "en"

    try:
        # Generate report
        result = await generate_report(
            validation,
            format=request.format,
            theme=request.theme,
            locale=locale,
            title=request.title,
            include_samples=request.include_samples,
            include_statistics=request.include_statistics,
            custom_metadata=request.custom_metadata,
        )

        return ReportResponse(
            filename=result.filename,
            content_type=result.content_type,
            size_bytes=result.size_bytes,
            generation_time_ms=result.generation_time_ms,
            metadata=ReportMetadataResponse(
                title=result.metadata.title,
                generated_at=result.metadata.generated_at,
                source_name=result.metadata.source_name,
                source_id=result.metadata.source_id,
                validation_id=result.metadata.validation_id,
                theme=result.metadata.theme.value,
                format=result.metadata.format.value,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/validations/{validation_id}/download",
    summary="Download validation report",
    description="Generate and download a validation report as a file with language support",
    responses={
        200: {
            "description": "Report file",
            "content": {
                "text/html": {},
                "text/csv": {},
                "application/json": {},
                "text/markdown": {},
                "application/pdf": {},
            },
        },
        404: {"description": "Validation not found"},
        400: {"description": "Invalid format or locale"},
    },
)
async def download_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    format: Annotated[str, Query(description="Report format")] = "html",
    theme: Annotated[str, Query(description="Visual theme")] = "professional",
    locale: Annotated[
        str, Query(description="Report language (en, ko, ja, zh, de, fr, es, pt, it, ru, ar, th, vi, id, tr)")
    ] = "en",
    include_samples: Annotated[
        bool, Query(description="Include sample values")
    ] = True,
    include_statistics: Annotated[
        bool, Query(description="Include statistics")
    ] = True,
) -> Response:
    """Download a validation report.

    Generates and returns the report as a downloadable file.
    Supports 15 languages for internationalization.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        format: Report format (html, csv, json, markdown).
        theme: Visual theme for the report.
        locale: Report language code.
        include_samples: Include sample problematic values.
        include_statistics: Include data statistics.

    Returns:
        Report file as download response.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format or locale is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    try:
        # Generate report with locale
        result = await generate_report(
            validation,
            format=format,
            theme=theme,
            locale=locale,
            include_samples=include_samples,
            include_statistics=include_statistics,
        )

        # Return as file download
        content = result.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        return Response(
            content=content,
            media_type=result.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{result.filename}"',
                "Content-Length": str(result.size_bytes),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/validations/{validation_id}/preview",
    summary="Preview validation report",
    description="Generate and return report for inline viewing with language support",
    responses={
        200: {
            "description": "Report content for preview",
            "content": {
                "text/html": {},
                "text/csv": {},
                "application/json": {},
                "text/markdown": {},
            },
        },
        404: {"description": "Validation not found"},
        400: {"description": "Invalid format or locale"},
    },
)
async def preview_validation_report(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
    format: Annotated[str, Query(description="Report format")] = "html",
    theme: Annotated[str, Query(description="Visual theme")] = "professional",
    locale: Annotated[
        str, Query(description="Report language (en, ko, ja, zh, etc.)")
    ] = "en",
) -> Response:
    """Preview a validation report inline.

    Similar to download but without Content-Disposition header,
    allowing browser to render the content inline.
    Supports 15 languages for internationalization.

    Args:
        service: Injected validation service.
        validation_id: Validation to generate report for.
        format: Report format (html, csv, json, markdown).
        theme: Visual theme for the report.
        locale: Report language code.

    Returns:
        Report content for inline viewing.

    Raises:
        HTTPException: 404 if validation not found.
        HTTPException: 400 if format or locale is not supported.
    """
    # Get validation
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    try:
        # Generate report with locale
        result = await generate_report(
            validation,
            format=format,
            theme=theme,
            locale=locale,
            include_samples=True,
            include_statistics=True,
        )

        # Return for inline viewing
        content = result.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        return Response(
            content=content,
            media_type=result.content_type,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Report History Endpoints
# =============================================================================


@router.get(
    "/history",
    response_model=GeneratedReportListResponse,
    summary="List generated reports",
    description="Get paginated list of generated reports with filtering",
)
async def list_report_history(
    service: ReportHistoryServiceDep,
    source_id: Annotated[str | None, Query(description="Filter by source ID")] = None,
    validation_id: Annotated[str | None, Query(description="Filter by validation ID")] = None,
    reporter_id: Annotated[str | None, Query(description="Filter by reporter ID")] = None,
    format: Annotated[str | None, Query(description="Filter by format")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    include_expired: Annotated[bool, Query(description="Include expired reports")] = False,
    search: Annotated[str | None, Query(description="Search by name")] = None,
    sort_by: Annotated[str, Query(description="Sort field")] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Sort order")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> GeneratedReportListResponse:
    """List generated reports with filtering and pagination.

    Args:
        service: Report history service.
        source_id: Filter by source ID.
        validation_id: Filter by validation ID.
        reporter_id: Filter by reporter ID.
        format: Filter by format (html, pdf, csv, json, markdown, junit, excel).
        status: Filter by status (pending, generating, completed, failed, expired).
        include_expired: Include expired reports (default: false).
        search: Search by report name.
        sort_by: Field to sort by.
        sort_order: Sort direction (asc/desc).
        page: Page number.
        page_size: Items per page.

    Returns:
        Paginated list of generated reports.
    """
    reports, total = await service.list_reports(
        source_id=source_id,
        validation_id=validation_id,
        reporter_id=reporter_id,
        format=format,
        status=status,
        include_expired=include_expired,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    items = []
    for report in reports:
        response = GeneratedReportResponse.from_model(report)
        response.download_url = f"/api/v1/reports/history/{report.id}/download"
        items.append(response)

    return GeneratedReportListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/history/statistics",
    response_model=ReportStatistics,
    summary="Get report statistics",
    description="Get statistics about generated reports",
)
async def get_report_statistics(
    service: ReportHistoryServiceDep,
) -> ReportStatistics:
    """Get statistics about generated reports.

    Args:
        service: Report history service.

    Returns:
        Report statistics.
    """
    stats = await service.get_statistics()
    return ReportStatistics(**stats)


@router.get(
    "/history/{report_id}",
    response_model=GeneratedReportResponse,
    summary="Get report details",
    description="Get details of a specific generated report",
)
async def get_report_history(
    service: ReportHistoryServiceDep,
    report_id: Annotated[str, Path(description="Report ID")],
) -> GeneratedReportResponse:
    """Get details of a specific generated report.

    Args:
        service: Report history service.
        report_id: Report ID.

    Returns:
        Report details.

    Raises:
        HTTPException: 404 if report not found.
    """
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    response = GeneratedReportResponse.from_model(report)
    response.download_url = f"/api/v1/reports/history/{report.id}/download"
    return response


@router.post(
    "/history",
    response_model=GeneratedReportResponse,
    status_code=201,
    summary="Create report record",
    description="Create a new report record (without generating content)",
)
async def create_report_record(
    service: ReportHistoryServiceDep,
    request: GeneratedReportCreate,
) -> GeneratedReportResponse:
    """Create a new report record.

    This creates a record in pending state. Use the generate endpoint
    to actually generate the report content.

    Args:
        service: Report history service.
        request: Report creation data.

    Returns:
        Created report record.
    """
    report = await service.create_report(
        name=request.name,
        format=request.format,
        validation_id=request.validation_id,
        source_id=request.source_id,
        reporter_id=request.reporter_id,
        description=request.description,
        theme=request.theme,
        locale=request.locale,
        config=request.config,
        metadata=request.metadata,
        expires_in_days=request.expires_in_days,
    )

    response = GeneratedReportResponse.from_model(report)
    response.download_url = f"/api/v1/reports/history/{report.id}/download"
    return response


@router.patch(
    "/history/{report_id}",
    response_model=GeneratedReportResponse,
    summary="Update report record",
    description="Update a report record's metadata",
)
async def update_report_record(
    service: ReportHistoryServiceDep,
    report_id: Annotated[str, Path(description="Report ID")],
    request: GeneratedReportUpdate,
) -> GeneratedReportResponse:
    """Update a report record.

    Only name, description, and metadata can be updated.

    Args:
        service: Report history service.
        report_id: Report ID.
        request: Update data.

    Returns:
        Updated report record.

    Raises:
        HTTPException: 404 if report not found.
    """
    report = await service.update_report(
        report_id=report_id,
        name=request.name,
        description=request.description,
        metadata=request.metadata,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    response = GeneratedReportResponse.from_model(report)
    response.download_url = f"/api/v1/reports/history/{report.id}/download"
    return response


@router.delete(
    "/history/{report_id}",
    status_code=204,
    summary="Delete report record",
    description="Delete a report record and its file",
)
async def delete_report_record(
    service: ReportHistoryServiceDep,
    report_id: Annotated[str, Path(description="Report ID")],
) -> None:
    """Delete a report record and its file.

    Args:
        service: Report history service.
        report_id: Report ID.

    Raises:
        HTTPException: 404 if report not found.
    """
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")


@router.get(
    "/history/{report_id}/download",
    summary="Download saved report",
    description="Download a previously generated and saved report",
    responses={
        200: {
            "description": "Report file",
            "content": {
                "text/html": {},
                "text/csv": {},
                "application/json": {},
                "text/markdown": {},
                "application/pdf": {},
            },
        },
        404: {"description": "Report not found or file missing"},
    },
)
async def download_saved_report(
    service: ReportHistoryServiceDep,
    report_id: Annotated[str, Path(description="Report ID")],
) -> Response:
    """Download a previously generated report.

    Args:
        service: Report history service.
        report_id: Report ID.

    Returns:
        Report file as download.

    Raises:
        HTTPException: 404 if report or file not found.
    """
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Report is not ready (status: {report.status})",
        )

    content, content_type = await service.get_report_content(report_id)
    if not content:
        raise HTTPException(status_code=404, detail="Report file not found")

    # Record download
    await service.record_download(report_id)

    # Build filename
    ext_map = {
        "html": ".html",
        "pdf": ".pdf",
        "csv": ".csv",
        "json": ".json",
        "markdown": ".md",
        "junit": ".xml",
        "excel": ".xlsx",
    }
    fmt = report.format.value if hasattr(report.format, "value") else report.format
    ext = ext_map.get(fmt, ".html")
    filename = f"{report.name}{ext}"

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


@router.post(
    "/history/{report_id}/generate",
    response_model=GeneratedReportResponse,
    summary="Generate report content",
    description="Generate content for an existing report record",
)
async def generate_report_content(
    service: ReportHistoryServiceDep,
    validation_service: ValidationServiceDep,
    report_id: Annotated[str, Path(description="Report ID")],
) -> GeneratedReportResponse:
    """Generate content for an existing report record.

    Args:
        service: Report history service.
        validation_service: Validation service.
        report_id: Report ID.

    Returns:
        Updated report with generation status.

    Raises:
        HTTPException: 404 if report not found.
        HTTPException: 400 if report cannot be generated.
    """
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status == ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report already generated")

    if not report.validation_id:
        raise HTTPException(
            status_code=400,
            detail="Report has no associated validation",
        )

    # Get validation
    validation = await validation_service.get_validation(report.validation_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Associated validation not found")

    # Mark as generating
    await service.mark_generating(report_id)

    try:
        # Generate report
        start_time = time.time()
        fmt = report.format.value if hasattr(report.format, "value") else report.format
        result = await generate_report(
            validation,
            format=fmt,
            theme=report.theme or "professional",
            locale=report.locale,
        )
        generation_time_ms = (time.time() - start_time) * 1000

        # Store content
        content = result.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        report = await service.mark_completed(report_id, content, generation_time_ms)

    except Exception as e:
        await service.mark_failed(report_id, str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    response = GeneratedReportResponse.from_model(report)
    response.download_url = f"/api/v1/reports/history/{report.id}/download"
    return response


@router.post(
    "/history/cleanup",
    summary="Cleanup expired reports",
    description="Delete all expired reports and their files",
)
async def cleanup_expired_reports(
    service: ReportHistoryServiceDep,
) -> dict[str, int]:
    """Delete all expired reports.

    Args:
        service: Report history service.

    Returns:
        Number of reports deleted.
    """
    count = await service.cleanup_expired()
    return {"deleted": count}


@router.post(
    "/bulk",
    response_model=BulkReportGenerateResponse,
    summary="Generate reports in bulk",
    description="Generate reports for multiple validations at once",
)
async def generate_bulk_reports(
    service: ReportHistoryServiceDep,
    validation_service: ValidationServiceDep,
    request: BulkReportGenerateRequest,
) -> BulkReportGenerateResponse:
    """Generate reports for multiple validations.

    Args:
        service: Report history service.
        validation_service: Validation service.
        request: Bulk generation request.

    Returns:
        Bulk generation results.
    """
    reports = []
    errors = []
    successful = 0
    failed = 0

    for validation_id in request.validation_ids:
        try:
            # Get validation
            validation = await validation_service.get_validation(validation_id)
            if not validation:
                errors.append({
                    "validation_id": validation_id,
                    "error": "Validation not found",
                })
                failed += 1
                continue

            # Create report record
            report = await service.create_report(
                name=f"Validation Report - {validation_id[:8]}",
                format=request.format,
                validation_id=validation_id,
                source_id=str(validation.source_id),
                reporter_id=request.reporter_id,
                theme=request.theme,
                locale=request.locale,
                config=request.config,
                expires_in_days=request.expires_in_days,
            )

            if request.save_to_history:
                # Mark as generating
                await service.mark_generating(str(report.id))

                # Generate report
                start_time = time.time()
                result = await generate_report(
                    validation,
                    format=request.format,
                    theme=request.theme,
                    locale=request.locale,
                )
                generation_time_ms = (time.time() - start_time) * 1000

                # Store content
                content = result.content
                if isinstance(content, str):
                    content = content.encode("utf-8")

                report = await service.mark_completed(str(report.id), content, generation_time_ms)

            response = GeneratedReportResponse.from_model(report)
            response.download_url = f"/api/v1/reports/history/{report.id}/download"
            reports.append(response)
            successful += 1

        except Exception as e:
            errors.append({
                "validation_id": validation_id,
                "error": str(e),
            })
            failed += 1

    return BulkReportGenerateResponse(
        total=len(request.validation_ids),
        successful=successful,
        failed=failed,
        reports=reports,
        errors=errors,
    )
