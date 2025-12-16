"""
Validators for specific standards requirements.

Provides specialized validation functions for git workflows,
file structure, and other organizational standards.
"""

import re
from pathlib import Path
from typing import Any

from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


def validate_branch_naming(
    branch_name: str,
    pattern: str = r"^(feature|bugfix|hotfix|release|chore)/[a-z0-9-]+$",
) -> dict[str, Any]:
    """
    Validate a git branch name against the naming convention.

    Args:
        branch_name: Branch name to validate
        pattern: Regex pattern for valid branch names

    Returns:
        Validation result with status and message
    """
    # Skip protected branches
    protected_branches = ["main", "master", "develop", "staging", "production"]
    if branch_name in protected_branches:
        return {
            "valid": True,
            "message": f"Protected branch '{branch_name}' is allowed",
        }

    if re.match(pattern, branch_name):
        return {
            "valid": True,
            "message": f"Branch name '{branch_name}' follows convention",
        }

    # Provide helpful feedback
    prefix_match = re.match(r"^([a-z]+)/", branch_name)
    if prefix_match:
        prefix = prefix_match.group(1)
        if prefix not in ["feature", "bugfix", "hotfix", "release", "chore"]:
            return {
                "valid": False,
                "message": f"Invalid prefix '{prefix}'. Use: feature/, bugfix/, hotfix/, release/, chore/",
                "suggestion": f"feature/{branch_name.split('/')[-1] if '/' in branch_name else branch_name}",
            }

    return {
        "valid": False,
        "message": f"Branch name '{branch_name}' does not follow convention",
        "pattern": pattern,
        "examples": [
            "feature/add-user-auth",
            "bugfix/fix-login-error",
            "hotfix/security-patch",
            "release/v1.2.0",
            "chore/update-deps",
        ],
    }


def validate_commit_message(
    message: str,
    pattern: str = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{10,}$",
) -> dict[str, Any]:
    """
    Validate a git commit message against conventional commits format.

    Args:
        message: Commit message (first line) to validate
        pattern: Regex pattern for valid commit messages

    Returns:
        Validation result with status and message
    """
    # Get first line of commit message
    first_line = message.split("\n")[0].strip()

    if re.match(pattern, first_line):
        return {
            "valid": True,
            "message": "Commit message follows conventional commits format",
        }

    # Provide helpful feedback
    type_match = re.match(r"^([a-z]+)", first_line)
    if type_match:
        commit_type = type_match.group(1)
        valid_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
        if commit_type not in valid_types:
            return {
                "valid": False,
                "message": f"Invalid commit type '{commit_type}'",
                "valid_types": valid_types,
                "suggestion": f"feat: {first_line}" if len(first_line) >= 10 else None,
            }

    # Check if message is too short
    if len(first_line) < 15:
        return {
            "valid": False,
            "message": "Commit message too short (minimum 10 characters after type)",
            "current_length": len(first_line),
        }

    return {
        "valid": False,
        "message": "Commit message does not follow conventional commits format",
        "pattern": pattern,
        "examples": [
            "feat: add user authentication system",
            "fix(auth): resolve login timeout issue",
            "docs: update API documentation",
            "refactor(db): optimize query performance",
        ],
    }


def validate_pr_template(
    pr_body: str,
    required_sections: list[str] | None = None,
) -> dict[str, Any]:
    """
    Validate a pull request description against template requirements.

    Args:
        pr_body: Pull request body/description
        required_sections: List of required section headers

    Returns:
        Validation result with status and missing sections
    """
    if required_sections is None:
        required_sections = [
            "## Description",
            "## Changes",
            "## Testing",
        ]

    pr_body_lower = pr_body.lower()
    missing_sections = []

    for section in required_sections:
        # Check for section header (case-insensitive)
        if section.lower() not in pr_body_lower:
            # Also check without ## prefix
            section_name = section.replace("## ", "").replace("# ", "")
            if section_name.lower() not in pr_body_lower:
                missing_sections.append(section)

    if not missing_sections:
        return {
            "valid": True,
            "message": "PR description includes all required sections",
        }

    return {
        "valid": False,
        "message": "PR description is missing required sections",
        "missing_sections": missing_sections,
        "template": """## Description
<!-- Describe the changes in this PR -->

## Changes
<!-- List the specific changes made -->
-

## Testing
<!-- Describe how the changes were tested -->
-

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
""",
    }


