"""Vector Bot - Fully offline RAG pipeline using LlamaIndex with Ollama."""

from .version import __version__
from .store import (
    create_store,
    delete_store,
    get_default_store,
    get_store,
    get_store_index_dir,
    get_stores_home,
    list_stores,
    rename_store,
    resolve_store,
    set_default_store,
    update_store,
)

__all__ = [
    "__version__",
    # Store management functions
    "create_store",
    "delete_store",
    "get_default_store",
    "get_store",
    "get_store_index_dir",
    "get_stores_home",
    "list_stores",
    "rename_store",
    "resolve_store",
    "set_default_store",
    "update_store",
]