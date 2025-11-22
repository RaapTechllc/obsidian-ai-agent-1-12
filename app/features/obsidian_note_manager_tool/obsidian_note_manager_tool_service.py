"""Business logic for Obsidian Note Manager Tool."""

from pathlib import Path

from app.core.logging import get_logger
from app.features.obsidian_note_manager_tool.obsidian_note_manager_tool_models import (
    BulkOperationCriteria,
    BulkOperationPreview,
    ObsidianNoteManagerToolResult,
)
from app.shared.vault.vault_manager import VaultManager

logger = get_logger(__name__)


async def execute_create_note(
    vault_manager: VaultManager,
    target: str,
    content: str,
    metadata: dict[str, str | list[str] | int | float | bool] | None,
    create_folders: bool,
) -> ObsidianNoteManagerToolResult:
    """Create new note with optional frontmatter.

    Args:
        vault_manager: VaultManager instance
        target: Note path to create
        content: Note content
        metadata: Optional frontmatter metadata
        create_folders: Create parent folders if missing

    Returns:
        ObsidianNoteManagerToolResult with creation details
    """
    logger.info("vault.create_note_started", target=target)

    try:
        # Create parent folders if needed
        if create_folders:
            parent = str(Path(target).parent)
            if parent != ".":
                vault_manager.create_folder(parent, exist_ok=True)

        # Write note
        vault_manager.write_note(target, content, metadata, overwrite=False)

        logger.info("vault.create_note_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="create_note",
            affected_count=1,
            affected_paths=[target],
            message=f"Created note: {target}",
        )

    except Exception as e:
        logger.error("vault.create_note_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="create_note",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to create note: {e!s}",
        )


async def execute_update_note(
    vault_manager: VaultManager,
    target: str,
    content: str,
    metadata: dict[str, str | list[str] | int | float | bool] | None,
) -> ObsidianNoteManagerToolResult:
    """Update existing note, replacing content and optionally metadata.

    Args:
        vault_manager: VaultManager instance
        target: Note path to update
        content: New note content
        metadata: Optional new frontmatter metadata

    Returns:
        ObsidianNoteManagerToolResult with update details
    """
    logger.info("vault.update_note_started", target=target)

    try:
        # Check note exists
        note = vault_manager.read_note(target)

        # Use existing frontmatter if no new metadata provided
        if metadata is None and note.frontmatter:
            metadata_dict: dict[str, str | list[str] | int | float | bool] = {
                "tags": note.frontmatter.tags,
            }
            if note.frontmatter.title:
                metadata_dict["title"] = note.frontmatter.title
            if note.frontmatter.created:
                metadata_dict["created"] = note.frontmatter.created.isoformat()
            if note.frontmatter.modified:
                metadata_dict["modified"] = note.frontmatter.modified.isoformat()
            # Add custom fields
            for key, value in note.frontmatter.custom.items():
                metadata_dict[key] = value
            metadata = metadata_dict

        # Overwrite note
        vault_manager.write_note(target, content, metadata, overwrite=True)

        logger.info("vault.update_note_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="update_note",
            affected_count=1,
            affected_paths=[target],
            message=f"Updated note: {target}",
        )

    except FileNotFoundError:
        logger.warning("vault.update_note_not_found", target=target)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="update_note",
            affected_count=0,
            affected_paths=[],
            message=f"Note not found: {target}",
        )
    except Exception as e:
        logger.error("vault.update_note_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="update_note",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to update note: {e!s}",
        )


async def execute_append_note(
    vault_manager: VaultManager,
    target: str,
    content: str,
) -> ObsidianNoteManagerToolResult:
    """Append content to existing note.

    Args:
        vault_manager: VaultManager instance
        target: Note path to append to
        content: Content to append

    Returns:
        ObsidianNoteManagerToolResult with append details
    """
    logger.info("vault.append_note_started", target=target)

    try:
        vault_manager.append_to_note(target, content)

        logger.info("vault.append_note_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="append_note",
            affected_count=1,
            affected_paths=[target],
            message=f"Appended to note: {target}",
        )

    except FileNotFoundError:
        logger.warning("vault.append_note_not_found", target=target)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="append_note",
            affected_count=0,
            affected_paths=[],
            message=f"Note not found: {target}",
        )
    except Exception as e:
        logger.error("vault.append_note_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="append_note",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to append to note: {e!s}",
        )


