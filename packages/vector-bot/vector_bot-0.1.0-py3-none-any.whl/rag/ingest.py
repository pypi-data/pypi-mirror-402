"""Document ingestion module for building and persisting vector index."""

import os
from pathlib import Path
from typing import List

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from rich.console import Console

from .store import get_store, get_store_index_dir, resolve_store, get_global_config
from .ollama_check import check_server, choose_chat_model, ensure_embed_model, list_local_models

console = Console()


def setup_llm_settings() -> None:
    """Configure LlamaIndex settings with Ollama models from global config."""
    config = get_global_config()

    # Get Ollama base URL from environment or global config
    base_url = os.environ.get(
        "OLLAMA_BASE_URL",
        config.get("ollama_base_url", "http://localhost:11434")
    )

    # Check server
    if not check_server(base_url):
        raise RuntimeError(f"Ollama server not running at {base_url}")

    # Get available models
    models = list_local_models(base_url)
    if not models:
        raise RuntimeError("No models installed. Run: ollama pull llama3.1")

    # Get chat model from environment or global config
    chat_model_config = os.environ.get(
        "OLLAMA_CHAT_MODEL",
        config.get("ollama_chat_model")
    )
    chat_model = choose_chat_model(chat_model_config, models)
    if not chat_model:
        raise RuntimeError("No suitable chat model found. Install one with: ollama pull llama3.1")

    # Get embedding model from environment or global config
    embed_model = os.environ.get(
        "OLLAMA_EMBED_MODEL",
        config.get("ollama_embed_model", "nomic-embed-text")
    )
    embed_ok, embed_msg = ensure_embed_model(base_url, embed_model)
    if not embed_ok:
        console.print(f"[yellow]{embed_msg}[/yellow]")
        raise RuntimeError(embed_msg)

    # Get timeout and batch size from environment or global config
    request_timeout = float(os.environ.get(
        "REQUEST_TIMEOUT",
        config.get("request_timeout", 60.0)
    ))
    embed_batch_size = int(os.environ.get(
        "EMBED_BATCH_SIZE",
        config.get("embed_batch_size", 10)
    ))

    # Configure Settings
    Settings.llm = Ollama(
        model=chat_model,
        base_url=base_url,
        temperature=0,
        request_timeout=request_timeout,
    )

    Settings.embed_model = OllamaEmbedding(
        model_name=embed_model,
        base_url=base_url,
        embed_batch_size=embed_batch_size,
    )

    console.print(f"[green]Using chat model: {chat_model}[/green]")
    console.print(f"[green]Using embedding model: {embed_model}[/green]")


def load_documents(docs_dir: Path) -> List:
    """Load documents from a single directory."""
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[yellow]Created docs directory: {docs_dir}[/yellow]")
        return []

    # Define file extensions to load
    extensions = [".txt", ".md", ".pdf", ".json", ".csv"]

    # Check for documents
    doc_files: list[Path] = []
    for ext in extensions:
        doc_files.extend(docs_dir.glob(f"*{ext}"))
        doc_files.extend(docs_dir.glob(f"**/*{ext}"))

    if not doc_files:
        console.print(f"[yellow]No documents found in {docs_dir}[/yellow]")
        return []

    # Filter out large files (>20MB)
    valid_files: list[Path] = []
    for file in doc_files:
        size_mb = file.stat().st_size / (1024 * 1024)
        if size_mb > 20:
            console.print(f"[yellow]Skipping large file (>{size_mb:.1f}MB): {file.name}[/yellow]")
        else:
            valid_files.append(file)

    if not valid_files:
        console.print("[yellow]No valid documents to index[/yellow]")
        return []

    console.print(f"[blue]Loading {len(valid_files)} documents from {docs_dir}...[/blue]")

    # Load documents
    reader = SimpleDirectoryReader(
        input_dir=str(docs_dir),
        recursive=True,
        exclude_hidden=True,
        required_exts=extensions,
    )

    documents = reader.load_data()
    console.print(f"[green]Loaded {len(documents)} document chunks[/green]")

    return documents


