"""API routes for conversation management.

Provides CRUD endpoints for conversation history:
- List conversations with pagination
- Get single conversation with messages
- Update conversation metadata (title)
- Delete conversation and messages
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations import service
from app.conversations.schemas import (
    ConversationDeleteResponse,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
)
from app.core.database import get_db
from app.core.logging import get_logger
from app.shared.schemas import PaginatedResponse, PaginationParams

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.get("", response_model=PaginatedResponse[ConversationSummary])
async def list_conversations(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ConversationSummary]:
    """List all conversations with pagination.

    Returns conversation summaries without full message history for performance.
    Use GET /v1/conversations/{id} to fetch full conversation with messages.

    Args:
        pagination: Pagination parameters (page, page_size).
        db: Database session.

    Returns:
        Paginated list of conversation summaries with message counts.
    """
    logger.info("conversations.list_started", page=pagination.page, page_size=pagination.page_size)

    conversations, total = await service.list_conversations(
        db, offset=pagination.offset, limit=pagination.page_size
    )

    # Build summary responses with message counts
    summaries = []
    for conv in conversations:
        message_count = await service.get_message_count(db, conv.id)
        # Build summary from ORM model
        summary = ConversationSummary.model_validate(
            {
                "id": conv.id,
                "session_id": conv.session_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": message_count,
            }
        )
        summaries.append(summary)

    return PaginatedResponse(
        items=summaries,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """Get a single conversation with full message history.

    Args:
        conversation_id: Conversation primary key.
        db: Database session.

    Returns:
        Conversation details with all messages ordered by created_at.

    Raises:
        404: Conversation not found.
    """
    logger.info("conversations.get_started", conversation_id=conversation_id)

    conversation = await service.get_conversation_by_id(db, conversation_id, include_messages=True)

    return ConversationDetail.model_validate(conversation)


@router.patch("/{conversation_id}", response_model=ConversationDetail)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """Update conversation metadata (title).

    Args:
        conversation_id: Conversation primary key.
        conversation_update: Update data.
        db: Database session.

    Returns:
        Updated conversation details with messages.

    Raises:
        404: Conversation not found.
        422: Validation error (empty title, etc.).
    """
    logger.info(
        "conversations.update_started",
        conversation_id=conversation_id,
        new_title=conversation_update.title,
    )

    conversation = await service.update_conversation(db, conversation_id, conversation_update)

    # Reload with messages for response
    conversation = await service.get_conversation_by_id(db, conversation_id, include_messages=True)

    return ConversationDetail.model_validate(conversation)


@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
) -> ConversationDeleteResponse:
    """Delete a conversation and all its messages.

    This is a hard delete operation. All messages will be permanently removed
    via cascade delete. This action cannot be undone.

    Args:
        conversation_id: Conversation primary key.
        db: Database session.

    Returns:
        Deletion confirmation with deleted conversation identifiers.

    Raises:
        404: Conversation not found.
    """
    logger.info("conversations.delete_started", conversation_id=conversation_id)

    conversation = await service.delete_conversation(db, conversation_id)

    return ConversationDeleteResponse(
        message="Conversation deleted successfully",
        deleted_id=conversation.id,
        deleted_session_id=conversation.session_id,
    )
