"""
Standards enforcement rules and engine.

Provides a rule-based system for defining and enforcing
organizational standards across repositories.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(str, Enum):
    """Rule categories."""

    SECURITY = "security"
    CODE_STYLE = "code_style"
    COMPLIANCE = "compliance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPENDENCIES = "dependencies"


@dataclass
class Issue:
    """A detected standards violation."""

    rule_id: str
    severity: Severity
    category: Category
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    remediation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "remediation": self.remediation,
            **self.metadata,
        }


@dataclass
class Rule:
    """
    A single standards enforcement rule.

    Rules can be pattern-based (regex) or function-based (custom logic).
    """

    id: str
    name: str
    description: str
    severity: Severity
    category: Category
    enabled: bool = True

    # For pattern-based rules
    pattern: str | None = None
    file_pattern: str = "*"  # Glob pattern for files to check

    # For function-based rules
    check_function: Callable[[Path, str], list[Issue]] | None = None

    # Remediation guidance
    remediation: str | None = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    def check_file(self, file_path: Path, content: str) -> list[Issue]:
        """
        Check a file against this rule.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of issues found
        """
        if not self.enabled:
            return []

        # Check if file matches the file pattern
        import fnmatch
        if not fnmatch.fnmatch(file_path.name, self.file_pattern):
            return []

        issues = []

        # Pattern-based check
        if self.pattern:
            for i, line in enumerate(content.split("\n"), 1):
                if re.search(self.pattern, line):
                    issues.append(Issue(
                        rule_id=self.id,
                        severity=self.severity,
                        category=self.category,
                        message=self.description,
                        file=str(file_path),
                        line=i,
                        remediation=self.remediation,
                    ))

        # Function-based check
        if self.check_function:
            issues.extend(self.check_function(file_path, content))

        return issues


@dataclass
class RuleSet:
    """A collection of related rules."""

    name: str
    description: str
    rules: list[Rule] = field(default_factory=list)
    enabled: bool = True

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the set."""
        self.rules.append(rule)

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule by ID."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False