def load_documents_from_dirs(docs_dirs: List[Path]) -> List:
    """Load documents from multiple directories.

    Args:
        docs_dirs: List of paths to document directories.

    Returns:
        Combined list of documents from all directories.
    """
    all_documents = []
    for docs_dir in docs_dirs:
        documents = load_documents(docs_dir)
        all_documents.extend(documents)

    if len(docs_dirs) > 1:
        console.print(f"[blue]Total: {len(all_documents)} chunks from {len(docs_dirs)} directories[/blue]")

    return all_documents


def ingest(
    store_name: str | None = None,
    verbose: bool = False,
    force: bool = False
) -> dict:
    """Run document ingestion to build or update the vector index.

    Args:
        store_name: Name of the store to ingest documents for. If None, uses default store.
        verbose: If True, show detailed progress during indexing.
        force: If True, force re-indexing even if index already exists.

    Returns:
        dict with indexing stats: {"chunk_count": N, "docs_count": N}
    """
    # Resolve which store to use
    store_name = resolve_store(store_name)
    store = get_store(store_name)

    # Get document directories (handles backwards compatibility)
    docs_dirs = [Path(d) for d in store.get("docs_dirs", [])]
    index_dir = get_store_index_dir(store_name)

    console.print("[bold]Document Ingestion[/bold]")
    console.print(f"[blue]Store: {store_name}[/blue]")
    if len(docs_dirs) > 1:
        console.print(f"[dim]Indexing {len(docs_dirs)} directories[/dim]")

    # Setup LLM settings
    setup_llm_settings()

    # Check if index already exists
    if not force and index_dir.exists() and (index_dir / "docstore.json").exists():
        console.print(f"[blue]Loading existing index from {index_dir}[/blue]")
        try:
            storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
            index = load_index_from_storage(storage_context)
            console.print("[green]OK Existing index loaded successfully[/green]")

            # Get stats from existing index
            docstore = index.docstore
            chunk_count = len(docstore.docs)

            # Count unique source documents
            source_files = set()
            for doc_id, doc in docstore.docs.items():
                if hasattr(doc, 'metadata') and 'file_path' in doc.metadata:
                    source_files.add(doc.metadata['file_path'])
                elif hasattr(doc, 'metadata') and 'file_name' in doc.metadata:
                    source_files.add(doc.metadata['file_name'])
            docs_count = len(source_files) if source_files else chunk_count

            console.print(f"[dim]Index contains {chunk_count} chunks from {docs_count} documents[/dim]")
            return {"chunk_count": chunk_count, "docs_count": docs_count}
        except Exception as e:
            console.print(f"[yellow]Could not load existing index: {e}[/yellow]")
            console.print("[blue]Creating new index...[/blue]")

    if force and index_dir.exists():
        console.print("[yellow]Force flag set - rebuilding index...[/yellow]")

    # Load documents from all directories
    documents = load_documents_from_dirs(docs_dirs)
    if not documents:
        dirs_str = ", ".join(str(d) for d in docs_dirs)
        raise RuntimeError(f"No documents found in: {dirs_str}")

    # Count unique source files from loaded documents
    source_files = set()
    for doc in documents:
        if hasattr(doc, 'metadata'):
            if 'file_path' in doc.metadata:
                source_files.add(doc.metadata['file_path'])
            elif 'file_name' in doc.metadata:
                source_files.add(doc.metadata['file_name'])
    docs_count = len(source_files) if source_files else len(documents)

    # Build index
    console.print("[blue]Building vector index...[/blue]")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=verbose,
    )

    # Persist index
    index_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(index_dir))

    chunk_count = len(documents)
    console.print(f"[green]OK Index saved to {index_dir}[/green]")
    console.print(f"[green]OK Indexed {chunk_count} chunks from {docs_count} documents[/green]")

    return {"chunk_count": chunk_count, "docs_count": docs_count}