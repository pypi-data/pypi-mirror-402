"""Plugin Registry for managing installed plugins.

This module provides the central registry for plugin management,
including discovery, registration, and lifecycle management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db.models import (
    CustomReporter,
    CustomValidator,
    Plugin,
    PluginStatus,
    PluginType,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for plugin management.

    This class provides methods to register, discover, install,
    enable/disable, and uninstall plugins.

    Attributes:
        _validators: Cached custom validators by name.
        _reporters: Cached custom reporters by name.
        _plugins: Cached plugins by name.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._validators: dict[str, CustomValidator] = {}
        self._reporters: dict[str, CustomReporter] = {}
        self._plugins: dict[str, Plugin] = {}
        self._initialized = False

    async def initialize(self, session: AsyncSession) -> None:
        """Initialize the registry by loading enabled plugins.

        Args:
            session: Database session.
        """
        if self._initialized:
            return

        logger.info("Initializing plugin registry...")

        # Load enabled plugins
        stmt = select(Plugin).where(Plugin.is_enabled == True)  # noqa: E712
        result = await session.execute(stmt)
        plugins = result.scalars().all()

        for plugin in plugins:
            self._plugins[plugin.name] = plugin
            logger.debug(f"Loaded plugin: {plugin.name} v{plugin.version}")

        # Load enabled validators
        stmt = select(CustomValidator).where(CustomValidator.is_enabled == True)  # noqa: E712
        result = await session.execute(stmt)
        validators = result.scalars().all()

        for validator in validators:
            self._validators[validator.name] = validator
            logger.debug(f"Loaded validator: {validator.name}")

        # Load enabled reporters
        stmt = select(CustomReporter).where(CustomReporter.is_enabled == True)  # noqa: E712
        result = await session.execute(stmt)
        reporters = result.scalars().all()

        for reporter in reporters:
            self._reporters[reporter.name] = reporter
            logger.debug(f"Loaded reporter: {reporter.name}")

        self._initialized = True
        logger.info(
            f"Plugin registry initialized: {len(self._plugins)} plugins, "
            f"{len(self._validators)} validators, {len(self._reporters)} reporters"
        )

    def clear_cache(self) -> None:
        """Clear all cached plugins, validators, and reporters."""
        self._validators.clear()
        self._reporters.clear()
        self._plugins.clear()
        self._initialized = False
        logger.info("Plugin registry cache cleared")

    # =========================================================================
    # Plugin Management
    # =========================================================================

    async def list_plugins(
        self,
        session: AsyncSession,
        plugin_type: PluginType | None = None,
        status: PluginStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Plugin], int]:
        """List plugins with optional filtering.

        Args:
            session: Database session.
            plugin_type: Filter by plugin type.
            status: Filter by status.
            search: Search in name, display_name, description.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (plugins list, total count).
        """
        stmt = select(Plugin)

        if plugin_type:
            stmt = stmt.where(Plugin.type == plugin_type.value)
        if status:
            stmt = stmt.where(Plugin.status == status.value)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Plugin.name.ilike(search_pattern))
                | (Plugin.display_name.ilike(search_pattern))
                | (Plugin.description.ilike(search_pattern))
            )

        # Get total count
        count_result = await session.execute(
            select(Plugin.id).select_from(stmt.subquery())
        )
        total = len(count_result.all())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit).order_by(Plugin.created_at.desc())
        result = await session.execute(stmt)
        plugins = result.scalars().all()

        return plugins, total

    async def get_plugin(
        self,
        session: AsyncSession,
        plugin_id: str | None = None,
        name: str | None = None,
    ) -> Plugin | None:
        """Get a plugin by ID or name.

        Args:
            session: Database session.
            plugin_id: Plugin ID.
            name: Plugin name.

        Returns:
            Plugin if found, None otherwise.
        """
        if plugin_id:
            stmt = select(Plugin).where(Plugin.id == plugin_id)
        elif name:
            stmt = select(Plugin).where(Plugin.name == name)
        else:
            return None

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_plugin(
        self,
        session: AsyncSession,
        name: str,
        display_name: str,
        description: str,
        version: str,
        plugin_type: PluginType,
        **kwargs: Any,
    ) -> Plugin:
        """Register a new plugin.

        Args:
            session: Database session.
            name: Plugin name (unique).
            display_name: Display name.
            description: Plugin description.
            version: Plugin version.
            plugin_type: Plugin type.
            **kwargs: Additional plugin attributes.

        Returns:
            Created plugin.

        Raises:
            ValueError: If plugin with same name exists.
        """
        existing = await self.get_plugin(session, name=name)
        if existing:
            raise ValueError(f"Plugin with name '{name}' already exists")

        plugin = Plugin(
            name=name,
            display_name=display_name,
            description=description,
            version=version,
            type=plugin_type.value,
            **kwargs,
        )
        session.add(plugin)
        await session.flush()

        logger.info(f"Registered plugin: {name} v{version}")
        return plugin

    async def install_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
        enable: bool = True,
    ) -> Plugin:
        """Install a plugin.

        Args:
            session: Database session.
            plugin_id: Plugin ID.
            enable: Whether to enable after installation.

        Returns:
            Updated plugin.

        Raises:
            ValueError: If plugin not found.
        """
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.install()
        if enable:
            plugin.enable()
            self._plugins[plugin.name] = plugin

        await session.flush()
        logger.info(f"Installed plugin: {plugin.name} v{plugin.version}")
        return plugin

    async def uninstall_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
        remove_data: bool = False,
    ) -> None:
        """Uninstall a plugin.

        Args:
            session: Database session.
            plugin_id: Plugin ID.
            remove_data: Whether to remove plugin data.
        """
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Remove from cache
        if plugin.name in self._plugins:
            del self._plugins[plugin.name]

        if remove_data:
            # Delete plugin entirely
            await session.delete(plugin)
            logger.info(f"Removed plugin: {plugin.name}")
        else:
            # Just mark as uninstalled
            plugin.uninstall()
            logger.info(f"Uninstalled plugin: {plugin.name}")

        await session.flush()

    async def enable_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> Plugin:
        """Enable a plugin.

        Args:
            session: Database session.
            plugin_id: Plugin ID.

        Returns:
            Updated plugin.
        """
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.enable()
        self._plugins[plugin.name] = plugin
        await session.flush()

        logger.info(f"Enabled plugin: {plugin.name}")
        return plugin

    async def disable_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> Plugin:
        """Disable a plugin.

        Args:
            session: Database session.
            plugin_id: Plugin ID.

        Returns:
            Updated plugin.
        """
        plugin = await self.get_plugin(session, plugin_id=plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin.disable()
        if plugin.name in self._plugins:
            del self._plugins[plugin.name]
        await session.flush()

        logger.info(f"Disabled plugin: {plugin.name}")
        return plugin

    # =========================================================================
    # Custom Validator Management
    # =========================================================================

    async def list_validators(
        self,
        session: AsyncSession,
        plugin_id: str | None = None,
        category: str | None = None,
        enabled_only: bool = False,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[CustomValidator], int]:
        """List custom validators with optional filtering.

        Args:
            session: Database session.
            plugin_id: Filter by plugin.
            category: Filter by category.
            enabled_only: Only return enabled validators.
            search: Search in name, display_name, description.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (validators list, total count).
        """
        stmt = select(CustomValidator)

        if plugin_id:
            stmt = stmt.where(CustomValidator.plugin_id == plugin_id)
        if category:
            stmt = stmt.where(CustomValidator.category == category)
        if enabled_only:
            stmt = stmt.where(CustomValidator.is_enabled == True)  # noqa: E712
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (CustomValidator.name.ilike(search_pattern))
                | (CustomValidator.display_name.ilike(search_pattern))
                | (CustomValidator.description.ilike(search_pattern))
            )

        # Get total count
        count_result = await session.execute(
            select(CustomValidator.id).select_from(stmt.subquery())
        )
        total = len(count_result.all())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit).order_by(CustomValidator.created_at.desc())
        result = await session.execute(stmt)
        validators = result.scalars().all()

        return validators, total

    async def get_validator(
        self,
        session: AsyncSession,
        validator_id: str | None = None,
        name: str | None = None,
    ) -> CustomValidator | None:
        """Get a custom validator by ID or name.

        Args:
            session: Database session.
            validator_id: Validator ID.
            name: Validator name.

        Returns:
            CustomValidator if found, None otherwise.
        """
        if validator_id:
            stmt = select(CustomValidator).where(CustomValidator.id == validator_id)
        elif name:
            stmt = select(CustomValidator).where(CustomValidator.name == name)
        else:
            return None

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_validator(
        self,
        session: AsyncSession,
        name: str,
        display_name: str,
        description: str,
        category: str,
        code: str,
        plugin_id: str | None = None,
        **kwargs: Any,
    ) -> CustomValidator:
        """Register a new custom validator.

        Args:
            session: Database session.
            name: Validator name (unique).
            display_name: Display name.
            description: Validator description.
            category: Validator category.
            code: Python code implementing the validator.
            plugin_id: Optional parent plugin ID.
            **kwargs: Additional validator attributes.

        Returns:
            Created validator.

        Raises:
            ValueError: If validator with same name exists.
        """
        existing = await self.get_validator(session, name=name)
        if existing:
            raise ValueError(f"Validator with name '{name}' already exists")

        validator = CustomValidator(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            code=code,
            plugin_id=plugin_id,
            **kwargs,
        )
        session.add(validator)
        await session.flush()

        # Update plugin validator count if applicable
        if plugin_id:
            plugin = await self.get_plugin(session, plugin_id=plugin_id)
            if plugin:
                plugin.validators_count += 1

        self._validators[name] = validator
        logger.info(f"Registered custom validator: {name}")
        return validator

    async def update_validator(
        self,
        session: AsyncSession,
        validator_id: str,
        **updates: Any,
    ) -> CustomValidator:
        """Update a custom validator.

        Args:
            session: Database session.
            validator_id: Validator ID.
            **updates: Fields to update.

        Returns:
            Updated validator.
        """
        validator = await self.get_validator(session, validator_id=validator_id)
        if not validator:
            raise ValueError(f"Validator {validator_id} not found")

        for key, value in updates.items():
            if hasattr(validator, key) and value is not None:
                setattr(validator, key, value)

        await session.flush()

        # Update cache
        if validator.is_enabled:
            self._validators[validator.name] = validator
        elif validator.name in self._validators:
            del self._validators[validator.name]

        logger.info(f"Updated custom validator: {validator.name}")
        return validator

    async def delete_validator(
        self,
        session: AsyncSession,
        validator_id: str,
    ) -> None:
        """Delete a custom validator.

        Args:
            session: Database session.
            validator_id: Validator ID.
        """
        validator = await self.get_validator(session, validator_id=validator_id)
        if not validator:
            raise ValueError(f"Validator {validator_id} not found")

        # Remove from cache
        if validator.name in self._validators:
            del self._validators[validator.name]

        # Update plugin validator count if applicable
        if validator.plugin_id:
            plugin = await self.get_plugin(session, plugin_id=validator.plugin_id)
            if plugin and plugin.validators_count > 0:
                plugin.validators_count -= 1

        await session.delete(validator)
        await session.flush()
        logger.info(f"Deleted custom validator: {validator.name}")

    def get_cached_validator(self, name: str) -> CustomValidator | None:
        """Get a validator from cache by name.

        Args:
            name: Validator name.

        Returns:
            CustomValidator if found in cache, None otherwise.
        """
        return self._validators.get(name)

    # =========================================================================
    # Custom Reporter Management
    # =========================================================================

    async def list_reporters(
        self,
        session: AsyncSession,
        plugin_id: str | None = None,
        enabled_only: bool = False,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[CustomReporter], int]:
        """List custom reporters with optional filtering.

        Args:
            session: Database session.
            plugin_id: Filter by plugin.
            enabled_only: Only return enabled reporters.
            search: Search in name, display_name, description.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (reporters list, total count).
        """
        stmt = select(CustomReporter)

        if plugin_id:
            stmt = stmt.where(CustomReporter.plugin_id == plugin_id)
        if enabled_only:
            stmt = stmt.where(CustomReporter.is_enabled == True)  # noqa: E712
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (CustomReporter.name.ilike(search_pattern))
                | (CustomReporter.display_name.ilike(search_pattern))
                | (CustomReporter.description.ilike(search_pattern))
            )

        # Get total count
        count_result = await session.execute(
            select(CustomReporter.id).select_from(stmt.subquery())
        )
        total = len(count_result.all())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit).order_by(CustomReporter.created_at.desc())
        result = await session.execute(stmt)
        reporters = result.scalars().all()

        return reporters, total

    async def get_reporter(
        self,
        session: AsyncSession,
        reporter_id: str | None = None,
        name: str | None = None,
    ) -> CustomReporter | None:
        """Get a custom reporter by ID or name.

        Args:
            session: Database session.
            reporter_id: Reporter ID.
            name: Reporter name.

        Returns:
            CustomReporter if found, None otherwise.
        """
        if reporter_id:
            stmt = select(CustomReporter).where(CustomReporter.id == reporter_id)
        elif name:
            stmt = select(CustomReporter).where(CustomReporter.name == name)
        else:
            return None

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_reporter(
        self,
        session: AsyncSession,
        name: str,
        display_name: str,
        description: str,
        plugin_id: str | None = None,
        **kwargs: Any,
    ) -> CustomReporter:
        """Register a new custom reporter.

        Args:
            session: Database session.
            name: Reporter name (unique).
            display_name: Display name.
            description: Reporter description.
            plugin_id: Optional parent plugin ID.
            **kwargs: Additional reporter attributes.

        Returns:
            Created reporter.

        Raises:
            ValueError: If reporter with same name exists.
        """
        existing = await self.get_reporter(session, name=name)
        if existing:
            raise ValueError(f"Reporter with name '{name}' already exists")

        reporter = CustomReporter(
            name=name,
            display_name=display_name,
            description=description,
            plugin_id=plugin_id,
            **kwargs,
        )
        session.add(reporter)
        await session.flush()

        # Update plugin reporter count if applicable
        if plugin_id:
            plugin = await self.get_plugin(session, plugin_id=plugin_id)
            if plugin:
                plugin.reporters_count += 1

        self._reporters[name] = reporter
        logger.info(f"Registered custom reporter: {name}")
        return reporter

    async def update_reporter(
        self,
        session: AsyncSession,
        reporter_id: str,
        **updates: Any,
    ) -> CustomReporter:
        """Update a custom reporter.

        Args:
            session: Database session.
            reporter_id: Reporter ID.
            **updates: Fields to update.

        Returns:
            Updated reporter.
        """
        reporter = await self.get_reporter(session, reporter_id=reporter_id)
        if not reporter:
            raise ValueError(f"Reporter {reporter_id} not found")

        for key, value in updates.items():
            if hasattr(reporter, key) and value is not None:
                setattr(reporter, key, value)

        await session.flush()

        # Update cache
        if reporter.is_enabled:
            self._reporters[reporter.name] = reporter
        elif reporter.name in self._reporters:
            del self._reporters[reporter.name]

        logger.info(f"Updated custom reporter: {reporter.name}")
        return reporter

    async def delete_reporter(
        self,
        session: AsyncSession,
        reporter_id: str,
    ) -> None:
        """Delete a custom reporter.

        Args:
            session: Database session.
            reporter_id: Reporter ID.
        """
        reporter = await self.get_reporter(session, reporter_id=reporter_id)
        if not reporter:
            raise ValueError(f"Reporter {reporter_id} not found")

        # Remove from cache
        if reporter.name in self._reporters:
            del self._reporters[reporter.name]

        # Update plugin reporter count if applicable
        if reporter.plugin_id:
            plugin = await self.get_plugin(session, plugin_id=reporter.plugin_id)
            if plugin and plugin.reporters_count > 0:
                plugin.reporters_count -= 1

        await session.delete(reporter)
        await session.flush()
        logger.info(f"Deleted custom reporter: {reporter.name}")

    def get_cached_reporter(self, name: str) -> CustomReporter | None:
        """Get a reporter from cache by name.

        Args:
            name: Reporter name.

        Returns:
            CustomReporter if found in cache, None otherwise.
        """
        return self._reporters.get(name)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_statistics(self, session: AsyncSession) -> dict[str, Any]:
        """Get plugin system statistics.

        Args:
            session: Database session.

        Returns:
            Dictionary of statistics.
        """
        # Count plugins by type
        plugins_result = await session.execute(select(Plugin))
        plugins = plugins_result.scalars().all()

        total_plugins = len(plugins)
        installed = sum(1 for p in plugins if p.status in (PluginStatus.INSTALLED.value, PluginStatus.ENABLED.value))
        enabled = sum(1 for p in plugins if p.is_enabled)

        by_type = {}
        for ptype in PluginType:
            by_type[ptype.value] = sum(1 for p in plugins if p.type == ptype.value)

        # Count validators and reporters
        validators_result = await session.execute(select(CustomValidator))
        validators = validators_result.scalars().all()

        reporters_result = await session.execute(select(CustomReporter))
        reporters = reporters_result.scalars().all()

        # Get categories
        categories = set()
        for v in validators:
            if v.category:
                categories.add(v.category)

        return {
            "total_plugins": total_plugins,
            "installed_plugins": installed,
            "enabled_plugins": enabled,
            "plugins_by_type": by_type,
            "total_validators": len(validators),
            "enabled_validators": sum(1 for v in validators if v.is_enabled),
            "total_reporters": len(reporters),
            "enabled_reporters": sum(1 for r in reporters if r.is_enabled),
            "validator_categories": sorted(list(categories)),
            "cached_validators": len(self._validators),
            "cached_reporters": len(self._reporters),
        }


# Global registry instance
plugin_registry = PluginRegistry()
