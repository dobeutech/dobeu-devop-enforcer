"""
Pytest configuration and shared fixtures for Dobeu Undertaker tests.
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from dobeu_undertaker.config.schema import (
    UndertakerConfig,
    StandardsConfig,
    AzureConfig,
    NotificationConfig,
    AgentsConfig,
    MonitoringConfig,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository structure for testing."""
    # Create basic repo structure
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    # Create sample files
    (tmp_path / "README.md").write_text("# Test Repository\n\nA test repository.")
    (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright (c) 2025 Test")
    (tmp_path / ".gitignore").write_text("__pycache__\n*.pyc\n.env\n")

    # Create sample Python files
    (tmp_path / "src" / "__init__.py").write_text('"""Test package."""\n')
    (tmp_path / "src" / "main.py").write_text('''\
"""Main module."""


def hello() -> str:
    """Return a greeting."""
    return "Hello, World!"


if __name__ == "__main__":
    print(hello())
''')

    # Create test file
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "test_main.py").write_text('''\
"""Tests for main module."""

from src.main import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello, World!"
''')

    return tmp_path


@pytest.fixture
def temp_repo_with_issues(tmp_path: Path) -> Path:
    """Create a temp repository with intentional issues for testing."""
    # Create basic structure
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()

    # Missing README.md (compliance issue)
    # Missing LICENSE (compliance issue)

    # Create file with security issues
    (tmp_path / "src" / "config.py").write_text('''\
"""Configuration with issues."""

# SEC001: Hardcoded password
DATABASE_PASSWORD = "super_secret_password_123"

# SEC002: Hardcoded API key
API_KEY = "sk-1234567890abcdefghijklmnop"

def connect():
    # SEC003: eval usage
    eval("print('dangerous')")
''')

    # Create file with style issues
    (tmp_path / "src" / "utils.py").write_text('''\
"""Utils with style issues."""

# STYLE001: Line too long
def very_long_function_name_that_exceeds_the_maximum_line_length_limit_configured_in_standards(parameter_one, parameter_two, parameter_three):
    pass

# STYLE002: Trailing whitespace
x = 1

# TODO without ticket
# TODO: fix this later
''')

    return tmp_path


@pytest.fixture
def default_config() -> UndertakerConfig:
    """Create a default configuration for testing."""
    return UndertakerConfig(
        name="test-undertaker",
        environment="development",
        standards=StandardsConfig(
            line_length=100,
            min_coverage_percent=80,
        ),
        azure=AzureConfig(),
        notifications=NotificationConfig(enabled=False),
        agents=AgentsConfig(parallel_execution=False),
        monitoring=MonitoringConfig(enable_tracing=False, enable_metrics=False),
    )


@pytest.fixture
def standards_config() -> StandardsConfig:
    """Create a standards configuration for testing."""
    return StandardsConfig(
        line_length=100,
        indent_size=4,
        quote_style="double",
        min_coverage_percent=80,
        require_readme=True,
        require_changelog=True,
    )


@pytest_asyncio.fixture
async def mock_azure_devops() -> AsyncGenerator[None, None]:
    """Mock Azure DevOps API responses."""
    # This would use respx or similar to mock HTTP calls
    yield


class MockAgentResponse:
    """Mock response from agent queries."""

    def __init__(self, content: str) -> None:
        self.content = content


@pytest.fixture
def mock_agent_success_response() -> str:
    """Mock successful agent response."""
    return '''{
    "status": "passed",
    "issues": [],
    "summary": "No issues found"
}'''


@pytest.fixture
def mock_agent_failure_response() -> str:
    """Mock agent response with issues."""
    return '''{
    "status": "failed",
    "issues": [
        {
            "severity": "high",
            "file": "src/config.py",
            "line": 5,
            "message": "Hardcoded password detected",
            "rule_id": "SEC001",
            "category": "security",
            "remediation": "Use environment variables"
        }
    ],
    "summary": "Found 1 security issue"
}'''
