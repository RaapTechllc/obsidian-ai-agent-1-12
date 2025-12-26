"""Fixtures for smart search tool tests."""

from pathlib import Path

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


@pytest.fixture
def test_vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault with test notes for smart search.

    Args:
        tmp_path: Pytest fixture providing temporary directory.

    Returns:
        Path to test vault root.
    """
    vault_root = tmp_path / "test_vault"
    vault_root.mkdir()

    # Create some test notes
    (vault_root / "project_alpha.md").write_text(
        """---
title: Project Alpha
tags:
  - project
  - ai
created: 2024-01-15
---

# Project Alpha

AI research project on agents.
"""
    )

    (vault_root / "urgent_bug.md").write_text(
        """---
title: URGENT Bug Fix
tags:
  - urgent
  - bug
created: 2024-01-20
---

# Critical System Bug

High priority bug fix needed.
"""
    )

    return vault_root


@pytest.fixture
def test_vault_manager(test_vault_path: Path) -> VaultManager:
    """Create VaultManager instance for testing.

    Args:
        test_vault_path: Path to test vault from test_vault_path fixture.

    Returns:
        VaultManager configured with test vault.
    """
    return VaultManager(vault_path=str(test_vault_path))


@pytest.fixture
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