async def execute_delete_note(
    vault_manager: VaultManager,
    target: str,
    confirm_destructive: bool,
) -> ObsidianNoteManagerToolResult:
    """Delete note with safety confirmation.

    Args:
        vault_manager: VaultManager instance
        target: Note path to delete
        confirm_destructive: Must be True to proceed

    Returns:
        ObsidianNoteManagerToolResult with deletion details
    """
    if not confirm_destructive:
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_note",
            affected_count=0,
            affected_paths=[],
            message="Invalid operation: delete_note requires confirm_destructive=True to prevent accidental data loss.",
        )

    logger.info("vault.delete_note_started", target=target)

    try:
        vault_manager.delete_note(target)

        logger.info("vault.delete_note_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="delete_note",
            affected_count=1,
            affected_paths=[target],
            message=f"Deleted note: {target}",
        )

    except FileNotFoundError:
        logger.warning("vault.delete_note_not_found", target=target)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_note",
            affected_count=0,
            affected_paths=[],
            message=f"Note not found: {target}",
        )
    except Exception as e:
        logger.error("vault.delete_note_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_note",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to delete note: {e!s}",
        )


async def execute_move_note(
    vault_manager: VaultManager,
    target: str,
    destination: str,
    create_folders: bool,
) -> ObsidianNoteManagerToolResult:
    """Move note to new location.

    Args:
        vault_manager: VaultManager instance
        target: Current note path
        destination: Destination path
        create_folders: Create parent folders if missing

    Returns:
        ObsidianNoteManagerToolResult with move details
    """
    logger.info("vault.move_note_started", target=target, destination=destination)

    try:
        vault_manager.move_note(target, destination, create_folders=create_folders)

        logger.info("vault.move_note_completed", target=target, destination=destination)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="move_note",
            affected_count=1,
            affected_paths=[destination],
            message=f"Moved note from {target} to {destination}",
        )

    except FileNotFoundError as e:
        logger.warning("vault.move_note_not_found", target=target, error=str(e))
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="move_note",
            affected_count=0,
            affected_paths=[],
            message=f"Note not found or destination issue: {e!s}",
        )
    except Exception as e:
        logger.error(
            "vault.move_note_failed", target=target, destination=destination, error=str(e), exc_info=True
        )
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="move_note",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to move note: {e!s}",
        )


async def execute_create_folder(
    vault_manager: VaultManager,
    target: str,
    exist_ok: bool,
) -> ObsidianNoteManagerToolResult:
    """Create folder in vault.

    Args:
        vault_manager: VaultManager instance
        target: Folder path to create
        exist_ok: If True, don't error if folder exists

    Returns:
        ObsidianNoteManagerToolResult with creation details
    """
    logger.info("vault.create_folder_started", target=target)

    try:
        vault_manager.create_folder(target, exist_ok=exist_ok)

        logger.info("vault.create_folder_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="create_folder",
            affected_count=1,
            affected_paths=[target],
            message=f"Created folder: {target}",
        )

    except FileExistsError:
        logger.warning("vault.create_folder_exists", target=target)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="create_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Folder already exists: {target}",
        )
    except Exception as e:
        logger.error("vault.create_folder_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="create_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to create folder: {e!s}",
        )


