"""LangChain integration for RAGVersion.

NOTE: This module has been reorganized into a package for better structure.
All imports are preserved for backward compatibility.
"""

# Re-export everything from the new package structure
from ragversion.integrations.langchain.sync import LangChainSync
from ragversion.integrations.langchain.loader import LangChainLoader
from ragversion.integrations.langchain.quick_start import quick_start

__all__ = ["LangChainSync", "LangChainLoader", "quick_start"]
