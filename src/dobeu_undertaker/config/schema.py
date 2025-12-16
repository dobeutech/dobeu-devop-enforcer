"""
Pydantic configuration schemas for Dobeu Undertaker.

Provides type-safe configuration with validation, defaults, and
environment variable support for all aspects of the undertaker.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RepoConfig(BaseModel):
    """Configuration for a single repository."""

    name: str = Field(..., description="Repository name")
    path: Path | None = Field(None, description="Local path to repository")
    remote_url: str | None = Field(None, description="Git remote URL")
    branch: str = Field("main", description="Branch to scan")
    inherit: list[str] = Field(default_factory=list, description="Standards to inherit")
    overrides: dict = Field(default_factory=dict, description="Per-repo standard overrides")


class StandardsConfig(BaseModel):
    """Configuration for standards enforcement."""

    # Code style
    line_length: int = Field(100, description="Maximum line length")
    indent_size: int = Field(4, description="Indentation size")
    quote_style: Literal["single", "double"] = Field("double", description="String quote style")

    # Naming conventions
    file_naming: Literal["snake_case", "kebab-case", "PascalCase"] = Field(
        "snake_case", description="File naming convention"
    )
    class_naming: Literal["PascalCase", "snake_case"] = Field(
        "PascalCase", description="Class naming convention"
    )
    function_naming: Literal["snake_case", "camelCase"] = Field(
        "snake_case", description="Function naming convention"
    )

    # Testing
    min_coverage_percent: int = Field(80, description="Minimum test coverage percentage")
    require_unit_tests: bool = Field(True, description="Require unit tests for new code")
    require_integration_tests: bool = Field(False, description="Require integration tests")

    # Documentation
    require_readme: bool = Field(True, description="Require README.md")
    require_changelog: bool = Field(True, description="Require CHANGELOG.md")
    require_docstrings: bool = Field(True, description="Require docstrings for public APIs")

    # Security
    block_secrets: bool = Field(True, description="Block commits with detected secrets")
    require_security_review: bool = Field(False, description="Require security review for PRs")
    allowed_licenses: list[str] = Field(
        default_factory=lambda: ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"],
        description="Allowed dependency licenses",
    )

    # Dependencies
    max_dependency_age_days: int = Field(365, description="Max age for dependencies")
    block_vulnerable_deps: bool = Field(True, description="Block vulnerable dependencies")
    require_lockfile: bool = Field(True, description="Require dependency lock file")

    # Git workflow
    branch_naming_pattern: str = Field(
        r"^(feature|bugfix|hotfix|release|chore)/[a-z0-9-]+$",
        description="Branch naming regex pattern",
    )
    commit_message_pattern: str = Field(
        r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{10,}$",
        description="Conventional commit pattern",
    )
    require_linear_history: bool = Field(True, description="Require linear git history")

    # Disabled rules
    disabled_rules: list[str] = Field(
        default_factory=list, description="Rule IDs to disable"
    )


class AzureConfig(BaseModel):
    """Azure platform integration configuration."""

    # Azure DevOps
    organization: str | None = Field(None, description="Azure DevOps organization")
    project: str | None = Field(None, description="Azure DevOps project name")
    pat_env_var: str = Field(
        "AZURE_DEVOPS_PAT", description="Environment variable for PAT"
    )

    # Azure Monitor
    instrumentation_key: str | None = Field(
        None, description="Application Insights instrumentation key"
    )
    connection_string_env_var: str = Field(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        description="Environment variable for App Insights connection string",
    )

    # Azure Key Vault
    key_vault_url: str | None = Field(None, description="Azure Key Vault URL")
    use_managed_identity: bool = Field(True, description="Use managed identity for auth")


class NotificationConfig(BaseModel):
    """Notification service configuration."""

    enabled: bool = Field(True, description="Enable notifications")

    # Slack
    slack_webhook_url: str | None = Field(None, description="Slack webhook URL")
    slack_channel: str | None = Field(None, description="Slack channel for notifications")

    # Microsoft Teams
    teams_webhook_url: str | None = Field(None, description="Teams webhook URL")

    # Email
    smtp_host: str | None = Field(None, description="SMTP server host")
    smtp_port: int = Field(587, description="SMTP server port")
    smtp_user: str | None = Field(None, description="SMTP username")
    smtp_password_env_var: str = Field(
        "SMTP_PASSWORD", description="Environment variable for SMTP password"
    )
    email_recipients: list[str] = Field(
        default_factory=list, description="Email recipients for notifications"
    )

    # Notification thresholds
    notify_on_critical: bool = Field(True, description="Notify on critical issues")
    notify_on_high: bool = Field(True, description="Notify on high-severity issues")
    notify_on_warning: bool = Field(False, description="Notify on warnings")


class AgentConfig(BaseModel):
    """Configuration for a specialized agent."""

    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Agent description")
    system_prompt: str = Field("", description="System prompt for the agent")
    allowed_tools: list[str] = Field(
        default_factory=lambda: ["Read", "Glob", "Grep"],
        description="Tools the agent can use",
    )
    timeout_seconds: int = Field(300, description="Agent timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")


class AgentsConfig(BaseModel):
    """Configuration for agent orchestration."""

    enabled_agents: list[str] | None = Field(
        None, description="List of enabled agent names (None = all)"
    )
    disabled_agents: list[str] = Field(
        default_factory=list, description="List of disabled agent names"
    )
    parallel_execution: bool = Field(True, description="Run agents in parallel")
    max_concurrent_agents: int = Field(6, description="Maximum concurrent agents")

    # Custom agent definitions
    custom_agents: dict[str, AgentConfig] = Field(
        default_factory=dict, description="Custom agent definitions"
    )


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    enable_tracing: bool = Field(True, description="Enable OpenTelemetry tracing")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Logging level"
    )
    structured_logging: bool = Field(True, description="Use structured JSON logging")

    # Export configuration
    otlp_endpoint: str | None = Field(None, description="OpenTelemetry collector endpoint")
    export_to_azure: bool = Field(True, description="Export telemetry to Azure Monitor")


class UndertakerConfig(BaseSettings):
    """
    Main configuration for Dobeu Undertaker.

    Supports loading from:
    - Environment variables (DOBEU_ prefix)
    - .env file
    - YAML configuration files
    - Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="DOBEU_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    # Core settings
    name: str = Field("dobeu-undertaker", description="Instance name")
    environment: Literal["development", "staging", "production"] = Field(
        "development", description="Deployment environment"
    )

    # Sub-configurations
    standards: StandardsConfig = Field(
        default_factory=StandardsConfig, description="Standards configuration"
    )
    azure: AzureConfig = Field(
        default_factory=AzureConfig, description="Azure integration configuration"
    )
    notifications: NotificationConfig = Field(
        default_factory=NotificationConfig, description="Notification configuration"
    )
    agents: AgentsConfig = Field(
        default_factory=AgentsConfig, description="Agent orchestration configuration"
    )
    monitoring: MonitoringConfig = Field(
        default_factory=MonitoringConfig, description="Monitoring configuration"
    )

    # Repository configuration
    repositories: list[RepoConfig] = Field(
        default_factory=list, description="List of repositories to manage"
    )

    # Global paths
    config_dir: Path = Field(
        Path.home() / ".dobeu", description="Global configuration directory"
    )
    cache_dir: Path = Field(
        Path.home() / ".dobeu" / "cache", description="Cache directory"
    )