async def execute_delete_folder(
    vault_manager: VaultManager,
    target: str,
    confirm_destructive: bool,
    recursive: bool,
) -> ObsidianNoteManagerToolResult:
    """Delete folder with safety confirmation.

    Args:
        vault_manager: VaultManager instance
        target: Folder path to delete
        confirm_destructive: Must be True to proceed
        recursive: If True, delete non-empty folders

    Returns:
        ObsidianNoteManagerToolResult with deletion details
    """
    if not confirm_destructive:
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_folder",
            affected_count=0,
            affected_paths=[],
            message="Invalid operation: delete_folder requires confirm_destructive=True to prevent accidental data loss.",
        )

    logger.info("vault.delete_folder_started", target=target, recursive=recursive)

    try:
        vault_manager.delete_folder(target, recursive=recursive)

        logger.info("vault.delete_folder_completed", target=target)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="delete_folder",
            affected_count=1,
            affected_paths=[target],
            message=f"Deleted folder: {target}",
        )

    except FileNotFoundError:
        logger.warning("vault.delete_folder_not_found", target=target)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Folder not found: {target}",
        )
    except OSError as e:
        logger.warning("vault.delete_folder_not_empty", target=target, error=str(e))
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Folder not empty (use recursive=True to delete): {target}",
        )
    except Exception as e:
        logger.error("vault.delete_folder_failed", target=target, error=str(e), exc_info=True)
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="delete_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to delete folder: {e!s}",
        )


async def execute_move_folder(
    vault_manager: VaultManager,
    target: str,
    destination: str,
) -> ObsidianNoteManagerToolResult:
    """Move folder to new location.

    Args:
        vault_manager: VaultManager instance
        target: Current folder path
        destination: Destination path

    Returns:
        ObsidianNoteManagerToolResult with move details
    """
    logger.info("vault.move_folder_started", target=target, destination=destination)

    try:
        vault_manager.move_folder(target, destination)

        logger.info("vault.move_folder_completed", target=target, destination=destination)

        return ObsidianNoteManagerToolResult(
            success=True,
            operation="move_folder",
            affected_count=1,
            affected_paths=[destination],
            message=f"Moved folder from {target} to {destination}",
        )

    except FileNotFoundError as e:
        logger.warning("vault.move_folder_not_found", target=target, error=str(e))
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="move_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Folder not found or destination issue: {e!s}",
        )
    except Exception as e:
        logger.error(
            "vault.move_folder_failed", target=target, destination=destination, error=str(e), exc_info=True
        )
        return ObsidianNoteManagerToolResult(
            success=False,
            operation="move_folder",
            affected_count=0,
            affected_paths=[],
            message=f"Failed to move folder: {e!s}",
        )


async def execute_bulk_tag(
    vault_manager: VaultManager,
    targets: list[str],
    metadata: dict[str, str | list[str] | int | float | bool],
) -> ObsidianNoteManagerToolResult:
    """Add tags to multiple notes.

    Args:
        vault_manager: VaultManager instance
        targets: List of note paths to tag
        metadata: Metadata to add (typically contains 'tags' key)

    Returns:
        ObsidianNoteManagerToolResult with bulk operation details
    """
    logger.info("vault.bulk_tag_started", target_count=len(targets))

    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for target in targets:
        try:
            # Read existing note
            note = vault_manager.read_note(target)

            # Merge tags (deduplicate)
            existing_tags = note.frontmatter.tags if note.frontmatter else []
            new_tags_raw = metadata.get("tags", [])

            # Normalize new_tags to list of strings
            new_tags: list[str] = []
            if isinstance(new_tags_raw, str):
                new_tags = [new_tags_raw]
            elif isinstance(new_tags_raw, list):
                new_tags = new_tags_raw

            merged_tags = list(set(existing_tags + new_tags))

            # Build metadata dict
            metadata_dict: dict[str, str | list[str] | int | float | bool] = {"tags": merged_tags}
            if note.frontmatter:
                if note.frontmatter.title:
                    metadata_dict["title"] = note.frontmatter.title
                if note.frontmatter.created:
                    metadata_dict["created"] = note.frontmatter.created.isoformat()
                if note.frontmatter.modified:
                    metadata_dict["modified"] = note.frontmatter.modified.isoformat()
                for key, value in note.frontmatter.custom.items():
                    if key not in metadata_dict:
                        metadata_dict[key] = value

            # Add any other metadata from input (besides tags)
            for key, value in metadata.items():
                if key != "tags":
                    metadata_dict[key] = value

            # Write back
            vault_manager.write_note(target, note.content, metadata_dict, overwrite=True)
            succeeded.append(target)

        except Exception as e:
            logger.warning("vault.bulk_tag_item_failed", target=target, error=str(e))
            failed.append({"path": target, "reason": str(e)})

    logger.info("vault.bulk_tag_completed", succeeded_count=len(succeeded), failed_count=len(failed))

    partial_success = len(succeeded) > 0 and len(failed) > 0

    return ObsidianNoteManagerToolResult(
        success=len(succeeded) > 0,
        operation="bulk_tag",
        affected_count=len(succeeded),
        affected_paths=succeeded,
        message=f"Tagged {len(succeeded)}/{len(targets)} notes",
        partial_success=partial_success if partial_success else None,
        failures=failed if failed else None,
    )


