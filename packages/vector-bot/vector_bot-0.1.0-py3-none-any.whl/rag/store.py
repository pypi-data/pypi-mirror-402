"""Store management module for Vector Bot.

Handles multiple document stores with persistent configuration.

Storage Layout:
    ~/.vector-bot/
        config.json           # Global config (default_store, ollama settings)
        stores/
            <store-name>/
                store.json    # Store metadata
                index/        # LlamaIndex persisted storage
"""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()

# Constants
STORES_HOME_NAME = ".vector-bot"
GLOBAL_CONFIG_FILE = "config.json"
STORES_DIR = "stores"
STORE_CONFIG_FILE = "store.json"
INDEX_DIR = "index"

# Store name validation pattern: alphanumeric, hyphens, underscores, 1-50 chars
STORE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")


def _get_default_global_config() -> dict[str, Any]:
    """Return the default global configuration."""
    return {
        "default_store": None,
        "ollama_base_url": "http://localhost:11434",
        "ollama_embed_model": "nomic-embed-text",
    }


def _validate_store_name(name: str) -> None:
    """Validate a store name.

    Args:
        name: The store name to validate.

    Raises:
        ValueError: If the name is invalid.
    """
    if not name:
        raise ValueError("Store name cannot be empty.")
    if not STORE_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid store name '{name}'. "
            "Store names must be 1-50 characters and contain only "
            "alphanumeric characters, hyphens, and underscores."
        )


def get_stores_home() -> Path:
    """Get the Vector Bot home directory.

    Returns the path to ~/.vector-bot, creating it if it doesn't exist.

    Returns:
        Path to the Vector Bot home directory.
    """
    home = Path.home() / STORES_HOME_NAME
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_global_config() -> dict[str, Any]:
    """Read the global configuration.

    Returns the contents of config.json, or default values if the file
    doesn't exist or is invalid.

    Returns:
        Dictionary containing global configuration.
    """
    config_path = get_stores_home() / GLOBAL_CONFIG_FILE
    default_config = _get_default_global_config()

    if not config_path.exists():
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        # Merge with defaults to ensure all keys exist
        return {**default_config, **config}
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[yellow]Warning: Could not read global config: {e}[/yellow]")
        return default_config


def save_global_config(config: dict[str, Any]) -> None:
    """Save the global configuration.

    Args:
        config: Configuration dictionary to save.
    """
    config_path = get_stores_home() / GLOBAL_CONFIG_FILE
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        raise OSError(f"Failed to save global config: {e}") from e


def _get_stores_dir() -> Path:
    """Get the stores directory path."""
    stores_dir = get_stores_home() / STORES_DIR
    stores_dir.mkdir(parents=True, exist_ok=True)
    return stores_dir


def _get_store_dir(name: str) -> Path:
    """Get the directory path for a specific store."""
    return _get_stores_dir() / name


def list_stores() -> list[dict[str, Any]]:
    """List all available stores.

    Returns:
        List of store info dictionaries, each containing:
        - name: Store name
        - docs_dirs: List of paths to documents directories
        - last_indexed: ISO timestamp of last indexing, or None
        - chunk_count: Number of indexed chunks
    """
    stores_dir = _get_stores_dir()
    stores: list[dict[str, Any]] = []

    if not stores_dir.exists():
        return stores

    for store_dir in stores_dir.iterdir():
        if not store_dir.is_dir():
            continue

        store_config_path = store_dir / STORE_CONFIG_FILE
        if not store_config_path.exists():
            continue

        try:
            with open(store_config_path, "r", encoding="utf-8") as f:
                store_data = json.load(f)

            # Handle both old (docs_dir) and new (docs_dirs) formats
            docs_dirs = store_data.get("docs_dirs")
            if docs_dirs is None:
                # Backwards compatibility: convert single docs_dir to list
                old_docs_dir = store_data.get("docs_dir")
                docs_dirs = [old_docs_dir] if old_docs_dir else []

            stores.append({
                "name": store_data.get("name", store_dir.name),
                "docs_dirs": docs_dirs,
                "last_indexed": store_data.get("last_indexed"),
                "chunk_count": store_data.get("chunk_count", 0),
            })
        except (json.JSONDecodeError, OSError):
            # Skip invalid store configurations
            continue

    return stores


