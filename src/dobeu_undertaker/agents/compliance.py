"""
Compliance Agent - Ensures license compliance and policy adherence.

Responsibilities:
- Verify all files have required license headers
- Check dependency licenses against allowed list
- Ensure copyright notices are current
- Validate required files exist (LICENSE, CONTRIBUTING, etc.)
- Check branch naming and commit message conventions
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class ComplianceAgent:
    """
    Compliance and policy enforcement agent.

    Ensures repositories adhere to organizational policies
    including licensing, documentation requirements, and
    workflow conventions.
    """

    SYSTEM_PROMPT = """\
You are a compliance agent for Dobeu Tech Solutions LLC. Your mission is to
ensure all repositories adhere to organizational policies and legal requirements.

## Compliance Areas

### 1. License Compliance
Check licensing requirements:
- LICENSE file exists at repository root
- License type is approved for use
- All source files have license headers (where required)
- Third-party licenses are compatible

Allowed licenses (unless overridden):
- MIT
- Apache-2.0
- BSD-3-Clause
- ISC

Flag issues with:
- GPL (viral licensing concerns)
- AGPL (network copyleft)
- Unknown or custom licenses
- Missing license attribution

### 2. Copyright Notices
Verify copyright information:
- Copyright year is current or includes current year
- Copyright holder is correct (Dobeu Tech Solutions LLC)
- Format follows organizational standard

Standard format:
`Copyright (c) 2024-2025 Dobeu Tech Solutions LLC`

### 3. Required Files
Check for mandatory files:
- README.md - Project documentation
- LICENSE - License file
- CONTRIBUTING.md - Contribution guidelines (for public repos)
- SECURITY.md - Security policy (for public repos)
- .gitignore - Git ignore patterns
- CHANGELOG.md - Version history

### 4. Git Workflow Compliance
Verify git conventions:
- Branch naming follows pattern (feature/, bugfix/, etc.)
- Commit messages follow conventional commits
- No direct commits to main/master
- PR template exists and is used

Branch pattern: `^(feature|bugfix|hotfix|release|chore)/[a-z0-9-]+$`
Commit pattern: `^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{10,}$`

### 5. Code of Conduct
For public repositories:
- CODE_OF_CONDUCT.md exists
- References appropriate conduct standards

## Output Format
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "critical|high|medium|low|info",
            "file": "path/to/file or N/A",
            "line": null,
            "message": "LICENSE file missing",
            "rule_id": "COMP001",
            "category": "licensing",
            "remediation": "Add LICENSE file with MIT license text"
        }
    ],
    "summary": "Found 4 compliance issues: 1 critical, 2 high, 1 medium"
}

## Severity Guidelines
- CRITICAL: Missing license, GPL dependency in proprietary code
- HIGH: Outdated copyright, missing required files
- MEDIUM: Branch naming violations, missing optional files
- LOW: Minor convention deviations
- INFO: Suggestions for improvement
"""

    # Required files by project type
    REQUIRED_FILES = {
        "all": ["README.md", "LICENSE", ".gitignore"],
        "public": ["CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"],
        "python": ["pyproject.toml", "requirements.txt"],
        "node": ["package.json"],
    }

    # Allowed licenses
    DEFAULT_ALLOWED_LICENSES = ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "MPL-2.0"]

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the compliance agent."""
        self.standards = standards or StandardsConfig()
        self.allowed_licenses = (
            self.standards.allowed_licenses or self.DEFAULT_ALLOWED_LICENSES
        )

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform compliance scan on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with compliance issues found
        """
        logger.info(f"ComplianceAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive compliance scan of the repository at {repo_path}.

Configuration:
- Allowed licenses: {', '.join(self.allowed_licenses)}
- Branch naming pattern: {self.standards.branch_naming_pattern}
- Commit message pattern: {self.standards.commit_message_pattern}

Check for:
1. LICENSE file exists and contains allowed license
2. README.md exists and is not empty
3. CHANGELOG.md exists (if configured)
4. Copyright notices are current (include 2025)
5. License headers in source files (if required)
6. Git branch names follow convention
7. Recent commit messages follow conventional commits

Use Glob to find files, Read to examine contents.
Use Bash with git commands to check branch names and commit messages.

Provide your findings as structured JSON following the output format
in your system prompt.
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Glob", "Grep", "Bash"],
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Compliance scan failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Compliance scan failed: {e}",
            }

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse agent response to extract structured findings."""
        import json

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
                "summary": "Failed to parse compliance scan response",
            }

    async def check_required_files(self, repo_path: Path) -> list[dict[str, Any]]:
        """
        Quick check for required files without full agent invocation.

        Args:
            repo_path: Path to the repository

        Returns:
            List of missing required files
        """
        issues = []

        for filename in self.REQUIRED_FILES["all"]:
            file_path = repo_path / filename
            if not file_path.exists():
                issues.append({
                    "severity": "high" if filename in ["LICENSE", "README.md"] else "medium",
                    "file": filename,
                    "message": f"Required file missing: {filename}",
                    "rule_id": "COMP001",
                    "category": "required_files",
                    "remediation": f"Create {filename} file",
                })

        return issues

    async def check_license_compatibility(
        self,
        repo_path: Path,
        dependencies: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """
        Check dependency licenses for compatibility.

        Args:
            repo_path: Path to the repository
            dependencies: List of dependencies with license info

        Returns:
            List of license compatibility issues
        """
        issues = []

        for dep in dependencies:
            license_id = dep.get("license", "Unknown")
            if license_id not in self.allowed_licenses and license_id != "Unknown":
                issues.append({
                    "severity": "high",
                    "file": "package dependencies",
                    "message": f"Dependency '{dep.get('name')}' has non-allowed license: {license_id}",
                    "rule_id": "COMP002",
                    "category": "licensing",
                    "remediation": f"Review license compatibility or find alternative to {dep.get('name')}",
                })

        return issues