async def execute_bulk_move(
    vault_manager: VaultManager,
    targets: list[str],
    destination_folder: str,
    create_folders: bool,
) -> ObsidianNoteManagerToolResult:
    """Move multiple notes to a destination folder.

    Args:
        vault_manager: VaultManager instance
        targets: List of note paths to move
        destination_folder: Folder to move notes into
        create_folders: Create destination folder if missing

    Returns:
        ObsidianNoteManagerToolResult with bulk operation details
    """
    logger.info("vault.bulk_move_started", target_count=len(targets), destination=destination_folder)

    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for target in targets:
        try:
            # Calculate destination path (preserve filename)
            from pathlib import Path

            filename = Path(target).name
            dest_path = f"{destination_folder}/{filename}"

            # Move note
            vault_manager.move_note(target, dest_path, create_folders=create_folders)
            succeeded.append(dest_path)

        except Exception as e:
            logger.warning("vault.bulk_move_item_failed", target=target, error=str(e))
            failed.append({"path": target, "reason": str(e)})

    logger.info("vault.bulk_move_completed", succeeded_count=len(succeeded), failed_count=len(failed))

    partial_success = len(succeeded) > 0 and len(failed) > 0

    return ObsidianNoteManagerToolResult(
        success=len(succeeded) > 0,
        operation="bulk_move",
        affected_count=len(succeeded),
        affected_paths=succeeded,
        message=f"Moved {len(succeeded)}/{len(targets)} notes to {destination_folder}",
        partial_success=partial_success if partial_success else None,
        failures=failed if failed else None,
    )


async def execute_bulk_update_metadata(
    vault_manager: VaultManager,
    targets: list[str],
    metadata: dict[str, str | list[str] | int | float | bool],
) -> ObsidianNoteManagerToolResult:
    """Update metadata for multiple notes.

    Args:
        vault_manager: VaultManager instance
        targets: List of note paths to update
        metadata: Metadata to apply to all notes

    Returns:
        ObsidianNoteManagerToolResult with bulk operation details
    """
    logger.info("vault.bulk_update_metadata_started", target_count=len(targets))

    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for target in targets:
        try:
            # Read existing note
            note = vault_manager.read_note(target)

            # Build metadata dict (merge existing with new)
            metadata_dict: dict[str, str | list[str] | int | float | bool] = {}
            if note.frontmatter:
                metadata_dict["tags"] = note.frontmatter.tags
                if note.frontmatter.title:
                    metadata_dict["title"] = note.frontmatter.title
                if note.frontmatter.created:
                    metadata_dict["created"] = note.frontmatter.created.isoformat()
                if note.frontmatter.modified:
                    metadata_dict["modified"] = note.frontmatter.modified.isoformat()
                for key, value in note.frontmatter.custom.items():
                    metadata_dict[key] = value

            # Apply new metadata (overwrites existing keys)
            for key, value in metadata.items():
                metadata_dict[key] = value

            # Write back
            vault_manager.write_note(target, note.content, metadata_dict, overwrite=True)
            succeeded.append(target)

        except Exception as e:
            logger.warning("vault.bulk_update_metadata_item_failed", target=target, error=str(e))
            failed.append({"path": target, "reason": str(e)})

    logger.info(
        "vault.bulk_update_metadata_completed", succeeded_count=len(succeeded), failed_count=len(failed)
    )

    partial_success = len(succeeded) > 0 and len(failed) > 0

    return ObsidianNoteManagerToolResult(
        success=len(succeeded) > 0,
        operation="bulk_update_metadata",
        affected_count=len(succeeded),
        affected_paths=succeeded,
        message=f"Updated metadata for {len(succeeded)}/{len(targets)} notes",
        partial_success=partial_success if partial_success else None,
        failures=failed if failed else None,
    )


