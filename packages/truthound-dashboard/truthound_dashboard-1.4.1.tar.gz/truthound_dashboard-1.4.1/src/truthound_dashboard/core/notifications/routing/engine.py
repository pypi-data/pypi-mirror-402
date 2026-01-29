"""Routing engine for notification dispatch.

This module provides the core routing engine that evaluates events
against configured routes and determines target channels.

Components:
    - RouteContext: Holds event data and metadata for rule evaluation
    - Route: Defines a route with rule, actions, and priority
    - RoutingResult: Result of route matching
    - ActionRouter: Main routing engine

Example:
    # Create routes
    routes = [
        Route(
            name="critical_alerts",
            rule=SeverityRule(min_severity="critical"),
            actions=["pagerduty-channel"],
            priority=100,
        ),
        Route(
            name="default",
            rule=AlwaysRule(),
            actions=["slack-channel"],
            priority=0,
        ),
    ]

    # Create router
    router = ActionRouter(routes=routes)

    # Match event
    context = RouteContext(event=validation_event)
    result = await router.match(context)

    for route in result.matched_routes:
        print(f"Matched: {route.name} -> {route.actions}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .rules import BaseRule

if TYPE_CHECKING:
    from truthound_dashboard.core.notifications.base import NotificationEvent


@dataclass
class RouteContext:
    """Context for route evaluation.

    Holds the event data and additional metadata that rules
    can use to make matching decisions.

    Attributes:
        event: The notification event being routed.
        metadata: Additional context metadata.
        timestamp: When routing is being evaluated.
    """

    event: "NotificationEvent"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_severity(self) -> str | None:
        """Get event severity if available."""
        # Try event data first
        if hasattr(self.event, "severity"):
            return self.event.severity
        if hasattr(self.event, "has_critical") and self.event.has_critical:
            return "critical"
        if hasattr(self.event, "has_high") and self.event.has_high:
            return "high"

        # Try metadata
        return self.metadata.get("severity")

    def get_issue_count(self) -> int | None:
        """Get issue count if available."""
        if hasattr(self.event, "total_issues"):
            return self.event.total_issues
        return self.metadata.get("issue_count")

    def get_pass_rate(self) -> float | None:
        """Get validation pass rate if available."""
        if hasattr(self.event, "pass_rate"):
            return self.event.pass_rate
        return self.metadata.get("pass_rate")

    def get_tags(self) -> list[str]:
        """Get context tags."""
        tags = list(self.metadata.get("tags", []))

        # Add event-derived tags
        if self.event.source_name:
            tags.append(f"source:{self.event.source_name}")
        if self.event.event_type:
            tags.append(f"type:{self.event.event_type}")

        return tags

    def get_data_asset(self) -> str | None:
        """Get data asset name/path."""
        if self.event.source_name:
            return self.event.source_name
        return self.metadata.get("data_asset")

    def get_metadata(self, key: str) -> Any:
        """Get metadata value by key."""
        # Check event data first
        if hasattr(self.event, "data") and key in self.event.data:
            return self.event.data[key]
        return self.metadata.get(key)

    def get_status(self) -> str | None:
        """Get validation status."""
        if hasattr(self.event, "status"):
            return self.event.status
        # Infer from event type
        if self.event.event_type in ("validation_failed", "schedule_failed"):
            return "failure"
        return self.metadata.get("status")

    def get_error_message(self) -> str | None:
        """Get error message if available."""
        if hasattr(self.event, "error_message"):
            return self.event.error_message
        return self.metadata.get("error_message")


@dataclass
class Route:
    """A routing rule with associated actions.

    Attributes:
        name: Unique route name.
        rule: The rule to evaluate.
        actions: List of channel IDs to notify.
        priority: Route priority (higher = evaluated first).
        is_active: Whether route is active.
        escalation_policy_id: Optional escalation policy to trigger.
        stop_on_match: If True, stop evaluating lower priority routes.
        metadata: Additional route metadata.
    """

    name: str
    rule: BaseRule
    actions: list[str]
    priority: int = 0
    is_active: bool = True
    escalation_policy_id: str | None = None
    stop_on_match: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize route to dictionary."""
        return {
            "name": self.name,
            "rule": self.rule.to_dict(),
            "actions": self.actions,
            "priority": self.priority,
            "is_active": self.is_active,
            "escalation_policy_id": self.escalation_policy_id,
            "stop_on_match": self.stop_on_match,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route | None":
        """Create Route from dictionary."""
        rule_data = data.get("rule")
        if not rule_data:
            return None

        rule = BaseRule.from_dict(rule_data)
        if rule is None:
            return None

        return cls(
            name=data.get("name", "unnamed"),
            rule=rule,
            actions=data.get("actions", []),
            priority=data.get("priority", 0),
            is_active=data.get("is_active", True),
            escalation_policy_id=data.get("escalation_policy_id"),
            stop_on_match=data.get("stop_on_match", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RoutingResult:
    """Result of route evaluation.

    Attributes:
        matched_routes: Routes that matched the context.
        all_actions: Deduplicated list of all action channel IDs.
        evaluation_time_ms: Time taken to evaluate routes.
        context: The evaluated context.
    """

    matched_routes: list[Route]
    all_actions: list[str]
    evaluation_time_ms: float
    context: RouteContext

    @property
    def has_matches(self) -> bool:
        """Check if any routes matched."""
        return len(self.matched_routes) > 0


class ActionRouter:
    """Main routing engine.

    Evaluates events against configured routes and returns
    matching routes sorted by priority.

    Routes are evaluated in priority order (highest first).
    If a route has `stop_on_match=True`, lower priority routes
    are skipped once it matches.

    Attributes:
        routes: List of configured routes.
        default_route: Optional fallback route if nothing matches.
    """

    def __init__(
        self,
        routes: list[Route] | None = None,
        default_route: Route | None = None,
    ) -> None:
        """Initialize the router.

        Args:
            routes: List of routes to evaluate.
            default_route: Fallback route if nothing matches.
        """
        self.routes = routes or []
        self.default_route = default_route
        self._sort_routes()

    def _sort_routes(self) -> None:
        """Sort routes by priority (highest first)."""
        self.routes.sort(key=lambda r: r.priority, reverse=True)

    def add_route(self, route: Route) -> None:
        """Add a route to the router.

        Args:
            route: Route to add.
        """
        self.routes.append(route)
        self._sort_routes()

    def remove_route(self, name: str) -> bool:
        """Remove a route by name.

        Args:
            name: Route name to remove.

        Returns:
            True if route was found and removed.
        """
        for i, route in enumerate(self.routes):
            if route.name == name:
                del self.routes[i]
                return True
        return False

    def get_route(self, name: str) -> Route | None:
        """Get a route by name.

        Args:
            name: Route name.

        Returns:
            Route if found, None otherwise.
        """
        for route in self.routes:
            if route.name == name:
                return route
        return None

    async def match(self, context: RouteContext) -> RoutingResult:
        """Evaluate all routes against the context.

        Args:
            context: The routing context to evaluate.

        Returns:
            RoutingResult with matched routes and actions.
        """
        import time

        start_time = time.perf_counter()
        matched_routes: list[Route] = []
        all_actions: set[str] = set()

        for route in self.routes:
            # Skip inactive routes
            if not route.is_active:
                continue

            # Evaluate rule
            try:
                if await route.rule.matches(context):
                    matched_routes.append(route)
                    all_actions.update(route.actions)

                    # Stop if this route has stop_on_match
                    if route.stop_on_match:
                        break
            except Exception:
                # Log error but continue with other routes
                continue

        # Use default route if nothing matched
        if not matched_routes and self.default_route:
            if self.default_route.is_active:
                try:
                    if await self.default_route.rule.matches(context):
                        matched_routes.append(self.default_route)
                        all_actions.update(self.default_route.actions)
                except Exception:
                    pass

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RoutingResult(
            matched_routes=matched_routes,
            all_actions=list(all_actions),
            evaluation_time_ms=elapsed_ms,
            context=context,
        )

    async def get_channels_for_event(
        self,
        event: "NotificationEvent",
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Convenience method to get channel IDs for an event.

        Args:
            event: The notification event.
            metadata: Optional additional metadata.

        Returns:
            List of channel IDs to notify.
        """
        context = RouteContext(
            event=event,
            metadata=metadata or {},
        )
        result = await self.match(context)
        return result.all_actions

    def to_dict(self) -> dict[str, Any]:
        """Serialize router configuration."""
        return {
            "routes": [r.to_dict() for r in self.routes],
            "default_route": self.default_route.to_dict() if self.default_route else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionRouter":
        """Create router from dictionary."""
        routes = []
        for route_data in data.get("routes", []):
            route = Route.from_dict(route_data)
            if route:
                routes.append(route)

        default_route = None
        if data.get("default_route"):
            default_route = Route.from_dict(data["default_route"])

        return cls(routes=routes, default_route=default_route)
