"""Query module for answering questions using the vector index."""

import os
from typing import Optional, Union

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from rich.console import Console

from .ollama_check import check_server, choose_chat_model, ensure_embed_model, list_local_models
from .store import get_store, get_store_index_dir, resolve_store, get_global_config

console = Console()


def setup_query_llm_settings(
    base_url: str,
    embed_model: str,
    chat_model: Optional[str] = None,
    request_timeout: float = 60.0,
    embed_batch_size: int = 10,
) -> None:
    """Configure LlamaIndex settings with Ollama models for querying."""
    # Check server
    if not check_server(base_url):
        raise RuntimeError(f"Ollama server not running at {base_url}")

    # Get available models
    models = list_local_models(base_url)
    if not models:
        raise RuntimeError("No models installed. Run: ollama pull llama3.1")

    # Choose chat model (auto-detect if not specified)
    resolved_chat_model = choose_chat_model(chat_model, models)
    if not resolved_chat_model:
        raise RuntimeError("No suitable chat model found. Install one with: ollama pull llama3.1")

    # Check embedding model
    embed_ok, embed_msg = ensure_embed_model(base_url, embed_model)
    if not embed_ok:
        console.print(f"[yellow]{embed_msg}[/yellow]")
        raise RuntimeError(embed_msg)

    # Configure Settings
    Settings.llm = Ollama(
        model=resolved_chat_model,
        base_url=base_url,
        temperature=0,
        request_timeout=request_timeout,
    )

    Settings.embed_model = OllamaEmbedding(
        model_name=embed_model,
        base_url=base_url,
        embed_batch_size=embed_batch_size,
    )

    console.print(f"[green]Using chat model: {resolved_chat_model}[/green]")
    console.print(f"[green]Using embedding model: {embed_model}[/green]")


def ask(
    question: str,
    store_name: Optional[str] = None,
    show_sources: bool = False,
    top_k: int = 4,
    verbose: bool = False,
) -> str:
    """Query the index with a question and return the answer.

    Args:
        question: The question to ask.
        store_name: Name of the store to query. If None, uses the default store.
        show_sources: Whether to include source document information in the response.
        top_k: Number of similar documents to retrieve.
        verbose: Whether to print verbose output.

    Returns:
        The answer string, optionally with source information.

    Raises:
        RuntimeError: If the store is not indexed or Ollama is not available.
    """
    # Resolve store name (uses default if None)
    store_name = resolve_store(store_name)
    store = get_store(store_name)
    index_dir = get_store_index_dir(store_name)

    # Check if index exists
    if not index_dir.exists() or not (index_dir / "docstore.json").exists():
        raise RuntimeError(
            f"Store '{store_name}' not indexed. Run: vector-bot store reindex {store_name}"
        )

    # Get Ollama config from global config and environment
    global_config = get_global_config()
    base_url = os.environ.get("OLLAMA_BASE_URL", global_config.get("ollama_base_url", "http://localhost:11434"))
    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", global_config.get("ollama_embed_model", "nomic-embed-text"))

    # Use store's chat_model if specified, otherwise auto-detect
    chat_model = store.get("chat_model")  # May be None, will auto-detect

    # Get optional settings
    request_timeout = float(global_config.get("request_timeout", 60.0))
    embed_batch_size = int(global_config.get("embed_batch_size", 10))

    # Setup LLM settings
    setup_query_llm_settings(
        base_url=base_url,
        embed_model=embed_model,
        chat_model=chat_model,
        request_timeout=request_timeout,
        embed_batch_size=embed_batch_size,
    )

    # Load index
    if verbose:
        console.print(f"[blue]Loading index from {index_dir}...[/blue]")

    storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
    index = load_index_from_storage(storage_context)

    # Create query engine
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        streaming=False,
    )

    # Execute query
    if verbose:
        console.print(f"[blue]Querying with top_k={top_k}...[/blue]")

    response = query_engine.query(question)

    # Process response
    answer = str(response).strip()

    if not answer or answer == "Empty Response":
        answer = "No relevant information found in the indexed documents."

    # Show sources if requested
    if show_sources and hasattr(response, "source_nodes"):
        source_info = []
        for node in response.source_nodes:
            if hasattr(node, "metadata"):
                filename = node.metadata.get("file_name", "Unknown")
                score = node.score if hasattr(node, "score") else 0
                source_info.append(f"  - {filename} (score: {score:.3f})")

        if source_info:
            answer += "\n\n[dim]Sources:[/dim]\n" + "\n".join(source_info)

    return answer


def query(
    question: str,
    store_name: Optional[str] = None,
    show_sources: bool = False,
    top_k: int = 4,
    verbose: bool = False,
) -> None:
    """Run a query and print the result.

    Args:
        question: The question to ask.
        store_name: Name of the store to query. If None, uses the default store.
        show_sources: Whether to include source document information in the response.
        top_k: Number of similar documents to retrieve.
        verbose: Whether to print verbose output.
    """
    try:
        answer = ask(question, store_name, show_sources, top_k, verbose)
        console.print(f"\n[bold]Answer:[/bold] {answer}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise
