"""
Documentation Agent - Validates documentation completeness and quality.

Responsibilities:
- Verify README.md exists and is comprehensive
- Check API documentation completeness
- Validate inline code comments for complex logic
- Ensure CHANGELOG is maintained
- Check for broken documentation links
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentationAgent:
    """
    Documentation quality and completeness agent.

    Ensures all projects have adequate documentation for
    users, contributors, and maintainers.
    """

    SYSTEM_PROMPT = """\
You are a documentation agent for Dobeu Tech Solutions LLC. Your mission is to
ensure all projects have comprehensive, accurate, and maintainable documentation.

## Analysis Areas

### 1. README Quality
A good README should include:
- Project title and description
- Installation instructions
- Quick start / usage examples
- Configuration options
- API overview (if applicable)
- Contributing guidelines link
- License information

Check for:
- Empty or stub README
- Outdated installation instructions
- Missing examples
- Broken badges

### 2. API Documentation
For libraries and services:
- Public functions/methods documented
- Parameter descriptions
- Return value documentation
- Exception/error documentation
- Usage examples

For REST APIs:
- OpenAPI/Swagger spec exists
- Endpoints documented
- Request/response examples
- Authentication documented

### 3. Inline Comments
Code comments should:
- Explain "why" not "what"
- Document complex algorithms
- Note non-obvious side effects
- Reference tickets for workarounds
- Be up-to-date with code

Flag:
- Complex functions without comments
- Outdated comments (TODOs from years ago)
- Commented-out code blocks

### 4. Changelog
CHANGELOG.md should:
- Follow Keep a Changelog format
- Have entries for each version
- Categorize changes (Added, Changed, Fixed, etc.)
- Include dates

### 5. Link Validation
Check for broken links in:
- README.md
- Documentation files
- Code comments with URLs
- Badge images

## Output Format
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "high|medium|low|info",
            "file": "README.md",
            "line": 15,
            "message": "Broken link: https://example.com/old-url",
            "rule_id": "DOC001",
            "category": "broken_links",
            "remediation": "Update link or remove if obsolete"
        }
    ],
    "summary": "Documentation 70% complete, 2 broken links found"
}

## Severity Guidelines
- HIGH: Missing README, no API docs for public library
- MEDIUM: Incomplete README sections, broken links
- LOW: Missing examples, outdated changelog
- INFO: Documentation improvements
"""

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the documentation agent."""
        self.standards = standards or StandardsConfig()

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform documentation scan on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with documentation issues found
        """
        logger.info(f"DocumentationAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive documentation scan of the repository at {repo_path}.

Configuration:
- Require README: {self.standards.require_readme}
- Require CHANGELOG: {self.standards.require_changelog}
- Require docstrings: {self.standards.require_docstrings}

Check for:
1. README.md completeness (title, description, install, usage, etc.)
2. CHANGELOG.md exists and follows format
3. API documentation for public functions/classes
4. Inline comments for complex logic
5. Broken links in documentation

Use Read to examine documentation files.
Use Glob to find all markdown files.
Use WebFetch to check if links are valid.

Pay special attention to:
- Empty or placeholder documentation
- Outdated version references
- Missing code examples

Provide your findings as structured JSON following the output format
in your system prompt.
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Glob", "Grep", "WebFetch"],
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Documentation scan failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Documentation scan failed: {e}",
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
                "summary": "Failed to parse documentation scan response",
            }

    async def generate_readme(self, repo_path: Path) -> str:
        """
        Generate a README template based on repository analysis.

        Args:
            repo_path: Path to the repository

        Returns:
            Generated README content
        """
        logger.info(f"DocumentationAgent generating README for {repo_path}")

        prompt = f"""\
Analyze the repository at {repo_path} and generate a comprehensive README.md.

Examine:
1. Package files (package.json, pyproject.toml, etc.) for project info
2. Source code structure
3. Any existing documentation
4. Entry points and main functionality

Generate a README with:
- Project title and badges
- Description (inferred from code/config)
- Installation instructions (based on package manager)
- Quick start example
- Configuration options
- API overview
- Contributing section
- License section

Output ONLY the README markdown content.
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Glob", "Grep"],
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return response_text

        except Exception as e:
            logger.error(f"README generation failed: {e}")
            return f"# Project\n\nREADME generation failed: {e}"
