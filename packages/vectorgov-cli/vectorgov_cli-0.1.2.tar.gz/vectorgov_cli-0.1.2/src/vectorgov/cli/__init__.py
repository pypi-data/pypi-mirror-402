"""
VectorGov CLI - Cliente de linha de comando para a API VectorGov.

Uso:
    vectorgov search "O que é ETP?"
    vectorgov ask "Quando o ETP pode ser dispensado?"
    vectorgov auth login
"""

__version__ = "0.1.2"

from .main import app

__all__ = ["app", "__version__"]
