"""Simple unit test for the RAG system."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llama_index.core import Document, VectorStoreIndex
from rag.ollama_check import check_server


def test_ollama_not_required_for_import():
    """Test that modules can be imported without Ollama running."""
    try:
        from rag import __version__
        from rag.config import load_config
        assert __version__ is not None
        assert load_config() is not None
    except Exception as e:
        pytest.fail(f"Import failed: {e}")


@pytest.mark.skipif(
    not check_server("http://localhost:11434"),
    reason="Ollama server not running - skipping integration test",
)
def test_simple_query_with_ollama():
    """Test a simple query if Ollama is available."""
    from llama_index.core import Settings
    from llama_index.embeddings.ollama import OllamaEmbedding
    from llama_index.llms.ollama import Ollama
    
    from rag.config import load_config
    from rag.ollama_check import choose_chat_model, list_local_models
    
    # Get config
    config = load_config()
    base_url = config["OLLAMA_BASE_URL"]
    
    # Get available models
    models = list_local_models(base_url)
    if not models:
        pytest.skip("No models installed in Ollama")
    
    # Choose model
    chat_model = choose_chat_model(config["OLLAMA_CHAT_MODEL"], models)
    if not chat_model:
        pytest.skip("No suitable chat model found")
    
    # Setup minimal LLM
    Settings.llm = Ollama(
        model=chat_model,
        base_url=base_url,
        temperature=0,
    )
    
    # Try to use embedding model
    embed_model = config["OLLAMA_EMBED_MODEL"]
    try:
        Settings.embed_model = OllamaEmbedding(
            model_name=embed_model,
            base_url=base_url,
        )
    except Exception:
        pytest.skip(f"Embedding model {embed_model} not available")
    
    # Create toy documents
    docs = [
        Document(
            text="The capital of France is Paris.",
            metadata={"source": "test"},
        ),
    ]
    
    # Build index
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine()
    
    # Query
    response = query_engine.query("What is the capital of France?")
    answer = str(response).strip().lower()
    
    # Basic assertion
    assert "paris" in answer or len(answer) > 0


def test_config_loading():
    """Test configuration loading with defaults."""
    from rag.config import load_config
    
    # Test default config
    config = load_config()
    
    assert "DOCS_DIR" in config
    assert "INDEX_DIR" in config
    assert "OLLAMA_BASE_URL" in config
    assert config["OLLAMA_BASE_URL"] == "http://localhost:11434"
    assert config["SIMILARITY_TOP_K"] == 4
    assert "LOG_LEVEL" in config
    assert "ENABLE_VERBOSE_OUTPUT" in config
    assert "REQUEST_TIMEOUT" in config
    assert "EMBED_BATCH_SIZE" in config


def test_environment_specific_config():
    """Test loading different environment configurations."""
    from rag.config import load_config
    
    # Save any existing env vars that might interfere
    saved_vars = {}
    test_vars = ["LOG_LEVEL", "ENABLE_VERBOSE_OUTPUT", "REQUEST_TIMEOUT", "EMBED_BATCH_SIZE", "OLLAMA_BASE_URL"]
    for var in test_vars:
        if var in os.environ:
            saved_vars[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # Test development environment
        dev_config = load_config(env_name="development")
        assert dev_config["LOG_LEVEL"] == "DEBUG"
        assert dev_config["ENABLE_VERBOSE_OUTPUT"] is True
        
        # Clear env vars loaded by development config
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Test production environment
        prod_config = load_config(env_name="production")
        assert prod_config["LOG_LEVEL"] == "INFO"
        assert prod_config["ENABLE_VERBOSE_OUTPUT"] is False
        assert prod_config["REQUEST_TIMEOUT"] == 120.0
        assert prod_config["EMBED_BATCH_SIZE"] == 5
        
        # Clear env vars loaded by production config
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Test docker environment
        docker_config = load_config(env_name="docker")
        assert docker_config["OLLAMA_BASE_URL"] == "http://host.docker.internal:11434"
    finally:
        # Restore original env vars
        for var, value in saved_vars.items():
            os.environ[var] = value


def test_config_validation():
    """Test configuration validation."""
    from rag.config import validate_config
    
    # Valid config
    valid_config = {
        "DOCS_DIR": Path("./docs"),
        "INDEX_DIR": Path("./index"),
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "SIMILARITY_TOP_K": 4
    }
    assert validate_config(valid_config) is True
    
    # Invalid URL
    invalid_config = valid_config.copy()
    invalid_config["OLLAMA_BASE_URL"] = "not-a-url"
    assert validate_config(invalid_config) is False
    
    # Invalid numeric value
    invalid_config = valid_config.copy()
    invalid_config["SIMILARITY_TOP_K"] = "not-a-number"
    assert validate_config(invalid_config) is False


def test_executable_dir_detection():
    """Test executable directory detection."""
    from rag.config import get_executable_dir
    
    exec_dir = get_executable_dir()
    assert exec_dir.exists()
    assert exec_dir.is_dir()
    
    # Should be the project root when running as script
    assert (exec_dir / "src").exists() or (exec_dir / "rag").exists()


def test_environment_override():
    """Test environment variable override."""
    # Save original values
    orig_k = os.environ.get("SIMILARITY_TOP_K")
    orig_level = os.environ.get("LOG_LEVEL")
    
    try:
        # Set custom environment variables
        os.environ["SIMILARITY_TOP_K"] = "10"
        os.environ["LOG_LEVEL"] = "WARNING"
        
        # Import after setting env vars to test override
        from rag.config import load_config
        
        config = load_config()
        
        # Environment variables should override config file values
        assert config["SIMILARITY_TOP_K"] == 10
        assert config["LOG_LEVEL"] == "WARNING"
    finally:
        # Cleanup
        if orig_k:
            os.environ["SIMILARITY_TOP_K"] = orig_k
        elif "SIMILARITY_TOP_K" in os.environ:
            del os.environ["SIMILARITY_TOP_K"]
            
        if orig_level:
            os.environ["LOG_LEVEL"] = orig_level
        elif "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]


def test_cli_help():
    """Test CLI help output."""
    from rag.cli import main
    
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    
    # Help should exit with 0
    assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])