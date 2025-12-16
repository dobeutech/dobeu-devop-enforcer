"""
Main Orchestrator Agent for Dobeu Undertaker.

This is the central agent that coordinates all DevOps enforcement activities.
It spawns specialized subagents for specific tasks and aggregates results.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from dobeu_undertaker.config.schema import UndertakerConfig, AgentConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class ScanResult:
    """Result of a repository scan."""

    def __init__(
        self,
        agent_name: str,
        status: str,
        issues: list[dict[str, Any]],
        summary: str,
        duration_ms: int,
    ) -> None:
        self.agent_name = agent_name
        self.status = status  # "passed", "failed", "warning", "error"
        self.issues = issues
        self.summary = summary
        self.duration_ms = duration_ms
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "issues": self.issues,
            "summary": self.summary,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class EnforcementResult:
    """Result of standards enforcement."""

    def __init__(
        self,
        agent_name: str,
        fixes_applied: list[dict[str, Any]],
        fixes_skipped: list[dict[str, Any]],
        errors: list[str],
    ) -> None:
        self.agent_name = agent_name
        self.fixes_applied = fixes_applied
        self.fixes_skipped = fixes_skipped
        self.errors = errors


class DobeuOrchestrator:
    """
    Main orchestrator for Dobeu Undertaker.

    Coordinates specialized subagents to perform comprehensive DevOps
    standards enforcement across repositories.
    """

    # System prompt for the orchestrator agent
    ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the Dobeu Undertaker, the DevOps standards enforcement orchestrator for
Dobeu Tech Solutions LLC. Your role is to coordinate compliance checks across
codebases and ensure uniform delivery standards.

## Core Responsibilities
1. Enforce coding standards and best practices
2. Ensure security compliance (OWASP, secrets detection)
3. Validate documentation completeness
4. Verify test coverage requirements
5. Audit dependencies for vulnerabilities
6. Ensure uniform CI/CD pipeline configurations

## Standards Philosophy
- Consistency over perfection: uniform standards across all repos
- Security by default: no secrets in code, no vulnerable dependencies
- Documentation as code: everything documented, nothing assumed
- Test-driven confidence: adequate coverage before deployment
- Automated enforcement: humans review, machines enforce

## Agent Coordination
You can spawn specialized subagents for focused tasks:
- SecurityAgent: SAST, secrets detection, OWASP compliance
- CodeStyleAgent: Formatting, linting, naming conventions
- ComplianceAgent: License compliance, policy adherence
- TestingAgent: Coverage analysis, test quality
- DocumentationAgent: README, API docs, inline comments
- DependencyAuditAgent: CVE scanning, version policy

## Output Format
Always provide structured, actionable output with:
- Clear pass/fail status per check
- Specific file:line references for issues
- Severity levels (critical, high, medium, low, info)
- Remediation guidance for each issue
"""

    # Subagent definitions for specialized tasks
    SUBAGENT_DEFINITIONS = {
        "security": AgentConfig(
            name="SecurityAgent",
            description="Scans for security vulnerabilities, secrets, and OWASP compliance",
            system_prompt="""\
You are a security-focused agent for Dobeu Tech Solutions. Your job is to:
1. Detect hardcoded secrets (API keys, passwords, tokens)
2. Identify OWASP Top 10 vulnerabilities
3. Check for insecure coding patterns
4. Verify secure configuration practices
5. Scan for SQL injection, XSS, and command injection risks

Report findings with severity levels and specific remediation steps.
""",
            allowed_tools=["Read", "Glob", "Grep", "Bash"],
        ),
        "code_style": AgentConfig(
            name="CodeStyleAgent",
            description="Enforces code formatting, linting, and naming conventions",
            system_prompt="""\
You are a code quality agent for Dobeu Tech Solutions. Your job is to:
1. Verify code formatting matches configured style (ruff, black, prettier)
2. Check naming conventions (files, variables, functions, classes)
3. Identify code smells and anti-patterns
4. Ensure import ordering and organization
5. Validate type annotations where required

Provide specific fixes for style violations.
""",
            allowed_tools=["Read", "Glob", "Grep", "Bash"],
        ),
        "compliance": AgentConfig(
            name="ComplianceAgent",
            description="Ensures license compliance and policy adherence",
            system_prompt="""\
You are a compliance agent for Dobeu Tech Solutions. Your job is to:
1. Verify all files have required license headers
2. Check dependency licenses against allowed list
3. Ensure copyright notices are current
4. Validate required files exist (LICENSE, CONTRIBUTING, etc.)
5. Check branch naming and commit message conventions

Report policy violations with remediation guidance.
""",
            allowed_tools=["Read", "Glob", "Grep", "Bash"],
        ),
        "testing": AgentConfig(
            name="TestingAgent",
            description="Analyzes test coverage and test quality",
            system_prompt="""\
You are a testing quality agent for Dobeu Tech Solutions. Your job is to:
1. Verify test coverage meets minimum thresholds
2. Identify untested critical paths
3. Check for test anti-patterns (flaky tests, no assertions)
4. Ensure integration and unit test separation
5. Validate test naming conventions

Provide guidance on improving test coverage and quality.
""",
            allowed_tools=["Read", "Glob", "Grep", "Bash"],
        ),
        "documentation": AgentConfig(
            name="DocumentationAgent",
            description="Validates documentation completeness and quality",
            system_prompt="""\
You are a documentation agent for Dobeu Tech Solutions. Your job is to:
1. Verify README.md exists and is comprehensive
2. Check API documentation completeness
3. Validate inline code comments for complex logic
4. Ensure CHANGELOG is maintained
5. Check for broken documentation links

Identify documentation gaps and suggest improvements.
""",
            allowed_tools=["Read", "Glob", "Grep", "WebFetch"],
        ),
        "dependency_audit": AgentConfig(
            name="DependencyAuditAgent",
            description="Audits dependencies for vulnerabilities and version policies",
            system_prompt="""\
You are a dependency audit agent for Dobeu Tech Solutions. Your job is to:
1. Scan for known CVEs in dependencies
2. Identify outdated packages
3. Check for deprecated dependencies
4. Verify dependency version pinning
5. Detect unnecessary or duplicate dependencies

Provide severity-ranked vulnerability reports with upgrade paths.
""",
            allowed_tools=["Read", "Glob", "Grep", "Bash", "WebFetch"],
        ),
    }

    def __init__(self, config: UndertakerConfig) -> None:
        """Initialize the orchestrator with configuration."""
        self.config = config
        self.results: list[ScanResult] = []

    async def scan_repository(
        self,
        repo_path: Path,
        parallel: bool = True,
    ) -> list[ScanResult]:
        """
        Scan a repository using all configured agents.

        Args:
            repo_path: Path to the repository to scan
            parallel: Whether to run agents in parallel

        Returns:
            List of ScanResult objects from each agent
        """
        logger.info(f"Starting repository scan: {repo_path}")

        agents_to_run = self._get_enabled_agents()

        if parallel:
            results = await self._run_agents_parallel(repo_path, agents_to_run)
        else:
            results = await self._run_agents_sequential(repo_path, agents_to_run)

        self.results = results
        return results

    def _get_enabled_agents(self) -> list[str]:
        """Get list of enabled agent names based on config."""
        # Default: all agents enabled
        all_agents = list(self.SUBAGENT_DEFINITIONS.keys())

        if self.config.agents.enabled_agents:
            return [a for a in all_agents if a in self.config.agents.enabled_agents]

        if self.config.agents.disabled_agents:
            return [a for a in all_agents if a not in self.config.agents.disabled_agents]

        return all_agents

    async def _run_agents_parallel(
        self,
        repo_path: Path,
        agent_names: list[str],
    ) -> list[ScanResult]:
        """Run multiple agents in parallel."""
        tasks = [
            self._run_single_agent(repo_path, name)
            for name in agent_names
        ]
        return await asyncio.gather(*tasks)

    async def _run_agents_sequential(
        self,
        repo_path: Path,
        agent_names: list[str],
    ) -> list[ScanResult]:
        """Run agents sequentially."""
        results = []
        for name in agent_names:
            result = await self._run_single_agent(repo_path, name)
            results.append(result)
        return results

    async def _run_single_agent(
        self,
        repo_path: Path,
        agent_name: str,
    ) -> ScanResult:
        """Run a single specialized agent."""
        start_time = asyncio.get_event_loop().time()
        agent_config = self.SUBAGENT_DEFINITIONS[agent_name]

        logger.info(f"Running {agent_name} on {repo_path}")

        prompt = f"""\
Scan the repository at {repo_path} for issues related to your specialization.

Repository context:
- Path: {repo_path}
- Standards config: {self.config.standards.model_dump_json()}

Provide a structured analysis with:
1. Overall status (passed/failed/warning)
2. List of issues found with severity and file:line references
3. Summary of findings
4. Specific remediation steps for each issue

Output your findings as JSON with this structure:
{{
    "status": "passed|failed|warning",
    "issues": [
        {{
            "severity": "critical|high|medium|low|info",
            "file": "path/to/file.py",
            "line": 42,
            "message": "Description of issue",
            "rule_id": "RULE_CODE",
            "remediation": "How to fix"
        }}
    ],
    "summary": "Brief overall summary"
}}
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=agent_config.system_prompt,
                    allowed_tools=agent_config.allowed_tools,
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, 'content'):
                    response_text += str(message.content)

            # Parse the JSON response
            result_data = self._parse_agent_response(response_text)

            end_time = asyncio.get_event_loop().time()
            duration_ms = int((end_time - start_time) * 1000)

            return ScanResult(
                agent_name=agent_config.name,
                status=result_data.get("status", "error"),
                issues=result_data.get("issues", []),
                summary=result_data.get("summary", "No summary provided"),
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            end_time = asyncio.get_event_loop().time()
            duration_ms = int((end_time - start_time) * 1000)

            return ScanResult(
                agent_name=agent_config.name,
                status="error",
                issues=[],
                summary=f"Agent execution failed: {e}",
                duration_ms=duration_ms,
            )

    def _parse_agent_response(self, response: str) -> dict[str, Any]:
        """Parse JSON response from agent, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "issues": [],
                "summary": f"Failed to parse agent response: {response[:200]}...",
            }

    async def enforce_standards(
        self,
        repo_path: Path,
        auto_fix: bool = False,
        dry_run: bool = False,
    ) -> list[EnforcementResult]:
        """
        Enforce standards and optionally auto-fix issues.

        Args:
            repo_path: Path to the repository
            auto_fix: Whether to automatically fix issues
            dry_run: Show what would be changed without making changes

        Returns:
            List of enforcement results
        """
        logger.info(f"Enforcing standards on {repo_path} (fix={auto_fix}, dry_run={dry_run})")

        # First scan to find issues
        scan_results = await self.scan_repository(repo_path, parallel=True)

        enforcement_results = []

        for scan_result in scan_results:
            fixes_applied = []
            fixes_skipped = []
            errors = []

            for issue in scan_result.issues:
                if auto_fix and not dry_run:
                    # Attempt to fix the issue using the agent
                    try:
                        fixed = await self._attempt_fix(repo_path, issue)
                        if fixed:
                            fixes_applied.append(issue)
                        else:
                            fixes_skipped.append(issue)
                    except Exception as e:
                        errors.append(f"Failed to fix {issue.get('file')}: {e}")
                        fixes_skipped.append(issue)
                else:
                    fixes_skipped.append(issue)

            enforcement_results.append(EnforcementResult(
                agent_name=scan_result.agent_name,
                fixes_applied=fixes_applied,
                fixes_skipped=fixes_skipped,
                errors=errors,
            ))

        return enforcement_results

    async def _attempt_fix(
        self,
        repo_path: Path,
        issue: dict[str, Any],
    ) -> bool:
        """Attempt to automatically fix an issue."""
        prompt = f"""\
Fix the following issue in {repo_path}:

File: {issue.get('file')}
Line: {issue.get('line')}
Issue: {issue.get('message')}
Remediation: {issue.get('remediation')}

Apply the fix and confirm it was successful.
"""

        try:
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    allowed_tools=["Read", "Edit", "Write"],
                    cwd=str(repo_path),
                    permission_mode="acceptEdits",
                ),
            ):
                pass  # Process the fix
            return True
        except Exception:
            return False

    async def generate_report(
        self,
        repo_path: Path,
        output_path: Path,
        report_format: str = "json",
    ) -> None:
        """Generate a compliance report."""
        if not self.results:
            self.results = await self.scan_repository(repo_path)

        report_data = {
            "repository": str(repo_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": self._calculate_overall_status(),
            "summary": self._generate_summary(),
            "results": [r.to_dict() for r in self.results],
        }

        if report_format == "json":
            output_path.write_text(json.dumps(report_data, indent=2))
        elif report_format == "markdown":
            output_path.write_text(self._format_markdown_report(report_data))
        elif report_format == "html":
            output_path.write_text(self._format_html_report(report_data))

    def _calculate_overall_status(self) -> str:
        """Calculate overall status from all agent results."""
        statuses = [r.status for r in self.results]
        if "failed" in statuses:
            return "failed"
        if "error" in statuses:
            return "error"
        if "warning" in statuses:
            return "warning"
        return "passed"

    def _generate_summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        total_issues = sum(len(r.issues) for r in self.results)
        critical = sum(
            len([i for i in r.issues if i.get("severity") == "critical"])
            for r in self.results
        )
        high = sum(
            len([i for i in r.issues if i.get("severity") == "high"])
            for r in self.results
        )

        return {
            "total_issues": total_issues,
            "critical": critical,
            "high": high,
            "agents_run": len(self.results),
            "total_duration_ms": sum(r.duration_ms for r in self.results),
        }

    def _format_markdown_report(self, data: dict[str, Any]) -> str:
        """Format report as Markdown."""
        lines = [
            f"# Compliance Report: {data['repository']}",
            f"\nGenerated: {data['generated_at']}",
            f"\n## Overall Status: {data['overall_status'].upper()}",
            "\n## Summary",
            f"- Total Issues: {data['summary']['total_issues']}",
            f"- Critical: {data['summary']['critical']}",
            f"- High: {data['summary']['high']}",
            "\n## Agent Results\n",
        ]

        for result in data['results']:
            lines.append(f"### {result['agent_name']}")
            lines.append(f"Status: {result['status']}")
            lines.append(f"Summary: {result['summary']}")
            if result['issues']:
                lines.append("\n#### Issues:")
                for issue in result['issues']:
                    lines.append(
                        f"- [{issue.get('severity', 'unknown').upper()}] "
                        f"{issue.get('file', 'unknown')}:{issue.get('line', '?')} - "
                        f"{issue.get('message', 'No message')}"
                    )
            lines.append("")

        return "\n".join(lines)

    def _format_html_report(self, data: dict[str, Any]) -> str:
        """Format report as HTML."""
        # Simple HTML template
        return f"""\
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Report - {data['repository']}</title>
    <style>
        body {{ font-family: sans-serif; margin: 2em; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .warning {{ color: orange; }}
        .issue {{ margin: 0.5em 0; padding: 0.5em; background: #f5f5f5; }}
        .critical {{ border-left: 4px solid red; }}
        .high {{ border-left: 4px solid orange; }}
    </style>
</head>
<body>
    <h1>Compliance Report</h1>
    <p>Repository: {data['repository']}</p>
    <p>Generated: {data['generated_at']}</p>
    <h2 class="{data['overall_status']}">Status: {data['overall_status'].upper()}</h2>
    <p>Total Issues: {data['summary']['total_issues']}</p>
</body>
</html>
"""

    async def watch_repositories(
        self,
        repo_paths: list[Path],
        interval: int = 300,
    ) -> None:
        """Watch repositories and run scans periodically."""
        logger.info(f"Watching {len(repo_paths)} repositories (interval={interval}s)")

        while True:
            for repo_path in repo_paths:
                try:
                    results = await self.scan_repository(repo_path)
                    overall_status = self._calculate_overall_status()

                    if overall_status in ("failed", "error"):
                        await self._send_notifications(repo_path, results)

                except Exception as e:
                    logger.error(f"Watch scan failed for {repo_path}: {e}")

            await asyncio.sleep(interval)

    async def _send_notifications(
        self,
        repo_path: Path,
        results: list[ScanResult],
    ) -> None:
        """Send notifications for compliance failures."""
        if self.config.notifications.enabled:
            from dobeu_undertaker.integrations.notifications import NotificationService

            notifier = NotificationService(self.config.notifications)
            await notifier.send_compliance_alert(repo_path, results)

    def display_results(self, results: list[ScanResult], console: Console) -> None:
        """Display scan results in a formatted table."""
        table = Table(title="Scan Results")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Issues", justify="right")
        table.add_column("Duration", justify="right")

        status_colors = {
            "passed": "green",
            "failed": "red",
            "warning": "yellow",
            "error": "red",
        }

        for result in results:
            color = status_colors.get(result.status, "white")
            table.add_row(
                result.agent_name,
                f"[{color}]{result.status.upper()}[/{color}]",
                str(len(result.issues)),
                f"{result.duration_ms}ms",
            )

        console.print(table)

        # Show summary
        summary = self._generate_summary()
        console.print(Panel(
            f"Total Issues: {summary['total_issues']} | "
            f"Critical: {summary['critical']} | "
            f"High: {summary['high']}",
            title="Summary",
            border_style="blue",
        ))

    def display_enforcement_results(
        self,
        results: list[EnforcementResult],
        console: Console,
    ) -> None:
        """Display enforcement results."""
        table = Table(title="Enforcement Results")
        table.add_column("Agent", style="cyan")
        table.add_column("Fixed", style="green", justify="right")
        table.add_column("Skipped", style="yellow", justify="right")
        table.add_column("Errors", style="red", justify="right")

        for result in results:
            table.add_row(
                result.agent_name,
                str(len(result.fixes_applied)),
                str(len(result.fixes_skipped)),
                str(len(result.errors)),
            )

        console.print(table)