def validate_file_structure(
    repo_path: Path,
    required_files: list[str] | None = None,
    required_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """
    Validate repository file structure against requirements.

    Args:
        repo_path: Path to the repository
        required_files: List of required files
        required_dirs: List of required directories

    Returns:
        Validation result with missing files/directories
    """
    if required_files is None:
        required_files = ["README.md", "LICENSE", ".gitignore"]

    if required_dirs is None:
        required_dirs = []

    missing_files = []
    missing_dirs = []

    for file_name in required_files:
        file_path = repo_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)

    for dir_name in required_dirs:
        dir_path = repo_path / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_name)

    if not missing_files and not missing_dirs:
        return {
            "valid": True,
            "message": "Repository has all required files and directories",
        }

    return {
        "valid": False,
        "message": "Repository is missing required files or directories",
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
    }


def validate_python_project(repo_path: Path) -> dict[str, Any]:
    """
    Validate Python project structure and configuration.

    Args:
        repo_path: Path to the repository

    Returns:
        Validation result with issues found
    """
    issues = []

    # Check for pyproject.toml or setup.py
    has_pyproject = (repo_path / "pyproject.toml").exists()
    has_setup = (repo_path / "setup.py").exists()

    if not has_pyproject and not has_setup:
        issues.append({
            "severity": "high",
            "message": "Missing pyproject.toml or setup.py",
            "remediation": "Add pyproject.toml for modern Python packaging",
        })
    elif has_setup and not has_pyproject:
        issues.append({
            "severity": "low",
            "message": "Using setup.py instead of pyproject.toml",
            "remediation": "Consider migrating to pyproject.toml",
        })

    # Check for requirements.txt or poetry.lock
    has_requirements = (repo_path / "requirements.txt").exists()
    has_poetry_lock = (repo_path / "poetry.lock").exists()
    has_pipfile_lock = (repo_path / "Pipfile.lock").exists()

    if not has_requirements and not has_poetry_lock and not has_pipfile_lock:
        issues.append({
            "severity": "high",
            "message": "No dependency lock file found",
            "remediation": "Add requirements.txt, poetry.lock, or Pipfile.lock",
        })

    # Check for tests directory
    has_tests = (repo_path / "tests").exists() or (repo_path / "test").exists()
    if not has_tests:
        issues.append({
            "severity": "medium",
            "message": "No tests directory found",
            "remediation": "Create tests/ directory with test files",
        })

    # Check for src layout
    has_src = (repo_path / "src").exists()
    if not has_src:
        issues.append({
            "severity": "info",
            "message": "Not using src/ layout",
            "remediation": "Consider using src/ layout for better isolation",
        })

    return {
        "valid": len([i for i in issues if i["severity"] in ["high", "critical"]]) == 0,
        "issues": issues,
        "project_type": "python",
    }


def validate_node_project(repo_path: Path) -> dict[str, Any]:
    """
    Validate Node.js project structure and configuration.

    Args:
        repo_path: Path to the repository

    Returns:
        Validation result with issues found
    """
    issues = []

    # Check for package.json
    package_json = repo_path / "package.json"
    if not package_json.exists():
        issues.append({
            "severity": "critical",
            "message": "Missing package.json",
            "remediation": "Run npm init or create package.json manually",
        })
        return {
            "valid": False,
            "issues": issues,
            "project_type": "node",
        }

    # Check for lock file
    has_package_lock = (repo_path / "package-lock.json").exists()
    has_yarn_lock = (repo_path / "yarn.lock").exists()
    has_pnpm_lock = (repo_path / "pnpm-lock.yaml").exists()

    if not has_package_lock and not has_yarn_lock and not has_pnpm_lock:
        issues.append({
            "severity": "high",
            "message": "No lock file found",
            "remediation": "Run npm install to generate package-lock.json",
        })

    # Check for .npmrc or engine requirements
    import json
    try:
        pkg_data = json.loads(package_json.read_text())

        if "engines" not in pkg_data:
            issues.append({
                "severity": "medium",
                "message": "No Node.js engine version specified",
                "remediation": 'Add "engines": {"node": ">=18"} to package.json',
            })

        if "scripts" not in pkg_data or "test" not in pkg_data.get("scripts", {}):
            issues.append({
                "severity": "medium",
                "message": "No test script defined",
                "remediation": 'Add "test" script to package.json',
            })

    except json.JSONDecodeError:
        issues.append({
            "severity": "critical",
            "message": "Invalid package.json",
            "remediation": "Fix JSON syntax in package.json",
        })

    return {
        "valid": len([i for i in issues if i["severity"] in ["high", "critical"]]) == 0,
        "issues": issues,
        "project_type": "node",
    }
