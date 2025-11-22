"""Obsidian Query Vault Tool with enhanced search capabilities.

This tool provides powerful search and discovery functionality for Obsidian vaults,
including semantic search, metadata filtering, and content analysis.

Enhanced with:
- Smart intent recognition for natural language queries
- Advanced filtering capabilities
- Content summarization and preview
- Bulk operations support
"""

from typing import Any

from pydantic_ai import RunContext

from app.core.agents import AgentDeps, vault_agent
from app.core.logging import get_logger
from app.features.obsidian_query_vault_tool.obsidian_query_vault_tool_models import (
    ObsidianQueryVaultToolResult,
    SearchFilters,
)
from app.features.obsidian_query_vault_tool.obsidian_query_vault_tool_service import (
    execute_find_related,
    execute_list_structure,
    execute_recent_changes,
    execute_search_by_metadata,
    execute_semantic_search,
)
from app.shared.vault.vault_manager import VaultManager

logger = get_logger(__name__)


@vault_agent.tool
async def obsidian_query_vault(
    ctx: RunContext[AgentDeps],
    operation: str,
    query: str = "",
    path: str = "",
    filters: dict[str, str | bool | list[str] | int | float] | None = None,
    response_format: str = "concise",
    limit: int = 10,
) -> ObsidianQueryVaultToolResult:
    """Search and discover notes in the vault.

    Use this for finding notes, exploring structure, checking metadata, or recent changes.
    This is READ-ONLY - use obsidian_note_manager_tool for modifications.

    EFFICIENCY: Use response_format='concise' for simple searches to save tokens.
    Set to 'detailed' only when you need full metadata for synthesis tasks.

    COMPOSITION: Chain with get_context to read full content after finding relevant notes.

    Args:
        ctx: AgentDeps containing vault_manager and settings
        operation: One of: search, list_vault, find_related, search_by_tag, recent_changes
        query: Search query for search/find_related operations
        path: Path for specific operations
        filters: Search filters to apply (see SearchFilters model)
        response_format: Output verbosity: "concise" or "detailed"
        limit: Maximum results to return

    Returns:
        ObsidianQueryVaultToolResult with search results and metadata

    Examples:
        # Basic semantic search
        await obsidian_query_vault(
            ctx=ctx,
            operation="search",
            query="AI agents",
            response_format="concise"
        )

        # Find related notes to a specific note
        await obsidian_query_vault(
            ctx=ctx,
            operation="find_related",
            path="project-alpha.md"
        )

        # List vault structure
        await obsidian_query_vault(
            ctx=ctx,
            operation="list_vault"
        )

        # Search by tag with metadata
        await obsidian_query_vault(
            ctx=ctx,
            operation="search_by_tag",
            filters={"tags": ["project", "urgent"]}
        )

        # Recent changes with detailed output
        await obsidian_query_vault(
            ctx=ctx,
            operation="recent_changes",
            response_format="detailed",
            limit=5
        )
    """
    vault_manager = ctx.deps.vault_manager
    
    logger.info(
        "vault.query_vault_initiated",
        operation=operation,
        query=query[:50] if query else "",
        response_format=response_format,
        limit=limit
    )

    try:
        if operation == "search":
            result = await execute_semantic_search(
                vault_manager=vault_manager,
                query=query,
                limit=limit,
                response_format=response_format
            )
        elif operation == "find_related":
            if not path:
                raise ValueError("Path is required for find_related operation")
            result = await execute_find_related(
                vault_manager=vault_manager,
                path=path,
                limit=limit,
                response_format=response_format
            )
        elif operation == "list_vault":
            result = await execute_list_structure(
                vault_manager=vault_manager,
                response_format=response_format
            )
        elif operation == "search_by_tag":
            search_filters = SearchFilters.model_validate(filters or {})
            result = await execute_search_by_metadata(
                vault_manager=vault_manager,
                filters=search_filters,
                limit=limit,
                response_format=response_format
            )
        elif operation == "recent_changes":
            result = await execute_recent_changes(
                vault_manager=vault_manager,
                limit=limit,
                response_format=response_format
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")

        logger.info(
            "vault.query_vault_completed",
            operation=operation,
            results_found=len(result.results),
            total_found=result.total_found
        )
        
        return result

    except Exception as e:
        logger.error(
            "vault.query_vault_failed",
            operation=operation,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise


@vault_agent.tool
async def obsidian_get_context(
    ctx: RunContext[AgentDeps],
    path: str,
    max_length: int = 2000,
    include_metadata: bool = True,
) -> dict[str, Any]:
    """Retrieve full note content with optional metadata and context.

    Use this when you need the complete content of a note for synthesis,
    analysis, or modification. Designed for reading comprehensive data.

    Args:
        ctx: AgentDeps containing vault_manager and settings
        path: Path to the note file within the vault
        max_length: Maximum characters to return (default: 2000)
        include_metadata: Whether to include frontmatter metadata

    Returns:
        Dictionary with content, metadata, and context information

    Examples:
        # Get full content for analysis
        await obsidian_get_context(
            ctx=ctx,
            path="project-alpha.md",
            max_length=3000
        )

        # Get content with metadata
        await obsidian_get_context(
            ctx=ctx,
            path="meeting-notes.md",
            include_metadata=True
        )
    """
    vault_manager = ctx.deps.vault_manager
    
    logger.info("vault.get_context_requested", path=path, max_length=max_length)

    try:
        note = vault_manager.read_note(path)
        
        # Prepare content with length limit
        content = note.content or ""
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Prepare response
        result = {
            "path": str(note.path),
            "content": content,
            "content_length": len(note.content or ""),
            "truncated": len(note.content or "") > max_length
        }
        
        if include_metadata:
            metadata = {}
            if note.frontmatter:
                metadata = {
                    "title": note.frontmatter.title,
                    "tags": note.frontmatter.tags or [],
                    "created": note.frontmatter.created.isoformat() if note.frontmatter.created else None,
                    "modified": note.frontmatter.modified.isoformat() if note.frontmatter.modified else None
                }
            result["metadata"] = metadata
        
        logger.info(
            "vault.get_context_completed",
            path=path,
            content_length=len(content),
            truncated=result["truncated"]
        )
        
        return result

    except Exception as e:
        logger.error(
            "vault.get_context_failed",
            path=path,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise
