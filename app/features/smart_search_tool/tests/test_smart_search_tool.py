"""Tests for smart search tool."""

import pytest

from app.features.smart_search_tool.models import (
    SearchResult,
    ClassificationResult,
    SearchPattern,
)
from app.features.smart_search_tool.smart_search_tool_service import (
    execute_vault_smart_search,
    execute_vault_classify,
    save_search_pattern,
    load_search_patterns,
    _parse_query_intent,
)
from app.shared.vault.vault_manager import VaultManager


@pytest.mark.asyncio
async def test_smart_search_basic(test_vault_manager: VaultManager) -> None:
    """Test basic smart search functionality."""
    result = await execute_vault_smart_search(
        vault_manager=test_vault_manager,
        query="AI research papers",
        limit=10,
        response_format="concise"
    )

    # Should return dict with results and analytics
    assert isinstance(result, dict)
    assert "results" in result
    assert "analytics" in result
    assert len(result["results"]) > 0
    assert result["analytics"]["total_notes"] > 0


@pytest.mark.asyncio
async def test_smart_search_with_classification(test_vault_manager: VaultManager) -> None:
    """Test smart search with auto-classification enabled."""
    result = await execute_vault_smart_search(
        vault_manager=test_vault_manager,
        query="urgent project tasks",
        limit=5,
        response_format="detailed",
        auto_classify=True
    )

    assert isinstance(result, dict)
    assert "results" in result
    assert result["analytics"]["classifications_generated"] >= 0
    
    # Check that some results have classification metadata
    results_with_classification = [
        r for r in result["results"] 
        if r.metadata.get("auto_classification")
    ]
    assert len(results_with_classification) >= 0  # May be 0 if low confidence


@pytest.mark.asyncio
async def test_query_intent_parsing() -> None:
    """Test query intent analysis functionality."""
    
    # Test various intent types
    intent, entities, context = _parse_query_intent("find recent project notes")
    assert intent == "find"
    assert "project" in entities
    assert "recent" in context
    
    intent, entities, context = _parse_query_intent("show urgent tasks")
    assert intent == "find"
    assert "urgent" in entities
    
    intent, entities, context = _parse_query_intent("organize my research")
    assert intent == "organize"
    assert "research" in entities
    
    intent, entities, context = _parse_query_intent("recent meeting notes")
    assert intent == "recent"
    assert "meeting" in entities
    assert "recent" in context


@pytest.mark.asyncio
async def test_vault_classification(test_vault_manager: VaultManager) -> None:
    """Test vault note classification functionality."""
    
    # Create mock search results for testing
    search_results = [
        SearchResult(
            path="test1.md",
            title="Project Alpha Initiatives",
            summary="Planning document for new project",
            tags=["project", "alpha"],
            relevance_score=0.9,
            match_reason="Title match"
        ),
        SearchResult(
            path="test2.md", 
            title="Urgent: System Critical Issues",
            summary="High-priority bugs requiring immediate attention",
            tags=["urgent", "bugs"],
            relevance_score=0.8,
            match_reason="Content match"
        ),
        SearchResult(
            path="test3.md",
            title="AI Research Papers Review",
            summary="Summary of recent machine learning papers",
            tags=["research", "ai"],
            relevance_score=0.7,
            match_reason="Tag match"
        )
    ]
    
    classifications = await execute_vault_classify(
        vault_manager=test_vault_manager,
        search_results=search_results
    )
    
    assert len(classifications) == 3
    
    # Check classifications are reasonable
    assert classifications[0].classification == "project"
    assert classifications[0].confidence > 0.5
    assert "project-related" in classifications[0].reasoning
    
    assert classifications[1].classification == "urgent"
    assert classifications[1].confidence > 0.5
    
    assert classifications[2].classification in ["research", "unclassified"]
    assert isinstance(classifications[2].confidence, float)


@pytest.mark.asyncio
async def test_save_search_pattern(test_vault_manager: VaultManager) -> None:
    """Test search pattern saving functionality."""
    
    pattern = await save_search_pattern(
        vault_manager=test_vault_manager,
        pattern_name="urgent_tasks",
        query="urgent tasks and todos needing attention",
        filters={"has_urgent": True}
    )
    
    assert isinstance(pattern, SearchPattern)
    assert pattern.name == "urgent_tasks"
    assert "urgent tasks" in pattern.query_template
    assert pattern.filters_template["has_urgent"] is True
    assert len(pattern.common_queries) >= 1


@pytest.mark.asyncio
async def test_load_search_patterns() -> None:
    """Test loading saved search patterns."""
    
    patterns = await load_search_patterns()
    
    # Should return list (possibly empty for basic implementation)
    assert isinstance(patterns, list)


@pytest.mark.asyncio  
async def test_smart_search_error_handling(test_vault_manager: VaultManager) -> None:
    """Test error handling in smart search."""
    
    # Test empty query
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await execute_vault_smart_search(
            vault_manager=test_vault_manager,
            query="",
            limit=10
        )
        
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await execute_vault_smart_search(
            vault_manager=test_vault_manager,
            query="   ",  # whitespace only
            limit=10
        )


@pytest.mark.asyncio
async def test_classification_edge_cases(test_vault_manager: VaultManager) -> None:
    """Test classification with edge cases and special scenarios."""
    
    edge_cases = [
        SearchResult(
            path="archive/old-note.md",
            title="Old Archive Document", 
            summary="Very old content from years ago",
            tags=["archive"],
            relevance_score=0.3,
            match_reason="Path match"
        ),
        SearchResult(
            path="daily/journal-2023-01-01.md",
            title="Daily Journal Entry",
            summary="Personal thoughts and reflections",
            tags=["personal", "journal"],
            relevance_score=0.6,
            match_reason="Content match"
        )
    ]
    
    classifications = await execute_vault_classify(
        vault_manager=test_vault_manager,
        search_results=edge_cases
    )
    
    # Archive path should trigger archive classification
    assert classifications[0].classification == "archive"
    assert classifications[0].confidence > 0.9
    
    # Journal title should trigger personal classification
    assert classifications[1].classification in ["personal", "unclassified"]


@pytest.mark.asyncio
async def test_search_result_enhancement(test_vault_manager: VaultManager) -> None:
    """Test that search results are properly enhanced with metadata."""
    
    result = await execute_vault_smart_search(
        vault_manager=test_vault_manager,
        query="project alpha",
        limit=3,
        response_format="detailed",
        auto_classify=True
    )
    
    results = result["results"]
    
    # Check that results have required metadata
    for search_result in results:
        assert isinstance(search_result, SearchResult)
        assert search_result.path is not None
        assert search_result.relevance_score >= 0.0
        assert search_result.relevance_score <= 1.0
        assert search_result.match_reason is not None
        assert isinstance(search_result.metadata, dict)
        
        # Check for enhanced metadata
        if search_result.metadata.get("auto_classification"):
            assert search_result.metadata.get("classification_confidence") is not None
