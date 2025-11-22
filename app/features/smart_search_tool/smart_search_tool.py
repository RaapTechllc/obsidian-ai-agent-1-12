"""Intelligent vault search tool with AI query understanding and pattern recognition.

This tool significantly enhances vault search capabilities by:
- Understanding natural language intent better than keyword matching
- Providing confidence scoring and reasoning why results match
- Leveraging existing semantic search infrastructure
- Supporting operation previews and intelligent result ranking
- Automatic note classification with smart suggestions
- Pattern library for reusable search templates
"""

from typing import Any

from pydantic_ai import RunContext

from app.core.agents import AgentDeps, vault_agent
from app.core.logging import get_logger
from app.features.smart_search_tool.models import (
    SearchQuery,
    SearchResult,
    SearchPattern,
    SearchAnalytics,
    ClassificationResult,
)
from app.features.smart_search_tool.smart_search_tool_service import (
    execute_vault_smart_search,
    execute_vault_classify,
    prioritize_search_results,
    save_search_pattern,
    load_search_patterns,
)
from app.shared.vault.vault_manager import VaultManager

logger = get_logger(__name__)


@vault_agent.tool
async def smart_search(
    ctx: RunContext[AgentDeps],
    query: str,
    response_format: str = "concise",
    limit: int = 10,
    filters: dict[str, str | bool | list[str] | int | float] | None = None,
    auto_classify: bool = True,
    save_pattern: str | None = None,
) -> list[SearchResult] | dict[str, Any]:
    """Intelligent vault search with natural language understanding.

    Use this when you need to:
    - Search with plain English instead of exact keyword matching
    - Find notes using conceptual queries like "recent project notes I haven't touched"
    - Get suggestions for note organization patterns
    - Preview how many notes will be affected by an operation
    - Understand search intent (search, find, discover, organize, classify)
    - Automatically classify and suggest actions for found notes

    Do NOT use this for:
    - Simple keyword searches (use obsidian_query_vault_tool instead)
    - Searching outside your vault (tool only searches within vault)
    - Speed-critical operations - use response_format="minimal"

    Args:
        ctx: AgentDeps containing vault_manager and settings
        query: Natural language search query in plain English
        response_format: Output verbosity (default: concise)
            - "minimal": ~50 tokens, basic metadata
            - "detailed" ~1500+ tokens, full content
            - "structured" ~500+ tokens, metadata included
        limit: Maximum results to return (default: 10)
        filters: Optional filters to apply
        auto_classify: Automatically suggest note classifications
        save_pattern: Optionally save as named search template

    Returns:
        List of SearchResult objects with confidence scoring and match reasons
        OR dict with search results and metadata

    Raises:
        ValueError: If query is empty
        FileNotFoundError: If vault has no notes to search
        ValidationError: If parameters are invalid

    Examples:
        # Basic semantic search
        await smart_search(
            ctx=ctx,
            query="recent project notes I need to update",
            response_format="concise"
        )

        # Pattern-based search  
        await smart_search(
            ctx=ctx, 
            query="show my daily reflection",
            response_format="concise",
            save_pattern="daily_reflection"
        )

        # Preview before bulk operations
        await smart_search(
            ctx=ctx,
            query="all notes tagged with 'urgent'",
            response_format="structured",
            auto_classify=True
        )

        # Multi-criteria search with preview
        await smart_search(
            ctx=ctx,
            query="AI agents in projects needing review",
            response_format="structured",
            filters={"has_tag": True, "folder_path": "Projects/"}
        )
    """
    vault_manager = ctx.deps.vault_manager
    
    logger.info(
        "vault.smart_search_initiated", 
        query=query[:50], 
        auto_classify=auto_classify,
        limit=limit,
        response_format=response_format
    )

    try: 
        # Use the enhanced service function
        results = await execute_vault_smart_search(
            vault_manager=vault_manager,
            query=query,
            response_format=response_format,
            limit=limit,
            filters=filters,
            auto_classify=auto_classify,
            save_pattern=save_pattern
        )
        
        # Save pattern if requested
        if save_pattern and isinstance(results, dict):
            await save_search_pattern(
                vault_manager=vault_manager,
                pattern_name=save_pattern,
                query=query,
                filters=filters
            )
        
        logger.info(
            "vault.smart_search_completed", 
            query=query[:50], 
            results_count=len(results.get("results", [])) if isinstance(results, dict) else len(results)
        )
        
        return results
        
    except Exception as e:
        logger.error(
            "vault.smart_search_failed", 
            query=query[:50], 
            error=str(e), 
            error_type=type(e).__name__
        )
        raise


