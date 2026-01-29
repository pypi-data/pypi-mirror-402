"""API router configuration.

This module configures the main API router and includes all sub-routers.
"""

from fastapi import APIRouter

from . import (
    # Phase 1-4
    alerts,
    drift,
    health,
    history,
    maintenance,
    mask,
    notifications,
    notifications_advanced,
    profile,
    reports,
    rules,
    scan,
    schedules,
    schemas,
    sources,
    triggers,
    validations,
    validators,
    versioning,
    websocket,
    # Phase 5
    catalog,
    collaboration,
    glossary,
    # Schema Evolution & Rule Suggestions
    rule_suggestions,
    schema_evolution,
    # Phase 9: Plugin System
    plugins,
    # Phase 10: ML & Lineage
    anomaly,
    lineage,
    model_monitoring,
    # Cross-Feature Integration
    cross_alerts,
)

api_router = APIRouter()

# Health endpoints (no prefix)
api_router.include_router(
    health.router,
    tags=["health"],
)

# Source management
api_router.include_router(
    sources.router,
    prefix="/sources",
    tags=["sources"],
)

# Schema management
api_router.include_router(
    schemas.router,
    tags=["schemas"],
)

# Rules management
api_router.include_router(
    rules.router,
    tags=["rules"],
)

# Validation endpoints
api_router.include_router(
    validations.router,
    prefix="/validations",
    tags=["validations"],
)

# Validator registry endpoints
api_router.include_router(
    validators.router,
    tags=["validators"],
)

# Profiling endpoints
api_router.include_router(
    profile.router,
    tags=["profiling"],
)

# History endpoints (Phase 2)
api_router.include_router(
    history.router,
    tags=["history"],
)

# Drift detection endpoints (Phase 2)
api_router.include_router(
    drift.router,
    tags=["drift"],
)

# PII scan endpoints
api_router.include_router(
    scan.router,
    prefix="/scans",
    tags=["pii-scan"],
)

# Data masking endpoints
api_router.include_router(
    mask.router,
    tags=["masks"],
)

# Schedule management endpoints (Phase 2)
api_router.include_router(
    schedules.router,
    tags=["schedules"],
)

# Notification management endpoints (Phase 3)
api_router.include_router(
    notifications.router,
    tags=["notifications"],
)

# =============================================================================
# Phase 5: Business Glossary & Data Catalog
# =============================================================================

# Glossary management endpoints
api_router.include_router(
    glossary.router,
    prefix="/glossary",
    tags=["glossary"],
)

# Catalog management endpoints
api_router.include_router(
    catalog.router,
    prefix="/catalog",
    tags=["catalog"],
)

# Collaboration endpoints (comments, activities)
api_router.include_router(
    collaboration.router,
    tags=["collaboration"],
)

# =============================================================================
# Phase 4: Reports & Maintenance & Versioning
# =============================================================================

# Report generation endpoints
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
)

# Maintenance and retention policy endpoints
api_router.include_router(
    maintenance.router,
    prefix="/maintenance",
    tags=["maintenance"],
)

# Versioning endpoints
api_router.include_router(
    versioning.router,
    tags=["versioning"],
)

# =============================================================================
# Schema Evolution & Rule Suggestions
# =============================================================================

# Schema evolution endpoints
api_router.include_router(
    schema_evolution.router,
    tags=["schema-evolution"],
)

# Rule suggestion endpoints
api_router.include_router(
    rule_suggestions.router,
    tags=["rule-suggestions"],
)

# Rule suggestion presets endpoint
api_router.include_router(
    rule_suggestions.presets_router,
    tags=["rule-suggestions"],
)

# =============================================================================
# Phase 14: Advanced Notifications
# =============================================================================

# Advanced notification endpoints (routing, deduplication, throttling, escalation)
api_router.include_router(
    notifications_advanced.router,
    tags=["notifications-advanced"],
)

# =============================================================================
# Phase 10: ML & Lineage
# =============================================================================

# Data lineage endpoints
api_router.include_router(
    lineage.router,
    prefix="/lineage",
    tags=["lineage"],
)

# Anomaly detection endpoints
api_router.include_router(
    anomaly.router,
    tags=["anomaly"],
)

# ML Model Monitoring endpoints
api_router.include_router(
    model_monitoring.router,
    tags=["model-monitoring"],
)

# =============================================================================
# Unified Alerts
# =============================================================================

# Unified alerts aggregation endpoints
api_router.include_router(
    alerts.router,
    tags=["alerts"],
)

# =============================================================================
# Cross-Feature Integration
# =============================================================================

# Cross-alert correlation endpoints (anomaly + drift)
api_router.include_router(
    cross_alerts.router,
    tags=["cross-alerts"],
)

# =============================================================================
# Trigger Monitoring & Webhooks
# =============================================================================

# Trigger monitoring and webhook endpoints
api_router.include_router(
    triggers.router,
    tags=["triggers"],
)

# =============================================================================
# WebSocket Real-time Updates
# =============================================================================

# WebSocket endpoints for real-time updates
api_router.include_router(
    websocket.router,
    tags=["websocket"],
)

# =============================================================================
# Phase 9: Plugin System
# =============================================================================

# Plugin marketplace and custom validators/reporters
api_router.include_router(
    plugins.router,
    tags=["plugins"],
)
