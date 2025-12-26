"""Database configuration and session management."""

import sqlite3
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Get database URL from settings
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")


# SQLite timezone handling - register adapters globally
def adapt_datetime_iso(val: datetime) -> str:
    """Convert datetime to ISO string for SQLite storage."""
    return val.isoformat()


def convert_datetime(val: bytes) -> datetime:
    """Convert stored datetime back to timezone-aware datetime."""
    dt_str = val.decode("utf-8")
    dt = datetime.fromisoformat(dt_str)
    # Ensure timezone-aware (default to UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


# Register SQLite adapters/converters for timezone-aware datetimes
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime)

# Configure engine with SQLite-specific settings
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10,
    "echo": settings.environment == "development",
}

# For SQLite, enable datetime parsing
if "sqlite" in database_url:
    engine_kwargs["connect_args"] = {
        "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    }

# Create async engine with connection pooling
engine = create_async_engine(database_url, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Yields:
        AsyncSession: Database session for the request.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
