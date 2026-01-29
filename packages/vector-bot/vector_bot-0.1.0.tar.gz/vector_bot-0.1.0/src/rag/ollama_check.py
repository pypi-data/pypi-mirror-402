"""Ollama health check and model discovery utilities."""

import json
import subprocess
import sys
from typing import List, Optional, Tuple

import requests
from rich.console import Console

console = Console()


def check_server(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is running."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def list_local_models(base_url: str = "http://localhost:11434") -> List[str]:
    """List available local models from Ollama."""
    models = []
    
    # Try API first
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
    except (requests.ConnectionError, requests.Timeout, json.JSONDecodeError):
        pass
    
    # Fallback to CLI
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        # Remove tag suffix if present for cleaner names
                        if ":" in model_name:
                            model_name = model_name.split(":")[0]
                        models.append(model_name)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return models


def choose_chat_model(env_model: Optional[str], available: List[str]) -> Optional[str]:
    """Choose a chat model from available models."""
    if env_model and env_model in available:
        return env_model
    
    # Preferred models in order
    preferred = ["llama3.3", "llama3.2", "llama3.1", "llama3", "mistral", "qwen", "gemma"]
    
    for pref in preferred:
        for model in available:
            if pref in model.lower():
                return model
    
    # Return first available if no preferred found
    return available[0] if available else None


def ensure_embed_model(base_url: str, model_name: str) -> Tuple[bool, str]:
    """Check if embedding model exists, return status and message."""
    models = list_local_models(base_url)
    
    # Check for exact match or partial match
    for model in models:
        if model_name in model or model in model_name:
            return True, f"Embedding model '{model_name}' is available"
    
    return False, f"Embedding model '{model_name}' not found. Run: ollama pull {model_name}"


def doctor(verbose: bool = False, env_name: Optional[str] = None) -> None:
    """Run diagnostics on Ollama setup."""
    from .config import load_config
    
    config = load_config(env_name)
    base_url = config["OLLAMA_BASE_URL"]
    
    console.print("[bold]Ollama Health Check[/bold]")
    console.print(f"Base URL: {base_url}")
    
    # Check server
    if not check_server(base_url):
        console.print("[red]ERROR Ollama server not running[/red]")
        console.print("Start it with: ollama serve")
        sys.exit(1)
    
    console.print("[green]OK Ollama server is running[/green]")
    
    # List models
    models = list_local_models(base_url)
    if not models:
        console.print("[yellow]WARNING No models installed[/yellow]")
        console.print("Install a model with: ollama pull llama3.1")
        sys.exit(1)
    
    console.print(f"\n[bold]Available models:[/bold] {', '.join(models)}")
    
    # Check chat model
    env_chat = config["OLLAMA_CHAT_MODEL"]
    chosen_chat = choose_chat_model(env_chat, models)
    
    if not chosen_chat:
        console.print("[red]ERROR No suitable chat model found[/red]")
        console.print("Install one with: ollama pull llama3.1")
        sys.exit(1)
    
    console.print(f"[green]OK Chat model:[/green] {chosen_chat}")
    if env_chat and env_chat != chosen_chat:
        console.print(f"  [yellow]Note: Env model '{env_chat}' not found, using '{chosen_chat}'[/yellow]")
    
    # Check embedding model
    embed_model = config["OLLAMA_EMBED_MODEL"]
    embed_ok, embed_msg = ensure_embed_model(base_url, embed_model)
    
    if embed_ok:
        console.print(f"[green]OK Embedding model:[/green] {embed_model}")
    else:
        console.print(f"[yellow]WARNING {embed_msg}[/yellow]")
    
    console.print("\n[green]Ready for RAG operations![/green]")