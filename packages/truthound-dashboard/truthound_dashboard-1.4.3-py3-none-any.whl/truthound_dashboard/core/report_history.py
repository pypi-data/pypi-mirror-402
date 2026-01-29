"""Report History Service.

This module provides services for managing generated report history,
including CRUD operations, statistics, and cleanup.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db.models import (
    CustomReporter,
    GeneratedReport,
    ReportFormatType,
    ReportStatus,
    Source,
    Validation,
)


class ReportHistoryService:
    """Service for managing generated report history.

    Provides CRUD operations for report history records,
    statistics aggregation, and cleanup functionality.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Async database session.
        """
        self.session = session
        self._reports_dir = Path("data/reports")

    async def list_reports(
        self,
        source_id: str | None = None,
        validation_id: str | None = None,
        reporter_id: str | None = None,
        format: str | None = None,
        status: str | None = None,
        include_expired: bool = False,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedReport], int]:
        """List generated reports with filtering and pagination.

        Args:
            source_id: Filter by source ID.
            validation_id: Filter by validation ID.
            reporter_id: Filter by reporter ID.
            format: Filter by format.
            status: Filter by status.
            include_expired: Include expired reports.
            search: Search by name.
            sort_by: Field to sort by.
            sort_order: Sort direction.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            Tuple of (reports list, total count).
        """
        # Build base query with relationships
        query = select(GeneratedReport).options(
            selectinload(GeneratedReport.source),
            selectinload(GeneratedReport.validation),
            selectinload(GeneratedReport.reporter),
        )

        # Apply filters
        conditions = []

        if source_id:
            conditions.append(GeneratedReport.source_id == source_id)

        if validation_id:
            conditions.append(GeneratedReport.validation_id == validation_id)

        if reporter_id:
            conditions.append(GeneratedReport.reporter_id == reporter_id)

        if format:
            try:
                format_enum = ReportFormatType(format.lower())
                conditions.append(GeneratedReport.format == format_enum)
            except ValueError:
                pass

        if status:
            try:
                status_enum = ReportStatus(status.lower())
                conditions.append(GeneratedReport.status == status_enum)
            except ValueError:
                pass

        if not include_expired:
            conditions.append(
                or_(
                    GeneratedReport.expires_at.is_(None),
                    GeneratedReport.expires_at > datetime.utcnow(),
                )
            )

        if search:
            conditions.append(GeneratedReport.name.ilike(f"%{search}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total = await self.session.scalar(count_query) or 0

        # Apply sorting
        sort_column = getattr(GeneratedReport, sort_by, GeneratedReport.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        reports = list(result.scalars().all())

        return reports, total

    async def get_report(self, report_id: str) -> GeneratedReport | None:
        """Get a single report by ID.

        Args:
            report_id: Report ID.

        Returns:
            GeneratedReport or None if not found.
        """
        query = (
            select(GeneratedReport)
            .options(
                selectinload(GeneratedReport.source),
                selectinload(GeneratedReport.validation),
                selectinload(GeneratedReport.reporter),
            )
            .where(GeneratedReport.id == report_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_report(
        self,
        name: str,
        format: str,
        validation_id: str | None = None,
        source_id: str | None = None,
        reporter_id: str | None = None,
        description: str | None = None,
        theme: str | None = None,
        locale: str = "en",
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        expires_in_days: int | None = 30,
    ) -> GeneratedReport:
        """Create a new report record.

        Args:
            name: Report name.
            format: Report format.
            validation_id: Associated validation ID.
            source_id: Associated source ID.
            reporter_id: Custom reporter ID.
            description: Report description.
            theme: Visual theme.
            locale: Language locale.
            config: Generation config.
            metadata: Additional metadata.
            expires_in_days: Days until expiration.

        Returns:
            Created GeneratedReport.
        """
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Parse format
        try:
            format_enum = ReportFormatType(format.lower())
        except ValueError:
            format_enum = ReportFormatType.HTML

        report = GeneratedReport(
            name=name,
            description=description,
            format=format_enum,
            theme=theme,
            locale=locale,
            status=ReportStatus.PENDING,
            config=config,
            metadata=metadata,
            validation_id=validation_id,
            source_id=source_id,
            reporter_id=reporter_id,
            expires_at=expires_at,
        )

        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        return report

    async def update_report(
        self,
        report_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GeneratedReport | None:
        """Update a report record.

        Args:
            report_id: Report ID.
            name: New name.
            description: New description.
            metadata: New metadata.

        Returns:
            Updated GeneratedReport or None if not found.
        """
        report = await self.get_report(report_id)
        if not report:
            return None

        if name is not None:
            report.name = name
        if description is not None:
            report.description = description
        if metadata is not None:
            report.metadata = metadata

        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def delete_report(self, report_id: str) -> bool:
        """Delete a report record and its file.

        Args:
            report_id: Report ID.

        Returns:
            True if deleted, False if not found.
        """
        report = await self.get_report(report_id)
        if not report:
            return False

        # Delete file if exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError:
                pass

        await self.session.delete(report)
        await self.session.commit()
        return True

    async def mark_generating(self, report_id: str) -> GeneratedReport | None:
        """Mark report as generating.

        Args:
            report_id: Report ID.

        Returns:
            Updated report or None.
        """
        report = await self.get_report(report_id)
        if not report:
            return None

        report.status = ReportStatus.GENERATING
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def mark_completed(
        self,
        report_id: str,
        content: bytes | str,
        generation_time_ms: float,
    ) -> GeneratedReport | None:
        """Mark report as completed and store content.

        Args:
            report_id: Report ID.
            content: Report content.
            generation_time_ms: Generation time in milliseconds.

        Returns:
            Updated report or None.
        """
        report = await self.get_report(report_id)
        if not report:
            return None

        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Calculate hash
        content_hash = hashlib.sha256(content).hexdigest()

        # Store file
        self._reports_dir.mkdir(parents=True, exist_ok=True)

        # Determine extension
        ext_map = {
            ReportFormatType.HTML: ".html",
            ReportFormatType.PDF: ".pdf",
            ReportFormatType.CSV: ".csv",
            ReportFormatType.JSON: ".json",
            ReportFormatType.MARKDOWN: ".md",
            ReportFormatType.JUNIT: ".xml",
            ReportFormatType.EXCEL: ".xlsx",
            ReportFormatType.CUSTOM: ".txt",
        }
        ext = ext_map.get(report.format, ".html")
        file_name = f"{report.id}{ext}"
        file_path = self._reports_dir / file_name

        with open(file_path, "wb") as f:
            f.write(content)

        # Update report
        report.mark_completed(
            file_path=str(file_path),
            file_size=len(content),
            generation_time_ms=generation_time_ms,
        )
        report.content_hash = content_hash

        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def mark_failed(
        self,
        report_id: str,
        error_message: str,
    ) -> GeneratedReport | None:
        """Mark report as failed.

        Args:
            report_id: Report ID.
            error_message: Error message.

        Returns:
            Updated report or None.
        """
        report = await self.get_report(report_id)
        if not report:
            return None

        report.mark_failed(error_message)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def record_download(self, report_id: str) -> GeneratedReport | None:
        """Record a download event.

        Args:
            report_id: Report ID.

        Returns:
            Updated report or None.
        """
        report = await self.get_report(report_id)
        if not report:
            return None

        report.increment_download()
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_report_content(self, report_id: str) -> tuple[bytes | None, str | None]:
        """Get report file content.

        Args:
            report_id: Report ID.

        Returns:
            Tuple of (content, content_type) or (None, None) if not found.
        """
        report = await self.get_report(report_id)
        if not report or not report.file_path:
            return None, None

        if not os.path.exists(report.file_path):
            return None, None

        content_type_map = {
            ReportFormatType.HTML: "text/html",
            ReportFormatType.PDF: "application/pdf",
            ReportFormatType.CSV: "text/csv",
            ReportFormatType.JSON: "application/json",
            ReportFormatType.MARKDOWN: "text/markdown",
            ReportFormatType.JUNIT: "application/xml",
            ReportFormatType.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ReportFormatType.CUSTOM: "text/plain",
        }

        with open(report.file_path, "rb") as f:
            content = f.read()

        content_type = content_type_map.get(report.format, "application/octet-stream")
        return content, content_type

    async def get_statistics(self) -> dict[str, Any]:
        """Get report statistics.

        Returns:
            Statistics dictionary.
        """
        # Total reports
        total_query = select(func.count(GeneratedReport.id))
        total = await self.session.scalar(total_query) or 0

        # Total size
        size_query = select(func.coalesce(func.sum(GeneratedReport.file_size), 0))
        total_size = await self.session.scalar(size_query) or 0

        # Reports by format
        format_query = select(
            GeneratedReport.format,
            func.count(GeneratedReport.id),
        ).group_by(GeneratedReport.format)
        format_result = await self.session.execute(format_query)
        by_format = {
            row[0].value if hasattr(row[0], "value") else row[0]: row[1]
            for row in format_result
        }

        # Reports by status
        status_query = select(
            GeneratedReport.status,
            func.count(GeneratedReport.id),
        ).group_by(GeneratedReport.status)
        status_result = await self.session.execute(status_query)
        by_status = {
            row[0].value if hasattr(row[0], "value") else row[0]: row[1]
            for row in status_result
        }

        # Total downloads
        downloads_query = select(
            func.coalesce(func.sum(GeneratedReport.downloaded_count), 0)
        )
        total_downloads = await self.session.scalar(downloads_query) or 0

        # Average generation time
        avg_time_query = select(
            func.avg(GeneratedReport.generation_time_ms)
        ).where(GeneratedReport.generation_time_ms.isnot(None))
        avg_time = await self.session.scalar(avg_time_query)

        # Expired count
        expired_query = select(func.count(GeneratedReport.id)).where(
            and_(
                GeneratedReport.expires_at.isnot(None),
                GeneratedReport.expires_at < datetime.utcnow(),
            )
        )
        expired_count = await self.session.scalar(expired_query) or 0

        # Unique reporters used
        reporters_query = select(
            func.count(func.distinct(GeneratedReport.reporter_id))
        ).where(GeneratedReport.reporter_id.isnot(None))
        reporters_used = await self.session.scalar(reporters_query) or 0

        return {
            "total_reports": total,
            "total_size_bytes": int(total_size),
            "reports_by_format": by_format,
            "reports_by_status": by_status,
            "total_downloads": int(total_downloads),
            "avg_generation_time_ms": float(avg_time) if avg_time else None,
            "expired_count": expired_count,
            "reporters_used": reporters_used,
        }

    async def cleanup_expired(self) -> int:
        """Delete expired reports.

        Returns:
            Number of reports deleted.
        """
        # Find expired reports
        query = select(GeneratedReport).where(
            and_(
                GeneratedReport.expires_at.isnot(None),
                GeneratedReport.expires_at < datetime.utcnow(),
            )
        )
        result = await self.session.execute(query)
        expired = list(result.scalars().all())

        count = 0
        for report in expired:
            # Delete file
            if report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                except OSError:
                    pass

            await self.session.delete(report)
            count += 1

        await self.session.commit()
        return count

    async def find_by_hash(self, content_hash: str) -> GeneratedReport | None:
        """Find report by content hash for deduplication.

        Args:
            content_hash: Content hash.

        Returns:
            Existing report with same hash or None.
        """
        query = (
            select(GeneratedReport)
            .where(
                and_(
                    GeneratedReport.content_hash == content_hash,
                    GeneratedReport.status == ReportStatus.COMPLETED,
                    or_(
                        GeneratedReport.expires_at.is_(None),
                        GeneratedReport.expires_at > datetime.utcnow(),
                    ),
                )
            )
            .order_by(desc(GeneratedReport.created_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
