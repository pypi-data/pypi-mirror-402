"""Migration module for Vector Bot.

Helps users migrate from the legacy index_storage system to the new store-based system.

Legacy system: ./index_storage/ directory in project root, DOCS_DIR in .env
New system: ~/.vector-bot/stores/<name>/index/ with store.json metadata
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from rich.console import Console

from .store import create_store, get_store, get_store_index_dir, set_default_store

console = Console()

# Legacy directory names
LEGACY_INDEX_DIR = "index_storage"
LEGACY_DOCSTORE_FILE = "docstore.json"
LEGACY_ENV_DOCS_KEY = "DOCS_DIR"


def detect_legacy_index(project_dir: Path | None = None) -> dict[str, Any] | None:
    """Detect a legacy index_storage directory.

    Checks for the presence of an index_storage/ directory with docstore.json inside.

    Args:
        project_dir: Directory to check. If None, uses current working directory.

    Returns:
        None if no legacy index found.
        Dictionary with info if found:
            - index_dir: Path to the legacy index directory
            - docs_dir: Path from .env DOCS_DIR if exists, else None
            - has_docstore: True if docstore.json exists
            - file_count: Number of files in index_storage
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Ensure project_dir is absolute
    if not project_dir.is_absolute():
        project_dir = project_dir.resolve()

    legacy_index_dir = project_dir / LEGACY_INDEX_DIR

    # Check if legacy index directory exists
    if not legacy_index_dir.exists() or not legacy_index_dir.is_dir():
        return None

    # Check for docstore.json
    docstore_path = legacy_index_dir / LEGACY_DOCSTORE_FILE
    has_docstore = docstore_path.exists() and docstore_path.is_file()

    # If no docstore, this might not be a valid legacy index
    if not has_docstore:
        return None

    # Count files in the directory
    file_count = sum(1 for item in legacy_index_dir.iterdir() if item.is_file())

    # Try to read DOCS_DIR from .env
    docs_dir: Path | None = None
    env_path = project_dir / ".env"
    if env_path.exists():
        env_values = dotenv_values(env_path)
        docs_dir_str = env_values.get(LEGACY_ENV_DOCS_KEY)
        if docs_dir_str:
            docs_dir = Path(docs_dir_str)
            # Resolve relative paths against project_dir
            if not docs_dir.is_absolute():
                docs_dir = (project_dir / docs_dir).resolve()

    return {
        "index_dir": legacy_index_dir,
        "docs_dir": docs_dir,
        "has_docstore": has_docstore,
        "file_count": file_count,
    }


def migrate_legacy_index(
    store_name: str,
    project_dir: Path | None = None,
    docs_dir: Path | None = None,
) -> dict[str, Any]:
    """Migrate a legacy index_storage to a new store.

    Creates a new store with the given name and copies index files from
    the legacy index_storage directory to the new store's index directory.

    Args:
        store_name: Name for the new store.
        project_dir: Directory containing legacy index. If None, uses cwd.
        docs_dir: Documents directory path. If None, reads from .env DOCS_DIR.

    Returns:
        The new store configuration dictionary.

    Raises:
        ValueError: If no legacy index found or store name already exists.
        FileNotFoundError: If docs_dir cannot be determined.
    """
    # Detect legacy index
    legacy_info = detect_legacy_index(project_dir)
    if legacy_info is None:
        raise ValueError(
            "No legacy index found. "
            "Expected 'index_storage/' directory with docstore.json."
        )

    # Check if store name already exists
    existing_store = get_store(store_name)
    if existing_store is not None:
        raise ValueError(f"Store '{store_name}' already exists.")

    # Determine docs_dir
    if docs_dir is None:
        docs_dir = legacy_info.get("docs_dir")

    if docs_dir is None:
        raise FileNotFoundError(
            "Could not determine documents directory. "
            "Please provide --docs argument or set DOCS_DIR in .env file."
        )

    # Ensure docs_dir is absolute
    if not docs_dir.is_absolute():
        docs_dir = docs_dir.resolve()

    # Create the new store (pass docs_dir as a list)
    store_config = create_store(store_name, [docs_dir])

    # Copy index files from legacy to new store
    new_index_dir = get_store_index_dir(store_name)
    legacy_index_dir = legacy_info["index_dir"]

    # Copy all files from legacy index to new index directory
    for item in legacy_index_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, new_index_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, new_index_dir / item.name)

    # Set as default store
    set_default_store(store_name)

    # Update store config with migration info
    from .store import update_store
    store_config = update_store(
        store_name,
        migrated_from=str(legacy_index_dir),
        migrated_at=datetime.now().isoformat(),
        chunk_count=legacy_info["file_count"],
    )

    return store_config


def cleanup_legacy_index(
    project_dir: Path | None = None,
    backup: bool = True,
) -> Path | None:
    """Clean up the legacy index_storage directory.

    Args:
        project_dir: Directory containing legacy index. If None, uses cwd.
        backup: If True, renames to index_storage.bak.{timestamp}/.
                If False, deletes the directory.

    Returns:
        Path to backup directory if backup=True, None otherwise.

    Raises:
        ValueError: If no legacy index found.
    """
    # Detect legacy index
    legacy_info = detect_legacy_index(project_dir)
    if legacy_info is None:
        raise ValueError(
            "No legacy index found. "
            "Expected 'index_storage/' directory with docstore.json."
        )

    legacy_index_dir = legacy_info["index_dir"]

    if backup:
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{LEGACY_INDEX_DIR}.bak.{timestamp}"
        backup_path = legacy_index_dir.parent / backup_name

        shutil.move(str(legacy_index_dir), str(backup_path))
        return backup_path
    else:
        # Delete the directory
        shutil.rmtree(legacy_index_dir)
        return None
