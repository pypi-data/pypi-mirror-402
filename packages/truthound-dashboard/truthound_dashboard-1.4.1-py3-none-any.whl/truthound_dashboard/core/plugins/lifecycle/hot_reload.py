"""Hot Reload Support.

This module provides hot reload capability for plugins,
including file watching and graceful reload with rollback.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

from .states import PluginState
from .machine import PluginStateMachine

logger = logging.getLogger(__name__)


class ReloadStrategy(str, Enum):
    """Strategy for handling hot reloads."""

    IMMEDIATE = "immediate"       # Reload immediately on change
    DEBOUNCED = "debounced"       # Wait for changes to settle
    MANUAL = "manual"             # Only reload on manual trigger
    SCHEDULED = "scheduled"       # Reload at scheduled intervals


@dataclass
class ReloadResult:
    """Result of a reload operation.

    Attributes:
        success: Whether reload succeeded.
        plugin_id: Plugin that was reloaded.
        old_version: Previous version.
        new_version: New version after reload.
        duration_ms: Time taken for reload.
        error: Error message if failed.
        rolled_back: Whether rollback was performed.
        changes: List of changes detected.
    """

    success: bool
    plugin_id: str
    old_version: str = ""
    new_version: str = ""
    duration_ms: float = 0
    error: str | None = None
    rolled_back: bool = False
    changes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "plugin_id": self.plugin_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "rolled_back": self.rolled_back,
            "changes": self.changes,
        }


@dataclass
class FileChange:
    """Represents a file change event.

    Attributes:
        path: File path.
        event_type: Type of change (created, modified, deleted).
        timestamp: When the change was detected.
        content_hash: Hash of new content (if applicable).
    """

    path: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    content_hash: str = ""


class FileWatcher:
    """Watches files for changes to trigger hot reload.

    Uses polling by default; can be extended to use
    inotify/FSEvents/ReadDirectoryChangesW for better performance.
    """

    def __init__(
        self,
        paths: list[str | Path],
        patterns: list[str] | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize the file watcher.

        Args:
            paths: Paths to watch (directories or files).
            patterns: File patterns to watch (e.g., ["*.py"]).
            poll_interval: Polling interval in seconds.
        """
        self._paths = [Path(p) for p in paths]
        self._patterns = patterns or ["*.py"]
        self._poll_interval = poll_interval
        self._running = False
        self._file_hashes: dict[str, str] = {}
        self._callbacks: list[Callable[[FileChange], None]] = []
        self._task: asyncio.Task | None = None

    def on_change(self, callback: Callable[[FileChange], None]) -> None:
        """Register a callback for file changes.

        Args:
            callback: Callback function.
        """
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start watching for changes."""
        if self._running:
            return

        self._running = True
        self._file_hashes = self._scan_files()
        self._task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started file watcher for {len(self._paths)} paths")

    async def stop(self) -> None:
        """Stop watching for changes."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Stopped file watcher")

    def _scan_files(self) -> dict[str, str]:
        """Scan watched paths and compute file hashes.

        Returns:
            Dict mapping file paths to content hashes.
        """
        hashes: dict[str, str] = {}

        for base_path in self._paths:
            if not base_path.exists():
                continue

            if base_path.is_file():
                hashes[str(base_path)] = self._compute_hash(base_path)
            else:
                for pattern in self._patterns:
                    for file_path in base_path.rglob(pattern):
                        if file_path.is_file():
                            hashes[str(file_path)] = self._compute_hash(file_path)

        return hashes

    def _compute_hash(self, path: Path) -> str:
        """Compute hash of file content.

        Args:
            path: File path.

        Returns:
            SHA256 hash of content.
        """
        try:
            content = path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""

    async def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                changes = self._detect_changes()
                for change in changes:
                    for callback in self._callbacks:
                        try:
                            callback(change)
                        except Exception as e:
                            logger.error(f"File change callback error: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Watch loop error: {e}")

    def _detect_changes(self) -> list[FileChange]:
        """Detect file changes since last scan.

        Returns:
            List of file changes.
        """
        changes: list[FileChange] = []
        current_hashes = self._scan_files()

        # Check for modified and new files
        for path, new_hash in current_hashes.items():
            old_hash = self._file_hashes.get(path)
            if old_hash is None:
                changes.append(
                    FileChange(
                        path=path,
                        event_type="created",
                        content_hash=new_hash,
                    )
                )
            elif old_hash != new_hash:
                changes.append(
                    FileChange(
                        path=path,
                        event_type="modified",
                        content_hash=new_hash,
                    )
                )

        # Check for deleted files
        for path in self._file_hashes:
            if path not in current_hashes:
                changes.append(
                    FileChange(
                        path=path,
                        event_type="deleted",
                    )
                )

        self._file_hashes = current_hashes
        return changes


