"""
Tests for the main orchestrator.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from dobeu_undertaker.orchestrator import (
    DobeuOrchestrator,
    ScanResult,
    EnforcementResult,
)
from dobeu_undertaker.config.schema import UndertakerConfig, StandardsConfig


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_create_scan_result(self) -> None:
        """Test creating a scan result."""
        result = ScanResult(
            agent_name="SecurityAgent",
            status="passed",
            issues=[],
            summary="No issues found",
            duration_ms=1500,
        )

        assert result.agent_name == "SecurityAgent"
        assert result.status == "passed"
        assert result.issues == []
        assert result.duration_ms == 1500

    def test_scan_result_to_dict(self) -> None:
        """Test converting scan result to dictionary."""
        result = ScanResult(
            agent_name="TestAgent",
            status="failed",
            issues=[{"severity": "high", "message": "Test issue"}],
            summary="Found 1 issue",
            duration_ms=2000,
        )

        data = result.to_dict()

        assert data["agent_name"] == "TestAgent"
        assert data["status"] == "failed"
        assert len(data["issues"]) == 1
        assert "timestamp" in data


class TestDobeuOrchestrator:
    """Tests for DobeuOrchestrator."""

    def test_init(self, default_config: UndertakerConfig) -> None:
        """Test orchestrator initialization."""
        orchestrator = DobeuOrchestrator(config=default_config)

        assert orchestrator.config == default_config
        assert orchestrator.results == []

    def test_get_enabled_agents_default(self, default_config: UndertakerConfig) -> None:
        """Test getting enabled agents with default config."""
        orchestrator = DobeuOrchestrator(config=default_config)
        agents = orchestrator._get_enabled_agents()

        # All agents should be enabled by default
        assert "security" in agents
        assert "code_style" in agents
        assert "compliance" in agents
        assert "testing" in agents
        assert "documentation" in agents
        assert "dependency_audit" in agents

    def test_get_enabled_agents_with_disabled(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test getting enabled agents with some disabled."""
        default_config.agents.disabled_agents = ["documentation", "testing"]
        orchestrator = DobeuOrchestrator(config=default_config)
        agents = orchestrator._get_enabled_agents()

        assert "security" in agents
        assert "documentation" not in agents
        assert "testing" not in agents

    def test_parse_agent_response_json(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test parsing JSON response from agent."""
        orchestrator = DobeuOrchestrator(config=default_config)

        response = '{"status": "passed", "issues": [], "summary": "OK"}'
        result = orchestrator._parse_agent_response(response)

        assert result["status"] == "passed"
        assert result["issues"] == []

    def test_parse_agent_response_markdown(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test parsing JSON in markdown code block."""
        orchestrator = DobeuOrchestrator(config=default_config)

        response = '''Here are the results:

```json
{"status": "failed", "issues": [{"severity": "high"}], "summary": "Issues found"}
```

Please review the above.'''

        result = orchestrator._parse_agent_response(response)

        assert result["status"] == "failed"
        assert len(result["issues"]) == 1

    def test_parse_agent_response_invalid(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test parsing invalid response."""
        orchestrator = DobeuOrchestrator(config=default_config)

        response = "This is not valid JSON at all"
        result = orchestrator._parse_agent_response(response)

        assert result["status"] == "error"

    def test_calculate_overall_status_passed(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test overall status when all passed."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult("Agent1", "passed", [], "OK", 100),
            ScanResult("Agent2", "passed", [], "OK", 100),
        ]

        assert orchestrator._calculate_overall_status() == "passed"

    def test_calculate_overall_status_failed(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test overall status when one failed."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult("Agent1", "passed", [], "OK", 100),
            ScanResult("Agent2", "failed", [{"severity": "high"}], "Issues", 100),
        ]

        assert orchestrator._calculate_overall_status() == "failed"

    def test_calculate_overall_status_warning(
        self,
        default_config: UndertakerConfig,
    ) -> None:
        """Test overall status with warnings."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult("Agent1", "passed", [], "OK", 100),
            ScanResult("Agent2", "warning", [{"severity": "low"}], "Minor", 100),
        ]

        assert orchestrator._calculate_overall_status() == "warning"

    def test_generate_summary(self, default_config: UndertakerConfig) -> None:
        """Test summary generation."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult(
                "Security",
                "failed",
                [
                    {"severity": "critical", "message": "Secret found"},
                    {"severity": "high", "message": "Eval usage"},
                ],
                "Issues found",
                1000,
            ),
            ScanResult(
                "Style",
                "warning",
                [{"severity": "low", "message": "Trailing whitespace"}],
                "Minor issues",
                500,
            ),
        ]

        summary = orchestrator._generate_summary()

        assert summary["total_issues"] == 3
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["agents_run"] == 2
        assert summary["total_duration_ms"] == 1500


class TestOrchestratorIntegration:
    """Integration tests for orchestrator (require mocking agent SDK)."""

    @pytest.mark.asyncio
    async def test_scan_repository_mocked(
        self,
        default_config: UndertakerConfig,
        temp_repo: Path,
        mock_agent_success_response: str,
    ) -> None:
        """Test scanning a repository with mocked agent."""
        orchestrator = DobeuOrchestrator(config=default_config)

        # Mock the _run_single_agent method
        async def mock_run_agent(repo_path: Path, agent_name: str) -> ScanResult:
            return ScanResult(
                agent_name=agent_name.title(),
                status="passed",
                issues=[],
                summary="No issues found",
                duration_ms=100,
            )

        with patch.object(orchestrator, "_run_single_agent", mock_run_agent):
            results = await orchestrator.scan_repository(temp_repo, parallel=False)

        assert len(results) == 6  # All 6 agents
        assert all(r.status == "passed" for r in results)

    @pytest.mark.asyncio
    async def test_generate_report_json(
        self,
        default_config: UndertakerConfig,
        temp_repo: Path,
        tmp_path: Path,
    ) -> None:
        """Test generating a JSON report."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult("TestAgent", "passed", [], "OK", 100),
        ]

        output_path = tmp_path / "report.json"
        await orchestrator.generate_report(
            repo_path=temp_repo,
            output_path=output_path,
            report_format="json",
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["overall_status"] == "passed"
        assert "results" in data

    @pytest.mark.asyncio
    async def test_generate_report_markdown(
        self,
        default_config: UndertakerConfig,
        temp_repo: Path,
        tmp_path: Path,
    ) -> None:
        """Test generating a Markdown report."""
        orchestrator = DobeuOrchestrator(config=default_config)
        orchestrator.results = [
            ScanResult("TestAgent", "failed", [{"severity": "high"}], "Issues", 100),
        ]

        output_path = tmp_path / "report.md"
        await orchestrator.generate_report(
            repo_path=temp_repo,
            output_path=output_path,
            report_format="markdown",
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Compliance Report" in content
        assert "FAILED" in content
