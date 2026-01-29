"""
Gerenciador de configuração do CLI VectorGov.

Armazena configurações em ~/.vectorgov/config.yaml
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Gerencia configurações do CLI em arquivo YAML."""

    def __init__(self):
        """Inicializa o gerenciador de configuração."""
        self.config_dir = Path.home() / ".vectorgov"
        self.config_file = self.config_dir / "config.yaml"
        self._config: Optional[Dict[str, Any]] = None

    def _ensure_dir(self):
        """Garante que o diretório de configuração existe."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo."""
        if self._config is not None:
            return self._config

        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

        return self._config

    def _save(self):
        """Salva configuração no arquivo."""
        self._ensure_dir()
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de uma configuração.

        Prioridade:
        1. Variável de ambiente (VECTORGOV_<KEY>)
        2. Arquivo de configuração
        3. Valor padrão

        Args:
            key: Nome da configuração
            default: Valor padrão se não encontrado

        Returns:
            Valor da configuração
        """
        # Tenta variável de ambiente primeiro
        env_key = f"VECTORGOV_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        # Tenta arquivo de configuração
        config = self._load()
        return config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Define valor de uma configuração.

        Args:
            key: Nome da configuração
            value: Valor a ser salvo
        """
        config = self._load()
        config[key] = value
        self._config = config
        self._save()

    def delete(self, key: str):
        """
        Remove uma configuração.

        Args:
            key: Nome da configuração
        """
        config = self._load()
        if key in config:
            del config[key]
            self._config = config
            self._save()

    def list_all(self) -> Dict[str, Any]:
        """
        Lista todas as configurações.

        Returns:
            Dicionário com todas as configurações
        """
        return self._load().copy()

    def clear(self):
        """Remove todas as configurações."""
        self._config = {}
        self._save()