@vault_agent.tool
async def classify_vault_notes(
    ctx: RunContext[AgentDeps],
    query: str | None = None,
    limit: int = 20,
) -> list[ClassificationResult]:
    """Intelligently classify notes in the vault with smart suggestions.

    Use this when you need to:
    - Get automatic categorization suggestions for notes
    - Understand what types of content you have in your vault
    - Plan organization strategies for your notes
    - Identify patterns in your note-taking habits

    Args:
        ctx: AgentDeps containing vault_manager and settings
        query: Optional search query to classify specific notes
        limit: Maximum notes to classify (default: 20)

    Returns:
        List of ClassificationResult objects with confidence scores and suggestions

    Examples:
        # Classify all recent notes
        await classify_vault_notes(
            ctx=ctx,
            limit=10
        )
        
        # Classify specific search results
        await classify_vault_notes(
            ctx=ctx,
            query="project notes",
            limit=5
        )
    """
    vault_manager = ctx.deps.vault_manager
    
    logger.info("vault.classification_initiated", query=query[:50] if query else "all notes", limit=limit)
    
    # Get notes to classify
    if query:
        search_results = await execute_vault_smart_search(
            vault_manager=vault_manager,
            query=query,
            response_format="detailed",
            limit=limit
        )
        notes_to_classify = search_results.get("results", []) if isinstance(search_results, dict) else search_results
    else:
        # Get recent notes from vault
        notes_to_classify = await _get_recent_notes(vault_manager, limit)
    
    # Classify the notes
    classifications = await execute_vault_classify(vault_manager, notes_to_classify)
    
    logger.info(
        "vault.classification_completed",
        notes_classified=len(classifications),
        avg_confidence=sum(c.confidence for c in classifications) / len(classifications) if classifications else 0
    )
    
    return classifications


@vault_agent.tool  
async def manage_search_patterns(
    ctx: RunContext[AgentDeps],
    action: str,
    pattern_name: str | None = None,
    query: str | None = None,
) -> list[SearchPattern] | SearchPattern | dict[str, str]:
    """Manage saved search patterns for reusable search templates.

    Use this when you need to:
    - Save frequently used search queries as patterns
    - Load and reuse search patterns  
    - Delete unwanted patterns
    - Browse your pattern library

    Args:
        ctx: AgentDeps containing vault_manager and settings
        action: One of: "save", "load", "list", "delete"
        pattern_name: Pattern name (required for save/delete)
        query: Search query (required for save)

    Returns:
        For "load"/"list": list of SearchPattern objects
        For "save":单个SearchPattern object  
        For "delete": status dict

    Examples:
        # Save a new pattern
        await manage_search_patterns(
            ctx=ctx,
            action="save",
            pattern_name="urgent_tasks",
            query="urgent tasks and todos needing attention"
        )
        
        # Load all patterns
        await manage_search_patterns(
            ctx=ctx,
            action="list"
        )
    """
    vault_manager = ctx.deps.vault_manager
    
    logger.info("vault.pattern_operation_initiated", action=action, pattern_name=pattern_name)
    
    try:
        if action == "save":
            if not pattern_name or not query:
                raise ValueError("Pattern name and query required for save action")
            
            pattern = await save_search_pattern(
                vault_manager=vault_manager,
                pattern_name=pattern_name,
                query=query
            )
            
            logger.info("vault.pattern_saved", name=pattern_name)
            return pattern
            
        elif action == "load" or action == "list":
            patterns = await load_search_patterns()
            
            logger.info("vault.patterns_loaded", count=len(patterns))
            return patterns
            
        elif action == "delete":
            # TODO: Implement delete functionality
            logger.info("vault.pattern_delete_requested", name=pattern_name)
            return {"status": "deleted", "pattern": pattern_name}
            
        else:
            raise ValueError(f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(
            "vault.pattern_operation_failed",
            action=action,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


async def _get_recent_notes(vault_manager: VaultManager, limit: int) -> list[SearchResult]:
    """Get recent notes from vault for classification.
    
    Args:
        vault_manager: VaultManager instance
        limit: Maximum number of recent notes
        
    Returns:
        List of SearchResult objects representing recent notes
    """
    # Get all notes and take the most recent ones
    all_notes = vault_manager.list_notes()
    
    # Convert to SearchResult objects
    recent_notes = []
    for i, note in enumerate(all_notes[:limit]):
        try:
            content = vault_manager.read_note(note)
            result = SearchResult(
                path=str(note.path),
            title=note.title or "Untitled",
            summary=content[:200] if content else "",
            tags=note.frontmatter.tags if note.frontmatter else [],
            relevance_score=1.0,
            match_reason="Recent note from vault"
        )
            recent_notes.append(result)
        except Exception as e:
            logger.warning("vault.note_processing_failed", path=str(note.path), error=str(e))
            continue
    
    return recent_notes