# Enhanced Bulk Operations


async def execute_bulk_find_and_tag(
    vault_manager: VaultManager,
    criteria: BulkOperationCriteria,
    tags_to_add: dict[str, str | list[str] | int | float | bool],
) -> ObsidianNoteManagerToolResult:
    """Find notes matching criteria and add tags to them.

    Args:
        vault_manager: VaultManager instance
        criteria: Search criteria for finding notes
        tags_to_add: Tags and metadata to add to found notes

    Returns:
        ObsidianNoteManagerToolResult with operation details
    """
    logger.info("vault.bulk_find_and_tag_started", criteria=criteria)

    # First, find notes matching criteria
    matching_notes = await _find_notes_by_criteria(vault_manager, criteria)
    
    if not matching_notes:
        return ObsidianNoteManagerToolResult(
            success=True,
            operation="bulk_find_and_tag",
            affected_count=0,
            affected_paths=[],
            message="No notes found matching criteria",
        )

    # Then apply tags to found notes
    result = await execute_bulk_tag(vault_manager, matching_notes, tags_to_add)
    
    return ObsidianNoteManagerToolResult(
        success=result.success,
        operation="bulk_find_and_tag",
        affected_count=result.affected_count,
        affected_paths=result.affected_paths,
        message=f"Found {len(matching_notes)} notes, tagged {result.affected_count} of them",
        partial_success=result.partial_success,
        failures=result.failures,
    )


async def execute_bulk_find_and_move(
    vault_manager: VaultManager,
    criteria: BulkOperationCriteria,
    destination_folder: str,
    create_folders: bool,
) -> ObsidianNoteManagerToolResult:
    """Find notes matching criteria and move them to destination folder.

    Args:
        vault_manager: VaultManager instance  
        criteria: Search criteria for finding notes
        destination_folder: Folder to move notes into
        create_folders: Create destination folder if missing

    Returns:
        ObsidianNoteManagerToolResult with operation details
    """
    logger.info("vault.bulk_find_and_move_started", criteria=criteria, destination=destination_folder)

    # First, find notes matching criteria
    matching_notes = await _find_notes_by_criteria(vault_manager, criteria)
    
    if not matching_notes:
        return ObsidianNoteManagerToolResult(
            success=True,
            operation="bulk_find_and_move", 
            affected_count=0,
            affected_paths=[],
            message="No notes found matching criteria",
        )

    # Then move found notes
    result = await execute_bulk_move(vault_manager, matching_notes, destination_folder, create_folders)
    
    return ObsidianNoteManagerToolResult(
        success=result.success,
        operation="bulk_find_and_move",
        affected_count=result.affected_count,
        affected_paths=result.affected_paths,
        message=f"Found {len(matching_notes)} notes, moved {result.affected_count} of them to {destination_folder}",
        partial_success=result.partial_success,
        failures=result.failures,
    )