def get_store(name: str) -> dict[str, Any] | None:
    """Get store configuration by name.

    Args:
        name: The name of the store.

    Returns:
        Store configuration dictionary, or None if store doesn't exist.
        Always returns docs_dirs as a list (converts legacy docs_dir if needed).
    """
    _validate_store_name(name)
    store_config_path = _get_store_dir(name) / STORE_CONFIG_FILE

    if not store_config_path.exists():
        return None

    try:
        with open(store_config_path, "r", encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)

        # Handle backwards compatibility: convert docs_dir to docs_dirs
        if "docs_dirs" not in result and "docs_dir" in result:
            result["docs_dirs"] = [result["docs_dir"]]

        return result
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[yellow]Warning: Could not read store config: {e}[/yellow]")
        return None


def create_store(
    name: str,
    docs_dirs: list[Path],
    chat_model: str | None = None,
) -> dict[str, Any]:
    """Create a new document store.

    Args:
        name: Unique name for the store.
        docs_dirs: List of paths to documents directories.
        chat_model: Optional chat model override for this store.

    Returns:
        The created store configuration.

    Raises:
        ValueError: If name is invalid or store already exists.
    """
    _validate_store_name(name)

    store_dir = _get_store_dir(name)
    if store_dir.exists():
        raise ValueError(f"Store '{name}' already exists.")

    # Convert to absolute paths if relative
    resolved_dirs = []
    for docs_dir in docs_dirs:
        if not docs_dir.is_absolute():
            docs_dir = docs_dir.resolve()
        resolved_dirs.append(str(docs_dir))

    # Create store directory structure
    store_dir.mkdir(parents=True, exist_ok=True)
    index_dir = store_dir / INDEX_DIR
    index_dir.mkdir(parents=True, exist_ok=True)

    # Create store configuration
    store_config = {
        "name": name,
        "docs_dirs": resolved_dirs,
        "created": datetime.now(timezone.utc).isoformat(),
        "last_indexed": None,
        "chunk_count": 0,
        "chat_model": chat_model,
    }

    store_config_path = store_dir / STORE_CONFIG_FILE
    try:
        with open(store_config_path, "w", encoding="utf-8") as f:
            json.dump(store_config, f, indent=2)
    except OSError as e:
        # Clean up on failure
        shutil.rmtree(store_dir, ignore_errors=True)
        raise OSError(f"Failed to create store configuration: {e}") from e

    return store_config


def update_store(name: str, **kwargs: Any) -> dict[str, Any]:
    """Update store configuration fields.

    Args:
        name: Name of the store to update.
        **kwargs: Fields to update (e.g., last_indexed, chunk_count).

    Returns:
        The updated store configuration.

    Raises:
        ValueError: If store doesn't exist.
    """
    _validate_store_name(name)

    store_config = get_store(name)
    if store_config is None:
        raise ValueError(f"Store '{name}' does not exist.")

    # Update fields
    for key, value in kwargs.items():
        if key == "docs_dirs" and value is not None:
            # Ensure docs_dirs are stored as absolute path strings
            resolved = []
            for p in value:
                path = Path(p) if isinstance(p, str) else p
                if not path.is_absolute():
                    path = path.resolve()
                resolved.append(str(path))
            store_config[key] = resolved
        else:
            store_config[key] = value

    # Save updated configuration
    store_config_path = _get_store_dir(name) / STORE_CONFIG_FILE
    try:
        with open(store_config_path, "w", encoding="utf-8") as f:
            json.dump(store_config, f, indent=2)
    except OSError as e:
        raise OSError(f"Failed to update store configuration: {e}") from e

    return store_config


