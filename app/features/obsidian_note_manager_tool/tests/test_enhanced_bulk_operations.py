"""Tests for enhanced bulk operations."""

import pytest
from pathlib import Path

from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_models import (
    BulkOperationCriteria,
    BulkOperationPreview,
)
from app.shared.vault.vault_manager import VaultManager


@pytest.mark.asyncio
async def test_bulk_find_by_criteria_by_tags(vault_manager: VaultManager) -> None:
    """Test finding notes by tag criteria."""
    # Create test notes with different tags
    vault_manager.write_note("project1.md", "Project 1 content", {"tags": ["project", "active"]}, overwrite=True)
    vault_manager.write_note("project2.md", "Project 2 content", {"tags": ["project", "completed"]}, overwrite=True)
    vault_manager.write_note("note1.md", "General note 1", {"tags": ["general"]}, overwrite=True)
    vault_manager.write_note("note2.md", "General note 2", None, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import _find_notes_by_criteria

    # Test finding notes with "project" tag
    criteria = BulkOperationCriteria(tags=["project"])
    result = await _find_notes_by_criteria(vault_manager, criteria)

    assert len(result) == 2
    assert "project1.md" in result
    assert "project2.md" in result


@pytest.mark.asyncio 
async def test_bulk_find_by_criteria_by_content(vault_manager: VaultManager) -> None:
    """Test finding notes by content criteria."""
    # Create test notes with different content
    vault_manager.write_note("tech1.md", "Content about AI technology", {"tags": ["tech"]}, overwrite=True)
    vault_manager.write_note("tech2.md", "Content about programming", {"tags": ["tech"]}, overwrite=True)
    vault_manager.write_note("personal1.md", "Personal thoughts", {"tags": ["personal"]}, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import _find_notes_by_criteria

    # Test finding notes containing "AI"
    criteria = BulkOperationCriteria(content_contains="AI")
    result = await _find_notes_by_criteria(vault_manager, criteria)

    assert len(result) == 1
    assert "tech1.md" in result


@pytest.mark.asyncio
async def test_bulk_find_by_criteria_by_folder_path(vault_manager: VaultManager) -> None:
    """Test finding notes by folder criteria."""
    # Create notes in different folders
    vault_manager.create_folder("Projects", exist_ok=True)
    vault_manager.create_folder("Daily", exist_ok=True)
    vault_manager.write_note("Projects/project1.md", "Project content", {"tags": ["project"]}, overwrite=True)
    vault_manager.write_note("Projects/project2.md", "Another project", {"tags": ["project"]}, overwrite=True)
    vault_manager.write_note("Daily/2025-01-15.md", "Daily note", {"tags": ["daily"]}, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import _find_notes_by_criteria

    # Test finding notes in "Projects" folder
    criteria = BulkOperationCriteria(folder_path="Projects")
    result = await _find_notes_by_criteria(vault_manager, criteria)

    assert len(result) == 2
    # Handle both Unix and Windows path separators
    project_files = [path.replace("\\", "/") for path in result]
    assert "Projects/project1.md" in project_files
    assert "Projects/project2.md" in project_files


@pytest.mark.asyncio
async def test_bulk_find_by_criteria_has_tag(vault_manager: VaultManager) -> None:
    """Test finding notes by has_tag criteria."""
    # Create notes with and without tags
    vault_manager.write_note("tagged1.md", "Tagged content", {"tags": ["test"]}, overwrite=True)
    vault_manager.write_note("tagged2.md", "Also tagged", {"tags": ["another"]}, overwrite=True)
    vault_manager.write_note("untagged1.md", "No tags here", None, overwrite=True)
    vault_manager.write_note("untagged2.md", "Also no tags", None, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import _find_notes_by_criteria

    # Test finding notes WITH tags
    criteria_has_tags = BulkOperationCriteria(has_tag=True)
    result_has_tags = await _find_notes_by_criteria(vault_manager, criteria_has_tags)

    assert len(result_has_tags) == 2
    assert not any(path.startswith("untagged") for path in result_has_tags)

    # Test finding notes WITHOUT tags
    criteria_no_tags = BulkOperationCriteria(has_tag=False)
    result_no_tags = await _find_notes_by_criteria(vault_manager, criteria_no_tags)

    assert len(result_no_tags) == 2
    assert all(path.replace("\\", "/").startswith("untagged") for path in result_no_tags)


@pytest.mark.asyncio
async def test_bulk_preview_operation(vault_manager: VaultManager) -> None:
    """Test bulk preview functionality."""
    # Create test notes
    vault_manager.write_note("note1.md", "Content 1", {"tags": ["test"]}, overwrite=True)
    vault_manager.write_note("note2.md", "Content 2", None, overwrite=True)
    vault_manager.write_note("note3.md", "Content 3", {"tags": ["test"]}, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import execute_bulk_preview

    # Preview bulk tagging operation
    criteria = BulkOperationCriteria(tags=["test"])
    preview = await execute_bulk_preview(
        vault_manager, 
        "bulk_tag", 
        criteria, 
        changes={"tags": ["reviewed"]}
    )

    assert isinstance(preview, BulkOperationPreview)
    assert preview.operation_type == "bulk_tag"
    assert len(preview.target_notes) == 2  # Only notes with "test" tag
    # Handle both Unix and Windows path separators
    target_files = [path.replace("\\", "/") for path in preview.target_notes]
    assert "note1.md" in target_files
    assert "note3.md" in target_files
    assert "note2.md" not in target_files  # No tags
    assert preview.estimated_risk == "low"  # Low risk for small number of notes


@pytest.mark.asyncio
async def test_execute_bulk_find_and_tag(vault_manager: VaultManager) -> None:
    """Test bulk find and tag operation."""
    # Create test notes
    vault_manager.write_note("article1.md", "Content about AI", {"tags": ["article"]}, overwrite=True)
    vault_manager.write_note("article2.md", "Content about ML", {"tags": ["article"]}, overwrite=True)
    vault_manager.write_note("note1.md", "General note", {"tags": ["general"]}, overwrite=True)

    from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_service import execute_bulk_find_and_tag

    # Find all notes with "article" tag and add "ai" tag
    criteria = BulkOperationCriteria(tags=["article"])
    tags_to_add = {"tags": "ai"}
    result = await execute_bulk_find_and_tag(vault_manager, criteria, tags_to_add)

    assert result.success is True
    assert result.operation == "bulk_find_and_tag"
    assert result.affected_count == 2

    # Verify tags were added
    note1 = vault_manager.read_note("article1.md")
    note2 = vault_manager.read_note("article2.md")
    note3 = vault_manager.read_note("note1.md")

    assert "ai" in (note1.frontmatter.tags if note1.frontmatter else [])
    assert "ai" in (note2.frontmatter.tags if note2.frontmatter else [])
    assert "ai" not in (note3.frontmatter.tags if note3.frontmatter else [])