class StandardsEngine:
    """
    Engine for running standards checks against repositories.

    Manages rule sets and coordinates checking across files.
    """

    def __init__(self) -> None:
        """Initialize the standards engine."""
        self.rule_sets: dict[str, RuleSet] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load built-in default rules."""
        # Security rules
        security_rules = RuleSet(
            name="security",
            description="Security-related rules",
            rules=[
                Rule(
                    id="SEC001",
                    name="Hardcoded Password",
                    description="Potential hardcoded password detected",
                    severity=Severity.CRITICAL,
                    category=Category.SECURITY,
                    pattern=r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
                    file_pattern="*.py",
                    remediation="Use environment variables or a secrets manager",
                ),
                Rule(
                    id="SEC002",
                    name="Hardcoded API Key",
                    description="Potential hardcoded API key detected",
                    severity=Severity.CRITICAL,
                    category=Category.SECURITY,
                    pattern=r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9]{16,}["\']',
                    remediation="Use environment variables or a secrets manager",
                ),
                Rule(
                    id="SEC003",
                    name="Eval Usage",
                    description="Use of eval() is dangerous",
                    severity=Severity.HIGH,
                    category=Category.SECURITY,
                    pattern=r'\beval\s*\(',
                    file_pattern="*.py",
                    remediation="Use ast.literal_eval() for safe evaluation or refactor",
                ),
                Rule(
                    id="SEC004",
                    name="Shell Injection Risk",
                    description="subprocess with shell=True is risky",
                    severity=Severity.HIGH,
                    category=Category.SECURITY,
                    pattern=r'subprocess\..*shell\s*=\s*True',
                    file_pattern="*.py",
                    remediation="Use shell=False and pass arguments as a list",
                ),
            ],
        )
        self.rule_sets["security"] = security_rules

        # Code style rules
        style_rules = RuleSet(
            name="code_style",
            description="Code style and formatting rules",
            rules=[
                Rule(
                    id="STYLE001",
                    name="Line Too Long",
                    description="Line exceeds maximum length",
                    severity=Severity.LOW,
                    category=Category.CODE_STYLE,
                    check_function=self._check_line_length,
                    remediation="Break line at appropriate point",
                ),
                Rule(
                    id="STYLE002",
                    name="Trailing Whitespace",
                    description="Line has trailing whitespace",
                    severity=Severity.LOW,
                    category=Category.CODE_STYLE,
                    pattern=r'\s+$',
                    remediation="Remove trailing whitespace",
                ),
                Rule(
                    id="STYLE003",
                    name="TODO Without Ticket",
                    description="TODO comment without ticket reference",
                    severity=Severity.INFO,
                    category=Category.CODE_STYLE,
                    pattern=r'#\s*TODO(?![:\s]*[A-Z]+-\d+)',
                    file_pattern="*.py",
                    remediation="Add ticket reference: # TODO: TICKET-123 description",
                ),
            ],
        )
        self.rule_sets["code_style"] = style_rules

        # Compliance rules
        compliance_rules = RuleSet(
            name="compliance",
            description="Compliance and policy rules",
            rules=[
                Rule(
                    id="COMP001",
                    name="Missing License Header",
                    description="File missing license header",
                    severity=Severity.MEDIUM,
                    category=Category.COMPLIANCE,
                    check_function=self._check_license_header,
                    remediation="Add license header to file",
                ),
            ],
        )
        self.rule_sets["compliance"] = compliance_rules

    def _check_line_length(
        self,
        file_path: Path,
        content: str,
        max_length: int = 100,
    ) -> list[Issue]:
        """Check for lines exceeding maximum length."""
        issues = []

        for i, line in enumerate(content.split("\n"), 1):
            if len(line) > max_length:
                issues.append(Issue(
                    rule_id="STYLE001",
                    severity=Severity.LOW,
                    category=Category.CODE_STYLE,
                    message=f"Line exceeds {max_length} characters (found {len(line)})",
                    file=str(file_path),
                    line=i,
                    remediation="Break line at appropriate point",
                ))

        return issues

    def _check_license_header(
        self,
        file_path: Path,
        content: str,
    ) -> list[Issue]:
        """Check for license header in source files."""
        # Only check source files
        if file_path.suffix not in [".py", ".js", ".ts", ".java", ".go"]:
            return []

        # Check first 20 lines for license/copyright
        first_lines = "\n".join(content.split("\n")[:20]).lower()

        if "copyright" not in first_lines and "license" not in first_lines:
            return [Issue(
                rule_id="COMP001",
                severity=Severity.MEDIUM,
                category=Category.COMPLIANCE,
                message="File missing license/copyright header",
                file=str(file_path),
                line=1,
                remediation="Add license header to file",
            )]

        return []

    def add_rule_set(self, rule_set: RuleSet) -> None:
        """Add a rule set to the engine."""
        self.rule_sets[rule_set.name] = rule_set

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule across all rule sets."""
        for rule_set in self.rule_sets.values():
            if rule_set.disable_rule(rule_id):
                return True
        return False

    def check_file(self, file_path: Path) -> list[Issue]:
        """
        Check a single file against all enabled rules.

        Args:
            file_path: Path to the file to check

        Returns:
            List of issues found
        """
        if not file_path.exists() or not file_path.is_file():
            return []

        try:
            content = file_path.read_text(errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []

        issues = []

        for rule_set in self.rule_sets.values():
            if not rule_set.enabled:
                continue

            for rule in rule_set.rules:
                try:
                    issues.extend(rule.check_file(file_path, content))
                except Exception as e:
                    logger.warning(f"Rule {rule.id} failed on {file_path}: {e}")

        return issues

    def check_repository(
        self,
        repo_path: Path,
        file_patterns: list[str] | None = None,
    ) -> list[Issue]:
        """
        Check all files in a repository.

        Args:
            repo_path: Path to the repository
            file_patterns: Optional list of glob patterns to check

        Returns:
            List of all issues found
        """
        if file_patterns is None:
            file_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go"]

        issues = []

        for pattern in file_patterns:
            for file_path in repo_path.glob(pattern):
                # Skip common non-source directories
                if any(
                    part in file_path.parts
                    for part in [".git", "node_modules", "__pycache__", ".venv", "venv"]
                ):
                    continue

                issues.extend(self.check_file(file_path))

        return issues
