"""
Security Agent - Scans for security vulnerabilities and secrets.

Responsibilities:
- Detect hardcoded secrets (API keys, passwords, tokens)
- Identify OWASP Top 10 vulnerabilities
- Check for insecure coding patterns
- Verify secure configuration practices
- Scan for injection vulnerabilities (SQL, XSS, command)
"""

from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from dobeu_undertaker.config.schema import StandardsConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class SecurityAgent:
    """
    Security-focused scanning agent.

    Uses pattern matching and static analysis to identify
    security vulnerabilities in code and configuration.
    """

    SYSTEM_PROMPT = """\
You are a security-focused agent for Dobeu Tech Solutions LLC. Your mission is to
identify security vulnerabilities before they reach production.

## Scanning Focus Areas

### 1. Secrets Detection
Look for hardcoded sensitive data:
- API keys and tokens (AWS, Azure, GCP, Stripe, etc.)
- Passwords and credentials
- Private keys and certificates
- Database connection strings
- JWT secrets

Common patterns to flag:
- `password = "..."` or `api_key = "..."`
- Base64-encoded strings that might be credentials
- Environment variable names without proper masking
- Config files with sensitive values

### 2. OWASP Top 10
Check for common vulnerabilities:
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, NoSQL, OS command, LDAP)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software Integrity Failures
- A09: Logging Failures
- A10: SSRF

### 3. Insecure Patterns
Flag dangerous code patterns:
- `eval()`, `exec()` with user input
- Unsanitized SQL queries
- Disabled security headers
- Insecure deserialization
- Path traversal vulnerabilities
- Command injection via subprocess

### 4. Configuration Security
Check for misconfigurations:
- Debug mode in production
- CORS allow-all configurations
- Missing authentication on endpoints
- Insecure cookie settings
- Disabled TLS verification

## Output Format
Provide findings as JSON:
{
    "status": "passed|failed|warning",
    "issues": [
        {
            "severity": "critical|high|medium|low|info",
            "file": "path/to/file.py",
            "line": 42,
            "message": "Hardcoded API key detected",
            "rule_id": "SEC001",
            "category": "secrets",
            "remediation": "Move to environment variable or secrets manager",
            "cwe": "CWE-798"
        }
    ],
    "summary": "Found 3 security issues: 1 critical, 2 high"
}

## Severity Guidelines
- CRITICAL: Active secrets, RCE vulnerabilities, auth bypass
- HIGH: SQL injection, XSS, hardcoded credentials
- MEDIUM: Missing security headers, weak crypto
- LOW: Informational security improvements
- INFO: Best practice suggestions
"""

    # Common secret patterns to detect
    SECRET_PATTERNS = [
        r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        r"(?i)(secret|password|passwd|pwd)['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        r"(?i)bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+",
        r"(?i)(aws[_-]?access[_-]?key[_-]?id)['\"]?\s*[:=]\s*['\"]AKIA[A-Z0-9]{16}['\"]",
        r"(?i)(aws[_-]?secret[_-]?access[_-]?key)['\"]?\s*[:=]\s*['\"][a-zA-Z0-9/+=]{40}['\"]",
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        r"(?i)ghp_[a-zA-Z0-9]{36}",  # GitHub PAT
        r"(?i)sk-[a-zA-Z0-9]{48}",  # OpenAI API key
    ]

    # Dangerous function patterns
    DANGEROUS_PATTERNS = [
        (r"\beval\s*\(", "eval() usage", "SEC002"),
        (r"\bexec\s*\(", "exec() usage", "SEC003"),
        (r"subprocess\..*shell\s*=\s*True", "Shell injection risk", "SEC004"),
        (r"pickle\.loads?\(", "Insecure deserialization", "SEC005"),
        (r"yaml\.load\s*\([^)]*\)", "Unsafe YAML loading", "SEC006"),
        (r"\.format\s*\([^)]*\)\s*$", "Potential format string injection", "SEC007"),
    ]

    def __init__(self, standards: StandardsConfig | None = None) -> None:
        """Initialize the security agent."""
        self.standards = standards or StandardsConfig()

    async def scan(self, repo_path: Path) -> dict[str, Any]:
        """
        Perform security scan on a repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Scan results with issues found
        """
        logger.info(f"SecurityAgent scanning {repo_path}")

        prompt = f"""\
Perform a comprehensive security scan of the repository at {repo_path}.

Focus on:
1. Secrets detection - scan all files for hardcoded credentials
2. OWASP Top 10 vulnerabilities
3. Insecure coding patterns
4. Security misconfigurations

Use Grep to search for patterns like:
- Password/secret/key assignments
- eval/exec usage
- SQL string concatenation
- Subprocess shell=True

Use Read to examine suspicious files in detail.

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
            logger.error(f"Security scan failed: {e}")
            return {
                "status": "error",
                "issues": [],
                "summary": f"Security scan failed: {e}",
            }

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse agent response to extract structured findings."""
        import json

        # Try to extract JSON from response
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
                "summary": f"Failed to parse security scan response",
            }

    async def quick_secrets_scan(self, repo_path: Path) -> list[dict[str, Any]]:
        """
        Quick pattern-based secrets scan without full agent invocation.

        Args:
            repo_path: Path to scan

        Returns:
            List of potential secrets found
        """
        import re

        findings = []

        # Scan common file types
        for ext in [".py", ".js", ".ts", ".env", ".yaml", ".yml", ".json", ".xml"]:
            for file_path in repo_path.rglob(f"*{ext}"):
                if ".git" in str(file_path):
                    continue

                try:
                    content = file_path.read_text(errors="ignore")
                    for i, line in enumerate(content.split("\n"), 1):
                        for pattern in self.SECRET_PATTERNS:
                            if re.search(pattern, line):
                                findings.append({
                                    "severity": "critical",
                                    "file": str(file_path.relative_to(repo_path)),
                                    "line": i,
                                    "message": "Potential secret detected",
                                    "rule_id": "SEC001",
                                    "category": "secrets",
                                })
                except Exception:
                    pass

        return findings
