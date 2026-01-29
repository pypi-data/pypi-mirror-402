"""
Utilitários do CLI VectorGov.
"""

from .config import ConfigManager
from .output import OutputFormat, format_search_results

__all__ = ["ConfigManager", "OutputFormat", "format_search_results"]
