"""Configuration management for Vector Bot.

This module handles configuration loading from multiple sources:
1. Environment variables and .env files (for OLLAMA settings, Docker/CI overrides)
2. Store-based configuration (for DOCS_DIR, INDEX_DIR, chat_model per store)

The store-based system is the preferred approach for multi-store setups.
Legacy environment-based paths are still supported with deprecation warnings.
"""

import os
import sys
import warnings
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from rich.console import Console

# Store imports - these functions are defined in store.py (created in parallel)
from .store import (
    get_global_config,
    get_store,
    get_store_index_dir,
    resolve_store,
)

console = Console()


def get_executable_dir() -> Path:
    """Get the directory where the executable/script is located."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return Path(sys.executable).parent
    else:
        # Running as Python script
        return Path(__file__).parent.parent.parent


def load_environment_config(env_name: Optional[str] = None) -> None:
    """Load environment-specific configuration from .env files.

    This loads OLLAMA_* settings and other global settings.
    DOCS_DIR and INDEX_DIR are now managed per-store and should not
    be set via environment (except for legacy compatibility).

    Args:
        env_name: Optional environment name (e.g., 'development', 'production')
    """
    executable_dir = get_executable_dir()

    # Priority order for loading .env files:
    env_files = []

    if env_name:
        # 1. Specific environment config
        env_files.append(executable_dir / f"configs/{env_name}.env")
        env_files.append(Path(f"configs/{env_name}.env"))
        env_files.append(Path(f".env.{env_name}"))

    # 2. Environment-specific from RAG_ENV variable
    rag_env = os.getenv("RAG_ENV")
    if rag_env:
        env_files.extend([
            executable_dir / f"configs/{rag_env}.env",
            Path(f"configs/{rag_env}.env"),
            Path(f".env.{rag_env}")
        ])

    # 3. Local .env file
    env_files.extend([
        executable_dir / ".env",
        Path(".env")
    ])

    # 4. Default development config
    env_files.extend([
        executable_dir / "configs/development.env",
        Path("configs/development.env")
    ])

    # Load the first existing file
    for env_file in env_files:
        if env_file.exists():
            # Use override=False to preserve existing environment variables
            load_dotenv(env_file, override=False)
            if os.getenv("RAG_VERBOSE") == "true":
                console.print(f"[dim]Loaded config from: {env_file}[/dim]")
            break


def _check_legacy_index_storage() -> None:
    """Check for legacy index_storage directory and warn about migration.

    This helps users migrate from the old single-index approach to
    the new multi-store system.
    """
    executable_dir = get_executable_dir()
    legacy_index_dir = executable_dir / "index_storage"

    if legacy_index_dir.exists() and legacy_index_dir.is_dir():
        # Check if it looks like a legacy index (has files, not store subdirs)
        contents = list(legacy_index_dir.iterdir())
        if contents and not any((legacy_index_dir / ".vectorbot").exists() for _ in [1]):
            # Has contents but no .vectorbot marker - likely legacy
            has_index_files = any(
                f.suffix in {'.json', '.faiss', '.pkl'} or f.name.startswith('doc')
                for f in contents if f.is_file()
            )
            if has_index_files:
                warnings.warn(
                    "Legacy index_storage directory detected. "
                    "Consider migrating to the store-based system using: "
                    "vectorbot store create <name> --docs-dir <path>",
                    DeprecationWarning,
                    stacklevel=3
                )


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if configuration is valid, False otherwise
    """
    errors = []

    # Validate required directories exist or can be created
    for dir_key in ["DOCS_DIR", "INDEX_DIR"]:
        if dir_key not in config:
            errors.append(f"{dir_key}: Required configuration key missing")
            continue

        dir_path = config[dir_key]
        if dir_path is None:
            errors.append(f"{dir_key}: Directory path is None")
            continue

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"{dir_key}: Cannot create directory {dir_path}: {e}")

    # Validate URL format
    url = config.get("OLLAMA_BASE_URL", "")
    if not url.startswith(("http://", "https://")):
        errors.append(f"OLLAMA_BASE_URL must start with http:// or https://, got: {url}")

    # Validate numeric values
    try:
        int(config.get("SIMILARITY_TOP_K", 4))
    except (ValueError, TypeError):
        errors.append(f"SIMILARITY_TOP_K must be an integer, got: {config.get('SIMILARITY_TOP_K')}")

    if errors:
        console.print("[red]Configuration validation errors:[/red]")
        for error in errors:
            console.print(f"  [red]- {error}[/red]")
        return False

    return True


