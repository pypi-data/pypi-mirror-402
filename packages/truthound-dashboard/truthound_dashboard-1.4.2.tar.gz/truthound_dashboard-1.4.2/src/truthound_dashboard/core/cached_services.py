"""Cached service wrappers for improved performance.

This module provides caching decorators and cached service classes
that wrap the base services with cache integration.

Cache keys are prefixed by resource type for easy invalidation:
- validation:{id} - Individual validation results
- validations:source:{source_id} - Validation list for a source
- schema:{source_id} - Active schema for a source
- profile:{source_id} - Latest profile for a source
- validators - Validator registry (long TTL)

Example:
    from truthound_dashboard.core.cached_services import (
        CachedValidationService,
        invalidate_validation_cache,
    )

    service = CachedValidationService(session)
    validation = await service.get_validation(id)  # May return cached

    # Invalidate cache when data changes
    await invalidate_validation_cache(validation_id=id)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

from truthound_dashboard.core.cache import get_cache, CacheBackend
from truthound_dashboard.core.versioning import create_version, VersioningStrategy
from truthound_dashboard.db import Validation

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
VALIDATION_TTL = 300  # 5 minutes for individual validations
VALIDATION_LIST_TTL = 60  # 1 minute for validation lists
SCHEMA_TTL = 600  # 10 minutes for schemas
PROFILE_TTL = 600  # 10 minutes for profiles
VALIDATORS_TTL = 3600  # 1 hour for validator registry

# Cache key prefixes
PREFIX_VALIDATION = "validation:"
PREFIX_VALIDATIONS_LIST = "validations:source:"
PREFIX_SCHEMA = "schema:"
PREFIX_PROFILE = "profile:"
PREFIX_VALIDATORS = "validators"

T = TypeVar("T")


def cache_key(*parts: str) -> str:
    """Build a cache key from parts.

    Args:
        parts: Key parts to join.

    Returns:
        Cache key string.
    """
    return ":".join(str(p) for p in parts)


async def get_cached_or_compute(
    cache: CacheBackend,
    key: str,
    compute_fn: Callable[[], Any],
    ttl: int = 300,
) -> Any:
    """Get value from cache or compute and cache it.

    Args:
        cache: Cache backend.
        key: Cache key.
        compute_fn: Async function to compute value if not cached.
        ttl: Time to live in seconds.

    Returns:
        Cached or computed value.
    """
    # Try cache first
    cached = await cache.get(key)
    if cached is not None:
        logger.debug(f"Cache hit: {key}")
        return cached

    # Compute and cache
    logger.debug(f"Cache miss: {key}")
    value = await compute_fn()

    if value is not None:
        await cache.set(key, value, ttl)

    return value


async def invalidate_validation_cache(
    *,
    validation_id: str | None = None,
    source_id: str | None = None,
) -> int:
    """Invalidate validation-related cache entries.

    Args:
        validation_id: Specific validation ID to invalidate.
        source_id: Invalidate all caches for a source.

    Returns:
        Number of cache entries invalidated.
    """
    cache = get_cache()
    count = 0

    if validation_id:
        key = f"{PREFIX_VALIDATION}{validation_id}"
        if await cache.delete(key):
            count += 1

    if source_id:
        # Invalidate validation list for source
        key = f"{PREFIX_VALIDATIONS_LIST}{source_id}"
        if await cache.delete(key):
            count += 1

        # Invalidate all validations for source (pattern match)
        count += await cache.invalidate_pattern(f"{PREFIX_VALIDATION}{source_id}")

    logger.debug(f"Invalidated {count} cache entries")
    return count


async def invalidate_schema_cache(source_id: str) -> bool:
    """Invalidate schema cache for a source.

    Args:
        source_id: Source ID.

    Returns:
        True if cache was invalidated.
    """
    cache = get_cache()
    key = f"{PREFIX_SCHEMA}{source_id}"
    return await cache.delete(key)


async def invalidate_profile_cache(source_id: str) -> bool:
    """Invalidate profile cache for a source.

    Args:
        source_id: Source ID.

    Returns:
        True if cache was invalidated.
    """
    cache = get_cache()
    key = f"{PREFIX_PROFILE}{source_id}"
    return await cache.delete(key)


class ValidationCacheService:
    """Cache wrapper for validation operations.

    Provides cached access to validation data with automatic
    cache invalidation on writes.
    """

    def __init__(self, cache: CacheBackend | None = None) -> None:
        """Initialize cache service.

        Args:
            cache: Cache backend. Uses default if not provided.
        """
        self._cache = cache or get_cache()

    async def get_validation(
        self,
        validation_id: str,
        compute_fn: Callable[[], Any],
    ) -> Validation | None:
        """Get validation from cache or compute.

        Args:
            validation_id: Validation ID.
            compute_fn: Async function to get validation if not cached.

        Returns:
            Validation or None.
        """
        key = f"{PREFIX_VALIDATION}{validation_id}"
        return await get_cached_or_compute(
            self._cache,
            key,
            compute_fn,
            VALIDATION_TTL,
        )

    async def get_validations_for_source(
        self,
        source_id: str,
        compute_fn: Callable[[], Any],
    ) -> Sequence[Validation]:
        """Get validations for source from cache or compute.

        Args:
            source_id: Source ID.
            compute_fn: Async function to get validations if not cached.

        Returns:
            Sequence of validations.
        """
        key = f"{PREFIX_VALIDATIONS_LIST}{source_id}"
        result = await get_cached_or_compute(
            self._cache,
            key,
            compute_fn,
            VALIDATION_LIST_TTL,
        )
        return result or []

    async def invalidate(
        self,
        *,
        validation_id: str | None = None,
        source_id: str | None = None,
    ) -> int:
        """Invalidate cached validation data.

        Args:
            validation_id: Specific validation to invalidate.
            source_id: Invalidate all for a source.

        Returns:
            Number of entries invalidated.
        """
        return await invalidate_validation_cache(
            validation_id=validation_id,
            source_id=source_id,
        )


class SchemaCacheService:
    """Cache wrapper for schema operations."""

    def __init__(self, cache: CacheBackend | None = None) -> None:
        """Initialize cache service."""
        self._cache = cache or get_cache()

    async def get_schema(
        self,
        source_id: str,
        compute_fn: Callable[[], Any],
    ) -> Any:
        """Get schema from cache or compute.

        Args:
            source_id: Source ID.
            compute_fn: Async function to get schema if not cached.

        Returns:
            Schema or None.
        """
        key = f"{PREFIX_SCHEMA}{source_id}"
        return await get_cached_or_compute(
            self._cache,
            key,
            compute_fn,
            SCHEMA_TTL,
        )

    async def invalidate(self, source_id: str) -> bool:
        """Invalidate schema cache for a source."""
        return await invalidate_schema_cache(source_id)


class ProfileCacheService:
    """Cache wrapper for profile operations."""

    def __init__(self, cache: CacheBackend | None = None) -> None:
        """Initialize cache service."""
        self._cache = cache or get_cache()

    async def get_profile(
        self,
        source_id: str,
        compute_fn: Callable[[], Any],
    ) -> Any:
        """Get profile from cache or compute.

        Args:
            source_id: Source ID.
            compute_fn: Async function to get profile if not cached.

        Returns:
            Profile or None.
        """
        key = f"{PREFIX_PROFILE}{source_id}"
        return await get_cached_or_compute(
            self._cache,
            key,
            compute_fn,
            PROFILE_TTL,
        )

    async def invalidate(self, source_id: str) -> bool:
        """Invalidate profile cache for a source."""
        return await invalidate_profile_cache(source_id)


class ValidatorsCacheService:
    """Cache wrapper for validator registry."""

    def __init__(self, cache: CacheBackend | None = None) -> None:
        """Initialize cache service."""
        self._cache = cache or get_cache()

    async def get_validators(
        self,
        compute_fn: Callable[[], Any],
    ) -> list[dict[str, Any]]:
        """Get validators from cache or compute.

        Args:
            compute_fn: Async function to get validators if not cached.

        Returns:
            List of validator definitions.
        """
        result = await get_cached_or_compute(
            self._cache,
            PREFIX_VALIDATORS,
            compute_fn,
            VALIDATORS_TTL,
        )
        return result or []

    async def invalidate(self) -> bool:
        """Invalidate validators cache."""
        return await self._cache.delete(PREFIX_VALIDATORS)


# Convenience function to create a versioned validation result
async def create_versioned_validation(
    validation: Validation,
    strategy: VersioningStrategy = VersioningStrategy.INCREMENTAL,
) -> None:
    """Create a version entry for a validation result.

    This integrates versioning with the validation workflow.
    Call after a validation is complete to track its version.

    Args:
        validation: Completed validation model.
        strategy: Versioning strategy to use.
    """
    if validation.status not in ("success", "failed"):
        return  # Only version completed validations

    await create_version(
        validation_id=validation.id,
        source_id=validation.source_id,
        result_json=validation.result_json,
        strategy=strategy,
        metadata={
            "passed": validation.passed,
            "total_issues": validation.total_issues,
            "status": validation.status,
        },
    )
    logger.debug(f"Created version for validation {validation.id}")


# Singleton instances for convenience
_validation_cache: ValidationCacheService | None = None
_schema_cache: SchemaCacheService | None = None
_profile_cache: ProfileCacheService | None = None
_validators_cache: ValidatorsCacheService | None = None


def get_validation_cache() -> ValidationCacheService:
    """Get singleton validation cache service."""
    global _validation_cache
    if _validation_cache is None:
        _validation_cache = ValidationCacheService()
    return _validation_cache


def get_schema_cache() -> SchemaCacheService:
    """Get singleton schema cache service."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = SchemaCacheService()
    return _schema_cache


def get_profile_cache() -> ProfileCacheService:
    """Get singleton profile cache service."""
    global _profile_cache
    if _profile_cache is None:
        _profile_cache = ProfileCacheService()
    return _profile_cache


def get_validators_cache() -> ValidatorsCacheService:
    """Get singleton validators cache service."""
    global _validators_cache
    if _validators_cache is None:
        _validators_cache = ValidatorsCacheService()
    return _validators_cache


def reset_cache_services() -> None:
    """Reset all cache service singletons (for testing)."""
    global _validation_cache, _schema_cache, _profile_cache, _validators_cache
    _validation_cache = None
    _schema_cache = None
    _profile_cache = None
    _validators_cache = None
