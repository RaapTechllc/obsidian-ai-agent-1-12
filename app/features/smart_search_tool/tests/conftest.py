"""Fixtures for smart search tool tests."""

import pytest

from app.features.smart_search_tool.models import (
    SearchResult,
    ClassificationResult,
)
from app.shared.vault.vault_manager import VaultManager


@pytest.fixture
def search_result_sample() -> SearchResult:
    """Sample search result for testing."""
    return SearchResult(
        path="test/project-alpha.md",
        title="Project Alpha Roadmap",
        summary="Planning document for Project Alpha initiatives and timeline",
        tags=["project", "alpha", "roadmap"],
        relevance_score=0.85,
        match_reason="Title + content match",
        metadata={
            "intent_type": "find",
            "entities_found": ["project"],
            "context_matches": []
        }
    )


@pytest.fixture
def classification_result_sample() -> ClassificationResult:
    """Sample classification result for testing."""
    return ClassificationResult(
        classification="project",
        confidence=0.85,
        reasoning="Title contains project-related keywords",
        suggested_actions=[
            "Add to Projects folder", 
            "Add project tag", 
            "Link to project timeline"
        ]
    )


@pytest.fixture async
def test_search_results(test_vault_manager: VaultManager) -> list[SearchResult]:
    """Multiple search results for comprehensive testing."""
    return [
        SearchResult(
            path="test/project-alpha.md",
            title="Project Alpha Roadmap", 
            summary="Planning document for Project Alpha",
            tags=["project", "alpha"],
            relevance_score=0.90,
            match_reason="Title match"
        ),
        SearchResult(
            path="test/urgent-bug.md",
            title="URGENT: Critical System Bug",
            summary="High priority bug requiring immediate fix",
            tags=["urgent", "bug"],
            relevance_score=0.85,
            match_reason="Urgent content"
        ),
        SearchResult(
            path="test/research-notes.md",
            title="AI Research Papers Summary",
            summary="Analysis of recent machine learning research",
            tags=["research", "ai"],
            relevance_score=0.75,
            match_reason="Content relevance"
        ),
        SearchResult(
            path="archive/old-doc.md",
            title="Old Documentation",
            summary="Legacy content for reference only",
            tags=["archive", "legacy"],
            relevance_score=0.30,
            match_reason="Archive content"
        )
    ]
