"""Pydantic models for Obsidian Note Manager Tool."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class BulkOperationPreview(BaseModel):
    """Preview of what a bulk operation will affect."""

    operation_type: str = Field(..., description="Type of operation (bulk_tag, bulk_move, etc.)")
    target_notes: list[str] = Field(..., description="Notes that will be affected")
    changes: dict[str, str] | None = Field(
        default=None, description="Summary changes for each note"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Potential issues with this operation"
    )
    estimated_risk: Literal["low", "medium", "high"] = Field(
        default="medium", description="Risk level for this operation"
    )


class BulkOperationHistory(BaseModel):
    """Record of a completed bulk operation for undo functionality."""

    id: str = Field(..., description="Unique operation identifier")
    timestamp: str = Field(..., description="When operation was performed")
    operation: str = Field(..., description="Operation type that was executed")
    backup_data: dict[str, dict] = Field(..., description="Backup of original note states")
    affected_paths: list[str] = Field(..., description="Paths that were modified")
    success: bool = Field(..., description="Whether operation was successful")


class BulkOperationCriteria(BaseModel):
    """Criteria for finding notes in smart bulk operations."""

    tags: list[str] | None = Field(default=None, description="Notes with these tags")
    content_contains: str | None = Field(default=None, description="Notes containing this text")
    path_pattern: str | None = Field(default=None, description="Notes matching path pattern")
    created_after: str | None = Field(default=None, description="Notes created after this date")
    created_before: str | None = Field(default=None, description="Notes created before this date")
    has_tag: bool | None = Field(default=None, description="Has any tags (true) or has no tags (false)")
    folder_path: str | None = Field(default=None, description="Notes in this folder")
    limit: int | None = Field(default=None, description="Maximum notes to return")


class ObsidianNoteManagerToolResult(BaseModel):
    """Result returned by obsidian_note_manager_tool."""

    success: bool = Field(..., description="Whether operation completed successfully")
    operation: str = Field(..., description="Operation type that was executed")
    affected_count: int = Field(..., description="Number of items affected by operation")
    affected_paths: list[str] = Field(..., description="List of paths that were modified")
    message: str = Field(..., description="Human-readable summary of operation result")
    warnings: list[str] | None = Field(
        default=None, description="Non-fatal issues encountered during operation"
    )

    # For bulk operations
    partial_success: bool | None = Field(
        default=None,
        description="True if some items succeeded and some failed (bulk operations only)",
    )
    failures: list[dict[str, str]] | None = Field(
        default=None,
        description="List of failed items with reasons (bulk operations only). Format: [{'path': '...', 'reason': '...'}]",
    )