def delete_store(name: str) -> bool:
    """Delete a store and all its data.

    Args:
        name: Name of the store to delete.

    Returns:
        True if store existed and was deleted, False if it didn't exist.
    """
    _validate_store_name(name)

    store_dir = _get_store_dir(name)
    if not store_dir.exists():
        return False

    # Check if this was the default store
    global_config = get_global_config()
    if global_config.get("default_store") == name:
        global_config["default_store"] = None
        save_global_config(global_config)

    try:
        shutil.rmtree(store_dir)
        return True
    except OSError as e:
        raise OSError(f"Failed to delete store '{name}': {e}") from e


def rename_store(old_name: str, new_name: str) -> dict[str, Any]:
    """Rename a store.

    Args:
        old_name: Current name of the store.
        new_name: New name for the store.

    Returns:
        The updated store configuration.

    Raises:
        ValueError: If old store doesn't exist, new name is invalid,
            or new name already exists.
    """
    _validate_store_name(old_name)
    _validate_store_name(new_name)

    old_dir = _get_store_dir(old_name)
    new_dir = _get_store_dir(new_name)

    if not old_dir.exists():
        raise ValueError(f"Store '{old_name}' does not exist.")

    if new_dir.exists():
        raise ValueError(f"Store '{new_name}' already exists.")

    # Rename directory
    try:
        old_dir.rename(new_dir)
    except OSError as e:
        raise OSError(f"Failed to rename store: {e}") from e

    # Update store configuration with new name
    store_config = get_store(new_name)
    if store_config:
        store_config["name"] = new_name
        store_config_path = new_dir / STORE_CONFIG_FILE
        with open(store_config_path, "w", encoding="utf-8") as f:
            json.dump(store_config, f, indent=2)

    # Update default store if needed
    global_config = get_global_config()
    if global_config.get("default_store") == old_name:
        global_config["default_store"] = new_name
        save_global_config(global_config)

    return store_config or {"name": new_name}


def get_store_index_dir(name: str) -> Path:
    """Get the index directory path for a store.

    Args:
        name: Name of the store.

    Returns:
        Path to the store's index directory.
    """
    _validate_store_name(name)
    return _get_store_dir(name) / INDEX_DIR


def get_default_store() -> str | None:
    """Get the name of the default store.

    Returns:
        Name of the default store, or None if not set.
    """
    global_config = get_global_config()
    return global_config.get("default_store")


def set_default_store(name: str) -> None:
    """Set the default store.

    Args:
        name: Name of the store to set as default.

    Raises:
        ValueError: If the store doesn't exist.
    """
    _validate_store_name(name)

    if get_store(name) is None:
        raise ValueError(f"Store '{name}' does not exist.")

    global_config = get_global_config()
    global_config["default_store"] = name
    save_global_config(global_config)


def resolve_store(name: str | None) -> str:
    """Resolve the store name to use.

    If a name is provided, validates it exists and returns it.
    If None, returns the default store if set.
    If no default and only one store exists, returns that store.

    Args:
        name: Optional store name to resolve.

    Returns:
        The resolved store name.

    Raises:
        ValueError: If the specified store doesn't exist, no default is set
            when needed, or multiple stores exist without a default.
    """
    if name is not None:
        _validate_store_name(name)
        if get_store(name) is None:
            raise ValueError(f"Store '{name}' does not exist.")
        return name

    # Try to use default store
    default = get_default_store()
    if default is not None:
        if get_store(default) is None:
            raise ValueError(
                f"Default store '{default}' no longer exists. "
                "Please set a new default with 'vector-bot store default <name>'."
            )
        return default

    # Check if there's exactly one store
    stores = list_stores()
    if len(stores) == 0:
        raise ValueError(
            "No stores exist. Create one with 'vector-bot store create <name> <docs-dir>'."
        )
    if len(stores) == 1:
        store_name: str = stores[0]["name"]
        return store_name

    # Multiple stores, no default
    store_names = ", ".join(s["name"] for s in stores)
    raise ValueError(
        f"Multiple stores exist ({store_names}) and no default is set. "
        "Either specify a store with --store or set a default with "
        "'vector-bot store default <name>'."
    )
