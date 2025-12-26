"""Pydantic schemas for conversation API requests/responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ========== Message Schemas ==========


class MessageBase(BaseModel):
    """Base schema for message data."""

    role: Literal["user", "assistant", "system"]
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a new message (internal use only).

    Used by the service layer to add messages to conversations.
    """

    conversation_id: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class MessageResponse(MessageBase):
    """Schema for message response in API.

    Returned when fetching conversation details or message history.

    Attributes:
        id: Message primary key.
        role: Message role (user, assistant, or system).
        content: Message text content.
        created_at: When the message was created.
        prompt_tokens: Token count for prompt (user messages).
        completion_tokens: Token count for completion (assistant messages).
    """

    id: int
    created_at: datetime
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    model_config = {"from_attributes": True}


# ========== Conversation Schemas ==========


class ConversationBase(BaseModel):
    """Base schema for conversation data."""

    title: str | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation.

    Args:
        session_id: Optional client-provided UUID. Auto-generated if not provided.
        title: Optional conversation title. Auto-generated from first message if not provided.
    """

    session_id: str | None = Field(
        default=None,
        description="Optional session ID. If not provided, one will be generated.",
    )


class ConversationUpdate(BaseModel):
    """Schema for updating conversation metadata.

    Currently only supports updating the title field.
    Session ID is immutable after creation.
    """

    title: str = Field(..., min_length=1, max_length=255)


class ConversationSummary(ConversationBase):
    """Schema for conversation list response (without messages).

    Used for paginated list endpoints where full message history
    would be too expensive to load.

    Attributes:
        id: Conversation primary key.
        session_id: UUID for conversation tracking.
        title: Conversation title (auto-generated or user-provided).
        created_at: When conversation was created.
        updated_at: When conversation was last updated.
        message_count: Number of messages in this conversation.
    """

    id: int
    session_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0, description="Number of messages in this conversation")

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationBase):
    """Schema for single conversation response (with full messages).

    Used when fetching a single conversation by ID, includes
    complete message history.

    Attributes:
        id: Conversation primary key.
        session_id: UUID for conversation tracking.
        title: Conversation title (auto-generated or user-provided).
        created_at: When conversation was created.
        updated_at: When conversation was last updated.
        messages: Full message history ordered by created_at.
    """

    id: int
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ========== Delete Response ==========


class ConversationDeleteResponse(BaseModel):
    """Schema for delete operation response.

    Confirms successful deletion and provides the deleted conversation's
    identifiers for client-side cleanup.

    Attributes:
        message: Success message.
        deleted_id: Primary key of deleted conversation.
        deleted_session_id: Session ID of deleted conversation.
    """

    message: str
    deleted_id: int
    deleted_session_id: str
