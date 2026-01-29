"""LlamaIndex integration for RAGVersion.

NOTE: This module has been reorganized into a package for better structure.
All imports are preserved for backward compatibility.
"""

# Re-export everything from the new package structure
from ragversion.integrations.llamaindex.sync import LlamaIndexSync
from ragversion.integrations.llamaindex.loader import LlamaIndexLoader
from ragversion.integrations.llamaindex.quick_start import quick_start

__all__ = ["LlamaIndexSync", "LlamaIndexLoader", "quick_start"]
