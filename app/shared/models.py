"""Shared database models and mixins."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(UTC)


class TZDateTime(TypeDecorator[datetime]):
    """Custom DateTime type that ensures timezone-aware datetimes.

    This handles the fact that SQLite doesn't preserve timezone info
    natively, while PostgreSQL does.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:  # noqa: ARG002
        """Convert datetime to UTC before storing."""
        if value is not None and value.tzinfo is None:
            # If naive, assume UTC
            value = value.replace(tzinfo=UTC)
        return value

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:  # noqa: ARG002
        """Ensure datetime returned from DB is timezone-aware."""
        if value is not None and value.tzinfo is None:
            # If naive (from SQLite), add UTC timezone
            value = value.replace(tzinfo=UTC)
        return value


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps.

    All models should inherit this mixin to automatically track
    when records are created and updated.

    Example:
        class Product(Base, TimestampMixin):
            __tablename__ = "products"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(200))
    """

    @declared_attr.directive
    def created_at(cls) -> Mapped[datetime]:
        """Timestamp when the record was created."""
        return mapped_column(TZDateTime(timezone=True), default=utcnow, nullable=False)

    @declared_attr.directive
    def updated_at(cls) -> Mapped[datetime]:
        """Timestamp when the record was last updated."""
        return mapped_column(
            TZDateTime(timezone=True),
            default=utcnow,
            onupdate=utcnow,
            nullable=False,
        )