async def execute_bulk_preview(
    vault_manager: VaultManager,
    operation_type: str,
    criteria: BulkOperationCriteria,
    changes: dict[str, str | list[str] | int | float | bool] | None = None,
    destination_folder: str | None = None,
) -> BulkOperationPreview:
    """Preview what a bulk operation will affect without making changes.

    Args:
        vault_manager: VaultManager instance
        operation_type: Type of operation to preview
        criteria: Search criteria for finding notes
        changes: Changes that would be applied (for tag/metadata operations)
        destination_folder: Destination for move operations

    Returns:
        BulkOperationPreview with preview details
    """
    logger.info("vault.bulk_preview_started", operation=operation_type, criteria=criteria)

    # Find notes matching criteria
    matching_notes = await _find_notes_by_criteria(vault_manager, criteria)
    
    if not matching_notes:
        return BulkOperationPreview(
            operation_type=operation_type,
            target_notes=[],
            changes=None,
            warnings=["No notes found matching criteria"],
            estimated_risk="low",
        )

    # Build preview based on operation type
    changes_dict: dict[str, str] = {}
    warnings: list[str] = []

    if operation_type in ["bulk_find_and_tag", "bulk_tag"]:
        for note_path in matching_notes:
            note_path_str = str(note_path)
            if changes:
                changes_dict[note_path_str] = f"Add tags: {changes.get('tags', [])}"

    elif operation_type in ["bulk_find_and_move", "bulk_move"]:
        for note_path in matching_notes:
            note_path_str = str(note_path)
            filename = Path(note_path_str).name
            new_path = f"{destination_folder}/{filename}"
            changes_dict[note_path_str] = f"Move to: {new_path}"

    # Assess risk based on number of notes
    if len(matching_notes) > 50:
        risk_level = "high"
        warnings.append("Large number of notes may impact performance")
    elif len(matching_notes) > 10:
        risk_level = "medium"
    else:
        risk_level = "low"

    return BulkOperationPreview(
        operation_type=operation_type,
        target_notes=matching_notes,
        changes=changes_dict,
        warnings=warnings,
        estimated_risk=risk_level,  # type: ignore
    )


async def _find_notes_by_criteria(
    vault_manager: VaultManager, criteria: BulkOperationCriteria
) -> list[str]:
    """Find notes matching the specified criteria.

    Args:
        vault_manager: VaultManager instance
        criteria: Search criteria for finding notes

    Returns:
        List of note paths matching criteria
    """
    logger.info("vault.find_notes_by_criteria", criteria=criteria)

    # Get all notes in vault
    all_notes = vault_manager.list_notes()
    matching_notes: list[str] = []

    for vault_path in all_notes:
        # Extract relative path from VaultPath object
        note_path_str = vault_path.relative_path
        note = vault_manager.read_note(note_path_str)
        matches = True

        # Check tags criteria
        if criteria.tags:
            note_tags = note.frontmatter.tags if note.frontmatter and note.frontmatter.tags else []
            if not any(tag in note_tags for tag in criteria.tags):
                matches = False

        # Check content contains
        if criteria.content_contains and matches:
            if criteria.content_contains not in note.content:
                matches = False

        # Check path pattern
        if criteria.path_pattern and matches:
            from fnmatch import fnmatch
            if not fnmatch(note_path_str, criteria.path_pattern):
                matches = False

        # Check has_tag (has any tags vs has no tags)
        if criteria.has_tag is not None and matches:
            note_tags = note.frontmatter.tags if note.frontmatter and note.frontmatter.tags else []
            has_tags = len(note_tags) > 0
            if has_tags != criteria.has_tag:
                matches = False

        # Check folder path
        if criteria.folder_path and matches:
            if not note_path_str.startswith(criteria.folder_path):
                matches = False

        # Add if matches
        if matches:
            matching_notes.append(note_path_str)

        # Apply limit if specified
        if criteria.limit and len(matching_notes) >= criteria.limit:
            break

    logger.info("vault.find_notes_completed", found_count=len(matching_notes))
    return matching_notes
