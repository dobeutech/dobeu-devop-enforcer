"""
Configuration loader with multi-source support.

Loads configuration from:
1. Default values
2. Global config file (~/.dobeu/config.yaml)
3. Repository config (.dobeu/config.yaml)
4. Environment variables
5. Explicit config file (--config flag)

Later sources override earlier ones.
"""

import os
from pathlib import Path
from typing import Any

import yaml
import aiofiles

from dobeu_undertaker.config.schema import UndertakerConfig, StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """
    Multi-source configuration loader for Dobeu Undertaker.

    Supports hierarchical configuration with inheritance,
    allowing organizations to define base standards that
    individual repositories can extend or override.
    """

    # Standard config file locations
    GLOBAL_CONFIG_PATH = Path.home() / ".dobeu" / "config.yaml"
    REPO_CONFIG_PATH = Path(".dobeu") / "config.yaml"

    # Standard library paths (for inherit: feature)
    STANDARDS_LIBRARY = {
        "dobeu-base": "standards/dobeu-base.yaml",
        "dobeu-python": "standards/dobeu-python.yaml",
        "dobeu-typescript": "standards/dobeu-typescript.yaml",
        "dobeu-infrastructure": "standards/dobeu-infrastructure.yaml",
    }

    def __init__(
        self,
        config_path: Path | None = None,
        repo_path: Path | None = None,
    ) -> None:
        """
        Initialize the config loader.

        Args:
            config_path: Explicit path to config file (highest priority)
            repo_path: Repository path to look for .dobeu/config.yaml
        """
        self.explicit_config_path = config_path
        self.repo_path = repo_path or Path.cwd()

    async def load(self) -> UndertakerConfig:
        """
        Load configuration from all sources.

        Returns:
            Merged UndertakerConfig with all sources combined
        """
        config_data: dict[str, Any] = {}

        # 1. Load global config
        if self.GLOBAL_CONFIG_PATH.exists():
            global_config = await self._load_yaml(self.GLOBAL_CONFIG_PATH)
            config_data = self._deep_merge(config_data, global_config)
            logger.debug(f"Loaded global config from {self.GLOBAL_CONFIG_PATH}")

        # 2. Load repository config
        repo_config_path = self.repo_path / self.REPO_CONFIG_PATH
        if repo_config_path.exists():
            repo_config = await self._load_yaml(repo_config_path)

            # Handle inheritance
            if "inherit" in repo_config:
                inherited = await self._resolve_inheritance(repo_config["inherit"])
                config_data = self._deep_merge(config_data, inherited)

            config_data = self._deep_merge(config_data, repo_config)
            logger.debug(f"Loaded repo config from {repo_config_path}")

        # 3. Load explicit config file (highest priority)
        if self.explicit_config_path and self.explicit_config_path.exists():
            explicit_config = await self._load_yaml(self.explicit_config_path)
            config_data = self._deep_merge(config_data, explicit_config)
            logger.debug(f"Loaded explicit config from {self.explicit_config_path}")

        # 4. Environment variables are handled by Pydantic
        return UndertakerConfig(**config_data)

    async def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load a YAML configuration file."""
        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                return yaml.safe_load(content) or {}
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            return {}

    async def _resolve_inheritance(self, inherit_list: list[str]) -> dict[str, Any]:
        """
        Resolve inherited configuration from standard library.

        Args:
            inherit_list: List of standard names to inherit (e.g., ["dobeu-base"])

        Returns:
            Merged configuration from all inherited standards
        """
        merged: dict[str, Any] = {}

        for standard_name in inherit_list:
            if standard_name in self.STANDARDS_LIBRARY:
                # Load from bundled standards
                standards_path = (
                    Path(__file__).parent.parent.parent.parent
                    / self.STANDARDS_LIBRARY[standard_name]
                )
                if standards_path.exists():
                    standard_config = await self._load_yaml(standards_path)
                    merged = self._deep_merge(merged, standard_config)
                    logger.debug(f"Inherited standard: {standard_name}")
            else:
                logger.warning(f"Unknown standard to inherit: {standard_name}")

        return merged

    def _deep_merge(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Override values take precedence. Lists are replaced, not merged.

        Args:
            base: Base dictionary
            override: Dictionary with values to override

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    async def create_default_config(path: Path) -> None:
        """
        Create a default configuration file.

        Args:
            path: Path to write the config file
        """
        default_config = """\
# Dobeu Undertaker Configuration
# https://github.com/dobeutech/dobeu-undertaker

# Inherit base Dobeu standards
inherit:
  - dobeu-base

# Environment (development, staging, production)
environment: development

# Standards configuration
standards:
  line_length: 100
  min_coverage_percent: 80
  require_readme: true
  require_changelog: true

  # Git workflow
  branch_naming_pattern: "^(feature|bugfix|hotfix|release|chore)/[a-z0-9-]+$"
  commit_message_pattern: "^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .{10,}$"

  # Allowed dependency licenses
  allowed_licenses:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
    - ISC

# Azure integration
azure:
  organization: ""
  project: ""
  # key_vault_url: "https://your-keyvault.vault.azure.net/"

# Notifications
notifications:
  enabled: true
  notify_on_critical: true
  notify_on_high: true
  # slack_webhook_url: ""
  # teams_webhook_url: ""

# Agent configuration
agents:
  parallel_execution: true
  max_concurrent_agents: 6
  # disabled_agents:
  #   - documentation  # Disable if not needed

# Monitoring
monitoring:
  enable_tracing: true
  enable_metrics: true
  log_level: INFO
  export_to_azure: true
"""

        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(default_config)

        logger.info(f"Created default config at {path}")


async def load_standards_for_repo(repo_path: Path) -> StandardsConfig:
    """
    Convenience function to load just the standards config for a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        StandardsConfig for the repository
    """
    loader = ConfigLoader(repo_path=repo_path)
    config = await loader.load()
    return config.standards
