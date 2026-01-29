"""Business logic services.

This module contains service classes that implement business logic
for the dashboard, separating concerns from API handlers.

Services handle:
- Data source management
- Schema learning and storage
- Validation execution and tracking
- Data profiling with history
- Drift detection
- Schedule management
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import (
    BaseRepository,
    DataMask,
    DriftComparison,
    PIIScan,
    Profile,
    Rule,
    Schedule,
    Schema,
    Source,
    Validation,
)

from .truthound_adapter import (
    CheckResult,
    MaskResult,
    ScanResult,
    get_adapter,
)


class SourceRepository(BaseRepository[Source]):
    """Repository for Source model operations."""

    model = Source

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Source]:
        """Get active sources only.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of active sources.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[Source.is_active],
        )

    async def get_by_name(self, name: str) -> Source | None:
        """Get source by name.

        Args:
            name: Source name to find.

        Returns:
            Source or None if not found.
        """
        result = await self.session.execute(select(Source).where(Source.name == name))
        return result.scalar_one_or_none()


class SchemaRepository(BaseRepository[Schema]):
    """Repository for Schema model operations."""

    model = Schema

    async def get_active_for_source(self, source_id: str) -> Schema | None:
        """Get active schema for a source.

        Args:
            source_id: Source ID.

        Returns:
            Active schema or None.
        """
        result = await self.session.execute(
            select(Schema)
            .where(Schema.source_id == source_id)
            .where(Schema.is_active)
            .order_by(Schema.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_for_source(self, source_id: str) -> None:
        """Deactivate all schemas for a source.

        Args:
            source_id: Source ID.
        """
        result = await self.session.execute(
            select(Schema).where(Schema.source_id == source_id).where(Schema.is_active)
        )
        schemas = result.scalars().all()
        for schema in schemas:
            schema.is_active = False


class RuleRepository(BaseRepository[Rule]):
    """Repository for Rule model operations."""

    model = Rule

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        active_only: bool = False,
    ) -> Sequence[Rule]:
        """Get rules for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            active_only: Only return active rules.

        Returns:
            Sequence of rules.
        """
        filters = [Rule.source_id == source_id]
        if active_only:
            filters.append(Rule.is_active)

        return await self.list(
            limit=limit,
            filters=filters,
            order_by=Rule.created_at.desc(),
        )

    async def get_active_for_source(self, source_id: str) -> Rule | None:
        """Get most recent active rule for a source.

        Args:
            source_id: Source ID.

        Returns:
            Active rule or None.
        """
        result = await self.session.execute(
            select(Rule)
            .where(Rule.source_id == source_id)
            .where(Rule.is_active)
            .order_by(Rule.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_for_source(self, source_id: str) -> int:
        """Deactivate all rules for a source.

        Args:
            source_id: Source ID.

        Returns:
            Number of rules deactivated.
        """
        result = await self.session.execute(
            select(Rule).where(Rule.source_id == source_id).where(Rule.is_active)
        )
        rules = result.scalars().all()
        for rule in rules:
            rule.is_active = False
        return len(rules)


class ValidationRepository(BaseRepository[Validation]):
    """Repository for Validation model operations."""

    model = Validation

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Validation]:
        """Get validations for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of validations.
        """
        return await self.list(
            limit=limit,
            filters=[Validation.source_id == source_id],
            order_by=Validation.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> Validation | None:
        """Get most recent validation for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest validation or None.
        """
        result = await self.session.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .order_by(Validation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class SourceService:
    """Service for managing data sources.

    Handles source CRUD operations and related business logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.repository = SourceRepository(session)
        self.schema_repo = SchemaRepository(session)
        self.validation_repo = ValidationRepository(session)

    async def get_by_id(self, id: str) -> Source | None:
        """Get source by ID."""
        return await self.repository.get_by_id(id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> Sequence[Source]:
        """List sources.

        Args:
            offset: Number to skip.
            limit: Maximum to return.
            active_only: Only return active sources.

        Returns:
            Sequence of sources.
        """
        if active_only:
            return await self.repository.get_active(offset=offset, limit=limit)
        return await self.repository.list(offset=offset, limit=limit)

    async def create(
        self,
        *,
        name: str,
        type: str,
        config: dict[str, Any],
        description: str | None = None,
    ) -> Source:
        """Create new source.

        Args:
            name: Source name.
            type: Source type (file, postgresql, etc.).
            config: Source configuration.
            description: Optional description.

        Returns:
            Created source.
        """
        return await self.repository.create(
            name=name,
            type=type,
            config=config,
            description=description,
        )

    async def update(
        self,
        id: str,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Source | None:
        """Update source.

        Args:
            id: Source ID.
            name: New name.
            config: New config.
            description: New description.
            is_active: New active status.

        Returns:
            Updated source or None.
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if config is not None:
            update_data["config"] = config
        if description is not None:
            update_data["description"] = description
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            return await self.repository.get_by_id(id)

        return await self.repository.update(id, **update_data)

    async def delete(self, id: str) -> bool:
        """Delete source and related data.

        Args:
            id: Source ID.

        Returns:
            True if deleted.
        """
        return await self.repository.delete(id)

    async def get_schema(self, source_id: str) -> Schema | None:
        """Get active schema for source.

        Args:
            source_id: Source ID.

        Returns:
            Active schema or None.
        """
        return await self.schema_repo.get_active_for_source(source_id)

    async def get_validations(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Validation]:
        """Get validations for source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of validations.
        """
        return await self.validation_repo.get_for_source(source_id, limit=limit)


class ValidationService:
    """Service for running and managing validations.

    Handles validation execution, result storage, and history.
    Supports both built-in truthound validators and custom validators.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.schema_repo = SchemaRepository(session)
        self.validation_repo = ValidationRepository(session)
        self.adapter = get_adapter()

    async def run_validation(
        self,
        source_id: str,
        *,
        validators: list[str] | None = None,
        validator_params: dict[str, dict[str, Any]] | None = None,
        custom_validators: list[dict[str, Any]] | None = None,
        schema_path: str | None = None,
        auto_schema: bool = False,
        columns: list[str] | None = None,
        min_severity: str | None = None,
        strict: bool = False,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
    ) -> Validation:
        """Run validation on a source.

        This method provides full access to truthound's th.check() parameters,
        allowing fine-grained control over validation behavior. It also supports
        running custom validators alongside built-in validators.

        Args:
            source_id: Source ID to validate.
            validators: Optional validator list. If None, all validators run.
            validator_params: Optional per-validator parameters.
                Format: {"ValidatorName": {"param1": value1, "param2": value2}}
                Example: {"Null": {"columns": ["email"], "mostly": 0.95},
                          "CompletenessRatio": {"column": "phone", "min_ratio": 0.98}}
            custom_validators: Optional list of custom validator configs.
                Format: [{"validator_id": "...", "column": "...", "params": {...}}]
            schema_path: Optional schema file path.
            auto_schema: Auto-learn schema if True.
            columns: Columns to validate. If None, validates all columns.
            min_severity: Minimum severity to report ("low", "medium", "high", "critical").
            strict: If True, raises exception on validation failures.
            parallel: If True, uses DAG-based parallel execution.
            max_workers: Max threads for parallel execution (requires parallel=True).
            pushdown: Enable query pushdown for SQL sources. None uses auto-detection.

        Returns:
            Validation record with results.

        Raises:
            ValueError: If source not found.
        """
        # Get source
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Create validation record
        validation = await self.validation_repo.create(
            source_id=source_id,
            status="running",
            started_at=datetime.utcnow(),
        )

        try:
            # Run built-in validation with all supported parameters
            result = await self.adapter.check(
                source.source_path or "",
                validators=validators,
                validator_params=validator_params,
                schema=schema_path,
                auto_schema=auto_schema,
                columns=columns,
                min_severity=min_severity,
                strict=strict,
                parallel=parallel,
                max_workers=max_workers,
                pushdown=pushdown,
            )

            # Run custom validators if specified
            custom_results = []
            if custom_validators:
                custom_results = await self._run_custom_validators(
                    source=source,
                    custom_validators=custom_validators,
                    validation_id=str(validation.id),
                )

            # Update validation with combined results
            await self._update_validation_success(
                validation, result, custom_results=custom_results
            )

            # Update source last validated
            source.last_validated_at = datetime.utcnow()

        except Exception as e:
            # Update validation with error
            validation.mark_error(str(e))

        await self.session.flush()
        await self.session.refresh(validation)
        return validation

    async def _run_custom_validators(
        self,
        source: Source,
        custom_validators: list[dict[str, Any]],
        validation_id: str,
    ) -> list[dict[str, Any]]:
        """Run custom validators on source data.

        Args:
            source: Data source to validate.
            custom_validators: List of custom validator configs.
            validation_id: Parent validation ID.

        Returns:
            List of custom validator results.
        """
        from truthound_dashboard.core.plugins import CustomValidatorExecutor
        from truthound_dashboard.core.plugins.registry import plugin_registry
        from truthound_dashboard.core.plugins.validator_executor import ValidatorContext

        results = []
        executor = CustomValidatorExecutor()

        # Load source data once
        try:
            import polars as pl

            source_path = source.source_path or ""
            if source.type == "csv":
                df = pl.read_csv(source_path)
            elif source.type == "parquet":
                df = pl.read_parquet(source_path)
            elif source.type == "json":
                df = pl.read_json(source_path)
            else:
                # Unsupported source type for custom validators
                return results
        except Exception:
            return results

        for cv_config in custom_validators:
            validator_id = cv_config.get("validator_id")
            column_name = cv_config.get("column")
            params = cv_config.get("params", {})

            if not validator_id or not column_name:
                continue

            # Get the custom validator
            validator = await plugin_registry.get_validator(
                self.session, validator_id=validator_id
            )
            if not validator or not validator.is_enabled:
                continue

            # Check column exists
            if column_name not in df.columns:
                results.append({
                    "validator_id": validator_id,
                    "validator_name": validator.name,
                    "column": column_name,
                    "passed": False,
                    "error": f"Column '{column_name}' not found",
                })
                continue

            # Create context
            column_values = df[column_name].to_list()
            context = ValidatorContext(
                column_name=column_name,
                column_values=column_values,
                parameters=params,
                schema={"dtype": str(df[column_name].dtype)},
                row_count=len(column_values),
            )

            # Execute
            try:
                result = await executor.execute(
                    validator=validator,
                    context=context,
                    session=self.session,
                    source_id=str(source.id),
                )
                results.append({
                    "validator_id": validator_id,
                    "validator_name": validator.name,
                    "column": column_name,
                    "passed": result.passed,
                    "issues": result.issues,
                    "message": result.message,
                    "execution_time_ms": result.execution_time_ms,
                })
            except Exception as e:
                results.append({
                    "validator_id": validator_id,
                    "validator_name": validator.name,
                    "column": column_name,
                    "passed": False,
                    "error": str(e),
                })

        return results

    async def _update_validation_success(
        self,
        validation: Validation,
        result: CheckResult,
        custom_results: list[dict[str, Any]] | None = None,
    ) -> None:
        """Update validation with successful result.

        Args:
            validation: Validation record to update.
            result: Check result from built-in validators.
            custom_results: Optional results from custom validators.
        """
        # Calculate combined pass/fail status
        builtin_passed = result.passed
        custom_passed = True
        custom_issues_count = 0

        if custom_results:
            for cr in custom_results:
                if not cr.get("passed", True):
                    custom_passed = False
                custom_issues_count += len(cr.get("issues", []))

        combined_passed = builtin_passed and custom_passed

        validation.status = "success" if combined_passed else "failed"
        validation.passed = combined_passed
        validation.has_critical = result.has_critical
        validation.has_high = result.has_high
        validation.total_issues = result.total_issues + custom_issues_count
        validation.critical_issues = result.critical_issues
        validation.high_issues = result.high_issues
        validation.medium_issues = result.medium_issues
        validation.low_issues = result.low_issues
        validation.row_count = result.row_count
        validation.column_count = result.column_count

        # Combine results
        combined_result = result.to_dict()
        if custom_results:
            combined_result["custom_validators"] = custom_results
            combined_result["custom_validators_passed"] = custom_passed
            combined_result["custom_issues_count"] = custom_issues_count

        validation.result_json = combined_result
        validation.completed_at = datetime.utcnow()

        if validation.started_at:
            delta = validation.completed_at - validation.started_at
            validation.duration_ms = int(delta.total_seconds() * 1000)

    async def get_validation(self, validation_id: str) -> Validation | None:
        """Get validation by ID.

        Args:
            validation_id: Validation ID.

        Returns:
            Validation or None.
        """
        return await self.validation_repo.get_by_id(validation_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Validation]:
        """List validations for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of validations.
        """
        return await self.validation_repo.get_for_source(source_id, limit=limit)


class SchemaService:
    """Service for schema learning and management.

    Handles schema learning, storage, and retrieval.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.schema_repo = SchemaRepository(session)
        self.adapter = get_adapter()

    async def learn_schema(
        self,
        source_id: str,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> Schema:
        """Learn and store schema for a source.

        Wraps truthound's th.learn() with full parameter support for schema
        inference customization.

        Args:
            source_id: Source ID.
            infer_constraints: If True, infers constraints (min/max, allowed values)
                from data statistics.
            categorical_threshold: Maximum unique values for categorical detection.
                Columns with unique values <= threshold are treated as categorical.
                If None, uses truthound default (20).
            sample_size: Number of rows to sample for large datasets.
                If None, uses all rows.

        Returns:
            Created schema record.

        Raises:
            ValueError: If source not found.
        """
        # Get source
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Learn schema with all parameters
        result = await self.adapter.learn(
            source.source_path or "",
            infer_constraints=infer_constraints,
            categorical_threshold=categorical_threshold,
            sample_size=sample_size,
        )

        # Deactivate existing schemas
        await self.schema_repo.deactivate_for_source(source_id)

        # Create new schema
        schema = await self.schema_repo.create(
            source_id=source_id,
            schema_yaml=result.schema_yaml,
            schema_json=result.schema,
            row_count=result.row_count,
            column_count=result.column_count,
            is_active=True,
        )

        return schema

    async def get_schema(self, source_id: str) -> Schema | None:
        """Get active schema for source.

        Args:
            source_id: Source ID.

        Returns:
            Active schema or None.
        """
        return await self.schema_repo.get_active_for_source(source_id)

    async def update_schema(
        self,
        source_id: str,
        schema_yaml: str,
    ) -> Schema | None:
        """Update schema YAML for a source.

        Args:
            source_id: Source ID.
            schema_yaml: New schema YAML.

        Returns:
            Updated schema or None.
        """
        import yaml

        schema = await self.schema_repo.get_active_for_source(source_id)
        if schema is None:
            return None

        # Parse and update
        try:
            schema_json = yaml.safe_load(schema_yaml)
        except yaml.YAMLError:
            schema_json = None

        schema.schema_yaml = schema_yaml
        schema.schema_json = schema_json

        await self.session.flush()
        await self.session.refresh(schema)
        return schema


class RuleService:
    """Service for managing custom validation rules.

    Handles rule CRUD operations and YAML parsing.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.rule_repo = RuleRepository(session)

    async def get_rule(self, rule_id: str) -> Rule | None:
        """Get rule by ID.

        Args:
            rule_id: Rule ID.

        Returns:
            Rule or None.
        """
        return await self.rule_repo.get_by_id(rule_id)

    async def get_rules_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        active_only: bool = False,
    ) -> Sequence[Rule]:
        """Get all rules for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            active_only: Only return active rules.

        Returns:
            Sequence of rules.
        """
        return await self.rule_repo.get_for_source(
            source_id,
            limit=limit,
            active_only=active_only,
        )

    async def get_active_rule(self, source_id: str) -> Rule | None:
        """Get the active rule for a source.

        Args:
            source_id: Source ID.

        Returns:
            Active rule or None.
        """
        return await self.rule_repo.get_active_for_source(source_id)

    async def create_rule(
        self,
        source_id: str,
        *,
        rules_yaml: str,
        name: str = "Default Rules",
        description: str | None = None,
        version: str | None = None,
        activate: bool = True,
    ) -> Rule:
        """Create a new rule for a source.

        Args:
            source_id: Source ID.
            rules_yaml: YAML content defining rules.
            name: Human-readable name.
            description: Optional description.
            version: Optional version string.
            activate: Whether to make this the active rule.

        Returns:
            Created rule.

        Raises:
            ValueError: If source not found or YAML is invalid.
        """
        import yaml

        # Verify source exists
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Parse YAML
        try:
            rules_json = yaml.safe_load(rules_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        # Deactivate existing rules if activating this one
        if activate:
            await self.rule_repo.deactivate_for_source(source_id)

        # Create rule
        rule = await self.rule_repo.create(
            source_id=source_id,
            name=name,
            description=description,
            rules_yaml=rules_yaml,
            rules_json=rules_json,
            is_active=activate,
            version=version,
        )

        return rule

    async def update_rule(
        self,
        rule_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        rules_yaml: str | None = None,
        version: str | None = None,
        is_active: bool | None = None,
    ) -> Rule | None:
        """Update an existing rule.

        Args:
            rule_id: Rule ID.
            name: New name.
            description: New description.
            rules_yaml: New YAML content.
            version: New version.
            is_active: New active status.

        Returns:
            Updated rule or None if not found.

        Raises:
            ValueError: If YAML is invalid.
        """
        import yaml

        rule = await self.rule_repo.get_by_id(rule_id)
        if rule is None:
            return None

        # Update fields
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if version is not None:
            rule.version = version

        # Update YAML and parse
        if rules_yaml is not None:
            try:
                rules_json = yaml.safe_load(rules_yaml)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {e}")
            rule.rules_yaml = rules_yaml
            rule.rules_json = rules_json

        # Handle activation
        if is_active is not None:
            if is_active and not rule.is_active:
                # Deactivate other rules when activating this one
                await self.rule_repo.deactivate_for_source(rule.source_id)
            rule.is_active = is_active

        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule.

        Args:
            rule_id: Rule ID.

        Returns:
            True if deleted.
        """
        return await self.rule_repo.delete(rule_id)

    async def activate_rule(self, rule_id: str) -> Rule | None:
        """Activate a rule and deactivate others for the same source.

        Args:
            rule_id: Rule ID to activate.

        Returns:
            Activated rule or None if not found.
        """
        rule = await self.rule_repo.get_by_id(rule_id)
        if rule is None:
            return None

        # Deactivate other rules
        await self.rule_repo.deactivate_for_source(rule.source_id)

        # Activate this rule
        rule.is_active = True

        await self.session.flush()
        await self.session.refresh(rule)
        return rule


class ProfileRepository(BaseRepository[Profile]):
    """Repository for Profile model operations."""

    model = Profile

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Profile]:
        """Get profiles for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of profiles.
        """
        return await self.list(
            limit=limit,
            filters=[Profile.source_id == source_id],
            order_by=Profile.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> Profile | None:
        """Get most recent profile for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest profile or None.
        """
        result = await self.session.execute(
            select(Profile)
            .where(Profile.source_id == source_id)
            .order_by(Profile.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class ScheduleRepository(BaseRepository[Schedule]):
    """Repository for Schedule model operations."""

    model = Schedule

    async def get_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Schedule]:
        """Get active schedules only.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of active schedules.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[Schedule.is_active],
        )

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[Schedule]:
        """Get schedules for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of schedules.
        """
        return await self.list(
            limit=limit,
            filters=[Schedule.source_id == source_id],
            order_by=Schedule.created_at.desc(),
        )


class DriftComparisonRepository(BaseRepository[DriftComparison]):
    """Repository for DriftComparison model operations."""

    model = DriftComparison

    async def get_for_sources(
        self,
        baseline_source_id: str | None = None,
        current_source_id: str | None = None,
        *,
        limit: int = 20,
    ) -> Sequence[DriftComparison]:
        """Get drift comparisons for sources.

        Args:
            baseline_source_id: Optional baseline source ID.
            current_source_id: Optional current source ID.
            limit: Maximum to return.

        Returns:
            Sequence of drift comparisons.
        """
        filters = []
        if baseline_source_id:
            filters.append(DriftComparison.baseline_source_id == baseline_source_id)
        if current_source_id:
            filters.append(DriftComparison.current_source_id == current_source_id)

        return await self.list(
            limit=limit,
            filters=filters if filters else None,
            order_by=DriftComparison.created_at.desc(),
        )

    async def get_latest(
        self,
        baseline_source_id: str,
        current_source_id: str,
    ) -> DriftComparison | None:
        """Get latest comparison between two sources.

        Args:
            baseline_source_id: Baseline source ID.
            current_source_id: Current source ID.

        Returns:
            Latest comparison or None.
        """
        result = await self.session.execute(
            select(DriftComparison)
            .where(
                and_(
                    DriftComparison.baseline_source_id == baseline_source_id,
                    DriftComparison.current_source_id == current_source_id,
                )
            )
            .order_by(DriftComparison.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class ProfileService:
    """Service for data profiling with history tracking.

    Handles data profiling operations and stores results.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.profile_repo = ProfileRepository(session)
        self.adapter = get_adapter()

    async def profile_source(
        self,
        source_id: str,
        *,
        sample_size: int | None = None,
        save: bool = True,
    ) -> Profile:
        """Profile a data source and optionally save result.

        Args:
            source_id: Source ID to profile.
            sample_size: Maximum number of rows to sample for profiling.
                If None, profiles all data. Useful for large datasets.
            save: Whether to save profile to database.

        Returns:
            Profile model with results.

        Raises:
            ValueError: If source not found.
        """
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        result = await self.adapter.profile(
            source.source_path or "",
            sample_size=sample_size,
        )

        if save:
            profile = await self.profile_repo.create(
                source_id=source_id,
                profile_json=result.to_dict(),
                row_count=result.row_count,
                column_count=result.column_count,
                size_bytes=result.size_bytes,
            )
            return profile

        # Return unsaved profile object
        profile = Profile(
            source_id=source_id,
            profile_json=result.to_dict(),
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes,
        )
        return profile

    async def get_latest_profile(self, source_id: str) -> Profile | None:
        """Get the latest profile for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest profile or None.
        """
        return await self.profile_repo.get_latest_for_source(source_id)

    async def list_profiles(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[Profile]:
        """List profiles for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of profiles.
        """
        return await self.profile_repo.get_for_source(source_id, limit=limit)


class HistoryService:
    """Service for validation history and analytics.

    Provides aggregated views of validation history with trend analysis.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.validation_repo = ValidationRepository(session)

    async def get_history(
        self,
        source_id: str,
        *,
        period: Literal["7d", "30d", "90d"] = "30d",
        granularity: Literal["hourly", "daily", "weekly"] = "daily",
    ) -> dict[str, Any]:
        """Get validation history with trend data.

        Args:
            source_id: Source ID.
            period: Time period to analyze.
            granularity: Aggregation granularity.

        Returns:
            Dictionary with summary, trend, failure_frequency, and recent_validations.
        """
        days = {"7d": 7, "30d": 30, "90d": 90}[period]
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get validations in period
        result = await self.session.execute(
            select(Validation)
            .where(Validation.source_id == source_id)
            .where(Validation.created_at >= start_date)
            .order_by(Validation.created_at.desc())
        )
        validations = list(result.scalars().all())

        # Calculate statistics
        total_runs = len(validations)
        passed_runs = sum(1 for v in validations if v.passed)
        failed_runs = sum(1 for v in validations if v.passed is False)
        success_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

        # Aggregate by granularity
        trend_data = self._aggregate_by_period(validations, granularity)

        # Calculate failure frequency
        failure_frequency = self._calculate_failure_frequency(validations)

        # Recent validations (top 10)
        recent_validations = [
            {
                "id": v.id,
                "status": v.status,
                "passed": v.passed,
                "has_critical": v.has_critical,
                "has_high": v.has_high,
                "total_issues": v.total_issues,
                "created_at": v.created_at.isoformat(),
            }
            for v in validations[:10]
        ]

        return {
            "summary": {
                "total_runs": total_runs,
                "passed_runs": passed_runs,
                "failed_runs": failed_runs,
                "success_rate": round(success_rate, 2),
            },
            "trend": trend_data,
            "failure_frequency": failure_frequency,
            "recent_validations": recent_validations,
        }

    def _aggregate_by_period(
        self,
        validations: list[Validation],
        granularity: Literal["hourly", "daily", "weekly"],
    ) -> list[dict[str, Any]]:
        """Aggregate validations by time period."""
        buckets: dict[str, list[Validation]] = defaultdict(list)

        for v in validations:
            if granularity == "hourly":
                key = v.created_at.strftime("%Y-%m-%d %H:00")
            elif granularity == "daily":
                key = v.created_at.strftime("%Y-%m-%d")
            else:  # weekly
                monday = v.created_at - timedelta(days=v.created_at.weekday())
                key = monday.strftime("%Y-%m-%d")

            buckets[key].append(v)

        trend = []
        for date, vals in sorted(buckets.items()):
            passed_count = sum(1 for v in vals if v.passed)
            success_rate = (passed_count / len(vals) * 100) if vals else 0
            trend.append(
                {
                    "date": date,
                    "success_rate": round(success_rate, 2),
                    "run_count": len(vals),
                    "passed_count": passed_count,
                    "failed_count": len(vals) - passed_count,
                }
            )

        return trend

    def _calculate_failure_frequency(
        self,
        validations: list[Validation],
    ) -> list[dict[str, Any]]:
        """Calculate failure frequency by issue type."""
        failures: Counter[str] = Counter()

        for v in validations:
            if v.result_json and "issues" in v.result_json:
                for issue in v.result_json["issues"]:
                    key = f"{issue.get('column', 'unknown')}.{issue.get('issue_type', 'unknown')}"
                    failures[key] += issue.get("count", 1)

        return [
            {"issue": issue, "count": count}
            for issue, count in failures.most_common(10)
        ]


class DriftService:
    """Service for drift detection.

    Handles drift comparison between datasets.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.drift_repo = DriftComparisonRepository(session)
        self.adapter = get_adapter()

    async def compare(
        self,
        baseline_source_id: str,
        current_source_id: str,
        *,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
        correction: str | None = None,
        sample_size: int | None = None,
        save: bool = True,
    ) -> DriftComparison:
        """Compare two datasets for drift detection.

        Args:
            baseline_source_id: Baseline source ID.
            current_source_id: Current source ID.
            columns: Optional list of columns to compare.
            method: Detection method. Supported:
                auto, ks, psi, chi2, js, kl, wasserstein, cvm, anderson
            threshold: Optional custom threshold.
            correction: Multiple testing correction (none, bonferroni, holm, bh).
            sample_size: Optional sample size.
            save: Whether to save comparison to database.

        Returns:
            DriftComparison model with results.

        Raises:
            ValueError: If source not found.
        """
        baseline = await self.source_repo.get_by_id(baseline_source_id)
        if baseline is None:
            raise ValueError(f"Baseline source '{baseline_source_id}' not found")

        current = await self.source_repo.get_by_id(current_source_id)
        if current is None:
            raise ValueError(f"Current source '{current_source_id}' not found")

        result = await self.adapter.compare(
            baseline.source_path or "",
            current.source_path or "",
            columns=columns,
            method=method,
            threshold=threshold,
            correction=correction,
            sample_size=sample_size,
        )

        config = {
            "columns": columns,
            "method": method,
            "threshold": threshold,
            "correction": correction,
            "sample_size": sample_size,
        }

        if save:
            comparison = await self.drift_repo.create(
                baseline_source_id=baseline_source_id,
                current_source_id=current_source_id,
                has_drift=result.has_drift,
                has_high_drift=result.has_high_drift,
                total_columns=result.total_columns,
                drifted_columns=len(result.drifted_columns),
                result_json=result.to_dict(),
                config=config,
            )
            return comparison

        # Return unsaved comparison object
        comparison = DriftComparison(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            has_drift=result.has_drift,
            has_high_drift=result.has_high_drift,
            total_columns=result.total_columns,
            drifted_columns=len(result.drifted_columns),
            result_json=result.to_dict(),
            config=config,
        )
        return comparison

    async def get_comparison(self, comparison_id: str) -> DriftComparison | None:
        """Get a drift comparison by ID.

        Args:
            comparison_id: Comparison ID.

        Returns:
            DriftComparison or None.
        """
        return await self.drift_repo.get_by_id(comparison_id)

    async def list_comparisons(
        self,
        *,
        baseline_source_id: str | None = None,
        current_source_id: str | None = None,
        limit: int = 20,
    ) -> Sequence[DriftComparison]:
        """List drift comparisons.

        Args:
            baseline_source_id: Optional baseline source ID filter.
            current_source_id: Optional current source ID filter.
            limit: Maximum to return.

        Returns:
            Sequence of drift comparisons.
        """
        return await self.drift_repo.get_for_sources(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            limit=limit,
        )


class ScheduleService:
    """Service for managing validation schedules.

    Handles schedule CRUD and integrates with APScheduler.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.schedule_repo = ScheduleRepository(session)

    async def create_schedule(
        self,
        source_id: str,
        *,
        name: str,
        cron_expression: str,
        notify_on_failure: bool = True,
        config: dict[str, Any] | None = None,
    ) -> Schedule:
        """Create a new schedule.

        Args:
            source_id: Source ID to schedule.
            name: Schedule name.
            cron_expression: Cron expression.
            notify_on_failure: Send notification on failure.
            config: Additional configuration.

        Returns:
            Created schedule.

        Raises:
            ValueError: If source not found or invalid cron expression.
        """
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Validate cron expression
        next_run = self._get_next_run(cron_expression)

        schedule = await self.schedule_repo.create(
            name=name,
            source_id=source_id,
            cron_expression=cron_expression,
            is_active=True,
            notify_on_failure=notify_on_failure,
            next_run_at=next_run,
            config=config,
        )

        return schedule

    async def get_schedule(self, schedule_id: str) -> Schedule | None:
        """Get schedule by ID.

        Args:
            schedule_id: Schedule ID.

        Returns:
            Schedule or None.
        """
        return await self.schedule_repo.get_by_id(schedule_id)

    async def list_schedules(
        self,
        *,
        source_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> Sequence[Schedule]:
        """List schedules.

        Args:
            source_id: Optional source ID filter.
            active_only: Only return active schedules.
            limit: Maximum to return.

        Returns:
            Sequence of schedules.
        """
        if source_id:
            return await self.schedule_repo.get_for_source(source_id, limit=limit)
        if active_only:
            return await self.schedule_repo.get_active(limit=limit)
        return await self.schedule_repo.list(limit=limit)

    async def update_schedule(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        cron_expression: str | None = None,
        notify_on_failure: bool | None = None,
        config: dict[str, Any] | None = None,
    ) -> Schedule | None:
        """Update a schedule.

        Args:
            schedule_id: Schedule ID.
            name: New name.
            cron_expression: New cron expression.
            notify_on_failure: New notification setting.
            config: New configuration.

        Returns:
            Updated schedule or None.
        """
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None

        if name is not None:
            schedule.name = name
        if cron_expression is not None:
            schedule.cron_expression = cron_expression
            schedule.next_run_at = self._get_next_run(cron_expression)
        if notify_on_failure is not None:
            schedule.notify_on_failure = notify_on_failure
        if config is not None:
            schedule.config = config

        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule.

        Args:
            schedule_id: Schedule ID.

        Returns:
            True if deleted.
        """
        return await self.schedule_repo.delete(schedule_id)

    async def pause_schedule(self, schedule_id: str) -> Schedule | None:
        """Pause a schedule.

        Args:
            schedule_id: Schedule ID.

        Returns:
            Updated schedule or None.
        """
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None

        schedule.pause()
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def resume_schedule(self, schedule_id: str) -> Schedule | None:
        """Resume a paused schedule.

        Args:
            schedule_id: Schedule ID.

        Returns:
            Updated schedule or None.
        """
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if schedule is None:
            return None

        schedule.resume()
        schedule.next_run_at = self._get_next_run(schedule.cron_expression)
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    def _get_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression.

        Returns:
            Next run datetime.

        Raises:
            ValueError: If invalid cron expression.
        """
        try:
            from apscheduler.triggers.cron import CronTrigger

            trigger = CronTrigger.from_crontab(cron_expression)
            next_fire = trigger.get_next_fire_time(None, datetime.utcnow())
            if next_fire is None:
                raise ValueError("Could not calculate next run time")
            return next_fire
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")


class PIIScanRepository(BaseRepository[PIIScan]):
    """Repository for PIIScan model operations."""

    model = PIIScan

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[PIIScan]:
        """Get PII scans for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of PII scans.
        """
        return await self.list(
            limit=limit,
            filters=[PIIScan.source_id == source_id],
            order_by=PIIScan.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> PIIScan | None:
        """Get most recent PII scan for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest PII scan or None.
        """
        result = await self.session.execute(
            select(PIIScan)
            .where(PIIScan.source_id == source_id)
            .order_by(PIIScan.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class PIIScanService:
    """Service for PII scanning operations.

    Handles PII detection and regulation compliance checking using th.scan().
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.scan_repo = PIIScanRepository(session)
        self.adapter = get_adapter()

    async def run_scan(
        self,
        source_id: str,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> PIIScan:
        """Run PII scan on a source.

        This method provides access to truthound's th.scan() parameters,
        allowing detection of personally identifiable information and
        checking compliance with privacy regulations.

        Args:
            source_id: Source ID to scan.
            columns: Optional columns to scan. If None, scans all columns.
            regulations: Optional regulations to check (gdpr, ccpa, lgpd).
            min_confidence: Minimum confidence threshold (0.0-1.0). Default 0.8.

        Returns:
            PIIScan record with results.

        Raises:
            ValueError: If source not found.
        """
        # Get source
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Create scan record
        scan = await self.scan_repo.create(
            source_id=source_id,
            status="running",
            min_confidence=min_confidence,
            regulations_checked=regulations,
            started_at=datetime.utcnow(),
        )

        try:
            # Run scan
            result = await self.adapter.scan(
                source.source_path or "",
                columns=columns,
                regulations=regulations,
                min_confidence=min_confidence,
            )

            # Update scan with results
            await self._update_scan_success(scan, result)

        except Exception as e:
            # Update scan with error
            scan.mark_error(str(e))

        await self.session.flush()
        await self.session.refresh(scan)
        return scan

    async def _update_scan_success(
        self,
        scan: PIIScan,
        result: ScanResult,
    ) -> None:
        """Update scan with successful result.

        Args:
            scan: PIIScan record to update.
            result: Scan result from adapter.
        """
        scan.status = "success" if not result.has_violations else "failed"
        scan.total_columns_scanned = result.total_columns_scanned
        scan.columns_with_pii = result.columns_with_pii
        scan.total_findings = result.total_findings
        scan.has_violations = result.has_violations
        scan.total_violations = result.total_violations
        scan.row_count = result.row_count
        scan.column_count = result.column_count
        scan.result_json = result.to_dict()
        scan.completed_at = datetime.utcnow()

        if scan.started_at:
            delta = scan.completed_at - scan.started_at
            scan.duration_ms = int(delta.total_seconds() * 1000)

    async def get_scan(self, scan_id: str) -> PIIScan | None:
        """Get PII scan by ID.

        Args:
            scan_id: Scan ID.

        Returns:
            PIIScan or None.
        """
        return await self.scan_repo.get_by_id(scan_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[PIIScan]:
        """List PII scans for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of PII scans.
        """
        return await self.scan_repo.get_for_source(source_id, limit=limit)

    async def get_latest_for_source(self, source_id: str) -> PIIScan | None:
        """Get most recent PII scan for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest PII scan or None.
        """
        return await self.scan_repo.get_latest_for_source(source_id)


class DataMaskRepository(BaseRepository[DataMask]):
    """Repository for DataMask model operations."""

    model = DataMask

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[DataMask]:
        """Get mask operations for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of mask operations.
        """
        return await self.list(
            limit=limit,
            filters=[DataMask.source_id == source_id],
            order_by=DataMask.created_at.desc(),
        )

    async def get_latest_for_source(self, source_id: str) -> DataMask | None:
        """Get most recent mask operation for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest mask operation or None.
        """
        result = await self.session.execute(
            select(DataMask)
            .where(DataMask.source_id == source_id)
            .order_by(DataMask.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class MaskService:
    """Service for data masking operations.

    Handles data masking using th.mask() with three strategies:
    - redact: Replace values with asterisks
    - hash: Replace values with SHA256 hash (deterministic)
    - fake: Replace values with realistic fake data
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.source_repo = SourceRepository(session)
        self.mask_repo = DataMaskRepository(session)
        self.adapter = get_adapter()

    async def run_mask(
        self,
        source_id: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
        output_format: str = "csv",
    ) -> DataMask:
        """Run data masking on a source.

        This method provides access to truthound's th.mask() with
        three masking strategies for PII protection.

        Args:
            source_id: Source ID to mask.
            columns: Optional columns to mask. If None, auto-detects PII.
            strategy: Masking strategy (redact, hash, fake). Default is redact.
            output_format: Output file format (csv, parquet, json). Default is csv.

        Returns:
            DataMask record with results.

        Raises:
            ValueError: If source not found or invalid strategy.
        """
        # Validate strategy
        if strategy not in ("redact", "hash", "fake"):
            raise ValueError(
                f"Invalid strategy: {strategy}. Use 'redact', 'hash', or 'fake'."
            )

        # Get source
        source = await self.source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Determine output path
        source_path = source.source_path or ""
        import os
        from pathlib import Path

        base_path = Path(source_path)
        output_dir = base_path.parent / "masked"
        output_dir.mkdir(exist_ok=True)
        output_filename = f"{base_path.stem}_masked_{strategy}.{output_format}"
        output_path = str(output_dir / output_filename)

        # Create mask record
        mask = await self.mask_repo.create(
            source_id=source_id,
            status="running",
            strategy=strategy,
            auto_detected=columns is None,
            started_at=datetime.utcnow(),
        )

        try:
            # Run masking
            result = await self.adapter.mask(
                source_path,
                output_path,
                columns=columns,
                strategy=strategy,
            )

            # Update mask with results
            await self._update_mask_success(mask, result)

        except Exception as e:
            # Update mask with error
            mask.mark_error(str(e))

        await self.session.flush()
        await self.session.refresh(mask)
        return mask

    async def _update_mask_success(
        self,
        mask: DataMask,
        result: MaskResult,
    ) -> None:
        """Update mask with successful result.

        Args:
            mask: DataMask record to update.
            result: Mask result from adapter.
        """
        mask.status = "success"
        mask.output_path = result.output_path
        mask.columns_masked = result.columns_masked
        mask.row_count = result.row_count
        mask.column_count = result.column_count
        mask.result_json = result.to_dict()
        mask.completed_at = datetime.utcnow()

        if mask.started_at:
            delta = mask.completed_at - mask.started_at
            mask.duration_ms = int(delta.total_seconds() * 1000)

    async def get_mask(self, mask_id: str) -> DataMask | None:
        """Get mask operation by ID.

        Args:
            mask_id: Mask ID.

        Returns:
            DataMask or None.
        """
        return await self.mask_repo.get_by_id(mask_id)

    async def list_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[DataMask]:
        """List mask operations for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.

        Returns:
            Sequence of mask operations.
        """
        return await self.mask_repo.get_for_source(source_id, limit=limit)

    async def get_latest_for_source(self, source_id: str) -> DataMask | None:
        """Get most recent mask operation for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest mask operation or None.
        """
        return await self.mask_repo.get_latest_for_source(source_id)
