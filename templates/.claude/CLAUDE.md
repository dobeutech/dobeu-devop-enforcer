# Dobeu Tech Solutions - Repository Instructions

## Overview
This repository is managed by Dobeu Tech Solutions LLC and follows organizational standards enforced by Dobeu Undertaker.

## Coding Standards

### Code Style
- Line length: 100 characters maximum
- Indentation: 4 spaces (Python), 2 spaces (TypeScript/JavaScript)
- Use double quotes for strings (Python), single quotes (JS/TS)

### Naming Conventions
- Files: `snake_case.py` or `kebab-case.ts`
- Classes: `PascalCase`
- Functions: `snake_case` (Python), `camelCase` (JS/TS)
- Constants: `UPPER_SNAKE_CASE`

### Git Workflow
- Branch naming: `feature/`, `bugfix/`, `hotfix/`, `release/`, `chore/`
- Commit messages: Follow Conventional Commits format
  - `feat: add user authentication`
  - `fix(auth): resolve login timeout`
  - `docs: update API documentation`

## Testing Requirements
- Minimum 80% test coverage
- Unit tests required for all new functionality
- Integration tests for API endpoints

## Documentation
- All public functions must have docstrings
- README.md must include installation and usage instructions
- CHANGELOG.md must be updated for each release

## Security
- No hardcoded secrets or credentials
- Use environment variables for configuration
- All dependencies must be from approved licenses

## Before Committing
1. Run linting: `ruff check .` or `eslint .`
2. Run tests: `pytest` or `npm test`
3. Check for secrets: No API keys or passwords in code
4. Update CHANGELOG if making significant changes

## Compliance Scanning
This repository is automatically scanned by Dobeu Undertaker on:
- Pull requests
- Commits to main branch

Critical and high-severity issues will block merges.
