"""Advanced notification management API endpoints.

This module provides REST API endpoints for managing advanced notification
features: routing rules, deduplication, throttling, and escalation.

Endpoints:
    Routing Rules:
        GET    /notifications/routing/rules              - List routing rules
        POST   /notifications/routing/rules              - Create routing rule
        GET    /notifications/routing/rules/{id}         - Get routing rule
        PUT    /notifications/routing/rules/{id}         - Update routing rule
        DELETE /notifications/routing/rules/{id}         - Delete routing rule
        GET    /notifications/routing/rules/types        - Get available rule types (incl. combinators)
        POST   /notifications/routing/rules/validate     - Validate rule configuration

    Deduplication:
        GET    /notifications/deduplication/configs      - List configs
        POST   /notifications/deduplication/configs      - Create config
        GET    /notifications/deduplication/configs/{id} - Get config
        PUT    /notifications/deduplication/configs/{id} - Update config
        DELETE /notifications/deduplication/configs/{id} - Delete config
        GET    /notifications/deduplication/stats        - Get statistics

    Throttling:
        GET    /notifications/throttling/configs         - List configs
        POST   /notifications/throttling/configs         - Create config
        GET    /notifications/throttling/configs/{id}    - Get config
        PUT    /notifications/throttling/configs/{id}    - Update config
        DELETE /notifications/throttling/configs/{id}    - Delete config
        GET    /notifications/throttling/stats           - Get statistics

    Escalation Policies:
        GET    /notifications/escalation/policies        - List policies
        POST   /notifications/escalation/policies        - Create policy
        GET    /notifications/escalation/policies/{id}   - Get policy
        PUT    /notifications/escalation/policies/{id}   - Update policy
        DELETE /notifications/escalation/policies/{id}   - Delete policy

    Escalation Incidents:
        GET    /notifications/escalation/incidents       - List incidents
        GET    /notifications/escalation/incidents/active - List active only
        GET    /notifications/escalation/incidents/{id}  - Get incident
        POST   /notifications/escalation/incidents/{id}/acknowledge - Acknowledge
        POST   /notifications/escalation/incidents/{id}/resolve - Resolve
        GET    /notifications/escalation/stats           - Get statistics
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import get_session
from .websocket import notify_incident_state_changed
from ..core.notifications.metrics.collectors import (
    DeduplicationMetrics,
    EscalationMetrics,
    ThrottlingMetrics,
)
from ..core.notifications.routing.rules import RuleRegistry
from ..core.notifications.routing.validator import (
    RuleValidationConfig,
    RuleValidator,
    ValidationErrorType,
)
from ..core.notifications.stats_aggregator import (
    StatsAggregator,
    TimeRange,
    get_stats_cache,
)
from ..db.models import (
    DeduplicationConfig,
    EscalationIncidentModel,
    EscalationPolicyModel,
    EscalationStateEnum,
    RoutingRuleModel,
    ThrottlingConfig,
)
from ..schemas.notifications_advanced import (
    AcknowledgeRequest,
    CacheInfo,
    CombinatorType,
    ConfigExportRequest,
    ConfigImportConflict,
    ConfigImportPreview,
    ConfigImportRequest,
    ConfigImportResult,
    DeduplicationConfigCreate,
    DeduplicationConfigListResponse,
    DeduplicationConfigResponse,
    DeduplicationConfigUpdate,
    DeduplicationStats,
    DeduplicationStatsEnhanced,
    EscalationEventBase,
    EscalationIncidentListResponse,
    EscalationIncidentResponse,
    EscalationPolicyCreate,
    EscalationPolicyListResponse,
    EscalationPolicyResponse,
    EscalationPolicyUpdate,
    EscalationSchedulerAction,
    EscalationSchedulerConfigRequest,
    EscalationSchedulerStatus,
    EscalationStats,
    EscalationStatsEnhanced,
    ExpressionValidateRequest,
    ExpressionValidateResponse,
    NestedRuleConfig,
    NotificationConfigBundle,
    ResolveRequest,
    RoutingRuleCreate,
    RoutingRuleListResponse,
    RoutingRuleResponse,
    RoutingRuleUpdate,
    RuleTypeInfo,
    RuleTypesResponse,
    RuleValidationResult,
    StatsCacheStatus,
    ThrottlingConfigCreate,
    ThrottlingConfigListResponse,
    ThrottlingConfigResponse,
    ThrottlingConfigUpdate,
    ThrottlingStats,
    ThrottlingStatsEnhanced,
    TimeRangeFilter,
    TriggerCheckResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications")

# Global metrics instances
_dedup_metrics = DeduplicationMetrics()
_throttle_metrics = ThrottlingMetrics()
_escalation_metrics = EscalationMetrics()


def get_dedup_metrics() -> DeduplicationMetrics:
    """Get the global deduplication metrics instance."""
    return _dedup_metrics


def get_throttle_metrics() -> ThrottlingMetrics:
    """Get the global throttling metrics instance."""
    return _throttle_metrics


def get_escalation_metrics() -> EscalationMetrics:
    """Get the global escalation metrics instance."""
    return _escalation_metrics


# =============================================================================
# Helper Functions
# =============================================================================


def _routing_rule_to_response(rule: RoutingRuleModel) -> RoutingRuleResponse:
    """Convert database model to response schema."""
    return RoutingRuleResponse(
        id=rule.id,
        name=rule.name,
        rule_config=rule.rule_config,
        actions=rule.actions,
        priority=rule.priority,
        is_active=rule.is_active,
        stop_on_match=rule.stop_on_match,
        metadata=rule.routing_metadata or {},
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _dedup_config_to_response(config: DeduplicationConfig) -> DeduplicationConfigResponse:
    """Convert database model to response schema."""
    return DeduplicationConfigResponse(
        id=config.id,
        name=config.name,
        strategy=config.strategy,
        policy=config.policy,
        window_seconds=config.window_seconds,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _throttle_config_to_response(config: ThrottlingConfig) -> ThrottlingConfigResponse:
    """Convert database model to response schema."""
    return ThrottlingConfigResponse(
        id=config.id,
        name=config.name,
        per_minute=config.per_minute,
        per_hour=config.per_hour,
        per_day=config.per_day,
        burst_allowance=config.burst_allowance,
        channel_id=config.channel_id,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _escalation_policy_to_response(
    policy: EscalationPolicyModel,
) -> EscalationPolicyResponse:
    """Convert database model to response schema."""
    return EscalationPolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description or "",
        levels=policy.levels,
        auto_resolve_on_success=policy.auto_resolve_on_success,
        max_escalations=policy.max_escalations,
        is_active=policy.is_active,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def _escalation_incident_to_response(
    incident: EscalationIncidentModel,
) -> EscalationIncidentResponse:
    """Convert database model to response schema."""
    events = []
    for event in incident.events or []:
        events.append(
            EscalationEventBase(
                from_state=event.get("from_state"),
                to_state=event.get("to_state", ""),
                actor=event.get("actor"),
                message=event.get("message", ""),
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat())),
            )
        )

    return EscalationIncidentResponse(
        id=incident.id,
        policy_id=incident.policy_id,
        incident_ref=incident.incident_ref,
        state=incident.state,
        current_level=incident.current_level,
        escalation_count=incident.escalation_count,
        context=incident.context or {},
        acknowledged_by=incident.acknowledged_by,
        acknowledged_at=incident.acknowledged_at,
        resolved_by=incident.resolved_by,
        resolved_at=incident.resolved_at,
        next_escalation_at=incident.next_escalation_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        events=events,
    )


async def _broadcast_incident_state_change(
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    from_state: str,
    to_state: str,
    current_level: int,
    actor: str | None = None,
    message: str | None = None,
) -> None:
    """Broadcast incident state change via WebSocket.

    This is called as a background task to avoid blocking the HTTP response.

    Args:
        incident_id: ID of the incident.
        incident_ref: External reference.
        policy_id: Associated policy ID.
        from_state: Previous state.
        to_state: New state.
        current_level: Current escalation level.
        actor: Who triggered the change.
        message: Optional message.
    """
    try:
        count = await notify_incident_state_changed(
            incident_id=incident_id,
            incident_ref=incident_ref,
            policy_id=policy_id,
            from_state=from_state,
            to_state=to_state,
            current_level=current_level,
            actor=actor,
            message=message,
        )
        if count > 0:
            logger.debug(
                f"Broadcast incident state change to {count} clients: "
                f"{incident_id} {from_state} -> {to_state}"
            )
    except Exception as e:
        logger.error(f"Failed to broadcast incident state change: {e}")


# =============================================================================
# Routing Rule Endpoints
# =============================================================================


@router.get("/routing/rules/types", response_model=RuleTypesResponse)
async def get_rule_types() -> RuleTypesResponse:
    """Get available routing rule types with their parameter schemas.

    Returns both simple rule types and combinator types (all_of, any_of, not).
    """
    rule_types = []

    # Add simple rule types from RuleRegistry
    for rule_type in RuleRegistry.list_types():
        rule_class = RuleRegistry.get(rule_type)
        if rule_class:
            rule_types.append(
                RuleTypeInfo(
                    type=rule_type,
                    name=rule_class.__name__.replace("Rule", "").replace("_", " "),
                    description=rule_class.__doc__ or "",
                    param_schema=rule_class.get_param_schema(),
                )
            )

    # Add combinator types
    combinator_types = [
        RuleTypeInfo(
            type=CombinatorType.ALL_OF.value,
            name="All Of",
            description="Matches when ALL nested rules match. Use for AND logic.",
            param_schema={
                "rules": {
                    "type": "array",
                    "required": True,
                    "description": "List of nested rules that must all match",
                    "items": {"type": "object", "description": "Nested rule configuration"},
                }
            },
        ),
        RuleTypeInfo(
            type=CombinatorType.ANY_OF.value,
            name="Any Of",
            description="Matches when ANY nested rule matches. Use for OR logic.",
            param_schema={
                "rules": {
                    "type": "array",
                    "required": True,
                    "description": "List of nested rules where at least one must match",
                    "items": {"type": "object", "description": "Nested rule configuration"},
                }
            },
        ),
        RuleTypeInfo(
            type=CombinatorType.NOT.value,
            name="Not",
            description="Negates the nested rule. Matches when the nested rule does NOT match.",
            param_schema={
                "rule": {
                    "type": "object",
                    "required": True,
                    "description": "The rule to negate",
                }
            },
        ),
    ]
    rule_types.extend(combinator_types)

    return RuleTypesResponse(rule_types=rule_types)


@router.get("/routing/rules", response_model=RoutingRuleListResponse)
async def list_routing_rules(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleListResponse:
    """List routing rules ordered by priority."""
    query = select(RoutingRuleModel).order_by(
        RoutingRuleModel.priority.desc(),
        RoutingRuleModel.created_at.desc(),
    )

    if active_only:
        query = query.where(RoutingRuleModel.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    rules = result.scalars().all()

    return RoutingRuleListResponse(
        items=[_routing_rule_to_response(r) for r in rules],
        total=len(rules),
        offset=offset,
        limit=limit,
    )


def _validate_rule_config_on_save(
    rule_config: dict[str, Any],
    max_depth: int = 10,
    max_rules_per_combinator: int = 50,
) -> None:
    """Validate rule configuration before saving.

    Raises HTTPException if validation fails.

    Args:
        rule_config: The rule configuration dictionary.
        max_depth: Maximum nesting depth.
        max_rules_per_combinator: Maximum rules per combinator.

    Raises:
        HTTPException: If validation fails with 400 status code.
    """
    validation_config = RuleValidationConfig(
        max_depth=max_depth,
        max_rules_per_combinator=max_rules_per_combinator,
        check_circular_refs=True,
    )
    validator = RuleValidator(validation_config)
    result = validator.validate(rule_config)

    if not result.valid:
        # Format error messages with paths for clarity
        error_details = []
        for error in result.errors:
            if error.path:
                error_details.append(f"[{error.path}] {error.message}")
            else:
                error_details.append(error.message)

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid rule configuration",
                "errors": error_details,
                "validation_result": {
                    "rule_count": result.rule_count,
                    "max_depth": result.max_depth,
                    "circular_paths": result.circular_paths,
                },
            },
        )


@router.post("/routing/rules", response_model=RoutingRuleResponse)
async def create_routing_rule(
    request: RoutingRuleCreate,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Create a new routing rule.

    Validates the rule configuration for:
    - Valid rule types
    - Required parameters
    - Circular references
    - Maximum nesting depth
    - Reserved field names
    """
    # Validate rule configuration before saving
    _validate_rule_config_on_save(request.rule_config)

    rule = RoutingRuleModel(
        name=request.name,
        rule_config=request.rule_config,
        actions=request.actions,
        priority=request.priority,
        is_active=request.is_active,
        stop_on_match=request.stop_on_match,
        routing_metadata=request.metadata,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    return _routing_rule_to_response(rule)


@router.get("/routing/rules/{rule_id}", response_model=RoutingRuleResponse)
async def get_routing_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Get a routing rule by ID."""
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    return _routing_rule_to_response(rule)


@router.put("/routing/rules/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: str,
    request: RoutingRuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> RoutingRuleResponse:
    """Update a routing rule.

    If rule_config is provided, validates it for:
    - Valid rule types
    - Required parameters
    - Circular references
    - Maximum nesting depth
    - Reserved field names
    """
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    # Validate rule_config if it's being updated
    if request.rule_config is not None:
        _validate_rule_config_on_save(request.rule_config)

    if request.name is not None:
        rule.name = request.name
    if request.rule_config is not None:
        rule.rule_config = request.rule_config
    if request.actions is not None:
        rule.actions = request.actions
    if request.priority is not None:
        rule.priority = request.priority
    if request.is_active is not None:
        rule.is_active = request.is_active
    if request.stop_on_match is not None:
        rule.stop_on_match = request.stop_on_match
    if request.metadata is not None:
        rule.routing_metadata = request.metadata

    await session.commit()
    await session.refresh(rule)

    return _routing_rule_to_response(rule)


@router.delete("/routing/rules/{rule_id}")
async def delete_routing_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a routing rule."""
    result = await session.execute(
        select(RoutingRuleModel).where(RoutingRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule is None:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    await session.delete(rule)
    await session.commit()

    return {"success": True, "message": "Routing rule deleted"}


def _convert_nested_rule_config_to_dict(config: NestedRuleConfig) -> dict[str, Any]:
    """Convert NestedRuleConfig Pydantic model to plain dict for validation.

    Args:
        config: The NestedRuleConfig to convert.

    Returns:
        Dictionary representation of the rule configuration.
    """
    result: dict[str, Any] = {"type": config.type}

    if config.params:
        result["params"] = config.params

    if config.rules:
        result["rules"] = [_convert_nested_rule_config_to_dict(r) for r in config.rules]

    if config.rule:
        result["rule"] = _convert_nested_rule_config_to_dict(config.rule)

    return result


@router.post("/routing/rules/validate", response_model=RuleValidationResult)
async def validate_rule_config(
    config: NestedRuleConfig,
    max_depth: int = Query(default=10, ge=1, le=50, description="Maximum nesting depth"),
    max_rules_per_combinator: int = Query(
        default=50, ge=1, le=200, description="Maximum rules per combinator"
    ),
    check_circular_refs: bool = Query(
        default=True, description="Check for circular references"
    ),
) -> RuleValidationResult:
    """Validate a rule configuration without creating it.

    Performs comprehensive validation including:
    - Rule type existence (via RuleRegistry)
    - Required parameter validation
    - Circular reference detection (direct and indirect)
    - Maximum nesting depth enforcement
    - Maximum rules per combinator enforcement
    - Reserved field name checking

    Args:
        config: The rule configuration to validate.
        max_depth: Maximum allowed nesting depth (default: 10).
        max_rules_per_combinator: Maximum rules in a single combinator (default: 50).
        check_circular_refs: Whether to check for circular references (default: True).

    Returns:
        Validation result with errors, warnings, and statistics.
    """
    # Convert Pydantic model to dict for the validator
    rule_dict = _convert_nested_rule_config_to_dict(config)

    # Create validator with configuration
    validation_config = RuleValidationConfig(
        max_depth=max_depth,
        max_rules_per_combinator=max_rules_per_combinator,
        check_circular_refs=check_circular_refs,
    )
    validator = RuleValidator(validation_config)

    # Perform validation
    result = validator.validate(rule_dict)

    # Convert to response model
    return RuleValidationResult(
        valid=result.valid,
        errors=result.error_messages(),
        warnings=result.warning_messages(),
        rule_count=result.rule_count,
        max_depth=result.max_depth,
        circular_paths=result.circular_paths,
    )


@router.post("/routing/rules/validate-expression", response_model=ExpressionValidateResponse)
async def validate_expression(
    request: ExpressionValidateRequest,
) -> ExpressionValidateResponse:
    """Validate a Python-like expression for use in routing rules.

    Performs syntax validation and optionally evaluates the expression
    with sample data to check for runtime errors.

    The expression is evaluated in a safe, sandboxed environment with:
    - AST-based parsing (no exec/eval)
    - Timeout protection
    - Blocked access to dangerous attributes

    Args:
        request: Expression validation request.

    Returns:
        Validation result with any errors and optional preview result.

    Example expressions:
        - severity == 'critical'
        - pass_rate < 0.8 and issue_count > 5
        - 'production' in tags
        - metadata.get('environment') == 'production'
    """
    from ..core.notifications.routing.expression_engine import (
        ExpressionContext,
        ExpressionError,
        ExpressionSecurityError,
        ExpressionTimeout,
        SafeExpressionEvaluator,
    )

    expression = request.expression.strip()
    warnings: list[str] = []
    error: str | None = None
    error_line: int | None = None
    preview_result: bool | None = None
    preview_error: str | None = None

    # Check for empty expression
    if not expression:
        return ExpressionValidateResponse(
            valid=False,
            error="Expression cannot be empty",
        )

    # Create evaluator with configured timeout
    evaluator = SafeExpressionEvaluator(
        timeout_seconds=request.timeout_seconds,
    )

    # Create sample context for preview evaluation
    sample_context = ExpressionContext(
        checkpoint_name="sample_validation",
        action_type="check",
        severity="high",
        issues=["null_values", "duplicates"],
        pass_rate=0.85,
        timestamp=datetime.utcnow(),
        metadata={
            "environment": "production",
            "table": "orders",
            "row_count": 10000,
        },
    )

    # Validate and evaluate
    try:
        preview_result = evaluator.evaluate(expression, sample_context)
    except ExpressionSecurityError as e:
        error = f"Security error: {e.reason}"
        return ExpressionValidateResponse(
            valid=False,
            error=error,
        )
    except ExpressionTimeout as e:
        error = f"Timeout: Expression took too long to evaluate"
        return ExpressionValidateResponse(
            valid=False,
            error=error,
            warnings=["Consider simplifying the expression"],
        )
    except ExpressionError as e:
        error = e.reason

        # Try to extract line number from syntax errors
        if "Syntax error:" in error:
            import re
            line_match = re.search(r"line (\d+)", error)
            if line_match:
                error_line = int(line_match.group(1))

        return ExpressionValidateResponse(
            valid=False,
            error=error,
            error_line=error_line,
        )
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        return ExpressionValidateResponse(
            valid=False,
            error=error,
        )

    # Add warnings for potential issues
    if "metadata[" in expression and ".get(" not in expression:
        warnings.append(
            "Consider using metadata.get('key') instead of metadata['key'] "
            "to handle missing keys gracefully"
        )

    if len(expression) > 500:
        warnings.append(
            "Expression is quite long. Consider breaking it into multiple rules."
        )

    return ExpressionValidateResponse(
        valid=True,
        error=None,
        preview_result=preview_result,
        preview_error=preview_error,
        warnings=warnings,
    )


# =============================================================================
# Deduplication Endpoints
# =============================================================================


@router.get("/deduplication/configs", response_model=DeduplicationConfigListResponse)
async def list_deduplication_configs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigListResponse:
    """List deduplication configurations."""
    query = select(DeduplicationConfig).order_by(DeduplicationConfig.created_at.desc())

    if active_only:
        query = query.where(DeduplicationConfig.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    configs = result.scalars().all()

    return DeduplicationConfigListResponse(
        items=[_dedup_config_to_response(c) for c in configs],
        total=len(configs),
        offset=offset,
        limit=limit,
    )


@router.post("/deduplication/configs", response_model=DeduplicationConfigResponse)
async def create_deduplication_config(
    request: DeduplicationConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Create a new deduplication configuration."""
    config = DeduplicationConfig(
        name=request.name,
        strategy=request.strategy.value,
        policy=request.policy.value,
        window_seconds=request.window_seconds,
        is_active=request.is_active,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    return _dedup_config_to_response(config)


@router.get("/deduplication/configs/{config_id}", response_model=DeduplicationConfigResponse)
async def get_deduplication_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Get a deduplication config by ID."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    return _dedup_config_to_response(config)


@router.put("/deduplication/configs/{config_id}", response_model=DeduplicationConfigResponse)
async def update_deduplication_config(
    config_id: str,
    request: DeduplicationConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> DeduplicationConfigResponse:
    """Update a deduplication config."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    if request.name is not None:
        config.name = request.name
    if request.strategy is not None:
        config.strategy = request.strategy.value
    if request.policy is not None:
        config.policy = request.policy.value
    if request.window_seconds is not None:
        config.window_seconds = request.window_seconds
    if request.is_active is not None:
        config.is_active = request.is_active

    await session.commit()
    await session.refresh(config)

    return _dedup_config_to_response(config)


@router.delete("/deduplication/configs/{config_id}")
async def delete_deduplication_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a deduplication config."""
    result = await session.execute(
        select(DeduplicationConfig).where(DeduplicationConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Deduplication config not found")

    await session.delete(config)
    await session.commit()

    return {"success": True, "message": "Deduplication config deleted"}


@router.get("/deduplication/stats", response_model=DeduplicationStats)
async def get_deduplication_stats(
    session: AsyncSession = Depends(get_session),
) -> DeduplicationStats:
    """Get deduplication statistics (runtime metrics)."""
    stats = await _dedup_metrics.get_stats()
    return DeduplicationStats(
        total_received=stats.total_received,
        total_deduplicated=stats.total_deduplicated,
        total_passed=stats.total_passed,
        dedup_rate=stats.dedup_rate,
        active_fingerprints=stats.active_fingerprints,
    )


@router.get("/deduplication/stats/enhanced", response_model=DeduplicationStatsEnhanced)
async def get_deduplication_stats_enhanced(
    session: AsyncSession = Depends(get_session),
    start_time: datetime | None = Query(
        default=None,
        description="Start of time range filter (inclusive)",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of time range filter (exclusive)",
    ),
    use_cache: bool = Query(
        default=True,
        description="Whether to use cached results",
    ),
    cache_ttl_seconds: int = Query(
        default=30,
        ge=1,
        le=3600,
        description="Cache TTL in seconds",
    ),
) -> DeduplicationStatsEnhanced:
    """Get enhanced deduplication statistics with config aggregates and caching info.

    This endpoint combines:
    - Runtime metrics (from in-memory collector)
    - Config aggregates (from database with efficient GROUP BY queries)
    - Cache information and time range filter
    """
    # Build time range filter
    time_range = None
    if start_time or end_time:
        time_range = TimeRange(start_time=start_time, end_time=end_time)

    # Get runtime metrics
    runtime_stats = await _dedup_metrics.get_stats()

    # Get config aggregates from database
    aggregator = StatsAggregator(session, cache_ttl_seconds=cache_ttl_seconds)
    db_stats = await aggregator.get_deduplication_stats(
        time_range=time_range,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )

    # Build response
    time_range_filter = None
    if time_range:
        time_range_filter = TimeRangeFilter(
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        )

    cache_info = CacheInfo(
        cached=db_stats.cached,
        cached_at=db_stats.cached_at,
        ttl_seconds=cache_ttl_seconds if use_cache else None,
    )

    return DeduplicationStatsEnhanced(
        # Runtime metrics
        total_received=runtime_stats.total_received,
        total_deduplicated=runtime_stats.total_deduplicated,
        total_passed=runtime_stats.total_passed,
        dedup_rate=runtime_stats.dedup_rate,
        active_fingerprints=runtime_stats.active_fingerprints,
        # Config aggregates
        total_configs=db_stats.total_configs,
        active_configs=db_stats.active_configs,
        by_strategy=db_stats.by_strategy,
        by_policy=db_stats.by_policy,
        avg_window_seconds=db_stats.avg_window_seconds,
        time_range=time_range_filter,
        cache_info=cache_info,
    )


# =============================================================================
# Throttling Endpoints
# =============================================================================


@router.get("/throttling/configs", response_model=ThrottlingConfigListResponse)
async def list_throttling_configs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    channel_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigListResponse:
    """List throttling configurations."""
    query = select(ThrottlingConfig).order_by(ThrottlingConfig.created_at.desc())

    if active_only:
        query = query.where(ThrottlingConfig.is_active == True)
    if channel_id is not None:
        query = query.where(ThrottlingConfig.channel_id == channel_id)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    configs = result.scalars().all()

    return ThrottlingConfigListResponse(
        items=[_throttle_config_to_response(c) for c in configs],
        total=len(configs),
        offset=offset,
        limit=limit,
    )


@router.post("/throttling/configs", response_model=ThrottlingConfigResponse)
async def create_throttling_config(
    request: ThrottlingConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Create a new throttling configuration."""
    config = ThrottlingConfig(
        name=request.name,
        per_minute=request.per_minute,
        per_hour=request.per_hour,
        per_day=request.per_day,
        burst_allowance=request.burst_allowance,
        channel_id=request.channel_id,
        is_active=request.is_active,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    return _throttle_config_to_response(config)


@router.get("/throttling/configs/{config_id}", response_model=ThrottlingConfigResponse)
async def get_throttling_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Get a throttling config by ID."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    return _throttle_config_to_response(config)


@router.put("/throttling/configs/{config_id}", response_model=ThrottlingConfigResponse)
async def update_throttling_config(
    config_id: str,
    request: ThrottlingConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> ThrottlingConfigResponse:
    """Update a throttling config."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    if request.name is not None:
        config.name = request.name
    if request.per_minute is not None:
        config.per_minute = request.per_minute
    if request.per_hour is not None:
        config.per_hour = request.per_hour
    if request.per_day is not None:
        config.per_day = request.per_day
    if request.burst_allowance is not None:
        config.burst_allowance = request.burst_allowance
    if request.channel_id is not None:
        config.channel_id = request.channel_id
    if request.is_active is not None:
        config.is_active = request.is_active

    await session.commit()
    await session.refresh(config)

    return _throttle_config_to_response(config)


@router.delete("/throttling/configs/{config_id}")
async def delete_throttling_config(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a throttling config."""
    result = await session.execute(
        select(ThrottlingConfig).where(ThrottlingConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(status_code=404, detail="Throttling config not found")

    await session.delete(config)
    await session.commit()

    return {"success": True, "message": "Throttling config deleted"}


@router.get("/throttling/stats", response_model=ThrottlingStats)
async def get_throttling_stats(
    session: AsyncSession = Depends(get_session),
) -> ThrottlingStats:
    """Get throttling statistics (runtime metrics)."""
    stats = await _throttle_metrics.get_stats()
    return ThrottlingStats(
        total_received=stats.total_received,
        total_throttled=stats.total_throttled,
        total_passed=stats.total_passed,
        throttle_rate=stats.throttle_rate,
        current_window_count=stats.current_window_count,
    )


@router.get("/throttling/stats/enhanced", response_model=ThrottlingStatsEnhanced)
async def get_throttling_stats_enhanced(
    session: AsyncSession = Depends(get_session),
    start_time: datetime | None = Query(
        default=None,
        description="Start of time range filter (inclusive)",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of time range filter (exclusive)",
    ),
    use_cache: bool = Query(
        default=True,
        description="Whether to use cached results",
    ),
    cache_ttl_seconds: int = Query(
        default=30,
        ge=1,
        le=3600,
        description="Cache TTL in seconds",
    ),
) -> ThrottlingStatsEnhanced:
    """Get enhanced throttling statistics with config aggregates and caching info.

    This endpoint combines:
    - Runtime metrics (from in-memory collector)
    - Config aggregates (from database with efficient GROUP BY queries)
    - Cache information and time range filter
    """
    # Build time range filter
    time_range = None
    if start_time or end_time:
        time_range = TimeRange(start_time=start_time, end_time=end_time)

    # Get runtime metrics
    runtime_stats = await _throttle_metrics.get_stats()

    # Get config aggregates from database
    aggregator = StatsAggregator(session, cache_ttl_seconds=cache_ttl_seconds)
    db_stats = await aggregator.get_throttling_stats(
        time_range=time_range,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )

    # Build response
    time_range_filter = None
    if time_range:
        time_range_filter = TimeRangeFilter(
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        )

    cache_info = CacheInfo(
        cached=db_stats.cached,
        cached_at=db_stats.cached_at,
        ttl_seconds=cache_ttl_seconds if use_cache else None,
    )

    return ThrottlingStatsEnhanced(
        # Runtime metrics
        total_received=runtime_stats.total_received,
        total_throttled=runtime_stats.total_throttled,
        total_passed=runtime_stats.total_passed,
        throttle_rate=runtime_stats.throttle_rate,
        current_window_count=runtime_stats.current_window_count,
        # Config aggregates
        total_configs=db_stats.total_configs,
        active_configs=db_stats.active_configs,
        configs_with_per_minute=db_stats.configs_with_per_minute,
        configs_with_per_hour=db_stats.configs_with_per_hour,
        configs_with_per_day=db_stats.configs_with_per_day,
        avg_burst_allowance=db_stats.avg_burst_allowance,
        time_range=time_range_filter,
        cache_info=cache_info,
    )


# =============================================================================
# Escalation Policy Endpoints
# =============================================================================


@router.get("/escalation/policies", response_model=EscalationPolicyListResponse)
async def list_escalation_policies(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    active_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyListResponse:
    """List escalation policies."""
    query = select(EscalationPolicyModel).order_by(
        EscalationPolicyModel.created_at.desc()
    )

    if active_only:
        query = query.where(EscalationPolicyModel.is_active == True)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    policies = result.scalars().all()

    return EscalationPolicyListResponse(
        items=[_escalation_policy_to_response(p) for p in policies],
        total=len(policies),
        offset=offset,
        limit=limit,
    )


@router.post("/escalation/policies", response_model=EscalationPolicyResponse)
async def create_escalation_policy(
    request: EscalationPolicyCreate,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Create a new escalation policy."""
    # Convert levels to dict format
    levels = [level.model_dump() for level in request.levels]

    policy = EscalationPolicyModel(
        name=request.name,
        description=request.description,
        levels=levels,
        auto_resolve_on_success=request.auto_resolve_on_success,
        max_escalations=request.max_escalations,
        is_active=request.is_active,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)

    return _escalation_policy_to_response(policy)


@router.get("/escalation/policies/{policy_id}", response_model=EscalationPolicyResponse)
async def get_escalation_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Get an escalation policy by ID."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    return _escalation_policy_to_response(policy)


@router.put("/escalation/policies/{policy_id}", response_model=EscalationPolicyResponse)
async def update_escalation_policy(
    policy_id: str,
    request: EscalationPolicyUpdate,
    session: AsyncSession = Depends(get_session),
) -> EscalationPolicyResponse:
    """Update an escalation policy."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    if request.name is not None:
        policy.name = request.name
    if request.description is not None:
        policy.description = request.description
    if request.levels is not None:
        policy.levels = [level.model_dump() for level in request.levels]
    if request.auto_resolve_on_success is not None:
        policy.auto_resolve_on_success = request.auto_resolve_on_success
    if request.max_escalations is not None:
        policy.max_escalations = request.max_escalations
    if request.is_active is not None:
        policy.is_active = request.is_active

    await session.commit()
    await session.refresh(policy)

    return _escalation_policy_to_response(policy)


@router.delete("/escalation/policies/{policy_id}")
async def delete_escalation_policy(
    policy_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete an escalation policy."""
    result = await session.execute(
        select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy_id)
    )
    policy = result.scalar_one_or_none()

    if policy is None:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    await session.delete(policy)
    await session.commit()

    return {"success": True, "message": "Escalation policy deleted"}


# =============================================================================
# Escalation Incident Endpoints
# =============================================================================


@router.get("/escalation/incidents", response_model=EscalationIncidentListResponse)
async def list_escalation_incidents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    policy_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentListResponse:
    """List escalation incidents."""
    query = select(EscalationIncidentModel).order_by(
        EscalationIncidentModel.created_at.desc()
    )

    if policy_id is not None:
        query = query.where(EscalationIncidentModel.policy_id == policy_id)
    if state is not None:
        query = query.where(EscalationIncidentModel.state == state)

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    incidents = result.scalars().all()

    return EscalationIncidentListResponse(
        items=[_escalation_incident_to_response(i) for i in incidents],
        total=len(incidents),
        offset=offset,
        limit=limit,
    )


@router.get("/escalation/incidents/active", response_model=EscalationIncidentListResponse)
async def list_active_incidents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentListResponse:
    """List active (non-resolved) escalation incidents."""
    query = (
        select(EscalationIncidentModel)
        .where(EscalationIncidentModel.state != EscalationStateEnum.RESOLVED.value)
        .order_by(EscalationIncidentModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    incidents = result.scalars().all()

    return EscalationIncidentListResponse(
        items=[_escalation_incident_to_response(i) for i in incidents],
        total=len(incidents),
        offset=offset,
        limit=limit,
    )


@router.get("/escalation/incidents/{incident_id}", response_model=EscalationIncidentResponse)
async def get_escalation_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Get an escalation incident by ID."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    return _escalation_incident_to_response(incident)


@router.post("/escalation/incidents/{incident_id}/acknowledge", response_model=EscalationIncidentResponse)
async def acknowledge_incident(
    incident_id: str,
    request: AcknowledgeRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Acknowledge an escalation incident."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    if incident.state == EscalationStateEnum.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Cannot acknowledge resolved incident")

    if incident.state == EscalationStateEnum.ACKNOWLEDGED.value:
        raise HTTPException(status_code=400, detail="Incident already acknowledged")

    # Record state transition
    old_state = incident.state
    incident.state = EscalationStateEnum.ACKNOWLEDGED.value
    incident.acknowledged_by = request.actor
    incident.acknowledged_at = datetime.utcnow()
    incident.add_event(
        from_state=old_state,
        to_state=EscalationStateEnum.ACKNOWLEDGED.value,
        actor=request.actor,
        message=request.message or f"Acknowledged by {request.actor}",
    )

    await session.commit()
    await session.refresh(incident)

    # Broadcast WebSocket event for real-time updates
    background_tasks.add_task(
        _broadcast_incident_state_change,
        incident_id=incident.id,
        incident_ref=incident.incident_ref,
        policy_id=incident.policy_id,
        from_state=old_state,
        to_state=EscalationStateEnum.ACKNOWLEDGED.value,
        current_level=incident.current_level,
        actor=request.actor,
        message=request.message or f"Acknowledged by {request.actor}",
    )

    return _escalation_incident_to_response(incident)


@router.post("/escalation/incidents/{incident_id}/resolve", response_model=EscalationIncidentResponse)
async def resolve_incident(
    incident_id: str,
    request: ResolveRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> EscalationIncidentResponse:
    """Resolve an escalation incident."""
    result = await session.execute(
        select(EscalationIncidentModel).where(EscalationIncidentModel.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Escalation incident not found")

    if incident.state == EscalationStateEnum.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Incident already resolved")

    # Record state transition
    old_state = incident.state
    incident.state = EscalationStateEnum.RESOLVED.value
    incident.resolved_by = request.actor
    incident.resolved_at = datetime.utcnow()
    incident.next_escalation_at = None

    actor_msg = request.actor or "system"
    incident.add_event(
        from_state=old_state,
        to_state=EscalationStateEnum.RESOLVED.value,
        actor=request.actor,
        message=request.message or f"Resolved by {actor_msg}",
    )

    await session.commit()
    await session.refresh(incident)

    # Broadcast WebSocket event for real-time updates
    background_tasks.add_task(
        _broadcast_incident_state_change,
        incident_id=incident.id,
        incident_ref=incident.incident_ref,
        policy_id=incident.policy_id,
        from_state=old_state,
        to_state=EscalationStateEnum.RESOLVED.value,
        current_level=incident.current_level,
        actor=request.actor,
        message=request.message or f"Resolved by {actor_msg}",
    )

    return _escalation_incident_to_response(incident)


@router.get("/escalation/stats", response_model=EscalationStats)
async def get_escalation_stats(
    session: AsyncSession = Depends(get_session),
    start_time: datetime | None = Query(
        default=None,
        description="Start of time range filter (inclusive)",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of time range filter (exclusive)",
    ),
    use_cache: bool = Query(
        default=True,
        description="Whether to use cached results",
    ),
    cache_ttl_seconds: int | None = Query(
        default=None,
        ge=1,
        le=3600,
        description="Cache TTL override in seconds",
    ),
) -> EscalationStats:
    """Get escalation statistics.

    Uses efficient aggregate queries with optional caching and time-range filtering.
    """
    # Build time range filter
    time_range = None
    if start_time or end_time:
        time_range = TimeRange(start_time=start_time, end_time=end_time)

    # Use StatsAggregator for efficient queries
    aggregator = StatsAggregator(session, cache_ttl_seconds=cache_ttl_seconds or 30)
    db_stats = await aggregator.get_escalation_stats(
        time_range=time_range,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )

    # Also get avg_resolution_time from metrics collector for real-time data
    metrics_stats = await _escalation_metrics.get_stats()
    avg_resolution_time_minutes = None

    # Prefer database resolution time if available, otherwise use metrics
    if db_stats.avg_resolution_time_seconds is not None:
        avg_resolution_time_minutes = db_stats.avg_resolution_time_seconds / 60.0
    elif metrics_stats.avg_resolution_time > 0:
        avg_resolution_time_minutes = metrics_stats.avg_resolution_time / 60.0

    return EscalationStats(
        total_incidents=db_stats.total_incidents,
        by_state=db_stats.by_state,
        active_count=db_stats.active_count,
        total_policies=db_stats.total_policies,
        avg_resolution_time_minutes=avg_resolution_time_minutes,
    )


@router.get("/escalation/stats/enhanced", response_model=EscalationStatsEnhanced)
async def get_escalation_stats_enhanced(
    session: AsyncSession = Depends(get_session),
    start_time: datetime | None = Query(
        default=None,
        description="Start of time range filter (inclusive)",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of time range filter (exclusive)",
    ),
    use_cache: bool = Query(
        default=True,
        description="Whether to use cached results",
    ),
    cache_ttl_seconds: int = Query(
        default=30,
        ge=1,
        le=3600,
        description="Cache TTL in seconds",
    ),
) -> EscalationStatsEnhanced:
    """Get enhanced escalation statistics with time range and caching info.

    This endpoint provides additional metadata including:
    - Time range filter applied
    - Cache information (hit/miss, cached_at, ttl)
    """
    # Build time range filter
    time_range = None
    if start_time or end_time:
        time_range = TimeRange(start_time=start_time, end_time=end_time)

    # Use StatsAggregator for efficient queries
    aggregator = StatsAggregator(session, cache_ttl_seconds=cache_ttl_seconds)
    db_stats = await aggregator.get_escalation_stats(
        time_range=time_range,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )

    # Get avg_resolution_time
    avg_resolution_time_minutes = None
    if db_stats.avg_resolution_time_seconds is not None:
        avg_resolution_time_minutes = db_stats.avg_resolution_time_seconds / 60.0
    else:
        # Fallback to metrics collector
        metrics_stats = await _escalation_metrics.get_stats()
        if metrics_stats.avg_resolution_time > 0:
            avg_resolution_time_minutes = metrics_stats.avg_resolution_time / 60.0

    # Build response
    time_range_filter = None
    if time_range:
        time_range_filter = TimeRangeFilter(
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        )

    cache_info = CacheInfo(
        cached=db_stats.cached,
        cached_at=db_stats.cached_at,
        ttl_seconds=cache_ttl_seconds if use_cache else None,
    )

    return EscalationStatsEnhanced(
        total_incidents=db_stats.total_incidents,
        by_state=db_stats.by_state,
        active_count=db_stats.active_count,
        total_policies=db_stats.total_policies,
        avg_resolution_time_minutes=avg_resolution_time_minutes,
        time_range=time_range_filter,
        cache_info=cache_info,
    )


# =============================================================================
# Escalation Scheduler Endpoints
# =============================================================================


def _get_scheduler_service() -> Any:
    """Get the escalation scheduler service.

    Returns:
        EscalationSchedulerService instance.
    """
    from ..core.notifications.escalation.scheduler import get_escalation_scheduler
    return get_escalation_scheduler()


@router.get("/escalation/scheduler/status", response_model=EscalationSchedulerStatus)
async def get_scheduler_status() -> EscalationSchedulerStatus:
    """Get the current status of the escalation scheduler.

    Returns scheduler running state, configuration, and metrics.
    """
    scheduler = _get_scheduler_service()
    status = scheduler.get_status()

    return EscalationSchedulerStatus(
        running=status["running"],
        enabled=status["enabled"],
        check_interval_seconds=status["check_interval_seconds"],
        last_check_at=status["last_check_at"],
        next_check_at=status["next_check_at"],
        check_count=status["check_count"],
        escalation_count=status["escalation_count"],
        error_count=status["error_count"],
        handlers=status["handlers"],
        strategy=status["strategy"],
    )


@router.post("/escalation/scheduler/start", response_model=EscalationSchedulerAction)
async def start_scheduler() -> EscalationSchedulerAction:
    """Start the escalation scheduler.

    Begins periodic checking for pending escalations.
    """
    scheduler = _get_scheduler_service()

    if scheduler.is_running:
        return EscalationSchedulerAction(
            success=False,
            message="Scheduler is already running",
            action="start",
            timestamp=datetime.utcnow().isoformat(),
        )

    await scheduler.start()

    return EscalationSchedulerAction(
        success=True,
        message="Escalation scheduler started",
        action="start",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/escalation/scheduler/stop", response_model=EscalationSchedulerAction)
async def stop_scheduler() -> EscalationSchedulerAction:
    """Stop the escalation scheduler.

    Stops periodic checking for pending escalations.
    """
    scheduler = _get_scheduler_service()

    if not scheduler.is_running:
        return EscalationSchedulerAction(
            success=False,
            message="Scheduler is not running",
            action="stop",
            timestamp=datetime.utcnow().isoformat(),
        )

    await scheduler.stop()

    return EscalationSchedulerAction(
        success=True,
        message="Escalation scheduler stopped",
        action="stop",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/escalation/scheduler/trigger", response_model=TriggerCheckResponse)
async def trigger_check() -> TriggerCheckResponse:
    """Trigger an immediate escalation check.

    Manually triggers the escalation checker without waiting for
    the scheduled interval.
    """
    scheduler = _get_scheduler_service()

    if not scheduler.is_running:
        return TriggerCheckResponse(
            success=False,
            message="Scheduler is not running",
            escalations_processed=0,
            timestamp=datetime.utcnow().isoformat(),
        )

    result = await scheduler.trigger_immediate_check()

    return TriggerCheckResponse(
        success=result["success"],
        message=result["message"],
        escalations_processed=result.get("escalations_processed", 0),
        timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
    )


@router.put("/escalation/scheduler/config", response_model=EscalationSchedulerStatus)
async def update_scheduler_config(
    request: EscalationSchedulerConfigRequest,
) -> EscalationSchedulerStatus:
    """Update escalation scheduler configuration.

    Note: Some changes may require a scheduler restart to take effect.
    """
    scheduler = _get_scheduler_service()

    # Update config
    if request.check_interval_seconds is not None:
        scheduler.config.check_interval_seconds = request.check_interval_seconds

    if request.max_escalations_per_check is not None:
        scheduler.config.max_escalations_per_check = request.max_escalations_per_check

    if request.enabled is not None:
        scheduler.config.enabled = request.enabled
        # If disabling, stop the scheduler
        if not request.enabled and scheduler.is_running:
            await scheduler.stop()

    # Return updated status
    status = scheduler.get_status()

    return EscalationSchedulerStatus(
        running=status["running"],
        enabled=status["enabled"],
        check_interval_seconds=status["check_interval_seconds"],
        last_check_at=status["last_check_at"],
        next_check_at=status["next_check_at"],
        check_count=status["check_count"],
        escalation_count=status["escalation_count"],
        error_count=status["error_count"],
        handlers=status["handlers"],
        strategy=status["strategy"],
    )


@router.post("/escalation/scheduler/reset-metrics", response_model=EscalationSchedulerAction)
async def reset_scheduler_metrics() -> EscalationSchedulerAction:
    """Reset escalation scheduler metrics.

    Resets counters for checks, escalations, and errors.
    """
    scheduler = _get_scheduler_service()
    scheduler.reset_metrics()

    return EscalationSchedulerAction(
        success=True,
        message="Scheduler metrics reset",
        action="reset-metrics",
        timestamp=datetime.utcnow().isoformat(),
    )


# =============================================================================
# Config Import/Export Endpoints
# =============================================================================


@router.get("/config/export", response_model=NotificationConfigBundle)
async def export_notification_config(
    include_routing_rules: bool = Query(default=True, description="Include routing rules"),
    include_deduplication: bool = Query(default=True, description="Include deduplication configs"),
    include_throttling: bool = Query(default=True, description="Include throttling configs"),
    include_escalation: bool = Query(default=True, description="Include escalation policies"),
    session: AsyncSession = Depends(get_session),
) -> NotificationConfigBundle:
    """Export all notification configurations as a portable bundle.

    Returns a JSON bundle containing all notification configurations that can
    be saved to a file and later imported to restore settings.

    Args:
        include_routing_rules: Include routing rules in export.
        include_deduplication: Include deduplication configs in export.
        include_throttling: Include throttling configs in export.
        include_escalation: Include escalation policies in export.

    Returns:
        NotificationConfigBundle with all requested configurations.
    """
    bundle = NotificationConfigBundle(
        version="1.0",
        exported_at=datetime.utcnow(),
        routing_rules=[],
        deduplication_configs=[],
        throttling_configs=[],
        escalation_policies=[],
    )

    # Export routing rules
    if include_routing_rules:
        result = await session.execute(
            select(RoutingRuleModel).order_by(RoutingRuleModel.priority.desc())
        )
        rules = result.scalars().all()
        bundle.routing_rules = [_routing_rule_to_response(r) for r in rules]

    # Export deduplication configs
    if include_deduplication:
        result = await session.execute(
            select(DeduplicationConfig).order_by(DeduplicationConfig.created_at.desc())
        )
        configs = result.scalars().all()
        bundle.deduplication_configs = [_dedup_config_to_response(c) for c in configs]

    # Export throttling configs
    if include_throttling:
        result = await session.execute(
            select(ThrottlingConfig).order_by(ThrottlingConfig.created_at.desc())
        )
        configs = result.scalars().all()
        bundle.throttling_configs = [_throttle_config_to_response(c) for c in configs]

    # Export escalation policies
    if include_escalation:
        result = await session.execute(
            select(EscalationPolicyModel).order_by(EscalationPolicyModel.created_at.desc())
        )
        policies = result.scalars().all()
        bundle.escalation_policies = [_escalation_policy_to_response(p) for p in policies]

    logger.info(
        f"Exported notification config: {len(bundle.routing_rules)} rules, "
        f"{len(bundle.deduplication_configs)} dedup configs, "
        f"{len(bundle.throttling_configs)} throttle configs, "
        f"{len(bundle.escalation_policies)} escalation policies"
    )

    return bundle


@router.post("/config/import/preview", response_model=ConfigImportPreview)
async def preview_notification_config_import(
    bundle: NotificationConfigBundle,
    session: AsyncSession = Depends(get_session),
) -> ConfigImportPreview:
    """Preview import operation to detect conflicts before execution.

    Analyzes the configuration bundle and detects any conflicts with
    existing configurations based on ID matching.

    Args:
        bundle: The configuration bundle to analyze.

    Returns:
        ConfigImportPreview with conflict information and counts.
    """
    conflicts: list[ConfigImportConflict] = []
    total_configs = (
        len(bundle.routing_rules)
        + len(bundle.deduplication_configs)
        + len(bundle.throttling_configs)
        + len(bundle.escalation_policies)
    )

    # Check routing rules for conflicts
    for rule in bundle.routing_rules:
        result = await session.execute(
            select(RoutingRuleModel).where(RoutingRuleModel.id == rule.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            conflicts.append(
                ConfigImportConflict(
                    config_type="routing_rule",
                    config_id=rule.id,
                    config_name=rule.name,
                    existing_name=existing.name,
                    suggested_action="skip",
                )
            )

    # Check deduplication configs for conflicts
    for config in bundle.deduplication_configs:
        result = await session.execute(
            select(DeduplicationConfig).where(DeduplicationConfig.id == config.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            conflicts.append(
                ConfigImportConflict(
                    config_type="deduplication",
                    config_id=config.id,
                    config_name=config.name,
                    existing_name=existing.name,
                    suggested_action="skip",
                )
            )

    # Check throttling configs for conflicts
    for config in bundle.throttling_configs:
        result = await session.execute(
            select(ThrottlingConfig).where(ThrottlingConfig.id == config.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            conflicts.append(
                ConfigImportConflict(
                    config_type="throttling",
                    config_id=config.id,
                    config_name=config.name,
                    existing_name=existing.name,
                    suggested_action="skip",
                )
            )

    # Check escalation policies for conflicts
    for policy in bundle.escalation_policies:
        result = await session.execute(
            select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            conflicts.append(
                ConfigImportConflict(
                    config_type="escalation",
                    config_id=policy.id,
                    config_name=policy.name,
                    existing_name=existing.name,
                    suggested_action="skip",
                )
            )

    new_configs = total_configs - len(conflicts)

    return ConfigImportPreview(
        total_configs=total_configs,
        new_configs=new_configs,
        conflicts=conflicts,
        routing_rules_count=len(bundle.routing_rules),
        deduplication_configs_count=len(bundle.deduplication_configs),
        throttling_configs_count=len(bundle.throttling_configs),
        escalation_policies_count=len(bundle.escalation_policies),
    )


@router.post("/config/import", response_model=ConfigImportResult)
async def import_notification_config(
    request: ConfigImportRequest,
    session: AsyncSession = Depends(get_session),
) -> ConfigImportResult:
    """Import notification configurations from a bundle.

    Imports configurations with conflict resolution based on the specified strategy:
    - skip: Skip configs that already exist (default)
    - overwrite: Replace existing configs with imported ones
    - rename: Create new configs with modified IDs

    Args:
        request: Import request containing the bundle and options.

    Returns:
        ConfigImportResult with summary of the import operation.
    """
    bundle = request.bundle
    conflict_resolution = request.conflict_resolution
    errors: list[str] = []
    created_ids: dict[str, list[str]] = {
        "routing_rules": [],
        "deduplication_configs": [],
        "throttling_configs": [],
        "escalation_policies": [],
    }
    created_count = 0
    skipped_count = 0
    overwritten_count = 0

    try:
        # Import routing rules
        for rule in bundle.routing_rules:
            try:
                result = await session.execute(
                    select(RoutingRuleModel).where(RoutingRuleModel.id == rule.id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if conflict_resolution == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_resolution == "overwrite":
                        existing.name = rule.name
                        existing.rule_config = rule.rule_config
                        existing.actions = rule.actions
                        existing.priority = rule.priority
                        existing.is_active = rule.is_active
                        existing.stop_on_match = rule.stop_on_match
                        existing.routing_metadata = rule.metadata
                        overwritten_count += 1
                        created_ids["routing_rules"].append(rule.id)
                    else:  # rename
                        import uuid
                        new_id = str(uuid.uuid4())
                        new_rule = RoutingRuleModel(
                            id=new_id,
                            name=f"{rule.name} (imported)",
                            rule_config=rule.rule_config,
                            actions=rule.actions,
                            priority=rule.priority,
                            is_active=rule.is_active,
                            stop_on_match=rule.stop_on_match,
                            routing_metadata=rule.metadata,
                        )
                        session.add(new_rule)
                        created_count += 1
                        created_ids["routing_rules"].append(new_id)
                else:
                    new_rule = RoutingRuleModel(
                        id=rule.id,
                        name=rule.name,
                        rule_config=rule.rule_config,
                        actions=rule.actions,
                        priority=rule.priority,
                        is_active=rule.is_active,
                        stop_on_match=rule.stop_on_match,
                        routing_metadata=rule.metadata,
                    )
                    session.add(new_rule)
                    created_count += 1
                    created_ids["routing_rules"].append(rule.id)
            except Exception as e:
                errors.append(f"Failed to import routing rule '{rule.name}': {str(e)}")

        # Import deduplication configs
        for config in bundle.deduplication_configs:
            try:
                result = await session.execute(
                    select(DeduplicationConfig).where(DeduplicationConfig.id == config.id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if conflict_resolution == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_resolution == "overwrite":
                        existing.name = config.name
                        existing.strategy = config.strategy
                        existing.policy = config.policy
                        existing.window_seconds = config.window_seconds
                        existing.is_active = config.is_active
                        overwritten_count += 1
                        created_ids["deduplication_configs"].append(config.id)
                    else:  # rename
                        import uuid
                        new_id = str(uuid.uuid4())
                        new_config = DeduplicationConfig(
                            id=new_id,
                            name=f"{config.name} (imported)",
                            strategy=config.strategy,
                            policy=config.policy,
                            window_seconds=config.window_seconds,
                            is_active=config.is_active,
                        )
                        session.add(new_config)
                        created_count += 1
                        created_ids["deduplication_configs"].append(new_id)
                else:
                    new_config = DeduplicationConfig(
                        id=config.id,
                        name=config.name,
                        strategy=config.strategy,
                        policy=config.policy,
                        window_seconds=config.window_seconds,
                        is_active=config.is_active,
                    )
                    session.add(new_config)
                    created_count += 1
                    created_ids["deduplication_configs"].append(config.id)
            except Exception as e:
                errors.append(f"Failed to import deduplication config '{config.name}': {str(e)}")

        # Import throttling configs
        for config in bundle.throttling_configs:
            try:
                result = await session.execute(
                    select(ThrottlingConfig).where(ThrottlingConfig.id == config.id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if conflict_resolution == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_resolution == "overwrite":
                        existing.name = config.name
                        existing.per_minute = config.per_minute
                        existing.per_hour = config.per_hour
                        existing.per_day = config.per_day
                        existing.burst_allowance = config.burst_allowance
                        existing.channel_id = config.channel_id
                        existing.is_active = config.is_active
                        overwritten_count += 1
                        created_ids["throttling_configs"].append(config.id)
                    else:  # rename
                        import uuid
                        new_id = str(uuid.uuid4())
                        new_config = ThrottlingConfig(
                            id=new_id,
                            name=f"{config.name} (imported)",
                            per_minute=config.per_minute,
                            per_hour=config.per_hour,
                            per_day=config.per_day,
                            burst_allowance=config.burst_allowance,
                            channel_id=config.channel_id,
                            is_active=config.is_active,
                        )
                        session.add(new_config)
                        created_count += 1
                        created_ids["throttling_configs"].append(new_id)
                else:
                    new_config = ThrottlingConfig(
                        id=config.id,
                        name=config.name,
                        per_minute=config.per_minute,
                        per_hour=config.per_hour,
                        per_day=config.per_day,
                        burst_allowance=config.burst_allowance,
                        channel_id=config.channel_id,
                        is_active=config.is_active,
                    )
                    session.add(new_config)
                    created_count += 1
                    created_ids["throttling_configs"].append(config.id)
            except Exception as e:
                errors.append(f"Failed to import throttling config '{config.name}': {str(e)}")

        # Import escalation policies
        for policy in bundle.escalation_policies:
            try:
                result = await session.execute(
                    select(EscalationPolicyModel).where(EscalationPolicyModel.id == policy.id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if conflict_resolution == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_resolution == "overwrite":
                        existing.name = policy.name
                        existing.description = policy.description
                        existing.levels = policy.levels
                        existing.auto_resolve_on_success = policy.auto_resolve_on_success
                        existing.max_escalations = policy.max_escalations
                        existing.is_active = policy.is_active
                        overwritten_count += 1
                        created_ids["escalation_policies"].append(policy.id)
                    else:  # rename
                        import uuid
                        new_id = str(uuid.uuid4())
                        new_policy = EscalationPolicyModel(
                            id=new_id,
                            name=f"{policy.name} (imported)",
                            description=policy.description,
                            levels=policy.levels,
                            auto_resolve_on_success=policy.auto_resolve_on_success,
                            max_escalations=policy.max_escalations,
                            is_active=policy.is_active,
                        )
                        session.add(new_policy)
                        created_count += 1
                        created_ids["escalation_policies"].append(new_id)
                else:
                    new_policy = EscalationPolicyModel(
                        id=policy.id,
                        name=policy.name,
                        description=policy.description,
                        levels=policy.levels,
                        auto_resolve_on_success=policy.auto_resolve_on_success,
                        max_escalations=policy.max_escalations,
                        is_active=policy.is_active,
                    )
                    session.add(new_policy)
                    created_count += 1
                    created_ids["escalation_policies"].append(policy.id)
            except Exception as e:
                errors.append(f"Failed to import escalation policy '{policy.name}': {str(e)}")

        await session.commit()

        logger.info(
            f"Imported notification config: {created_count} created, "
            f"{skipped_count} skipped, {overwritten_count} overwritten, "
            f"{len(errors)} errors"
        )

        return ConfigImportResult(
            success=len(errors) == 0,
            message=f"Import completed: {created_count} created, {skipped_count} skipped, {overwritten_count} overwritten",
            created_count=created_count,
            skipped_count=skipped_count,
            overwritten_count=overwritten_count,
            errors=errors,
            created_ids=created_ids,
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to import notification config: {e}")
        return ConfigImportResult(
            success=False,
            message=f"Import failed: {str(e)}",
            created_count=0,
            skipped_count=0,
            overwritten_count=0,
            errors=[str(e)],
            created_ids={},
        )


# =============================================================================
# Stats Cache Management Endpoints
# =============================================================================


@router.get("/stats/cache", response_model=StatsCacheStatus)
async def get_stats_cache_status() -> StatsCacheStatus:
    """Get stats cache status.

    Returns cache hit rate, entry count, and configuration.
    """
    cache = get_stats_cache()
    stats = await cache.get_stats()

    return StatsCacheStatus(
        total_entries=stats["total_entries"],
        valid_entries=stats["valid_entries"],
        expired_entries=stats["expired_entries"],
        max_entries=stats["max_entries"],
        default_ttl_seconds=stats["default_ttl_seconds"],
        total_hits=stats["total_hits"],
        total_misses=stats["total_misses"],
        hit_rate=stats["hit_rate"],
    )


@router.post("/stats/cache/invalidate")
async def invalidate_stats_cache(
    target: str = Query(
        default="all",
        description="Cache target to invalidate: all, escalation, deduplication, throttling",
    ),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Invalidate stats cache entries.

    Use this endpoint to force fresh database queries on the next stats request.

    Args:
        target: Which cache entries to invalidate
            - all: Invalidate all stats cache entries
            - escalation: Invalidate only escalation stats
            - deduplication: Invalidate only deduplication stats
            - throttling: Invalidate only throttling stats
    """
    aggregator = StatsAggregator(session)

    if target == "all":
        await aggregator.invalidate_all_cache()
        message = "All stats cache entries invalidated"
    elif target == "escalation":
        count = await aggregator.invalidate_escalation_cache()
        message = f"{count} escalation cache entries invalidated"
    elif target == "deduplication":
        count = await aggregator.invalidate_deduplication_cache()
        message = f"{count} deduplication cache entries invalidated"
    elif target == "throttling":
        count = await aggregator.invalidate_throttling_cache()
        message = f"{count} throttling cache entries invalidated"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target: {target}. Must be one of: all, escalation, deduplication, throttling",
        )

    return {
        "success": True,
        "message": message,
        "target": target,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Jinja2 Template Validation Endpoints
# =============================================================================


@router.post("/routing/rules/validate-jinja2")
async def validate_jinja2_template(
    request: dict[str, Any],
) -> dict[str, Any]:
    """Validate a Jinja2 template for use in routing rules.

    This endpoint validates Jinja2 template syntax and optionally
    renders the template with provided sample data.

    Args:
        request: Dictionary containing:
            - template: The Jinja2 template string to validate
            - sample_data: Optional sample event data for rendering preview
            - expected_result: Optional expected result ("true" or "false")

    Returns:
        Dictionary containing:
            - valid: Whether the template is syntactically valid
            - rendered_output: The rendered output if sample_data provided
            - error: Error message if validation failed
            - error_line: Line number where error occurred (if applicable)
    """
    from ..core.notifications.routing.jinja2_engine import Jinja2Engine

    template = request.get("template", "")
    sample_data = request.get("sample_data", {})
    expected_result = request.get("expected_result", "true")

    if not template:
        return {
            "valid": False,
            "error": "Template cannot be empty",
            "rendered_output": None,
            "error_line": None,
        }

    try:
        # Create Jinja2 engine instance
        engine = Jinja2Engine()

        # Validate template syntax by compiling it
        compiled = engine.compile_template(template)

        result: dict[str, Any] = {
            "valid": True,
            "error": None,
            "error_line": None,
            "rendered_output": None,
        }

        # If sample data provided, render the template
        if sample_data:
            try:
                rendered = engine.render(template, sample_data)
                result["rendered_output"] = str(rendered)

                # Check if output matches expected result
                if expected_result:
                    rendered_lower = str(rendered).lower().strip()
                    expected_lower = expected_result.lower().strip()
                    result["matches_expected"] = rendered_lower == expected_lower

            except Exception as render_error:
                # Template is valid but rendering failed with given data
                result["rendered_output"] = None
                result["render_error"] = str(render_error)

        return result

    except Exception as e:
        error_msg = str(e)
        error_line = None

        # Try to extract line number from Jinja2 error
        if "line" in error_msg.lower():
            import re

            line_match = re.search(r"line\s+(\d+)", error_msg, re.IGNORECASE)
            if line_match:
                error_line = int(line_match.group(1))

        return {
            "valid": False,
            "error": error_msg,
            "error_line": error_line,
            "rendered_output": None,
        }

