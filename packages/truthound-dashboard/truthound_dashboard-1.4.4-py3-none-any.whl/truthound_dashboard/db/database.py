"""Database connection and session management.

This module provides async database connection handling using SQLAlchemy 2.0.
It supports both production SQLite and in-memory databases for testing.

Example:
    # Using context manager
    async with get_session() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()

    # Using FastAPI dependency
    @router.get("/sources")
    async def list_sources(session: AsyncSession = Depends(get_db_session)):
        ...
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from truthound_dashboard.config import get_settings

from .base import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url(in_memory: bool = False) -> str:
    """Get database URL.

    Args:
        in_memory: If True, use in-memory SQLite for testing.

    Returns:
        SQLAlchemy async database URL.
    """
    if in_memory:
        return "sqlite+aiosqlite:///:memory:"

    settings = get_settings()
    settings.ensure_directories()
    return f"sqlite+aiosqlite:///{settings.database_path}"


def get_engine(in_memory: bool = False) -> AsyncEngine:
    """Get or create database engine.

    Args:
        in_memory: If True, create in-memory database.

    Returns:
        AsyncEngine instance.
    """
    global _engine

    if _engine is None or in_memory:
        url = get_database_url(in_memory)
        engine = create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in url else {},
        )
        if not in_memory:
            _engine = engine
        return engine

    return _engine


def get_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Get or create session factory.

    Args:
        engine: Optional engine to use. If None, uses default engine.

    Returns:
        Session factory for creating database sessions.
    """
    global _session_factory

    if engine is not None:
        # Create new factory for provided engine (used in testing)
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as async context manager.

    Yields:
        AsyncSession for database operations.

    Example:
        async with get_session() as session:
            result = await session.execute(select(Source))
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession for use in route handlers.

    Example:
        @router.get("/sources")
        async def get_sources(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with get_session() as session:
        yield session


async def _run_migrations(engine: AsyncEngine) -> None:
    """Run database migrations for schema updates.

    This handles backward compatibility when new columns are added.
    SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS,
    so we check column existence first.

    Args:
        engine: Database engine to use.
    """
    migrations = [
        # (table_name, column_name, column_definition, default_value)
        ("schedules", "trigger_type", "VARCHAR(50)", "cron"),
        ("schedules", "trigger_config", "JSON", None),
        ("schedules", "trigger_count", "INTEGER", 0),
        ("schedules", "last_trigger_result", "JSON", None),
    ]

    async with engine.begin() as conn:
        for table, column, col_type, default in migrations:
            # Check if column exists
            result = await conn.execute(
                text(f"PRAGMA table_info({table})")
            )
            columns = [row[1] for row in result.fetchall()]

            if column not in columns:
                # Add the column
                if default is not None:
                    if isinstance(default, str):
                        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT '{default}'"
                    else:
                        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}"
                else:
                    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"

                try:
                    await conn.execute(text(sql))
                    logger.info(f"Migration: Added column {table}.{column}")
                except Exception as e:
                    logger.warning(f"Migration skipped for {table}.{column}: {e}")


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist,
    then runs migrations for schema updates.

    Args:
        engine: Optional engine to use. If None, uses default engine.
    """
    target_engine = engine or get_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run migrations for existing databases
    await _run_migrations(target_engine)


async def drop_db(engine: AsyncEngine | None = None) -> None:
    """Drop all database tables.

    Warning: This will delete all data!

    Args:
        engine: Optional engine to use. If None, uses default engine.
    """
    target_engine = engine or get_engine()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def reset_db(engine: AsyncEngine | None = None) -> None:
    """Reset database by dropping and recreating all tables.

    Warning: This will delete all data!

    Args:
        engine: Optional engine to use. If None, uses default engine.
    """
    await drop_db(engine)
    await init_db(engine)


def reset_connection() -> None:
    """Reset global engine and session factory.

    Useful for testing or when configuration changes.
    """
    global _engine, _session_factory
    _engine = None
    _session_factory = None
