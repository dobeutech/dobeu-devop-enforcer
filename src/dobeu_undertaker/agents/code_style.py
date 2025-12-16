"""
Code Style Agent - Enforces formatting, linting, and naming conventions.

Responsibilities:
- Verify code formatting matches configured style
- Check naming conventions (files, variables, functions, classes)
- Identify code smells and anti-patterns
- Ensure import ordering and organization
- Validate type annotations where required
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class CodeStyleAgent:
    """
    Code quality and style enforcement agent.

    Ensures consistent code formatting and naming conventions
    across all repositories in the organization.
    """

    SYSTEM_PROMPT = """\
You are a code quality agent for Dobeu Tech Solutions LLC. Your mission is to
enforce consistent coding standards across all codebases.

## Enforcement Areas

### 1. Code Formatting
Check that code follows the configured style:
- Line length limits (default: 100 characters)
- Indentation (spaces vs tabs, size)
- Trailing whitespace
- Blank line conventions
- Quote style consistency

For Python: Check ruff/black compatibility
For JavaScript/TypeScript: Check prettier compatibility

### 2. Naming Conventions
Verify naming follows standards:
- Files: snake_case.py, kebab-case.ts, PascalCase.tsx (configurable)
- Classes: PascalCase
- Functions: snake_case (Python), camelCase (JS/TS)
- Constants: UPPER_SNAKE_CASE
- Private members: _leading_underscore

Flag violations like:
- `class my_class` (should be MyClass)
- `def MyFunction()` (should be my_function)
- `myVar = ...` in Python (should be my_var)

### 3. Code Smells
Identify anti-patterns:
- Functions over 50 lines
- Files over 500 lines
- Deep nesting (>4 levels)
- Too many parameters (>5)
- Duplicate code blocks
- Magic numbers/strings
- Dead code (unused imports, variables, functions)

### 4. Import Organization
Check import structure:
- Standard library first
- Third-party packages second
- Local imports third
- Alphabetical ordering within groups
- No wildcard imports (from x import *)
- No circular imports

### 5. Type Annotations
For typed languages or typed Python:
- Public functions should have type hints
- Return types should be specified
- Generic types properly parameterized
- No `Any` without justification

## Output Format
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "high|medium|low|info",
            "file": "src/module.py",
            "line": 42,
            "message": "Line exceeds 100 characters (found 127)",
            "rule_id": "STYLE001",
            "category": "formatting",
            "remediation": "Break line at appropriate point"
        }
    ],
    "summary": "Found 15 style issues: 2 high, 8 medium, 5 low"
}

## Severity Guidelines
- HIGH: Naming convention violations, missing type hints on public API
- MEDIUM: Line length, import ordering, excessive complexity
- LOW: Whitespace issues, minor formatting
- INFO: Suggestions for improvement
"""

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the code style agent."""
        self.standards = standards or StandardsConfig()

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform code style scan on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with style issues found
        """
        logger.info(f"CodeStyleAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive code style scan of the repository at {repo_path}.

Configuration:
- Line length: {self.standards.line_length}
- Indent size: {self.standards.indent_size}
- Quote style: {self.standards.quote_style}
- File naming: {self.standards.file_naming}
- Class naming: {self.standards.class_naming}
- Function naming: {self.standards.function_naming}

Focus on:
1. Files violating naming conventions
2. Lines exceeding length limit
3. Improper import organization
4. Missing type annotations on public functions
5. Code complexity issues

Use Glob to find source files, then Read to examine them.
Use Bash to run linters if available (ruff, eslint, etc.).

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
            logger.error(f"Code style scan failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Code style scan failed: {e}",
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
                "summary": "Failed to parse code style scan response",
            }

    async def auto_fix(self, repo_path: Path, dry_run: bool = False) -> dict[str, Any]:
        """
        Automatically fix style issues where possible.

        Args:
            repo_path: Path to the repository
            dry_run: If True, show what would be fixed without making changes

        Returns:
            Results of auto-fix operation
        """
        mode = "dry-run" if dry_run else "fix"
        logger.info(f"CodeStyleAgent auto-fix ({mode}) on {repo_path}")

        prompt = f"""\
{"Analyze" if dry_run else "Fix"} code style issues in the repository at {repo_path}.

{"Show what would be fixed without making changes." if dry_run else "Apply automatic fixes for:"}
1. Import sorting and organization
2. Trailing whitespace removal
3. Line length (where automatically fixable)
4. Quote style consistency

If available, run:
- ruff format {"--check" if dry_run else ""} (Python)
- prettier {"--check" if dry_run else "--write"} (JS/TS)

Report what {"would be" if dry_run else "was"} fixed.
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Edit", "Write", "Bash"] if not dry_run else ["Read", "Glob", "Bash"],
                    cwd=str(repo_path),
                    permission_mode="acceptEdits" if not dry_run else "bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return {"status": "success", "output": response_text}

        except Exception as e:
            logger.error(f"Code style auto-fix failed: {e}")
            return {"status": "error", "error": str(e)}
