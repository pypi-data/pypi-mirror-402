"""
SimpleMem Configuration System

Priority (highest to lowest):
1. Function/Constructor parameters
2. Environment variables
3. Default values
"""
import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SimpleMemConfig:
    """SimpleMem configuration container"""

    # LLM Configuration
    openai_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    openai_base_url: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_BASE_URL")
    )
    llm_model: str = field(
        default_factory=lambda: os.environ.get("SIMPLEMEM_MODEL", "gpt-4.1-mini")
    )

    # Embedding Configuration
    embedding_model: str = field(
        default_factory=lambda: os.environ.get(
            "SIMPLEMEM_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"
        )
    )
    embedding_dimension: int = 1024
    embedding_context_length: int = 32768

    # Memory Building Parameters
    window_size: int = 40
    overlap_size: int = 2

    # Retrieval Parameters
    semantic_top_k: int = 25
    keyword_top_k: int = 5
    structured_top_k: int = 5

    # Database Configuration
    lancedb_path: str = field(
        default_factory=lambda: os.environ.get("SIMPLEMEM_DB_PATH", "./lancedb_data")
    )
    memory_table_name: str = "memory_entries"

    # Advanced Features
    enable_thinking: bool = False
    use_streaming: bool = True
    use_json_format: bool = False

    # Parallel Processing
    enable_parallel_processing: bool = True
    max_parallel_workers: int = 16
    enable_parallel_retrieval: bool = True
    max_retrieval_workers: int = 8

    # Planning and Reflection
    enable_planning: bool = True
    enable_reflection: bool = True
    max_reflection_rounds: int = 2


# Backwards compatibility aliases
OPENAI_API_KEY = property(lambda self: self.openai_api_key)
OPENAI_BASE_URL = property(lambda self: self.openai_base_url)
LLM_MODEL = property(lambda self: self.llm_model)
EMBEDDING_MODEL = property(lambda self: self.embedding_model)
EMBEDDING_DIMENSION = property(lambda self: self.embedding_dimension)
EMBEDDING_CONTEXT_LENGTH = property(lambda self: self.embedding_context_length)
WINDOW_SIZE = property(lambda self: self.window_size)
OVERLAP_SIZE = property(lambda self: self.overlap_size)
SEMANTIC_TOP_K = property(lambda self: self.semantic_top_k)
KEYWORD_TOP_K = property(lambda self: self.keyword_top_k)
STRUCTURED_TOP_K = property(lambda self: self.structured_top_k)
LANCEDB_PATH = property(lambda self: self.lancedb_path)
MEMORY_TABLE_NAME = property(lambda self: self.memory_table_name)
ENABLE_THINKING = property(lambda self: self.enable_thinking)
USE_STREAMING = property(lambda self: self.use_streaming)
USE_JSON_FORMAT = property(lambda self: self.use_json_format)
ENABLE_PARALLEL_PROCESSING = property(lambda self: self.enable_parallel_processing)
MAX_PARALLEL_WORKERS = property(lambda self: self.max_parallel_workers)
ENABLE_PARALLEL_RETRIEVAL = property(lambda self: self.enable_parallel_retrieval)
MAX_RETRIEVAL_WORKERS = property(lambda self: self.max_retrieval_workers)
ENABLE_PLANNING = property(lambda self: self.enable_planning)
ENABLE_REFLECTION = property(lambda self: self.enable_reflection)
MAX_REFLECTION_ROUNDS = property(lambda self: self.max_reflection_rounds)


# Global config instance
_config: Optional[SimpleMemConfig] = None


def get_config() -> SimpleMemConfig:
    """Get or create the global config instance"""
    global _config
    if _config is None:
        _config = SimpleMemConfig()
    return _config


def set_config(config: SimpleMemConfig) -> None:
    """Set the global config instance"""
    global _config
    _config = config


def reset_config() -> None:
    """Reset config to default"""
    global _config
    _config = None


# Create a module-level config object that acts like the old config module
class _ConfigModule:
    """
    A module-like object that provides backwards compatibility with the old config.py style.
    Allows accessing config values like: config.OPENAI_API_KEY
    """

    def __getattr__(self, name: str):
        cfg = get_config()
        # Map old-style uppercase names to new dataclass attributes
        attr_map = {
            "OPENAI_API_KEY": "openai_api_key",
            "OPENAI_BASE_URL": "openai_base_url",
            "LLM_MODEL": "llm_model",
            "EMBEDDING_MODEL": "embedding_model",
            "EMBEDDING_DIMENSION": "embedding_dimension",
            "EMBEDDING_CONTEXT_LENGTH": "embedding_context_length",
            "WINDOW_SIZE": "window_size",
            "OVERLAP_SIZE": "overlap_size",
            "SEMANTIC_TOP_K": "semantic_top_k",
            "KEYWORD_TOP_K": "keyword_top_k",
            "STRUCTURED_TOP_K": "structured_top_k",
            "LANCEDB_PATH": "lancedb_path",
            "MEMORY_TABLE_NAME": "memory_table_name",
            "ENABLE_THINKING": "enable_thinking",
            "USE_STREAMING": "use_streaming",
            "USE_JSON_FORMAT": "use_json_format",
            "ENABLE_PARALLEL_PROCESSING": "enable_parallel_processing",
            "MAX_PARALLEL_WORKERS": "max_parallel_workers",
            "ENABLE_PARALLEL_RETRIEVAL": "enable_parallel_retrieval",
            "MAX_RETRIEVAL_WORKERS": "max_retrieval_workers",
            "ENABLE_PLANNING": "enable_planning",
            "ENABLE_REFLECTION": "enable_reflection",
            "MAX_REFLECTION_ROUNDS": "max_reflection_rounds",
        }
        if name in attr_map:
            return getattr(cfg, attr_map[name])
        raise AttributeError(f"Config has no attribute '{name}'")


# Create a singleton instance for backwards compatibility
config = _ConfigModule()

__all__ = [
    "SimpleMemConfig",
    "get_config",
    "set_config",
    "reset_config",
    "config",
]