def _get_ollama_settings() -> Dict[str, Any]:
    """Get OLLAMA settings from environment with defaults.

    These settings can be overridden via environment variables for
    Docker/CI scenarios.

    Returns:
        Dictionary with OLLAMA_BASE_URL and OLLAMA_EMBED_MODEL
    """
    return {
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_EMBED_MODEL": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    }


def load_store_config(store_name: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration for a specific store.

    This is the preferred way to load configuration in the multi-store system.
    It merges:
    - OLLAMA settings from global config (with env override)
    - DOCS_DIR from the store's docs_dir
    - INDEX_DIR from the store's index path
    - OLLAMA_CHAT_MODEL from the store's chat_model (if set)

    Args:
        store_name: Name of the store to load config for. If None, uses
                   the default store from global config.

    Returns:
        Merged configuration dictionary ready for use

    Raises:
        ValueError: If the store doesn't exist or configuration is invalid
    """
    # Resolve which store to use
    store = resolve_store(store_name)

    if store is None:
        raise ValueError(
            f"Store '{store_name}' not found. "
            "Create a store first with: vectorbot store create <name> --docs-dir <path>"
        )

    # Get global config for OLLAMA defaults
    global_config = get_global_config()

    # Start with OLLAMA settings (env vars override global config)
    ollama_settings = _get_ollama_settings()

    # Build the merged config
    config = {
        # Directories from store
        "DOCS_DIR": Path(store.docs_dir),
        "INDEX_DIR": get_store_index_dir(store.name),

        # OLLAMA settings: env > store > global > defaults
        "OLLAMA_BASE_URL": ollama_settings["OLLAMA_BASE_URL"],
        "OLLAMA_EMBED_MODEL": ollama_settings["OLLAMA_EMBED_MODEL"],

        # Chat model: env > store > global > None (auto-detect)
        "OLLAMA_CHAT_MODEL": (
            os.getenv("OLLAMA_CHAT_MODEL") or
            store.chat_model or
            global_config.get("default_chat_model")
        ),

        # Other settings from environment with defaults
        "SIMILARITY_TOP_K": int(os.getenv("SIMILARITY_TOP_K", "4")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "ENABLE_VERBOSE_OUTPUT": os.getenv("ENABLE_VERBOSE_OUTPUT", "false").lower() == "true",
        "REQUEST_TIMEOUT": float(os.getenv("REQUEST_TIMEOUT", "60.0")),
        "EMBED_BATCH_SIZE": int(os.getenv("EMBED_BATCH_SIZE", "10")),

        # Store metadata (useful for display/debugging)
        "_store_name": store.name,
        "_store_description": store.description,
    }

    # Validate the merged configuration
    if not validate_config(config):
        raise ValueError(f"Configuration validation failed for store '{store.name}'")

    return config


def load_config(
    env_name: Optional[str] = None,
    store_name: Optional[str] = None
) -> Dict[str, Any]:
    """Load configuration from environment variables, .env files, and stores.

    This function supports both the legacy environment-based configuration
    and the new store-based system.

    Args:
        env_name: Optional environment name for .env file loading
        store_name: Optional store name. If provided, loads store-based config.
                   If None and stores exist, uses the default store.

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If configuration validation fails
    """
    # Load environment-specific config (for OLLAMA settings, etc.)
    load_environment_config(env_name)

    # Check for legacy index_storage and warn
    _check_legacy_index_storage()

    # If store_name is explicitly provided, use store-based config
    if store_name is not None:
        return load_store_config(store_name)

    # Try to use the default store if one exists
    try:
        default_store = resolve_store(None)
        if default_store is not None:
            return load_store_config(None)
    except Exception:
        # Store system not available or no default store - fall through to legacy
        pass

    # Legacy fallback: load from environment variables
    # This path is for backward compatibility
    executable_dir = get_executable_dir()

    def resolve_path(path_str: str, base_dir: Optional[Path] = None) -> Path:
        """Resolve a path relative to executable directory."""
        path = Path(path_str)
        if path.is_absolute():
            return path

        # Always resolve relative to executable directory
        return (executable_dir / path).resolve()

    # Build configuration from environment (legacy mode)
    config = {
        "DOCS_DIR": resolve_path(os.getenv("DOCS_DIR", "./docs")),
        "INDEX_DIR": resolve_path(os.getenv("INDEX_DIR", "./index_storage")),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_CHAT_MODEL": os.getenv("OLLAMA_CHAT_MODEL"),
        "OLLAMA_EMBED_MODEL": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        "SIMILARITY_TOP_K": int(os.getenv("SIMILARITY_TOP_K", "4")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "ENABLE_VERBOSE_OUTPUT": os.getenv("ENABLE_VERBOSE_OUTPUT", "false").lower() == "true",
        "REQUEST_TIMEOUT": float(os.getenv("REQUEST_TIMEOUT", "60.0")),
        "EMBED_BATCH_SIZE": int(os.getenv("EMBED_BATCH_SIZE", "10")),
    }

    # Validate configuration
    if not validate_config(config):
        raise ValueError("Configuration validation failed")

    return config


def get_config_value(
    key: str,
    default: Optional[Any] = None,
    env_name: Optional[str] = None,
    store_name: Optional[str] = None
) -> Any:
    """Get a specific configuration value.

    Args:
        key: Configuration key to retrieve
        default: Default value if key not found
        env_name: Optional environment name for .env loading
        store_name: Optional store name for store-based config

    Returns:
        The configuration value or default
    """
    config = load_config(env_name, store_name)
    return config.get(key, default)
