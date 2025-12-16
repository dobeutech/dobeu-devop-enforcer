"""
Testing Agent - Analyzes test coverage and test quality.

Responsibilities:
- Verify test coverage meets minimum thresholds
- Identify untested critical paths
- Check for test anti-patterns (flaky tests, no assertions)
- Ensure integration and unit test separation
- Validate test naming conventions
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class TestingAgent:
    """
    Test quality and coverage analysis agent.

    Ensures adequate test coverage and identifies testing
    anti-patterns that could lead to unreliable test suites.
    """

    SYSTEM_PROMPT = """\
You are a testing quality agent for Dobeu Tech Solutions LLC. Your mission is to
ensure test suites are comprehensive, reliable, and maintainable.

## Analysis Areas

### 1. Test Coverage
Verify coverage meets requirements:
- Overall coverage percentage (default: 80%)
- Critical path coverage (should be higher)
- New code coverage (should be 100%)
- Branch coverage (not just line coverage)

Check for:
- Coverage reports (coverage.xml, lcov.info)
- Coverage configuration (pytest-cov, nyc, etc.)
- CI coverage gates

### 2. Untested Critical Paths
Identify high-risk untested code:
- Authentication/authorization logic
- Payment processing
- Data validation
- Error handling paths
- Security-sensitive operations

Flag functions/classes with:
- High cyclomatic complexity but low coverage
- Security annotations but no tests
- Public API endpoints without tests

### 3. Test Anti-Patterns
Detect problematic test patterns:
- Tests without assertions
- Sleep-based timing (flaky tests)
- Hardcoded test data that can expire
- Tests depending on execution order
- Overly broad exception catches in tests
- Missing cleanup/teardown
- Commented-out tests
- `skip` decorators without reason

### 4. Test Organization
Verify proper structure:
- Unit tests vs integration tests separated
- Test files mirror source structure
- Fixtures properly scoped
- Mocks used appropriately (not excessively)

### 5. Test Naming
Check naming conventions:
- Test functions start with `test_`
- Descriptive names indicating what's tested
- Test classes mirror source classes
- Test files named `test_*.py` or `*_test.py`

## Output Format
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "high|medium|low|info",
            "file": "tests/test_auth.py",
            "line": 42,
            "message": "Test has no assertions",
            "rule_id": "TEST001",
            "category": "anti-pattern",
            "remediation": "Add assertion to verify expected behavior"
        }
    ],
    "metrics": {
        "coverage_percent": 75,
        "test_count": 150,
        "files_without_tests": ["src/auth.py", "src/payment.py"]
    },
    "summary": "Coverage 75% (below 80% threshold), 3 anti-patterns found"
}

## Severity Guidelines
- HIGH: Coverage below threshold, untested critical paths
- MEDIUM: Test anti-patterns, missing integration tests
- LOW: Naming convention violations, organization issues
- INFO: Suggestions for improvement
"""

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the testing agent."""
        self.standards = standards or StandardsConfig()

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform test quality scan on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with testing issues found
        """
        logger.info(f"TestingAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive test quality scan of the repository at {repo_path}.

Configuration:
- Minimum coverage: {self.standards.min_coverage_percent}%
- Require unit tests: {self.standards.require_unit_tests}
- Require integration tests: {self.standards.require_integration_tests}

Check for:
1. Test coverage (look for coverage reports or run coverage)
2. Test anti-patterns (no assertions, sleeps, etc.)
3. Critical paths without tests (auth, payment, etc.)
4. Test organization (unit vs integration separation)
5. Test naming conventions

Use Glob to find test files, Read to examine them.
Use Bash to run test discovery or coverage if possible.

Focus especially on:
- tests/ directory structure
- pytest.ini or pyproject.toml [tool.pytest] config
- coverage configuration
- Files that should have tests but don't

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
            logger.error(f"Testing scan failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Testing scan failed: {e}",
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
                "summary": "Failed to parse testing scan response",
            }

    async def run_tests(self, repo_path: Path) -> dict[str, Any]:
        """
        Run the test suite and collect results.

        Args:
            repo_path: Path to the repository

        Returns:
            Test execution results
        """
        logger.info(f"TestingAgent running tests in {repo_path}")

        prompt = f"""\
Run the test suite in the repository at {repo_path}.

1. First, identify the test framework (pytest, jest, etc.)
2. Run the tests with coverage if possible
3. Report results including:
   - Number of tests passed/failed/skipped
   - Coverage percentage
   - Any test failures with details

For Python: Try `pytest --cov -v`
For Node: Try `npm test` or `npm run test:coverage`
"""

        try:
            response_text = ""
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=self.SYSTEM_PROMPT,
                    allowed_tools=["Read", "Glob", "Bash"],
                    cwd=str(repo_path),
                    permission_mode="bypassPermissions",
                ),
            ):
                if hasattr(message, "content"):
                    response_text += str(message.content)

            return {"status": "success", "output": response_text}

        except Exception as e:
            logger.error(f"Test run failed: {e}")
            return {"status": "error", "error": str(e)}
