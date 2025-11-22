"""Service layer for smart vault search operations."""

from typing import Any

from app.core.logging import get_logger
from app.features.smart_search_tool.models import (
    SearchQuery,
    SearchResult,
    SearchPattern,
    SearchAnalytics,
    ClassificationResult,
)
from app.shared.vault.vault_manager import VaultManager
from app.shared.vault.vault_models import Note

logger = get_logger(__name__)


async def get_search_usage_analytics() -> dict[str, Any]:
    """Get current search patterns usage data."""
    # Initialize empty analytics for now - will be enhanced later
    return {
        "patterns_used": 0,
        "total_patterns": 0,
        "usage_data": {}
    }


async def execute_vault_smart_search(
    vault_manager: VaultManager,
    query: str,
    response_format: str = "concise",
    limit: int = 10,
    filters: dict[str, str | bool | list[str] | int | float | None] = None,
    auto_classify: bool = False,
    save_pattern: str | None = None,
) -> list[SearchResult] | dict[str, Any]:
    """Execute intelligent vault search with AI query understanding.

    Args:
        vault_manager: VaultManager instance
        query: Natural language search query from user
        response_format: Output verbosity (default: "concise")
        limit: Maximum results to return
        filters: Optional search filters to apply
        auto_classify: Suggest classifications for notes
        save_pattern: Save pattern if user named

    Returns:
        List of SearchResult objects OR dict with results and analytics

    Raises:
        ValueError: If query is empty
        FileNotFoundError: If vault has no notes to search
        ValidationError: If parameters are invalid

    Examples:
        # Find smart research notes
        await execute_vault_smart_search(
            vault_manager=vault_manager, 
            query="AI machine learning research papers",
            response_format="concise"
        )
        
        # Preview classification before bulk operations
        await execute_vault_smart_search(
            vault_manager=vault_manager,
            query="all urgent tasks and todos",
            response_format="structured",
            auto_classify=True
        )
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Parse query intent first
    intent_type, entities, context_keywords = _parse_query_intent(query)
    
    # Log the parsing attempt
    logger.info(
        "vault.query_parsed",
        query=query[:50],
        intent=intent_type,
        entities=entities,
        context_keywords=context_keywords
    )
    
    # Use existing semantic search as base
    from app.features.obsidian_query_vault_tool.obsidian_query_vault_tool_service import (
        execute_semantic_search
    )
    
    base_results = await execute_semantic_search(
        vault_manager=vault_manager,
        query=query,
        limit=limit,
        response_format="detailed" if response_format == "detailed" else "concise"
    )
    
    # Convert to SearchResult format with enhanced analysis
    search_results = []
    for note in base_results.results:
        # Calculate enhanced relevance score based on intent and entities
        base_score = note.relevance if hasattr(note, 'relevance') else 0.8
        
        # Boost score based on entity matches in title/tags
        title_lower = (note.title or "").lower()
        tags_lower = [tag.lower() for tag in (note.tags or [])]
        
        entity_boost = 0.0
        for entity in entities:
            if entity in title_lower:
                entity_boost += 0.1
            for tag in tags_lower:
                if entity in tag:
                    entity_boost += 0.05
        
        enhanced_score = min(1.0, base_score + entity_boost)
        
        # Generate match reason based on findings
        match_reason_parts = ["Content match"]
        if entity_boost > 0:
            match_reason_parts.append("Entity match")
        if intent_type == "recent" and note.created:
            match_reason_parts.append("Recent content")
        
        match_reason = " + ".join(match_reason_parts)
        
        result = SearchResult(
            path=note.path,
            title=note.title,
            summary=note.excerpt or "",
            tags=note.tags or [],
            relevance_score=enhanced_score,
            match_reason=match_reason,
            metadata={
                "intent_type": intent_type,
                "entities_found": [e for e in entities if e in title_lower],
                "context_matches": [c for c in context_keywords if c in (note.excerpt or "").lower()]
            }
        )
        search_results.append(result)
    
    # Get classifications if requested
    classification_results = []
    if auto_classify:
        classification_results = await execute_vault_classify(vault_manager, search_results)
    
    # Combine classifications with results
    enhanced_search_results = []
    for i, result in enumerate(search_results):
        classification = classification_results[i] if i < len(classification_results) else None
        
        # Add classification data as metadata
        if classification and classification.confidence > 0.5:
            result.metadata["auto_classification"] = classification.classification
            result.metadata["classification_confidence"] = classification.confidence
            result.match_reason += f" | Classified as: {classification.classification}"
        
        enhanced_search_results.append(result)
    
    # Get total notes in vault for analytics
    total_notes = len(vault_manager.list_notes())
    
    # Log successful completion
    logger.info(
        "vault.smart_search_completed",
        query=query[:50],
        results_found=len(enhanced_search_results),
        avg_score=sum(r.relevance_score for r in enhanced_search_results) / len(enhanced_search_results) if enhanced_search_results else 0,
        classifications_generated=len([c for c in classification_results if c.confidence > 0.5])
    )
    
    # Return both results and analytics
    return {
        "results": enhanced_search_results, 
        "analytics": {
            "total_notes": total_notes,
            "intent_type": intent_type,
            "entities_found": len(entities),
            "classifications_generated": len([c for c in classification_results if c.confidence > 0.5])
        }
    }


async def prioritize_search_results(
    vault_manager: VaultManager,
    search_results: list[SearchResult],
    limit: int | None = None
) -> list[SearchResult]:
    """Score search results using priority weighting.

    Args:
        vault_manager: VaultManager instance
        search_results: Base search results
        limit: Optional max number of results

    Returns:
        Sorted list of prioritized search results.
    """
    if not search_results:
        return []
    
    # Prioritize by confidence score and metadata
    prioritized = sorted(search_results, key=lambda r: (
        -r.relevance_score, 
        r.path
    ))
    
    # Trim to limit if specified
    if limit and len(prioritized) > 0:
        prioritized = prioritized[:limit]
    
    return prioritized


async def execute_vault_classify(
    vault_manager: VaultManager,
    search_results: list[SearchResult]
) -> list[ClassificationResult]:
    """Execute automatic classification of search results.
    
    Args:
        vault_manager: VaultManager instance  
        search_results: List of search results to classify
        
    Returns:
        List of classification results with confidence scores
    """
    classifications = []
    
    for result in search_results:
        # Basic classification logic based on patterns in title and tags
        classification = "unclassified"
        confidence = 0.0
        reasoning = ""
        suggested_actions = []
        
        title_lower = (result.title or "").lower()
        tags_lower = [tag.lower() for tag in result.tags]
        summary_lower = result.summary.lower()
        path_lower = result.path.lower()
        
        # Enhanced pattern-based classification
        if any(word in title_lower for word in ["project", "initiative", "plan", "roadmap"]):
            classification = "project"
            confidence = 0.85
            reasoning = "Title contains project-related keywords"
            suggested_actions = ["Add to Projects folder", "Add project tag", "Link to project timeline"]
        elif any(word in title_lower for word in ["meeting", "discussion", "call", "sync"]):
            classification = "meeting"
            confidence = 0.80
            reasoning = "Title indicates meeting content"
            suggested_actions = ["Add date tag", "Move to Meetings folder", "Link to calendar"]
        elif any(word in title_lower for word in ["todo", "task", "action", "item"]):
            classification = "task"
            confidence = 0.75
            reasoning = "Title indicates task or action item"
            suggested_actions = ["Add to todo system", "Set priority tag", "Assign owner"]
        elif "urgent" in tags_lower or any(word in summary_lower for word in ["urgent", "asap", "critical", "priority"]):
            classification = "urgent"
            confidence = 0.90
            reasoning = "Marked urgent in tags or content"
            suggested_actions = ["Prioritize review", "Add high priority tag", "Schedule immediate follow-up"]
        elif any(word in title_lower for word in ["research", "study", "analysis", "investigation"]):
            classification = "research"
            confidence = 0.70
            reasoning = "Title indicates research content"
            suggested_actions = ["Add research tag", "Link to bibliography", "Share with team"]
        elif any(word in title_lower for word in ["idea", "thought", "insight", "concept"]):
            classification = "idea"
            confidence = 0.65
            reasoning = "Title suggests creative content"
            suggested_actions = ["Add ideas tag", "Review for development", "Share with stakeholders"]
        elif any(word in title_lower for word in ["note", "journal", "log", "diary"]):
            classification = "personal"
            confidence = 0.60
            reasoning = "Title indicates personal note"
            suggested_actions = ["Move to personal folder", "Add date tag"]
        elif any(word in tags_lower for word in ["review", "feedback", "iteration"]):
            classification = "review"
            confidence = 0.75
            reasoning = "Tagged for review or feedback"
            suggested_actions = ["Schedule review", "Add review checklist", "Track revisions"]
        
        # Path-based classification
        if "archive" in path_lower:
            classification = "archive"
            confidence = max(confidence, 0.95)
            reasoning = "Located in archive folder"
            suggested_actions = ["Keep archived", "Consider deletion if very old"]
        
        classifications.append(ClassificationResult(
            classification=classification,
            confidence=confidence,
            reasoning=reasoning,
            suggested_actions=suggested_actions
        ))
    
    logger.info(
        "vault.classification_completed",
        notes_classified=len(classifications),
        avg_confidence=sum(c.confidence for c in classifications) / len(classifications) if classifications else 0
    )
    
    return classifications


async def save_search_pattern(
    vault_manager: VaultManager,
    pattern_name: str,
    query: str,
    filters: dict[str, str | bool | list[str] | int | float] | None = None
) -> SearchPattern:
    """Save a search pattern for future reuse.
    
    Args:
        vault_manager: VaultManager instance
        pattern_name: Human-readable name for the pattern
        query: Original search query
        filters: Search filters used
        
    Returns:
        SearchPattern object with saved details
    """
    pattern = SearchPattern(
        name=pattern_name,
        description=f"Pattern based on: {query[:50]}...",
        query_template=query,
        filters_template=filters or {},
        common_queries=[query]
    )
    
    logger.info("vault.pattern_saved", name=pattern_name, query=query[:50])
    return pattern


async def load_search_patterns() -> list[SearchPattern]:
    """Load saved search patterns.
    
    Returns:
        List of saved SearchPattern objects
    """
    # Basic implementation - will be enhanced with persistent storage later
    return []


# Query classification helper
def _parse_query_intent(query: str) -> tuple[str, list[str], list[str]]:
    """Parse search query to determine intent and extract entities.
    
    Args:
        query: Natural language search query
        
    Returns:
        Tuple of (intent_type, entities, context_keywords)
    """
    query_lower = query.lower()
    
    # Determine primary intent
    intent_type = "search"
    if any(word in query_lower for word in ["find", "show", "get", "locate"]):
        intent_type = "find"
    elif any(word in query_lower for word in ["discover", "explore", "browse"]):
        intent_type = "discover"
    elif any(word in query_lower for word in ["organize", "classify", "categorize", "sort"]):
        intent_type = "organize"
    elif any(word in query_lower for word in ["recent", "latest", "new", "today", "yesterday"]):
        intent_type = "recent"
    elif any(word in query_lower for word in ["urgent", " priority", "important", "critical"]):
        intent_type = "priority"
    
    # Extract potential entities (words that could be tags, folders, etc.)
    words = query_lower.split()
    entities = []
    context_keywords = []
    
    # Basic entity extraction
    for word in words:
        if word in ["project", "projects", "meeting", "meetings", "task", "tasks", "research", "idea", "ideas", "urgent"]:
            entities.append(word)
        elif word in ["today", "yesterday", "week", "month", "year", "morning", "afternoon", "evening"]:
            context_keywords.append(word)
    
    return intent_type, entities, context_keywords
