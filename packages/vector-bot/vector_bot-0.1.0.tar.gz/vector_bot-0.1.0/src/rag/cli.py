"""Command-line interface for Vector Bot."""

import argparse
import sys
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from .ingest import ingest
from .migrate import cleanup_legacy_index, detect_legacy_index, migrate_legacy_index
from .ollama_check import doctor as run_doctor
from .query import query
from .store import (
    create_store,
    delete_store,
    get_default_store,
    get_store,
    get_store_index_dir,
    list_stores,
    rename_store,
    resolve_store,
    set_default_store,
    update_store,
)
from .version import __version__

console = Console()


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run doctor command with store listing."""
    run_doctor(verbose=args.verbose)

    # Also list stores at the end
    console.print("\n[bold]Configured Stores:[/bold]")
    stores = list_stores()
    default_store = get_default_store()

    if not stores:
        console.print("  [dim]No stores configured. Create one with: vector-bot store new <name>[/dim]")
    else:
        for store in stores:
            marker = " *" if store["name"] == default_store else ""
            console.print(f"  - {store['name']}{marker}")

    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Run ingest command for a store."""
    from datetime import datetime

    try:
        store_name = resolve_store(args.store)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Run ingest - it handles store resolution internally
    stats = ingest(
        store_name=store_name,
        verbose=args.verbose,
        force=False,
    )

    # Update store metadata after successful indexing
    update_store(
        store_name,
        last_indexed=datetime.now().isoformat(),
        chunk_count=stats.get("chunk_count"),
    )

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Run query command for a store."""
    try:
        store_name = resolve_store(args.store)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Query using store - it handles index resolution internally
    top_k = args.k if args.k is not None else 4
    query(
        question=args.question,
        store_name=store_name,
        show_sources=args.show_sources,
        top_k=top_k,
        verbose=args.verbose,
    )

    return 0


def cmd_store_new(args: argparse.Namespace) -> int:
    """Create a new store."""
    from pathlib import Path

    name = args.name
    docs_paths = args.docs  # List of paths or None

    # Prompt for docs path if not provided
    if not docs_paths:
        docs_input = console.input(f"[bold]Documents path for '{name}':[/bold] ").strip()
        if not docs_input:
            console.print("[red]Error: Documents path is required.[/red]")
            return 1
        docs_paths = [docs_input]

    # Convert to Path objects
    docs_dirs = [Path(p) for p in docs_paths]

    try:
        create_store(name, docs_dirs)
        console.print(f"[green]Store '{name}' created successfully.[/green]")
        if len(docs_dirs) > 1:
            console.print(f"[dim]Indexing {len(docs_dirs)} directories.[/dim]")

        # Set as default if it's the first store
        stores = list_stores()
        if len(stores) == 1:
            set_default_store(name)
            console.print("[dim]Set as default store.[/dim]")

        return 0
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_store_list(args: argparse.Namespace) -> int:
    """List all stores."""
    stores = list_stores()
    default_store = get_default_store()

    if not stores:
        console.print("[dim]No stores configured.[/dim]")
        console.print("Create one with: vector-bot store new <name>")
        return 0

    table = Table(title="Vector Bot Stores")
    table.add_column("Name", style="cyan")
    table.add_column("Default", style="green")
    table.add_column("Documents", style="dim")
    table.add_column("Last Indexed", style="dim")
    table.add_column("Chunks", style="dim", justify="right")

    for store in stores:
        is_default = "*" if store["name"] == default_store else ""
        last_indexed = store.get("last_indexed", "-")
        if last_indexed and last_indexed != "-":
            # Format datetime nicely
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_indexed)
                last_indexed = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

        chunk_count = store.get("chunk_count")
        chunks_str = str(chunk_count) if chunk_count is not None else "-"

        # Format docs_dirs for display
        docs_dirs = store.get("docs_dirs", [])
        if len(docs_dirs) == 0:
            docs_display = "-"
        elif len(docs_dirs) == 1:
            docs_display = docs_dirs[0]
        else:
            docs_display = f"{len(docs_dirs)} directories"

        table.add_row(
            store["name"],
            is_default,
            docs_display,
            last_indexed,
            chunks_str,
        )

    console.print(table)
    return 0


def cmd_store_info(args: argparse.Namespace) -> int:
    """Show info for a specific store."""
    name = args.name
    store = get_store(name)

    if not store:
        console.print(f"[red]Error: Store '{name}' not found.[/red]")
        return 1

    default_store = get_default_store()
    is_default = name == default_store

    console.print(f"[bold]Store: {name}[/bold]")
    console.print(f"  Default: {'yes' if is_default else 'no'}")

    # Display document directories
    docs_dirs = store.get("docs_dirs", [])
    if len(docs_dirs) == 0:
        console.print("  Documents: -")
    elif len(docs_dirs) == 1:
        console.print(f"  Documents: {docs_dirs[0]}")
    else:
        console.print(f"  Documents: {len(docs_dirs)} directories")
        for d in docs_dirs:
            console.print(f"    - {d}")

    index_dir = get_store_index_dir(name)
    console.print(f"  Index path: {index_dir}")
    console.print(f"  Index exists: {'yes' if index_dir.exists() else 'no'}")

    last_indexed = store.get("last_indexed", "-")
    console.print(f"  Last indexed: {last_indexed}")

    chunk_count = store.get("chunk_count")
    console.print(f"  Chunk count: {chunk_count if chunk_count is not None else '-'}")

    return 0


def cmd_store_default(args: argparse.Namespace) -> int:
    """Set default store."""
    name = args.name
    store = get_store(name)

    if not store:
        console.print(f"[red]Error: Store '{name}' not found.[/red]")
        return 1

    set_default_store(name)
    console.print(f"[green]Default store set to '{name}'.[/green]")
    return 0


def cmd_store_reindex(args: argparse.Namespace) -> int:
    """Reindex a store."""
    from datetime import datetime

    name = args.name
    if not name:
        name = get_default_store()
        if not name:
            console.print("[red]Error: No store specified and no default store set.[/red]")
            return 1

    store = get_store(name)
    if not store:
        console.print(f"[red]Error: Store '{name}' not found.[/red]")
        return 1

    console.print(f"[bold]Reindexing store: {name}[/bold]")

    # Run ingest with force=True to rebuild
    stats = ingest(
        store_name=name,
        verbose=True,
        force=True,
    )

    # Update store metadata
    update_store(
        name,
        last_indexed=datetime.now().isoformat(),
        chunk_count=stats.get("chunk_count"),
    )

    return 0


def cmd_store_rename(args: argparse.Namespace) -> int:
    """Rename a store."""
    old_name = args.old_name
    new_name = args.new_name

    try:
        rename_store(old_name, new_name)
        console.print(f"[green]Store '{old_name}' renamed to '{new_name}'.[/green]")
        return 0
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_store_delete(args: argparse.Namespace) -> int:
    """Delete a store."""
    name = args.name
    force = args.force

    store = get_store(name)
    if not store:
        console.print(f"[red]Error: Store '{name}' not found.[/red]")
        return 1

    # Confirm unless --force
    if not force:
        confirm = console.input(f"[yellow]Delete store '{name}'? This will remove the index. (y/N):[/yellow] ")
        if confirm.lower() not in ("y", "yes"):
            console.print("[dim]Cancelled.[/dim]")
            return 0

    try:
        delete_store(name)
        console.print(f"[green]Store '{name}' deleted.[/green]")
        return 0
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_migrate(args: argparse.Namespace) -> int:
    """Migrate from legacy index_storage to new store system."""
    from pathlib import Path

    # Detect legacy index
    legacy_info = detect_legacy_index()
    if legacy_info is None:
        console.print("[red]Error: No legacy index found.[/red]")
        console.print(
            "[dim]Expected 'index_storage/' directory with docstore.json "
            "in current directory.[/dim]"
        )
        return 1

    # Show what was found
    console.print("[bold]Legacy index detected:[/bold]")
    console.print(f"  Index directory: {legacy_info['index_dir']}")
    console.print(f"  Documents directory: {legacy_info['docs_dir'] or '[not found in .env]'}")
    console.print(f"  Files in index: {legacy_info['file_count']}")
    console.print()

    # Get store name
    store_name = args.name
    if not store_name:
        store_name = console.input("[bold]Enter name for the new store:[/bold] ").strip()
        if not store_name:
            console.print("[red]Error: Store name is required.[/red]")
            return 1

    # Get docs directory
    docs_dir = None
    if args.docs:
        docs_dir = Path(args.docs)
    elif legacy_info["docs_dir"] is None:
        docs_path = console.input("[bold]Enter documents directory path:[/bold] ").strip()
        if not docs_path:
            console.print("[red]Error: Documents directory is required.[/red]")
            return 1
        docs_dir = Path(docs_path)

    # Run migration
    try:
        console.print(f"\n[bold]Migrating to store '{store_name}'...[/bold]")
        store_config = migrate_legacy_index(
            store_name=store_name,
            docs_dir=docs_dir,
        )
        console.print(f"[green]Migration successful![/green]")
        console.print()
        console.print("[bold]New store info:[/bold]")
        console.print(f"  Name: {store_config['name']}")
        docs_dirs = store_config.get('docs_dirs', [])
        console.print(f"  Documents: {docs_dirs[0] if docs_dirs else '-'}")
        console.print(f"  Index: {get_store_index_dir(store_name)}")
        console.print(f"  Set as default: yes")
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Offer to clean up legacy index
    console.print()
    if args.no_backup:
        cleanup_confirm = console.input(
            "[yellow]Delete legacy index_storage/ directory? (y/N):[/yellow] "
        )
    else:
        cleanup_confirm = console.input(
            "[yellow]Move legacy index_storage/ to backup? (Y/n):[/yellow] "
        )

    should_cleanup = (
        cleanup_confirm.lower() in ("y", "yes", "")
        if not args.no_backup
        else cleanup_confirm.lower() in ("y", "yes")
    )

    if should_cleanup:
        try:
            backup_path = cleanup_legacy_index(backup=not args.no_backup)
            if backup_path:
                console.print(f"[green]Legacy index backed up to: {backup_path}[/green]")
            else:
                console.print("[green]Legacy index deleted.[/green]")
        except ValueError as e:
            console.print(f"[yellow]Warning: Could not clean up: {e}[/yellow]")
    else:
        console.print("[dim]Legacy index_storage/ left in place.[/dim]")

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="vector-bot",
        description="Vector Bot: Local RAG pipeline using LlamaIndex with Ollama",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-s", "--store",
        metavar="NAME",
        help="Use specific store (default: uses default store)",
        default=None,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=False,
    )

    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check Ollama server health, available models, and list stores",
    )
    doctor_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest documents and build/update the vector index for current store",
    )
    ingest_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )

    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the index with a question",
    )
    query_parser.add_argument(
        "question",
        help="The question to ask",
    )
    query_parser.add_argument(
        "--k",
        type=int,
        default=None,
        help="Number of similar chunks to retrieve",
    )
    query_parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Show source documents used for the answer",
    )
    query_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    # Store command with subparsers
    store_parser = subparsers.add_parser(
        "store",
        help="Store management subcommands",
    )
    store_subparsers = store_parser.add_subparsers(
        dest="store_command",
        help="Store management commands",
        required=True,
    )

    # store new
    store_new_parser = store_subparsers.add_parser(
        "new",
        help="Create a new store",
    )
    store_new_parser.add_argument(
        "name",
        help="Name for the new store",
    )
    store_new_parser.add_argument(
        "--docs",
        metavar="PATH",
        action="append",
        help="Path to documents directory (can be specified multiple times)",
        default=None,
    )

    # store list
    store_subparsers.add_parser(
        "list",
        help="List all stores",
    )

    # store info
    store_info_parser = store_subparsers.add_parser(
        "info",
        help="Show info for a store",
    )
    store_info_parser.add_argument(
        "name",
        help="Store name",
    )

    # store default
    store_default_parser = store_subparsers.add_parser(
        "default",
        help="Set the default store",
    )
    store_default_parser.add_argument(
        "name",
        help="Store name to set as default",
    )

    # store reindex
    store_reindex_parser = store_subparsers.add_parser(
        "reindex",
        help="Rebuild the index for a store",
    )
    store_reindex_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Store name (uses default if not specified)",
    )

    # store rename
    store_rename_parser = store_subparsers.add_parser(
        "rename",
        help="Rename a store",
    )
    store_rename_parser.add_argument(
        "old_name",
        help="Current store name",
    )
    store_rename_parser.add_argument(
        "new_name",
        help="New store name",
    )

    # store delete
    store_delete_parser = store_subparsers.add_parser(
        "delete",
        help="Delete a store",
    )
    store_delete_parser.add_argument(
        "name",
        help="Store name to delete",
    )
    store_delete_parser.add_argument(
        "--force",
        action="store_true",
        help="Delete without confirmation",
    )

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate from legacy index_storage to new store system",
    )
    migrate_parser.add_argument(
        "--name",
        metavar="NAME",
        help="Name for the new store (prompts if not provided)",
        default=None,
    )
    migrate_parser.add_argument(
        "--docs",
        metavar="PATH",
        help="Documents directory (reads from .env if not provided)",
        default=None,
    )
    migrate_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Delete legacy index instead of backing up",
    )

    # Parse arguments
    args = parser.parse_args(argv)

    try:
        # Ensure command is provided
        if not args.command:
            parser.print_help()
            return 1

        # Execute commands
        if args.command == "doctor":
            return cmd_doctor(args)
        elif args.command == "ingest":
            return cmd_ingest(args)
        elif args.command == "query":
            return cmd_query(args)
        elif args.command == "store":
            if args.store_command == "new":
                return cmd_store_new(args)
            elif args.store_command == "list":
                return cmd_store_list(args)
            elif args.store_command == "info":
                return cmd_store_info(args)
            elif args.store_command == "default":
                return cmd_store_default(args)
            elif args.store_command == "reindex":
                return cmd_store_reindex(args)
            elif args.store_command == "rename":
                return cmd_store_rename(args)
            elif args.store_command == "delete":
                return cmd_store_delete(args)
        elif args.command == "migrate":
            return cmd_migrate(args)

        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
