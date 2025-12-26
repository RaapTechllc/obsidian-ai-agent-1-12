"""Service layer for conversation business logic.

This module provides CRUD operations for conversations and messages.
All database operations are async and use SQLAlchemy 2.0 syntax.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.conversations.models import Conversation, Message
from app.conversations.schemas import ConversationCreate, ConversationUpdate, MessageCreate
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_conversation(
    db: AsyncSession,
    conversation_in: ConversationCreate,
) -> Conversation:
    """Create a new conversation.

    Args:
        db: Database session.
        conversation_in: Conversation creation data.

    Returns:
        Created conversation instance.

    Raises:
        ValidationError: If session_id already exists.
    """
    # Generate session_id if not provided
    session_id = conversation_in.session_id or str(uuid.uuid4())

    # Check if session_id already exists
    result = await db.execute(select(Conversation).where(Conversation.session_id == session_id))
    if result.scalar_one_or_none() is not None:
        logger.error(
            "conversations.create_failed", error="Session ID already exists", session_id=session_id
        )
        raise ValidationError(f"Conversation with session_id '{session_id}' already exists")

    # Create conversation
    conversation = Conversation(session_id=session_id, title=conversation_in.title)

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    logger.info(
        "conversations.created", conversation_id=conversation.id, session_id=conversation.session_id
    )

    return conversation


async def get_conversation_by_session_id(
    db: AsyncSession,
    session_id: str,
    include_messages: bool = True,
) -> Conversation:
    """Get conversation by session_id.

    Args:
        db: Database session.
        session_id: Conversation session identifier.
        include_messages: Whether to eager load messages.

    Returns:
        Conversation instance.

    Raises:
        NotFoundError: If conversation not found.
    """
    query = select(Conversation).where(Conversation.session_id == session_id)

    if include_messages:
        query = query.options(selectinload(Conversation.messages))

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise NotFoundError(f"Conversation with session_id '{session_id}' not found")

    return conversation


async def get_conversation_by_id(
    db: AsyncSession,
    conversation_id: int,
    include_messages: bool = True,
) -> Conversation:
    """Get conversation by primary key ID.

    Args:
        db: Database session.
        conversation_id: Conversation primary key.
        include_messages: Whether to eager load messages.

    Returns:
        Conversation instance.

    Raises:
        NotFoundError: If conversation not found.
    """
    query = select(Conversation).where(Conversation.id == conversation_id)

    if include_messages:
        query = query.options(selectinload(Conversation.messages))

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise NotFoundError(f"Conversation with id {conversation_id} not found")

    return conversation


async def list_conversations(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Conversation], int]:
    """List conversations with pagination.

    Args:
        db: Database session.
        offset: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        Tuple of (conversations list, total count).
    """
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Conversation))
    total = count_result.scalar_one()

    # Get paginated conversations (without messages for performance)
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
    )
    conversations = list(result.scalars().all())

    logger.info(
        "conversations.list_completed",
        total=total,
        returned=len(conversations),
        offset=offset,
        limit=limit,
    )

    return conversations, total


async def update_conversation(
    db: AsyncSession,
    conversation_id: int,
    conversation_update: ConversationUpdate,
) -> Conversation:
    """Update conversation metadata.

    Args:
        db: Database session.
        conversation_id: Conversation primary key.
        conversation_update: Update data.

    Returns:
        Updated conversation instance.

    Raises:
        NotFoundError: If conversation not found.
    """
    conversation = await get_conversation_by_id(db, conversation_id, include_messages=False)

    # Update fields
    conversation.title = conversation_update.title
    conversation.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(conversation)

    logger.info(
        "conversations.updated",
        conversation_id=conversation.id,
        session_id=conversation.session_id,
        new_title=conversation.title,
    )

    return conversation


async def delete_conversation(
    db: AsyncSession,
    conversation_id: int,
) -> Conversation:
    """Delete conversation and all its messages (cascade).

    Args:
        db: Database session.
        conversation_id: Conversation primary key.

    Returns:
        Deleted conversation instance (before deletion).

    Raises:
        NotFoundError: If conversation not found.
    """
    conversation = await get_conversation_by_id(db, conversation_id, include_messages=False)

    session_id = conversation.session_id

    await db.delete(conversation)
    await db.commit()

    logger.info("conversations.deleted", conversation_id=conversation_id, session_id=session_id)

    return conversation


async def add_message(
    db: AsyncSession,
    message_in: MessageCreate,
) -> Message:
    """Add a message to a conversation.

    Args:
        db: Database session.
        message_in: Message creation data.

    Returns:
        Created message instance.
    """
    message = Message(
        conversation_id=message_in.conversation_id,
        role=message_in.role,
        content=message_in.content,
        prompt_tokens=message_in.prompt_tokens,
        completion_tokens=message_in.completion_tokens,
    )

    db.add(message)

    # Update conversation.updated_at timestamp
    conversation = await get_conversation_by_id(
        db, message_in.conversation_id, include_messages=False
    )
    conversation.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(message)

    logger.info(
        "conversations.message_added",
        conversation_id=message_in.conversation_id,
        message_id=message.id,
        role=message.role,
    )

    return message


async def auto_generate_title(
    db: AsyncSession,
    conversation_id: int,
    first_user_message: str,
    max_length: int = 50,
) -> Conversation:
    """Auto-generate conversation title from first user message.

    Args:
        db: Database session.
        conversation_id: Conversation primary key.
        first_user_message: First user message content.
        max_length: Maximum title length.

    Returns:
        Updated conversation instance.
    """
    conversation = await get_conversation_by_id(db, conversation_id, include_messages=False)

    # Only auto-generate if title is None
    if conversation.title is None:
        # Truncate to max_length, add ellipsis if needed
        title = first_user_message.strip()
        if len(title) > max_length:
            title = title[: max_length - 3] + "..."

        conversation.title = title
        conversation.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(conversation)

        logger.info(
            "conversations.title_auto_generated",
            conversation_id=conversation.id,
            session_id=conversation.session_id,
            title=title,
        )

    return conversation


async def get_message_count(
    db: AsyncSession,
    conversation_id: int,
) -> int:
    """Get count of messages in a conversation.

    Args:
        db: Database session.
        conversation_id: Conversation primary key.

    Returns:
        Number of messages in conversation.
    """
    result = await db.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
    )
    return result.scalar_one()
