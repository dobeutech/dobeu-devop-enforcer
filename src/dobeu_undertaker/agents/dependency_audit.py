"""
Dependency Audit Agent - Audits dependencies for vulnerabilities and version policies.

Responsibilities:
- Scan for known CVEs in dependencies
- Identify outdated packages
- Check for deprecated dependencies
- Verify dependency version pinning
- Detect unnecessary or duplicate dependencies
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class DependencyAuditAgent:
    """
    Dependency security and policy audit agent.

    Scans dependencies for known vulnerabilities, checks for
    outdated packages, and ensures version policies are followed.
    """

    SYSTEM_PROMPT = """\
You are a dependency audit agent for Dobeu Tech Solutions LLC. Your mission is to
ensure all dependencies are secure, up-to-date, and properly managed.

## Audit Areas

### 1. Vulnerability Scanning
Check for known vulnerabilities:
- CVEs in current dependency versions
- Security advisories from package registries
- Known malicious packages

Tools to use:
- Python: `pip-audit`, `safety check`
- Node: `npm audit`, `yarn audit`
- Check GitHub Advisory Database

### 2. Outdated Dependencies
Identify packages needing updates:
- Major version behind (potential breaking changes)
- Minor version behind (missing features)
- Patch version behind (missing bug fixes)
- Dependencies past end-of-life

Report:
- Current version vs latest version
- Age of current version
- Whether update includes security fixes

### 3. Deprecated Packages
Check for deprecated dependencies:
- Packages marked deprecated on registry
- Packages with archived repositories
- Packages with no updates in >2 years
- Packages with known replacements

### 4. Version Pinning
Verify proper version management:
- Lock file exists and is up-to-date
- Version ranges are appropriate
- No floating versions (>= or *)
- Hash verification where supported

### 5. Dependency Health
Check overall dependency health:
- Unnecessary dependencies (unused)
- Duplicate dependencies
- Dependencies with many dependencies (bloat)
- Dependencies from untrusted sources

## Output Format
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "critical|high|medium|low|info",
            "file": "package.json",
            "line": null,
            "message": "CVE-2024-1234 in lodash@4.17.20",
            "rule_id": "DEP001",
            "category": "vulnerability",
            "remediation": "Upgrade lodash to 4.17.21 or later",
            "cve": "CVE-2024-1234",
            "affected_package": "lodash",
            "current_version": "4.17.20",
            "fixed_version": "4.17.21"
        }
    ],
    "summary": "Found 2 vulnerabilities (1 high, 1 medium), 15 outdated packages"
}

## Severity Guidelines
- CRITICAL: Known exploited vulnerabilities, RCE CVEs
- HIGH: High-severity CVEs, severely outdated packages
- MEDIUM: Medium CVEs, deprecated packages
- LOW: Minor outdated packages, version pinning issues
- INFO: Dependency health suggestions
"""

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the dependency audit agent."""
        self.standards = standards or StandardsConfig()

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform dependency audit on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with dependency issues found
        """
        logger.info(f"DependencyAuditAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive dependency audit of the repository at {repo_path}.

Configuration:
- Max dependency age: {self.standards.max_dependency_age_days} days
- Block vulnerable deps: {self.standards.block_vulnerable_deps}
- Require lock file: {self.standards.require_lockfile}

Check for:
1. Vulnerability scanning (CVEs in dependencies)
2. Outdated packages (behind current versions)
3. Deprecated packages
4. Lock file presence and freshness
5. Unnecessary or duplicate dependencies

Steps:
1. First identify the package type:
   - Python: look for requirements.txt, pyproject.toml, Pipfile
   - Node: look for package.json, package-lock.json, yarn.lock
2. Run appropriate audit commands:
   - Python: `pip-audit` or `safety check` if available
   - Node: `npm audit` or `yarn audit`
3. Check for outdated packages:
   - Python: `pip list --outdated`
   - Node: `npm outdated`
4. Verify lock file exists and is committed

Use WebFetch to check for CVE information if needed.

Provide your findings as structured JSON following the output format
in your system prompt.
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Glob", "Grep", "Bash", "WebFetch"],
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Dependency audit failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Dependency audit failed: {e}",
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
                "summary": "Failed to parse dependency audit response",
            }

    async def update_dependencies(
        self,
        repo_path: Path,
        security_only: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Update dependencies (optionally security updates only).

        Args:
            repo_path: Path to the repository
            security_only: Only apply security updates
            dry_run: Show what would be updated without making changes

        Returns:
            Results of update operation
        """
        mode = "dry-run" if dry_run else "apply"
        scope = "security-only" if security_only else "all"
        logger.info(f"DependencyAuditAgent updating deps ({mode}, {scope}) in {repo_path}")

        prompt = f"""\
{"Analyze" if dry_run else "Update"} dependencies in the repository at {repo_path}.

Mode: {"Security updates only" if security_only else "All updates"}
{"Show what would be updated without making changes." if dry_run else "Apply updates."}

Steps:
1. Identify package manager
2. {"List" if dry_run else "Apply"} {"security " if security_only else ""}updates
3. {"Show" if dry_run else "Update"} lock file
4. Report what {"would be" if dry_run else "was"} changed

For Python:
- `pip install --upgrade <packages>` (or `poetry update`)

For Node:
- `npm update` or `npm audit fix {"--dry-run" if dry_run else ""}`
"""

        try:
            response_text = ""
            allowed = ["Read", "Glob", "Bash"]
            if not dry_run:
                allowed.extend(["Edit", "Write"])

            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=allowed,
                    cwd=str(repo_path),
                    permission_mode="acceptEdits" if not dry_run else "bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return {"status": "success", "output": response_text}

        except Exception as e:
            logger.error(f"Dependency update failed: {e}")
            return {"status": "error", "error": str(e)}
