"""
SimpleMem: Efficient Lifelong Memory for LLM Agents

Usage:
    from simplemem import SimpleMemSystem

    system = SimpleMemSystem(api_key="your-key", clear_db=True)
    system.add_dialogue("Alice", "Hello!", "2025-01-15T10:00:00")
    system.finalize()
    answer = system.ask("What did Alice say?")
"""

from simplemem.__version__ import __version__
from simplemem.system import SimpleMemSystem, create_system
from simplemem.models.memory_entry import MemoryEntry, Dialogue
from simplemem.config import SimpleMemConfig, get_config, set_config

__all__ = [
    # Version
    "__version__",
    # Main classes
    "SimpleMemSystem",
    "create_system",
    # Data models
    "MemoryEntry",
    "Dialogue",
    # Configuration
    "SimpleMemConfig",
    "get_config",
    "set_config",
]