class HotReloadManager:
    """Manages hot reload for plugins.

    This class coordinates the reload process:
    1. Detect changes (via file watcher or manual trigger)
    2. Save current plugin state
    3. Unload old version
    4. Load new version
    5. Restore state or rollback on failure
    """

    def __init__(
        self,
        strategy: ReloadStrategy = ReloadStrategy.DEBOUNCED,
        debounce_delay: float = 0.5,
    ) -> None:
        """Initialize the hot reload manager.

        Args:
            strategy: Reload strategy.
            debounce_delay: Delay for debounced strategy.
        """
        self._strategy = strategy
        self._debounce_delay = debounce_delay
        self._state_machines: dict[str, PluginStateMachine] = {}
        self._watchers: dict[str, FileWatcher] = {}
        self._pending_reloads: dict[str, asyncio.Task] = {}
        self._saved_states: dict[str, dict[str, Any]] = {}

        # Callbacks
        self._before_reload: list[Callable[[str], Awaitable[None]]] = []
        self._after_reload: list[Callable[[str, ReloadResult], Awaitable[None]]] = []

    def register_plugin(
        self,
        plugin_id: str,
        state_machine: PluginStateMachine,
        watch_paths: list[str | Path] | None = None,
    ) -> None:
        """Register a plugin for hot reload.

        Args:
            plugin_id: Plugin identifier.
            state_machine: Plugin's state machine.
            watch_paths: Paths to watch for changes.
        """
        self._state_machines[plugin_id] = state_machine

        if watch_paths and self._strategy != ReloadStrategy.MANUAL:
            watcher = FileWatcher(watch_paths)
            watcher.on_change(lambda change: self._on_file_change(plugin_id, change))
            self._watchers[plugin_id] = watcher

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin from hot reload.

        Args:
            plugin_id: Plugin identifier.
        """
        if plugin_id in self._watchers:
            asyncio.create_task(self._watchers[plugin_id].stop())
            del self._watchers[plugin_id]

        if plugin_id in self._state_machines:
            del self._state_machines[plugin_id]

        if plugin_id in self._pending_reloads:
            self._pending_reloads[plugin_id].cancel()
            del self._pending_reloads[plugin_id]

    def on_before_reload(
        self, callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Register a callback to run before reload.

        Args:
            callback: Callback function (receives plugin_id).
        """
        self._before_reload.append(callback)

    def on_after_reload(
        self, callback: Callable[[str, ReloadResult], Awaitable[None]]
    ) -> None:
        """Register a callback to run after reload.

        Args:
            callback: Callback function (receives plugin_id, result).
        """
        self._after_reload.append(callback)

    async def start_watching(self, plugin_id: str | None = None) -> None:
        """Start watching for changes.

        Args:
            plugin_id: Specific plugin to watch, or None for all.
        """
        if plugin_id:
            if plugin_id in self._watchers:
                await self._watchers[plugin_id].start()
        else:
            for watcher in self._watchers.values():
                await watcher.start()

    async def stop_watching(self, plugin_id: str | None = None) -> None:
        """Stop watching for changes.

        Args:
            plugin_id: Specific plugin to stop, or None for all.
        """
        if plugin_id:
            if plugin_id in self._watchers:
                await self._watchers[plugin_id].stop()
        else:
            for watcher in self._watchers.values():
                await watcher.stop()

    def _on_file_change(self, plugin_id: str, change: FileChange) -> None:
        """Handle file change event.

        Args:
            plugin_id: Plugin that owns the file.
            change: File change event.
        """
        logger.debug(f"File change detected for {plugin_id}: {change.path}")

        if self._strategy == ReloadStrategy.IMMEDIATE:
            asyncio.create_task(self.reload(plugin_id, changes=[change.path]))
        elif self._strategy == ReloadStrategy.DEBOUNCED:
            self._schedule_debounced_reload(plugin_id, change)

    def _schedule_debounced_reload(
        self, plugin_id: str, change: FileChange
    ) -> None:
        """Schedule a debounced reload.

        Args:
            plugin_id: Plugin to reload.
            change: Triggering change.
        """
        # Cancel existing pending reload
        if plugin_id in self._pending_reloads:
            self._pending_reloads[plugin_id].cancel()

        # Schedule new reload
        async def delayed_reload():
            await asyncio.sleep(self._debounce_delay)
            await self.reload(plugin_id, changes=[change.path])

        self._pending_reloads[plugin_id] = asyncio.create_task(delayed_reload())

    async def reload(
        self,
        plugin_id: str,
        changes: list[str] | None = None,
        force: bool = False,
    ) -> ReloadResult:
        """Reload a plugin.

        Args:
            plugin_id: Plugin to reload.
            changes: List of changed files.
            force: Force reload even if no changes detected.

        Returns:
            ReloadResult with reload outcome.
        """
        start_time = time.perf_counter()

        if plugin_id not in self._state_machines:
            return ReloadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"Plugin {plugin_id} not registered for hot reload",
            )

        state_machine = self._state_machines[plugin_id]
        old_version = state_machine.context.version

        # Check if plugin can be reloaded
        if state_machine.state not in {PluginState.ACTIVE, PluginState.LOADED}:
            return ReloadResult(
                success=False,
                plugin_id=plugin_id,
                old_version=old_version,
                error=f"Cannot reload plugin in state {state_machine.state.value}",
            )

        try:
            # Execute before callbacks
            for callback in self._before_reload:
                await callback(plugin_id)

            # Save current state
            self._saved_states[plugin_id] = self._save_state(state_machine)

            # Transition to RELOADING
            await state_machine.transition_async(
                PluginState.RELOADING,
                trigger="hot_reload",
                metadata={"changes": changes},
            )

            # Perform reload (plugin-specific logic would go here)
            # For now, we simulate by transitioning back to ACTIVE
            await asyncio.sleep(0.1)  # Simulate reload time

            # Transition back to ACTIVE
            await state_machine.transition_async(
                PluginState.ACTIVE,
                trigger="reload_complete",
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = ReloadResult(
                success=True,
                plugin_id=plugin_id,
                old_version=old_version,
                new_version=state_machine.context.version,
                duration_ms=duration_ms,
                changes=changes or [],
            )

            # Execute after callbacks
            for callback in self._after_reload:
                await callback(plugin_id, result)

            logger.info(
                f"Hot reload completed for {plugin_id} in {duration_ms:.2f}ms"
            )

            return result

        except Exception as e:
            # Attempt rollback
            rolled_back = await self._rollback(plugin_id)

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = ReloadResult(
                success=False,
                plugin_id=plugin_id,
                old_version=old_version,
                duration_ms=duration_ms,
                error=str(e),
                rolled_back=rolled_back,
                changes=changes or [],
            )

            logger.error(f"Hot reload failed for {plugin_id}: {e}")

            # Execute after callbacks
            for callback in self._after_reload:
                await callback(plugin_id, result)

            return result

    def _save_state(self, state_machine: PluginStateMachine) -> dict[str, Any]:
        """Save plugin state for potential rollback.

        Args:
            state_machine: Plugin's state machine.

        Returns:
            Saved state data.
        """
        return {
            "state": state_machine.state.value,
            "version": state_machine.context.version,
            "config": state_machine.context.config.copy(),
            "state_data": state_machine.context.state_data.copy(),
        }

    async def _rollback(self, plugin_id: str) -> bool:
        """Attempt to rollback a failed reload.

        Args:
            plugin_id: Plugin to rollback.

        Returns:
            True if rollback succeeded.
        """
        if plugin_id not in self._saved_states:
            return False

        if plugin_id not in self._state_machines:
            return False

        state_machine = self._state_machines[plugin_id]
        saved = self._saved_states[plugin_id]

        try:
            # Restore state
            state_machine.context.version = saved["version"]
            state_machine.context.config = saved["config"]
            state_machine.context.state_data = saved["state_data"]

            # Transition back to previous state
            target_state = PluginState(saved["state"])
            if state_machine.can_transition_to(target_state):
                await state_machine.transition_async(
                    target_state,
                    trigger="rollback",
                )
                logger.info(f"Successfully rolled back {plugin_id}")
                return True
            else:
                # Try to go to LOADED as fallback
                if state_machine.can_transition_to(PluginState.LOADED):
                    await state_machine.transition_async(
                        PluginState.LOADED,
                        trigger="rollback_fallback",
                    )
                    return True

        except Exception as e:
            logger.error(f"Rollback failed for {plugin_id}: {e}")

        return False

    def get_status(self, plugin_id: str) -> dict[str, Any]:
        """Get hot reload status for a plugin.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Status information.
        """
        if plugin_id not in self._state_machines:
            return {"registered": False}

        state_machine = self._state_machines[plugin_id]
        watcher = self._watchers.get(plugin_id)

        return {
            "registered": True,
            "state": state_machine.state.value,
            "watching": watcher._running if watcher else False,
            "strategy": self._strategy.value,
            "has_pending_reload": plugin_id in self._pending_reloads,
        }
