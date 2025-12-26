"""SQLAlchemy models for conversation persistence.

This module defines the database schema for storing conversation history:
- Conversation: Session metadata and title
- Message: Individual messages (user/assistant/system) with token tracking
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from collections.abc import Sequence


class Conversation(Base, TimestampMixin):
    """Conversation session tracking.

    Stores conversation metadata and links to message history.
    Each conversation has a unique session_id used for client correlation
    via X-Conversation-ID header.

    Attributes:
        id: Primary key.
        session_id: UUID for client-provided conversation tracking.
        title: Auto-generated from first user message or user-provided.
        messages: One-to-many relationship to Message records.
        created_at: Timestamp when conversation created (from TimestampMixin).
        updated_at: Timestamp of last update (from TimestampMixin).
    """

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Session identifier (UUID) - indexed for fast lookups via X-Conversation-ID header
    session_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Title - auto-generated from first user message or user-provided
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)

    # Relationships
    messages: Mapped["Sequence[Message]"] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    # Inherited from TimestampMixin: created_at, updated_at


class Message(Base, TimestampMixin):
    """Individual message in a conversation.

    Stores user/assistant/system messages with token usage tracking.
    Messages are immutable once created (no updates).

    Attributes:
        id: Primary key.
        conversation_id: Foreign key to conversations table.
        role: Message role - "user", "assistant", or "system".
        content: Message text content.
        prompt_tokens: Token count for prompt (user messages).
        completion_tokens: Token count for completion (assistant messages).
        conversation: Many-to-one relationship to Conversation.
        created_at: Timestamp when message created (from TimestampMixin).
        updated_at: Timestamp of last update (from TimestampMixin).
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to conversation
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message fields
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Token usage tracking (optional, nullable)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # Inherited from TimestampMixin: created_at, updated_at
